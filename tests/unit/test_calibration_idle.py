"""Calibration cadence and idle boundaries."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that calibration due and pending counts include only Implement completions since the latest estimate_calibration signal
# relates: [clutch/calibration.py, clutch/config.py, clutch/drain.py, clutch/journal.py, clutch/serve.py, tests/fakes.py]
# owner: engine
# verified: 45e4e081
# hash: 8fbf3c04c42438885fa64204205ebda3bf9929a4dad3b441ba4c895afd88bc31

from clutch.calibration import due, pending
from clutch.journal import EventType
from tests.fakes import FakeClock, FakeJournal


def call(journal, clock, stem, surface="implement"):
    key = f"llm/{stem}/1/{surface}/1/1"
    journal.append(EventType.EFFECT_INTENT, {}, key=key)
    clock.advance(60)
    journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": "p", "model": "m"}}, key=key)


def test_due_counts_implement_completions_since_the_latest_calibration():
    clock = FakeClock()
    journal = FakeJournal(clock)
    call(journal, clock, "a")
    call(journal, clock, "b")
    journal.append(EventType.SIGNAL, {"signal": "estimate_calibration"})
    call(journal, clock, "c")
    call(journal, clock, "d", "review")
    # Wrong: count old completions or review completions.
    assert not due(journal.read(), 2)
    call(journal, clock, "e")
    # Wrong: fail to count a completion after the signal.
    assert due(journal.read(), 2)


def test_pending_counts_only_since_latest_calibration():
    journal = FakeJournal()
    call(journal, journal.clock, "old")
    journal.append(EventType.SIGNAL, {"signal": "estimate_calibration"})
    call(journal, journal.clock, "a")
    call(journal, journal.clock, "b")
    call(journal, journal.clock, "review", "review")
    # Wrong: include old or review calls, or return a boolean instead of the count.
    assert pending(journal.read()) == 2
