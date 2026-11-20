# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test live call source
# relates: []
# owner: engine
# verified: 96e46658
# hash: 7b66dfdd711c628225e81f04bdc533bfc481484d20ee22c3ef919618a8060a6d
from pathlib import Path


def test_live_call_has_no_provider_argv_parser():
    root = Path(__file__).resolve().parents[2]
    source = (root / "clutch/observe.py").read_text()
    for marker in ("cli-entry.js", "model_reasoning_effort", "@google/gemini-cli"):
        assert marker not in source
    assert not (root / "tests/unit/test_live_call_gemini.py").exists()
