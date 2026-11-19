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
