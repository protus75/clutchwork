from pathlib import Path


def test_live_call_has_no_provider_argv_parser():
    root = Path(__file__).resolve().parents[2]
    source = (root / "clutch/observe.py").read_text()
    for marker in ("cli-entry.js", "model_reasoning_effort", "@google/gemini-cli"):
        assert marker not in source
    assert not (root / "tests/unit/test_live_call_gemini.py").exists()
