"""Conflict reruns cannot use shared paths to bypass overlapping fences."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Conflict reruns cannot use shared paths to bypass overlapping fences.
# relates: [clutch/config.py, clutch/drain.py, clutch/journal.py, clutch/scheduler.py, clutch/tickets.py, tests/dispatch_settle.py]
# owner: engine
# verified: 0a308920
# hash: da7c81cbd062528ed3d8dcae7b052af1f0a9c4c89b55e61dae8939198215739f

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch.config import Parallel
from clutch.drain import fill_slots
from clutch.journal import Event, EventType
from clutch.scheduler import Scheduler
from clutch.tickets import Frontmatter, Ticket, fences_overlap
from tests.dispatch_settle import dispatch_settled


def ticket(stem, path):
    return Ticket(
        stem=stem,
        frontmatter=Frontmatter(state="confirmed", source="human", priority="P1", kind="feature"),
        sections={},
        depends=(),
        context=(),
        on_demand=(),
        scope_fence=(path,),
        verification=(),
        expected_minutes=20,
        stuck_minutes=40,
    )


@pytest.mark.parametrize("rerun", [set(), {"candidate"}, {"busy"}])
def test_overlap_symmetric(rerun):
    candidate, busy = ticket("candidate", "docs/file"), ticket("busy", "docs")
    assert fences_overlap(candidate, busy, ["docs"], rerun) is bool(rerun)
    assert fences_overlap(busy, candidate, ["docs"], rerun) is bool(rerun)


@pytest.mark.parametrize("rerun,blocked", [(set(), False), ({"candidate"}, True), ({"busy"}, True)])
def test_fill_slots(rerun, blocked):
    candidate, busy = ticket("candidate", "docs/file"), ticket("busy", "docs")
    selected, counts = fill_slots([candidate], [busy], 1, ["docs"], {}, rerun)
    assert selected == ([] if blocked else [candidate])
    assert counts == ({"candidate": 1} if blocked else {})


@pytest.mark.asyncio
@pytest.mark.parametrize("signal", [None, "candidate", "busy"])
async def test_scheduler_reads_rerun_for_both_sides(signal):
    candidate, busy = ticket("candidate", "docs/file"), ticket("busy", "docs")
    events = [] if signal is None else [Event(1, EventType.SIGNAL, "time", signal, None, {"signal": "merge_conflict_rerun"})]
    calls = []

    async def dispatch(item):
        calls.append(item)

    async def sha(stem):
        return "sha"

    scheduler = Scheduler(
        SimpleNamespace(read=lambda: events),
        dispatch,
        state_dir=Path("/state"),
        fs=SimpleNamespace(write=lambda path, data: None),
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        caps=lambda: None,
        ticket_sha=sha,
        quarantined=set,
        drought_parked=set,
        completed_unmerged=lambda: 0,
        max_unmerged=1,
    )
    scheduler.parallel = lambda: Parallel(enabled=True, max_runs=2, shared_paths=["docs"])
    scheduler.update(candidate)
    scheduler.flying[busy.stem] = busy
    result = await dispatch_settled(scheduler)
    assert result is (candidate if signal is None else None)
    assert calls == ([candidate] if signal is None else [])
    assert scheduler.skips == ({} if signal is None else {"candidate": 1})
