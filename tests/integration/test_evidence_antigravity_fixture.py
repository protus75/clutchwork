# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the Antigravity normalizer reads the recorded stream fixture with no unknown events and gets the expected tool events, model and cache tokens.
# relates: [clutch/evidence/antigravity.py]
# owner: clutch/evidence/antigravity.py
# verified: 69d790e1
# hash: 1353cdb1baf8e52a6f3ff91469f0b787da1005a0d07bf3d740c506991dc1982b
from pathlib import Path

from clutch.evidence.antigravity import normalize


def test_fixture():
    raw = (Path(__file__).resolve().parents[1] / "fixtures/evidence/antigravity/stream.jsonl").read_bytes()
    events = normalize(raw, None, lambda b: b.decode())
    assert [e.kind for e in events].count("tool_call") == 2
    assert [e.kind for e in events].count("tool_result") == 2
    assert all(e.kind != "unknown" for e in events)
    assert events[-1].model == "model-a" and events[-1].tokens["input_cache_read"] == 40
