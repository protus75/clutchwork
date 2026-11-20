import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch.drain import eligible
from clutch.journal import Event, EventType
from clutch.scheduler import Scheduler
from tests.dispatch_settle import dispatch_settled


def ticket(stem, priority="P2", state="confirmed", depends=(), runs_before=()):
    return NS(stem=stem, frontmatter=NS(state=state, priority=priority), depends=depends, runs_before=runs_before)


def test_common_filter():
    good = ticket("good", depends=("done",))
    items = [ticket("draft", state="draft"), ticket("closed"), ticket("mapped"), ticket("blocked", depends=("missing",)), good]
    assert eligible(items, {"closed": "merged"}, {"done"}, {"mapped": "replacement"}) == [good]  # Each omitted condition admits its corresponding ticket.


def test_input_order_and_caller_states():
    low, high = ticket("low"), ticket("high", "P0")
    assert eligible([low, high], {"low": "running", "high": "gate_failed"}, set(), {}) == [low, high]  # Sorting or filtering caller states changes the result.


def scheduler(items, events=(), held=frozenset()):
    writes, selected, dispatched = [], [], []

    async def dispatch(t):
        dispatched.append(t.stem)

    async def sha(stem):
        return "sha"

    obj = Scheduler(
        NS(read=lambda: list(events)),
        dispatch,
        state_dir=Path("/state"),
        fs=NS(write=lambda path, data: writes.append(json.loads(data))),
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        caps=lambda: None,
        ticket_sha=sha,
        quarantined=lambda: set(held),
        drought_parked=set,
        completed_unmerged=lambda: 0,
        max_unmerged=1,
    )
    obj.select = lambda t, stage: selected.append(t.stem) or True
    for t in items:
        obj.update(t)
    return obj, writes, selected, dispatched


@pytest.mark.asyncio
async def test_select_order_and_exclusions():
    events = [Event(1, EventType.STATE_TRANSITION, "2026-01-01T00:00:00+00:00", "running", None, {"to": "running"})]
    obj, _, selected, _ = scheduler([ticket("low"), ticket("high", "P0"), ticket("held"), ticket("running")], events, {"held"})
    await dispatch_settled(obj)
    assert selected == ["low", "high"]  # Sorting first or selecting held/running tickets changes the calls.


@pytest.mark.asyncio
async def test_soft_edge_only_applies_to_survivors():
    a, c, b = ticket("a", "P0"), ticket("c", "P1"), ticket("b", "P2", runs_before=("a",))
    obj, writes, _, dispatched = scheduler([b, c, a], held={"b"})
    await dispatch_settled(obj)
    assert dispatched == ["a"]  # Ordering before filtering lets b delay a.
    assert writes[0]["order"] == ["a", "c"]  # The queue must use the same post-filter set.
