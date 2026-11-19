import json
import os

import pytest

from clutch import events


def record(kind, stem=None, **body):
    return {"type": kind, "ticket": stem, "body": body}


def append(path, item):
    with path.open("a") as f:
        f.write(json.dumps(item) + "\n")


def test_journal_deltas_and_noise(tmp_path):
    directory = tmp_path / "journal"
    directory.mkdir()
    segment = directory / "one.jsonl"
    append(segment, record("state_transition", "old", to="merged"))
    append(segment, record("signal", "old-draft", signal="ticket_intake", source="box:old", state="draft"))
    append(tmp_path / "engine.log", {"event": "engine_stop", "ts": "1", "verb": "drain", "outcome": "ok"})
    seen, lines = events.poll(tmp_path, None)
    assert lines == []  # Replaying old history differs.
    seen, lines = events.poll(tmp_path, seen)
    assert lines == []  # Reprinting history differs.
    for item in [
        record("state_transition", "alpha", to="running"),
        record("state_transition", "alpha", to="merged"),
        record("state_transition", "beta", to="premise_failed", routed="reject_queue"),
        record("signal", "gamma", signal="ticket_intake", source="box:roadmap_row", state="draft"),
        record("signal", signal="roadmap_gate", release="v2", passed=False),
        record("signal", signal="release", tag="v2.1"),
    ]:
        append(segment, item)
    seen, lines = events.poll(tmp_path, seen)
    assert lines == [
        "start alpha -- clutch roadmap status",
        "settle alpha merged -- clutch roadmap status",
        "draft gamma box:roadmap_row -- clutch prompt drafts",
        "gate - v2 failed -- clutch roadmap status",
        "release - v2.1 -- clutch roadmap status",
        "reject_queue beta premise_failed -- clutch prompt diagnose beta",
    ]  # Dropping, reordering, or duplicating a change differs.
    append(segment, record("signal", "beta", signal="reject_verdict"))
    for item in [
        record("signal", "human", signal="ticket_intake", source="human", state="draft"),
        record("intent", "x"),
        record("completion", "x"),
        record("signal", "x", signal="provider_call_outcome"),
        record("state_transition", "x", to="premise_failed"),
    ]:
        append(segment, item)
    seen, lines = events.poll(tmp_path, seen)
    assert lines == ["reject_release beta -- clutch view status"]  # Noise or a missing release differs.
    assert events.poll(tmp_path, seen)[1] == []  # Repeating the release differs.
    assert events.EVENTS == ("start", "settle", "reject_queue", "reject_release", "draft", "gate", "release", "engine_start", "engine_stop", "engine_lost")
    segment.write_text("")
    assert events.poll(tmp_path, seen)[1] == []  # Replaying after truncation differs.


def test_engine_lifecycle(tmp_path):
    log = tmp_path / "engine.log"
    (tmp_path / "clutch.lock").write_text(json.dumps({"pid": os.getpid(), "started_at": "2026-01-01T00:00:00+00:00"}))
    seen, _ = events.poll(tmp_path, None)
    append(log, {"event": "engine_start", "ts": "1", "verb": "drain", "pid": os.getpid()})
    seen, lines = events.poll(tmp_path, seen)
    assert lines == [f"engine_start - drain started (pid {os.getpid()}) -- clutch view status"]  # A false loss or missing start differs.
    append(log, {"event": "engine_stop", "ts": "2", "verb": "drain", "outcome": "ok"})
    seen, lines = events.poll(tmp_path, seen)
    assert lines == ["engine_stop - drain stopped (ok) -- clutch prompt drain-loop"]  # A missing stop or repeated start differs.
    assert events.poll(tmp_path, seen)[1] == []  # Repeating either lifecycle row differs.
    append(log, {"event": "engine_start", "ts": "3", "verb": "serve", "pid": os.getpid()})
    (tmp_path / "clutch.lock").unlink()
    seen, lines = events.poll(tmp_path, seen)
    assert lines == [
        f"engine_start - serve started (pid {os.getpid()}) -- clutch view status",
        "engine_lost - serve ended without a stop record (killed?) -- clutch prompt drain-loop",
    ]  # Missing or duplicated loss differs.
    assert events.poll(tmp_path, seen)[1] == []  # Repeating loss differs.


def test_stream_sleeps_and_writes(tmp_path):
    directory = tmp_path / "journal"
    directory.mkdir()
    segment = directory / "one.jsonl"
    calls, output = [], []

    def sleep(interval):
        calls.append(interval)
        if len(calls) == 1:
            append(segment, record("state_transition", "finished", to="merged"))
        else:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        events.stream(tmp_path, sleep=sleep, write=output.append)
    assert calls == [5, 5]  # A missing sleep or wrong interval differs.
    assert output == ["settle finished merged -- clutch roadmap status"]  # A missing or duplicate write differs.
