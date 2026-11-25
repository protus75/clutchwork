# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for events cursor encode/decode round-trip, corrupt-cursor rejection, and wait_once baseline, timeout, resume, truncation and timing validation.
# relates: [clutch/events.py]
# owner: clutch/events.py
# verified: bdb23dbf
# hash: 5bb5ac4fa9141c6c5ea5e3370020135a0ffa472de74df9ce7df6c8e40f370c9f
import base64
import json

import pytest

from clutch import events


def token(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode()


def test_cursor_roundtrip():
    seen = (7, {"a", "b"}, {("engine_start", "t1"), ("engine_stop", "t2")}, {"v1": True, "v2": False})
    assert events.decode_cursor(events.encode_cursor(seen)) == seen  # Missing or stringified fields differ.


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "!",
        base64.urlsafe_b64encode(b"{").decode(),
        token({"v": 2, "offset": 0, "reject": [], "engine": [], "gates": {}}),
        token({"v": 1, "offset": True, "reject": [], "engine": [], "gates": {}}),
        token({"v": 1, "offset": -1, "reject": [], "engine": [], "gates": {}}),
        token({"v": 1, "offset": 0, "reject": [], "engine": [], "gates": {"r": 1}}),
        token({"v": 1, "offset": 0, "reject": [], "engine": [["a"]], "gates": {}}),
    ],
)
def test_bad_cursor(bad):
    with pytest.raises(ValueError):  # Accepting a corrupt cursor differs.
        events.decode_cursor(bad)


def test_baseline_timeout_and_resume(tmp_path):
    journal = tmp_path / "journal"
    journal.mkdir()
    segment = journal / "one.jsonl"

    def append(stem):
        with segment.open("a") as f:
            f.write(json.dumps({"type": "state_transition", "ticket": stem, "body": {"to": "running"}}) + "\n")

    append("old")
    now = [0.0]
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    cursor, lines, timed_out = events.wait_once(tmp_path, timeout=12, interval=5, sleep=sleep, clock=lambda: now[0])
    assert (lines, timed_out, sleeps, events.decode_cursor(cursor)[0]) == ([], True, [5, 5, 2], 1)  # Replay, wrong deadline, or lost offset differs.
    append("new")
    sleeps.clear()
    cursor, lines, timed_out = events.wait_once(tmp_path, cursor=cursor, timeout=12, sleep=sleep, clock=lambda: now[0])
    assert (lines, timed_out, sleeps) == (["start new -- clutch roadmap status"], False, [])  # Sleeping first or missing the event differs.
    cursor, lines, timed_out = events.wait_once(tmp_path, cursor=cursor, timeout=0, sleep=sleep, clock=lambda: now[0])
    assert (lines, timed_out, sleeps) == ([], True, [])  # Replaying or sleeping at zero differs.
    segment.write_text("")
    cursor, lines, timed_out = events.wait_once(tmp_path, cursor=cursor, timeout=0, sleep=sleep, clock=lambda: now[0])
    assert (events.decode_cursor(cursor)[0], lines, timed_out) == (0, [], True)  # Retaining the old offset differs.


def test_event_during_sleep(tmp_path):
    directory = tmp_path / "journal"
    directory.mkdir()
    calls = []

    def sleep(seconds):
        calls.append(seconds)
        (directory / "one.jsonl").write_text(json.dumps({"type": "state_transition", "ticket": "fresh", "body": {"to": "running"}}) + "\n")

    cursor, lines, timed_out = events.wait_once(tmp_path, timeout=12, interval=5, sleep=sleep, clock=lambda: 0)
    assert (lines, timed_out, calls, events.decode_cursor(cursor)[0]) == (["start fresh -- clutch roadmap status"], False, [5], 1)  # Missing or delaying the wakeup differs.


@pytest.mark.parametrize("kwargs", [{"timeout": -1}, {"timeout": float("nan")}, {"timeout": float("inf")}, {"interval": 0}])
def test_invalid_timing(tmp_path, kwargs):
    with pytest.raises(ValueError):  # Allowing invalid timing differs.
        events.wait_once(tmp_path, sleep=lambda _: pytest.fail("slept"), **kwargs)
