"""Serve contains ticket failures without containing consumer failures."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that Serve contains a ticket's dispatch exception as an infra_error terminal while other tickets complete, but lets stop, cancellation and consumer failures propagate; also provides the shared serve dispatch rig fixture
# relates: [clutch/__main__.py, clutch/daemon.py, clutch/journal.py, clutch/runner.py, clutch/scheduler.py, clutch/serve.py, tests/fakes.py, tests/git_fake.py]
# owner: engine
# verified: 333d8906
# hash: 2ecee8cefd07c2885ebb581332f8c90446d1757d303b0706498cb097046fe8c6

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from clutch import __main__ as cli
from clutch import serve
from clutch.daemon import TicketWriter
from clutch.journal import EventType
from clutch.runner import Checkout
from clutch.scheduler import Scheduler
from clutch.tickets import parse_ticket
from tests.fakes import FakeClock, FakeJournal
from tests.git_fake import GitFake
from tests.unit.test_parse_ticket_evidence import ticket_text


@pytest_asyncio.fixture
async def rig(monkeypatch, tmp_path):
    (tmp_path / "context.txt").write_text("context")
    text = ticket_text("feature")
    journal = FakeJournal()
    core = MagicMock()
    core.control._recover = [].clear
    scheduler = Scheduler.__new__(Scheduler)
    scheduler.failures, scheduler.pending = [], {}
    core.scheduler = scheduler
    prepared = {}

    def build(*args, **kwargs):
        prepared["call"] = kwargs["prepare"]
        return core

    monkeypatch.setattr(cli, "build_daemon_core", build)
    monkeypatch.setattr(cli, "build_notifications", MagicMock())
    log = MagicMock()
    monkeypatch.setattr(serve, "engine_log", lambda *args: log)
    monkeypatch.setattr(serve.Redactor, "from_config", MagicMock())
    checkout = Checkout(repo=tmp_path, config=SimpleNamespace(state_dir=tmp_path), env={}, exec_=None, fs=MagicMock(), clock=FakeClock(), journal=journal, git=GitFake(rev_parse="sha", _run=text))
    callback = MagicMock(spec=TicketWriter)
    callback.ctx = SimpleNamespace(boundary=SimpleNamespace())
    callback.queue = SimpleNamespace(pending={}, contexts={})
    callback.continuations = {}

    async def prepare(local):
        return callback

    owner = serve.Serve(checkout, read=lambda _: None, stems=lambda: [], prepare=prepare)
    owner.select = lambda *_: True
    owner.check_retro = AsyncMock()
    dispatch = await prepared["call"](checkout)
    return SimpleNamespace(owner=owner, dispatch=dispatch, callback=callback, journal=journal, scheduler=scheduler, log=log, text=text, repo=tmp_path)


def bodies(rig, stem):
    return [event.body for event in rig.journal.read() if event.ticket == stem and event.type == EventType.STATE_TRANSITION]


@pytest.mark.asyncio
async def test_raises_contained_while_other_ticket_completes(rig):
    a, b = parse_ticket("aa", rig.text, rig.repo), parse_ticket("bb", rig.text, rig.repo)
    entered, release = asyncio.Event(), asyncio.Event()

    async def run(ticket):
        if ticket.stem == "aa":
            entered.set()
            await release.wait()
            raise ValueError("boom")
        await entered.wait()
        rig.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="bb")
        release.set()
        return "merged"

    rig.callback.side_effect = run
    assert await asyncio.gather(rig.dispatch(a), rig.dispatch(b)) == ["infra_error", "merged"]
    assert bodies(rig, "aa") == [{"to": "running", "ticket_sha": "sha"}, {"to": "infra_error", "stage": "dispatch", "reason": "dispatch_exception", "error": "ValueError: boom"}]
    assert bodies(rig, "bb")[-1] == {"to": "merged"}
    assert rig.scheduler.pending == {"aa": a}
    assert rig.scheduler.failures == [] and not rig.owner.stopping
    rig.log.event.assert_any_call("dispatch_exception", stem="aa", error="ValueError: boom")
    assert all(call.args[0] != "worker_failure" for call in rig.log.event.call_args_list)


@pytest.mark.asyncio
@pytest.mark.parametrize("ending", ["stopping", "cancel"])
async def test_stopping_and_cancel_propagate(rig, ending):
    ticket = parse_ticket("aa", rig.text, rig.repo)

    async def run(_):
        if ending == "stopping":
            rig.owner.stop()
            raise ValueError("boom")
        raise asyncio.CancelledError()

    rig.callback.side_effect = run
    with pytest.raises(ValueError if ending == "stopping" else asyncio.CancelledError):
        await rig.dispatch(ticket)
    assert bodies(rig, "aa") == [{"to": "running", "ticket_sha": "sha"}]
    assert rig.log.event.call_count == 0


@pytest.mark.asyncio
async def test_consumer_failure_remains_fatal(rig):
    error = ValueError("consumer")
    rig.scheduler.failures.append(error)
    with pytest.raises(ValueError, match="consumer") as raised:
        rig.scheduler.raise_failure()
    assert raised.value is error
