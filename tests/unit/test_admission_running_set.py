# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test admission running set
# relates: [clutch/daemon.py, clutch/scheduler.py, tests/dispatch_settle.py]
# owner: engine
# verified: 0a308920
# hash: 35619069da5b6cb43dbcb55d37131a6e204053b3bf2cc3201f2978999108cee7
import asyncio
from types import SimpleNamespace

import pytest

from clutch import scheduler as scheduler_module
from clutch.daemon import DaemonAdmission, TicketWriter
from clutch.scheduler import Scheduler
from tests.dispatch_settle import dispatch_settled


@pytest.mark.asyncio
async def test_admission_owns_mutation_and_dispatch_windows():
    entered, release = asyncio.Event(), asyncio.Event()

    async def dispatch(ticket):
        entered.set()
        await release.wait()
        return ticket

    admission = DaemonAdmission(dispatch)
    async with admission.mutations():
        assert not admission.idle()
        assert admission.mutating is asyncio.current_task()
    assert admission.mutating is None
    assert admission.idle()
    running = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="selected")))
    await entered.wait()
    assert not admission.idle()
    release.set()
    assert (await running).stem == "selected"
    assert admission.idle()


@pytest.mark.asyncio
async def test_scheduler_and_writer_have_no_active_attribute(monkeypatch, tmp_path):
    async def dispatch(ticket):
        return "done"

    async def sha(stem):
        return ""

    journal = SimpleNamespace(read=lambda: [], dir=tmp_path, _fs=None, _clock=None)
    monkeypatch.setattr(scheduler_module, "write_queue", lambda *args: None)
    scheduler = Scheduler(
        journal, dispatch, state_dir=tmp_path, fs=None, clock=None, caps=lambda: None, ticket_sha=sha, quarantined=set, drought_parked=set, completed_unmerged=lambda: 0, max_unmerged=1
    )
    writer = TicketWriter(SimpleNamespace(), None)
    ticket = SimpleNamespace(stem="selected", frontmatter=SimpleNamespace(state="confirmed", priority="P2"), depends=(), runs_before=())
    scheduler.update(ticket)
    assert "active" not in vars(scheduler) and "active" not in vars(writer)
    assert await dispatch_settled(scheduler) is ticket
    assert "active" not in vars(scheduler) and "active" not in vars(writer)
