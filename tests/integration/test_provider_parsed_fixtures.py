import json
from pathlib import Path

import pytest

from clutch.providers import ClaudeAdapter, CodexAdapter, GeminiAdapter


@pytest.mark.parametrize(("name", "adapter"), [("claude", ClaudeAdapter), ("codex", CodexAdapter), ("gemini", GeminiAdapter)])
def test_fixture_result(name, adapter):
    raw = (Path(__file__).resolve().parents[1] / "fixtures" / "evidence" / name / "stream.jsonl").read_text()
    lines = [json.loads(line) for line in raw.splitlines()]
    terminal = next(line for line in reversed(lines) if line["type"] == ("turn.completed" if name == "codex" else "result"))
    usage = terminal.get("stats" if name == "gemini" else "usage", {})
    inputs = usage.get("input_tokens", 0)
    if name == "claude":
        inputs += usage.get("cache_creation_input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
    result = adapter.parse(object.__new__(adapter), raw)
    assert result.input_tokens == inputs
    assert result.output_tokens == usage["output_tokens"]
    assert result.text
