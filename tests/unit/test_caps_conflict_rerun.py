"""Conflict rerun accounting is separate from failure caps."""

import pytest

from clutch.caps import CONFLICT_RERUN_LIMIT, CONFLICT_RERUN_ROAD, conflict_rerun_spent, conflict_reruns, failed_attempts, remaining, spent
from clutch.config import Caps
from clutch.journal import Event, EventType


def event(kind, stem, body):
    return Event(1, kind, "time", stem, None, body)


def rerun(stem, attempt):
    return event(EventType.SIGNAL, stem, {"signal": "merge_conflict_rerun", "attempt": attempt})


def test_limit_and_retry_are_separate():
    caps = Caps(retry=1)
    events = [rerun("work", 1), rerun("work", 2)]
    assert CONFLICT_RERUN_LIMIT == 2
    assert CONFLICT_RERUN_ROAD == "split the ticket, or run it with parallel disabled"
    assert not conflict_rerun_spent(events[:1], "work")
    assert conflict_rerun_spent(events, "work")
    assert remaining(caps, events, "work", "retry") == remaining(caps, [], "work", "retry") == 1
    assert spent(caps, events, "work") is None
    assert failed_attempts(events, "work") == 0


def test_counts_only_matching_signal_and_stem():
    events = [rerun("other", 1), rerun("work", 1), event(EventType.SIGNAL, "work", {"signal": "diagnosis"}), event(EventType.STATE_TRANSITION, "work", {"signal": "merge_conflict_rerun"})]
    assert conflict_reruns(events, "missing") == 0
    assert conflict_reruns(events, "work") == 1


@pytest.mark.parametrize("actor", ["operator", "supervisor"])
def test_keep_resets_count(actor):
    events = [rerun("work", 1), rerun("work", 2), event(EventType.SIGNAL, "work", {"signal": "reject_verdict", "verdict": "keep", "actor": actor})]
    assert conflict_reruns(events, "work") == 0
    assert conflict_reruns([*events, rerun("work", 3)], "work") == 1
