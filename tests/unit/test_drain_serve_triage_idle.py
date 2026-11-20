# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test drain serve triage idle
# relates: [clutch/__main__.py, clutch/box.py, clutch/config.py, clutch/control.py, clutch/journal.py, clutch/triage.py, tests/fakes.py]
# owner: engine
# verified: 0a308920
# hash: 63cd831aadbd8aebfcc951ac3cb625e67d32add7f8823f9bd833fa402cc0519f
from unittest.mock import AsyncMock

import pytest

from clutch.box import UnknownBoxId
from clutch.control import ControlInbox
from clutch.journal import EventType
from tests.fakes import FakeClock, FakeJournal


def inbox_with_decision(lifecycle="old"):
    journal = FakeJournal(FakeClock())
    journal.append(
        EventType.SIGNAL,
        {
            "kind": "control_decision",
            "request_id": "req",
            "lifecycle_id": lifecycle,
            "verb": "triage",
            "hold_id": None,
            "ids": ["box-000001"],
            "actor": "operator",
            "decision": "accepted",
            "reason": "matching lifecycle",
        },
    )
    return ControlInbox(journal=journal, lifecycle_id="live", holds=set, apply=lambda _: None, files=list, read=lambda _: b"", known=lambda _: False)


@pytest.mark.asyncio
async def test_settle_once_across_lifecycles():
    inbox = inbox_with_decision()
    run = AsyncMock()
    await inbox.settle_triage(run)
    await inbox.settle_triage(run)
    run.assert_awaited_once_with(("box-000001",))


@pytest.mark.asyncio
async def test_empty_and_refused():
    inbox = inbox_with_decision()
    run = AsyncMock(side_effect=UnknownBoxId("unknown"))
    await inbox.settle_triage(run)
    await inbox.settle_triage(run)
    run.assert_awaited_once()
    empty = inbox_with_decision()
    empty.journal = FakeJournal(FakeClock())
    run.reset_mock()
    await empty.settle_triage(run)
    run.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ["drain", "serve"])
async def test_idle_calls_requested_pass(tmp_path, monkeypatch, engine):
    from types import SimpleNamespace

    from clutch import __main__ as entry
    from clutch import triage
    from clutch.config import Caps
    from tests.unit.test_supervise_idle_hooks import Checkout, EndPoll, drain_rig, serve_rig
    from tests.unit.test_supervise_idle_point import Journal

    seen = []
    provider = object()
    llm = object()

    async def preflight(checkout, session):
        assert session is provider
        return llm

    async def triage_pass(checkout, supplied, ids):
        seen.append((supplied, ids))

    async def settle(run):
        await run(("box-000001",))

    monkeypatch.setattr(entry, "_preflighted_llm", preflight)
    monkeypatch.setattr(triage, "triage_pass", triage_pass)
    c = Checkout(
        tmp_path,
        Journal(),
        SimpleNamespace(caps=Caps()),
        SimpleNamespace(inbox=SimpleNamespace(settle_triage=settle), providers=provider, projection=SimpleNamespace(stop_requested=False, retro_id=None), storm_holds=lambda: {}),
    )
    if engine == "drain":
        d = drain_rig(tmp_path, monkeypatch, c, object())
        d.last_dispatched = None
        await d.run()
    else:
        s = serve_rig(tmp_path, monkeypatch, c, None)
        s.control.inbox.settle_triage = settle
        s.control.providers = provider
        with pytest.raises(EndPoll):
            await s.dispatch()
    assert seen == [(llm, frozenset({"box-000001"}))]
