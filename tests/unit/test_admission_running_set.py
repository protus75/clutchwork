import asyncio
from types import SimpleNamespace

import pytest

from clutch import scheduler as scheduler_module
from clutch.daemon import DaemonAdmission, TicketWriter
from clutch.scheduler import Scheduler


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
    running = asyncio.create_task(admission.dispatch("selected"))
    await entered.wait()
    assert not admission.idle()
    release.set()
    assert await running == "selected"
    assert admission.idle()


@pytest.mark.asyncio
async def test_scheduler_and_writer_have_no_active_attribute(monkeypatch, tmp_path):
    async def dispatch(ticket):
        return "done"

    async def sha(stem):
        return ""

    journal = SimpleNamespace(read=lambda: [], dir=tmp_path, _fs=None, _clock=None)
    monkeypatch.setattr(scheduler_module, "write_queue", lambda *args: None)
    scheduler = Scheduler(journal, dispatch, caps=lambda: None, ticket_sha=sha, quarantined=set, drought_parked=set, completed_unmerged=lambda: 0, max_unmerged=1)
    writer = TicketWriter(SimpleNamespace(), None)
    ticket = SimpleNamespace(stem="selected", frontmatter=SimpleNamespace(state="confirmed", priority="P2"), depends=(), runs_before=())
    scheduler.update(ticket)
    assert "active" not in vars(scheduler) and "active" not in vars(writer)
    assert await scheduler.dispatch_next() is ticket
    assert "active" not in vars(scheduler) and "active" not in vars(writer)
