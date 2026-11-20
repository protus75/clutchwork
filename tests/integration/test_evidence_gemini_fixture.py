# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test evidence gemini fixture
# relates: [clutch/evidence/gemini.py]
# owner: clutch/evidence/gemini.py
# verified: 148a8874
# hash: e71d7a0784bdf4738a032eb96725f6f18d0eb29074f52aadf9ef5892bf6cee3c
import hashlib
import json
from pathlib import Path

from clutch.evidence.gemini import normalize


def test_real_stream():
    path = Path(__file__).resolve().parents[1] / "fixtures" / "evidence" / "gemini" / "stream.jsonl"
    raw = path.read_bytes()
    lines = [json.loads(line) for line in raw.splitlines()]
    events = normalize(raw, None, lambda data: "sha256:" + hashlib.sha256(data).hexdigest())
    assert len(events) == len(lines)
    assert all(event.kind != "unknown" for event in events)
    assert [event.kind for event in events].count("tool_call") == 3
    assert [event.kind for event in events].count("tool_result") == 3
    result = next(event for event in events if event.kind == "result")
    stats = next(line["stats"] for line in lines if line["type"] == "result")
    assert result.tokens["input_uncached"] + result.tokens["input_cache_read"] == stats["input_tokens"]
