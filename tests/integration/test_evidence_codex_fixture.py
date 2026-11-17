import hashlib
import json
from pathlib import Path

from clutch.evidence.codex import INPUT_INCLUDES_CACHED, normalize


def test_real_stream():
    path = Path(__file__).resolve().parents[1] / "fixtures" / "evidence" / "codex" / "stream.jsonl"
    raw = path.read_bytes()
    lines = [json.loads(line) for line in raw.splitlines()]
    events = normalize(raw, None, lambda b: "sha256:" + hashlib.sha256(b).hexdigest())
    assert len(events) == len(lines)
    usages = 0
    for source, event in zip(lines, events, strict=True):
        kind = source["type"]
        item_type = source.get("item", {}).get("type")
        if (
            kind in {"thread.started", "turn.completed", "error", "turn.failed"}
            or (kind == "item.started" and item_type == "command_execution")
            or (kind == "item.completed" and item_type in {"command_execution", "file_change", "agent_message", "reasoning"})
        ):
            assert event.kind != "unknown"
        if kind == "turn.completed":
            usages += 1
            usage = source["usage"]
            assert usage["cached_input_tokens"] > 0
            assert INPUT_INCLUDES_CACHED == (usage["cached_input_tokens"] <= usage["input_tokens"])
            assert event.tokens["input_uncached"] == (usage["input_tokens"] - usage["cached_input_tokens"] if INPUT_INCLUDES_CACHED else usage["input_tokens"])
    assert usages > 0
