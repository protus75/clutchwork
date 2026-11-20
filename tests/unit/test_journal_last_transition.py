# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test journal last transition
# relates: [clutch/journal.py]
# owner: clutch/journal.py
# verified: 0a308920
# hash: 59f48d07c64064ab546ae92cfd51b6019ed6c7c4ea488e897ccbbea7165839e8
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
