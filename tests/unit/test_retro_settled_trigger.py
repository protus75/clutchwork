"""The automatic retro cadence counts distinct settled tickets."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: The automatic retro cadence counts distinct settled tickets.
# relates: [clutch/config.py, clutch/journal.py, clutch/retro.py]
# owner: engine
# verified: 9a610809
# hash: bbd7e597ab44043262ae456a591dc151e6b2446eb1bcb484fabfd58864147348

import inspect

import pytest

from clutch.config import Retro
from clutch.journal import Event, EventType
from clutch.retro import Window, select_trigger


def event(stem, state, *, type_=EventType.STATE_TRANSITION, ts="2026-01-01T00:00:00+00:00"):
    return Event(1, type_, ts, stem, None, {"to": state})


def trigger(events, settings=None, started_at="2026-01-01T00:00:00+00:00"):
    window = Window("initial", tuple(events), started_at, 1)
    return select_trigger(window, {"merged_count": 0, "spikes": {}}, settings or Retro(), forced=False)


@pytest.mark.parametrize("state", ["merged", "already_satisfied", "rejected"])
def test_each_settled_state_counts_at_boundary(state):
    events = [event(f"ticket-{n}", state) for n in range(40)]
    assert trigger(events[:39]) is None
    assert trigger(events) == "settled"


def test_distinct_stems_and_transition_type_are_required():
    events = [event(f"ticket-{n}", "rejected") for n in range(39)]
    assert trigger(events + [event("ticket-0", "merged")]) is None
    assert trigger(events + [event(None, "merged")]) is None
    assert trigger(events + [event("other", "merged", type_=EventType.SIGNAL)]) is None


@pytest.mark.parametrize("state", ["abandoned", "gate_failed"])
def test_unsettled_states_do_not_count(state):
    assert trigger([event(f"ticket-{n}", state) for n in range(40)]) is None


def test_no_clock_and_disabled_trigger():
    assert "now" not in inspect.signature(select_trigger).parameters
    assert trigger([event("ticket", "running", ts="2027-01-01T00:00:00+00:00")]) is None
    assert trigger([event(f"ticket-{n}", "rejected") for n in range(40)], Retro(settled={"enabled": False})) is None
