"""Requisition parks do not consume the failed-attempt budget."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Requisition parks do not consume the failed-attempt budget.
# relates: [clutch/caps.py, clutch/config.py, clutch/journal.py]
# owner: engine
# verified: 0a308920
# hash: 867747ec07217e96cf7f8efcf4e92be98c8bf4f1b867a403c16ad15d9c6c5550

from clutch.caps import failed_attempt, failed_attempts, spent
from clutch.config import Caps
from clutch.journal import Event, EventType


def events_for(bodies):
    return [Event(1, EventType.STATE_TRANSITION, "2026-01-01T00:00:00+00:00", "red", None, body) for body in bodies]


def test_only_requisition_premise_is_exempt():
    assert not failed_attempt({"to": "premise_failed", "stage": "requisition"})
    assert failed_attempt({"to": "premise_failed", "stage": "implement"})
    assert failed_attempt({"to": "premise_failed"})


def test_requisition_parks_do_not_spend_attempts():
    snag = {"to": "premise_failed", "stage": "requisition"}
    events = events_for([snag] * 5)
    assert failed_attempts(events, "red") == 0
    assert spent(Caps(), events, "red") is None


def test_other_failures_still_spend_attempts():
    events = events_for([{"to": "premise_failed", "stage": "requisition"}] * 4 + [{"to": "gate_failed"}] * 5)
    assert failed_attempts(events, "red") == 5
    assert spent(Caps(), events, "red") == "attempts"
