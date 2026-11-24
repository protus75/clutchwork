# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that events.poll reports a roadmap gate result only when a release's last pass/fail state changes, including after the journal is truncated.
# relates: [clutch/events.py]
# owner: clutch/events.py
# verified: 68e44cc9
# hash: 67e3388867777b959d8d5cbb3892b359e3a3514350178d8b201ae88746c5121c
from clutch import events


def gate(release, passed):
    return {"type": "signal", "body": {"signal": "roadmap_gate", "release": release, "passed": passed}}


def test_gate_results_follow_last_per_release(monkeypatch, tmp_path):
    journal = [gate("v2", True), gate("v2", False), gate("v1", False)]
    monkeypatch.setattr(events.observe, "journal", lambda state: journal)
    monkeypatch.setattr(events.observe, "read_lines", lambda path, limit: [])
    seen, _ = events.poll(tmp_path, None)

    journal.extend([gate("v2", False), gate("v1", False), gate("v3", False)])
    seen, lines = events.poll(tmp_path, seen)
    assert lines == ["gate - v3 failed -- clutch roadmap status"]  # Repeats or a missing first result differ.

    journal.append(gate("v2", True))
    seen, lines = events.poll(tmp_path, seen)
    assert lines == ["gate - v2 passed -- clutch roadmap status"]  # Suppressing a flip differs.

    journal.append(gate("v2", False))
    seen, lines = events.poll(tmp_path, seen)
    assert lines == ["gate - v2 failed -- clutch roadmap status"]  # Failing to update the prior result differs.

    journal[:] = [gate("v2", True)]
    seen, _ = events.poll(tmp_path, seen)
    journal.append(gate("v2", True))
    seen, lines = events.poll(tmp_path, seen)
    assert lines == []  # Ignoring the new baseline after truncation differs.
    journal.append(gate("v2", False))
    seen, lines = events.poll(tmp_path, seen)
    assert lines == ["gate - v2 failed -- clutch roadmap status"]  # Suppressing a post-truncation flip differs.
