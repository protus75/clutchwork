"""Settled checkpoint windows count distinct terminal ticket stems."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Settled checkpoint windows count distinct terminal ticket stems.
# relates: [clutch/checkpoint.py, clutch/journal.py]
# owner: engine
# verified: 0a308920
# hash: 0751cd3f26301a2897054b9d19975ec963be6f3f6e5e0f055531dd93c62e63dc

from clutch.checkpoint import settled_since_last_push
from clutch.journal import Event, EventType


def event(type_, ticket=None, key=None, **body):
    return Event(1, type_, "2026-01-01T00:00:00+00:00", ticket, key, body)


def test_settled_threshold_and_states():
    states = ["merged", "already_satisfied", "rejected"]
    events = [event(EventType.STATE_TRANSITION, f"t{n}", to=states[n % 3]) for n in range(10)]
    assert settled_since_last_push(events) == 10
    assert settled_since_last_push(events[:-1]) == 9


def test_last_completion_distinct_and_exclusions():
    events = [
        event(EventType.STATE_TRANSITION, "old", to="merged"),
        event(EventType.EFFECT_COMPLETION, key="checkpoint-push/0"),
        event(EventType.STATE_TRANSITION, "middle", to="rejected"),
        event(EventType.EFFECT_COMPLETION, key="other/1"),
        event(EventType.EFFECT_COMPLETION, key="checkpoint-push/1"),
        event(EventType.STATE_TRANSITION, "same", to="merged"),
        event(EventType.STATE_TRANSITION, "same", to="rejected"),
        event(EventType.STATE_TRANSITION, "abandoned", to="abandoned"),
        event(EventType.STATE_TRANSITION, "failed", to="gate_failed"),
        event(EventType.STATE_TRANSITION, None, to="merged"),
        event(EventType.SIGNAL, "signal", to="merged"),
        event(EventType.STATE_TRANSITION, "new", to="already_satisfied"),
    ]
    assert settled_since_last_push(events) == 2
