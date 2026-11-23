# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests continuation selection in TicketWriter, Serve and Scheduler. An edited terminal ticket dispatches fresh at implement. An unchanged or live-edited ticket resumes the producing run at its next stage.
# relates: [clutch/config.py, clutch/daemon.py, clutch/journal.py, clutch/scheduler.py, clutch/serve.py, clutch/stages.py, clutch/tickets.py, tests/fakes.py]
# owner: engine
# verified: 14394697
# hash: b8a26fb42e9b1bdf2db923fc4eeaee1f3c5515a0eeb4c4c1bd873bc06e2003fe
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest

from clutch import daemon, serve
from clutch.config import Caps
from clutch.daemon import DaemonAdmission, TicketWriter
from clutch.journal import EventType
from clutch.scheduler import Scheduler
from clutch.stages import StagesRun
from clutch.tickets import Frontmatter, Ticket
from tests.fakes import FakeClock, FakeFileSystem, FakeJournal, turn


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["edited_terminal", "unchanged", "edited_live"])
async def test_continuation_selection_and_writer(monkeypatch, case):
    old = Ticket("work", Frontmatter(state="confirmed", source="human", priority="P0", kind="feature"), {}, (), (), (), ("old/",), (), 20, 40)
    fresh = replace(old, scope_fence=("old/", "new/"))
    normalized = replace(old, frontmatter=old.frontmatter.model_copy(update={"agent_tier": "high"}))
    journal = FakeJournal()
    boundary = NS(run=None, ticket=None, next_stage=None)
    ctx = NS(boundary=boundary)
    writer = TicketWriter(ctx, None)
    seen = []
    sha = "new" if case != "unchanged" else "old"

    async def drive(ctx, ticket, **kwargs):
        seen.append((ticket, ctx.boundary.run, sha if ctx.boundary.run is None else ctx.boundary.run.ticket_sha))
        if len(seen) == 1:
            ctx.boundary.ticket = normalized
            ctx.boundary.run = StagesRun(attempt=7, ticket_sha="old")
            ctx.boundary.next_stage = "check"
            return "running"
        return "ticket_changed" if ctx.boundary.run is not None and sha != "old" else "ok"

    monkeypatch.setattr(daemon.runner, "drive", drive)
    await writer(old)
    journal.append(EventType.STATE_TRANSITION, {"to": "running", "ticket_sha": "old"}, ticket="work")
    if case != "edited_live":
        journal.append(EventType.STATE_TRANSITION, {"to": "gate_failed", "reason": "ticket_changed", "dispatch": "reject_queue", "routed": "reject_queue"}, ticket="work")
        journal.append(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "operator", "ticket_sha": sha}, ticket="work")
    owner = object.__new__(serve.Serve)
    owner.writers = {"work": writer}
    offered = old if case == "unchanged" else fresh
    owner.published = {"work": (offered, sha)}
    owner.checkout = NS(journal=journal)
    fresh_calls = []

    async def dispatch(ticket):
        fresh_calls.append(ticket)
        return await writer(ticket)

    admission = DaemonAdmission(dispatch)
    admission.resume = owner.resume
    scheduler = Scheduler(
        journal,
        admission.dispatch,
        state_dir=Path("/state"),
        fs=FakeFileSystem(),
        clock=FakeClock(),
        caps=Caps,
        ticket_sha=AsyncMock(return_value=sha),
        quarantined=set,
        drought_parked=set,
        completed_unmerged=lambda: 0,
        max_unmerged=1,
    )
    scheduler.continuations = lambda: ((c.ticket, c.run.ticket_sha) for c in writer.continuations.values())
    selected = []
    scheduler.next_stage = owner.next_stage
    scheduler.select = lambda ticket, stage: selected.append((ticket.scope_fence, stage)) or True
    scheduler.update(offered)
    chosen = await scheduler.dispatch_next()
    while scheduler.tasks:
        await turn()
    scheduler.raise_failure()
    if case == "edited_terminal":
        assert chosen is fresh  # Wrong: retained stale ticket displaces the fresh offer.
        assert selected == [(("old/", "new/"), "implement")]  # Wrong: selection sees the old fence or stage.
        assert seen[-1] == (fresh, None, "new") and fresh_calls == [fresh]  # Wrong: old run crosses into the new revision.
    else:
        assert chosen is normalized  # Wrong: whole-ticket equality rejects normalized continuation.
        assert selected == [(("old/",), "check")]  # Wrong: continuation is selected as a new implement stage.
        assert seen[-1][0] is normalized and seen[-1][1].attempt == 7 and seen[-1][2] == "old" and not fresh_calls  # Wrong: restart instead of resuming the producing run.
