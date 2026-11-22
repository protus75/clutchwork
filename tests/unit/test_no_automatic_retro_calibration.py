"""Overdue windows never schedule maintenance or hold ticket admission."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that overdue retro and calibration never run automatically or hold admission in serve or drain, and that operator-requested retros run once under the right boundaries
# relates: [clutch/calibration.py, clutch/drain.py, clutch/serve.py, tests/unit/test_serve_dispatch_containment.py, tests/unit/test_status_overdue.py]
# owner: engine
# verified: 45e4e081
# hash: b38034dbd7d679caf54a62e98722a1cec682bf33ab37800846aa04d6611d8433

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from clutch import calibration, drain, serve
from tests.unit.test_serve_dispatch_containment import rig
from tests.unit.test_status_overdue import history, settings
from tests.unit.test_supervise_idle_hooks import Checkout, EndPoll, drain_rig, serve_rig


@pytest.mark.asyncio
async def test_serve_dispatch_and_admission_while_overdue(monkeypatch):
    journal = history(merges=25, calls=100)
    c = Checkout(Path("/repo"), journal, settings())
    owner = serve_rig(c.repo, monkeypatch, c, None)
    log = Mock()
    owner.log = log
    owner.served_retro_id = None
    owner.control.projection.retro_id = None
    owner.control.providers = SimpleNamespace(active=False)
    owner.control.admission = None
    owner.writers, owner.upgrade = {}, None
    owner.storm = SimpleNamespace(held_stages=lambda: {})
    forbidden = Mock(side_effect=AssertionError("automatic maintenance"))
    monkeypatch.setattr(serve, "Retro", forbidden)
    monkeypatch.setattr(calibration, "calibrate", forbidden)
    monkeypatch.setattr(serve, "supervise_idle", AsyncMock())
    before = journal.read()
    with pytest.raises(EndPoll):
        await owner.dispatch()
    # Wrong: block admission for an overdue count.
    assert owner.select(SimpleNamespace(stem="eligible"), "implement") is True
    owner.core.scheduler.dispatch_next.assert_awaited_once()
    # Wrong: retain the automatic maintenance attributes/helper.
    assert [name for name in ("check_retro", "retro_due", "retro_checked") if hasattr(owner, name)] == []
    assert not hasattr(calibration, "calibrate_when_due")
    # Wrong: start maintenance, append a calibration signal or log retro_check.
    forbidden.assert_not_called()
    assert journal.read() == before
    assert log.mock_calls == []
    # Wrong: treat overdue alone as a request, ignore a request or serve it twice.
    assert owner.retro_pending() is False
    owner.control.projection.retro_id = "requested"
    assert owner.retro_pending() is True
    assert owner.select(SimpleNamespace(stem="eligible"), "implement") is False
    owner.served_retro_id = "requested"
    assert owner.retro_pending() is False


@pytest.mark.asyncio
async def test_drain_between_tickets_does_not_run_maintenance(monkeypatch):
    journal = history(merges=25, calls=100)
    control = SimpleNamespace(inbox=SimpleNamespace(settle_triage=AsyncMock()), projection=SimpleNamespace(stop_requested=False, retro_id=None))
    c = Checkout(Path("/repo"), journal, settings(), control)
    owner = drain_rig(c.repo, monkeypatch, c, object())
    owner.last_dispatched = "merged-24"
    owner.served_retro_id = None
    owner.retro = AsyncMock(side_effect=AssertionError("automatic retro"))
    owner._run_retro = AsyncMock(side_effect=AssertionError("automatic retro check"))
    forbidden = Mock(side_effect=AssertionError("automatic calibration"))
    monkeypatch.setattr(calibration, "calibrate", forbidden)
    log = Mock()
    monkeypatch.setattr(drain, "engine_log", lambda *a: log)
    monkeypatch.setattr(drain, "supervise_idle", AsyncMock())
    before = journal.read()
    await owner.run()
    # Wrong: skip the between-ticket boundary, invoke its retro or calibrate.
    drain.supervise_idle.assert_awaited_once()
    owner._run_retro.assert_not_awaited()
    owner.retro.assert_not_awaited()
    forbidden.assert_not_called()
    assert journal.read() == before
    assert log.mock_calls == []


@pytest.mark.asyncio
async def test_serve_requested_retro_runs_under_mutation_lock(monkeypatch):
    c = Checkout(Path("/repo"), history(), settings())
    owner = serve_rig(c.repo, monkeypatch, c, None)
    owner.served_retro_id = None
    owner.retro = None
    calls = []

    class RequestedRetro:
        def __init__(self, checkout, pipeline):
            calls.append(("construct", owner.locked))

        async def __call__(self, *, forced):
            calls.append(("run", owner.locked, forced))

    monkeypatch.setattr(serve, "Retro", RequestedRetro)
    await owner.run_retro("manual")
    # Wrong: drop the request, run outside the lock or use the automatic due path.
    assert calls == [("construct", True), ("run", True, True)]
    # Wrong: leave a completed request pending or retain its active hook.
    assert owner.served_retro_id == "manual" and owner.retro is None


@pytest.mark.asyncio
async def test_drain_requested_retro_runs_once_between_tickets(monkeypatch):
    control = SimpleNamespace(inbox=SimpleNamespace(settle_triage=AsyncMock()), projection=SimpleNamespace(stop_requested=False, retro_id="manual"))
    c = SimpleNamespace(repo=Path("/repo"), journal=history(merges=25, calls=100), config=settings(), control=control, env={}, clock=None, sleep=None, git=None, fs=None)
    owner = drain_rig(c.repo, monkeypatch, c, object())
    owner.last_dispatched, owner.served_retro_id = "merged-24", None
    calls = []

    async def run(*, forced):
        calls.append(("retro", forced))

    async def controlled(task, *args):
        return await task

    async def supervise(*args):
        calls.append(("supervise",))

    owner.retro = AsyncMock(side_effect=run)
    owner.retro.due = True
    owner._await_controlled = controlled
    monkeypatch.setattr(drain.Redactor, "from_config", lambda *a: None)
    monkeypatch.setattr(drain, "engine_log", lambda *a: Mock())
    monkeypatch.setattr(drain, "supervise_idle", supervise)
    # A repeated request must fail deterministically instead of looping.
    owner._select = Mock(side_effect=[(None, False), (None, False), AssertionError("request did not quiesce")])
    await owner.run()
    await owner.run()
    # Wrong: omit a request, call it unforced, run after supervision or repeat it.
    assert calls == [("retro", True), ("supervise",), ("supervise",)]
    assert owner.served_retro_id == "manual"


@pytest.mark.asyncio
async def test_serve_constructor_has_no_automatic_state(rig):
    # Wrong: remove the methods but retain automatic trigger state on new engines.
    assert not hasattr(type(rig.owner), "check_retro")
    assert [name for name in ("retro_due", "retro_checked") if hasattr(rig.owner, name)] == []
