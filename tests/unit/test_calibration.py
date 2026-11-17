from pathlib import Path

from clutch.calibration import calibrate, implement_runs, render
from clutch.journal import EventType
from tests.fakes import FakeClock, FakeFileSystem, FakeJournal


def call(journal, clock, stem, minutes, provider="codex", model="m1", surface="implement"):
    key = f"llm/{stem}/1/{surface}/1/1"
    journal.append(EventType.EFFECT_INTENT, {}, key=key)
    clock.advance(minutes * 60)
    journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": provider, "model": model}}, key=key)


def test_implement_runs_pair_each_completion_with_its_latest_intent():
    clock = FakeClock()
    journal = FakeJournal(clock)
    call(journal, clock, "a", 6)
    call(journal, clock, "a", 2, surface="review")
    key = "llm/b/1/implement/1/1"
    journal.append(EventType.EFFECT_INTENT, {}, key=key)
    clock.advance(600)
    call(journal, clock, "b", 3, "claude", "m2")
    journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": "codex", "model": "m1"}}, key="llm/c/1/implement/1/1")
    assert implement_runs(journal.read()) == [("a", "codex", "m1", 6.0), ("b", "claude", "m2", 3.0)]


def test_calibrate_journals_one_row_per_provider_and_model():
    clock = FakeClock()
    journal = FakeJournal(clock)
    fs = FakeFileSystem()
    repo = Path("/repo")
    for stem, contents in (("old", "- expected: 100m"), ("a", "- expected: 30m"), ("b", "- expected: 60m"), ("c", "- expected: 20m"), ("d", "no estimate")):
        fs.write(repo / f"tickets/{stem}/ticket.md", contents.encode())
    call(journal, clock, "old", 50)
    call(journal, clock, "a", 3)
    call(journal, clock, "b", 9)
    call(journal, clock, "c", 2, "claude", "m2")
    call(journal, clock, "d", 1)
    call(journal, clock, "gone", 1)
    rows = [
        {"provider": "claude", "model": "m2", "runs": 1, "expected_p50": 20.0, "actual_p50": 2.0, "actual_p90": 2.0},
        {"provider": "codex", "model": "m1", "runs": 2, "expected_p50": 45.0, "actual_p50": 6.0, "actual_p90": 8.4},
    ]
    assert calibrate(journal, fs, repo, 5) == rows
    signals = [e for e in journal.read() if e.type == EventType.SIGNAL]
    assert len(signals) == 1
    assert signals[0].ticket is None
    assert signals[0].body == {"signal": "estimate_calibration", "window": 5, "rows": rows}


def test_calibrate_journals_an_empty_table():
    journal = FakeJournal()
    assert calibrate(journal, FakeFileSystem(), Path("/repo"), 100) == []
    assert [e.body for e in journal.read()] == [{"signal": "estimate_calibration", "window": 100, "rows": []}]


def test_render():
    row = {"provider": "codex", "model": "m1", "runs": 2, "expected_p50": 45.0, "actual_p50": 6.0, "actual_p90": 8.4}
    assert render([row]) == "codex/m1: 2 runs, estimate p50 45.0m, actual p50 6.0m, actual p90 8.4m\n"
    assert render([]) == "none\n"
