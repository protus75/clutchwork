# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test premise park keep
# relates: [clutch/drain.py, clutch/journal.py]
# owner: engine
# verified: 9a610809
# hash: 3475d9ef53fec10463c067b000fd75a7e85af91178d49cea2b408ee773915112
from clutch.drain import parked_blob
from clutch.journal import Event, EventType


def event(kind, body, stem="work"):
    return Event(1, kind, "2026-01-01T00:00:00+00:00", stem, None, body)


def test_operator_keep_releases_only_the_current_premise_park():
    running = event(EventType.STATE_TRANSITION, {"to": "running", "ticket_sha": "B"})
    failure = event(EventType.STATE_TRANSITION, {"to": "premise_failed"})
    keep = event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "operator"})
    machine = event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "machine"})
    history = [running, failure]
    assert parked_blob(history, "work") == "B"  # A failure without a verdict remains held.
    assert parked_blob(history + [keep], "work") is None  # The operator releases the current hold.
    assert parked_blob(history + [machine], "work") == "B"  # Machine keeps cannot release it.
    assert parked_blob(history + [keep, event(EventType.STATE_TRANSITION, {"to": "running", "ticket_sha": "C"}), failure], "work") == "C"  # A new run creates a new hold.
    assert parked_blob(history + [event(EventType.SIGNAL, keep.body, "other")], "work") == "B"  # Another stem cannot release it.
    budget = [running, event(EventType.STATE_TRANSITION, {"to": "gate_failed", "reason": "diff_budget"}), keep]
    assert parked_blob(budget, "work") == "B"  # The operator keep does not change diff-budget holds.
