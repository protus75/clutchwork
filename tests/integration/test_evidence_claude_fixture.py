# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test evidence claude fixture
# relates: [clutch/evidence/claude.py]
# owner: clutch/evidence/claude.py
# verified: 148a8874
# hash: bc5161cffedea9fe375a2afa302b8c9027aded463c1e53334006b7d08317a6be
from pathlib import Path

from clutch.evidence.claude import normalize

ROOT = Path(__file__).resolve().parents[2]


def test_real_claude_stream():
    stream = (ROOT / "tests/fixtures/evidence/claude/stream.jsonl").read_bytes()
    events = normalize(stream, None, lambda data: "sha256:fixture")
    kinds = {event.kind for event in events}
    assert {"tool_call", "tool_result", "reasoning", "usage"} <= kinds
    assert not [event for event in events if event.kind == "unknown"]
    calls = {event.tool.id for event in events if event.kind == "tool_call"}
    results = {event.tool.id for event in events if event.kind == "tool_result"}
    assert calls and calls <= results
