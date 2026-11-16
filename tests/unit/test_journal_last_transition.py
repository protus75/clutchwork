from datetime import UTC, datetime

import pytest

from clutch.journal import EventType, Journal, last_transition, require_transition


def test_latest_transition_and_missing(tmp_path):
    journal = Journal(tmp_path, lambda: datetime(2026, 1, 1, tzinfo=UTC))
    for stem, state, marker in [("a", "running", "first"), ("b", "running", "foreign"), ("a", "gate_failed", "middle"), ("a", "running", "last"), ("b", "gate_failed", "foreign-last")]:
        journal.append(EventType.STATE_TRANSITION, {"to": state, "marker": marker}, ticket=stem)
    events = journal.read()
    assert last_transition(events, "a") == {"to": "running", "marker": "last"}
    assert last_transition(events, "absent") is None
    with pytest.raises(RuntimeError, match="absent"):
        require_transition(events, "absent")
