# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test provider parsed fixtures
# relates: [clutch/providers.py]
# owner: clutch/providers.py
# verified: 69d790e1
# hash: 67eb4782f3fe48d29897e006d21777f0074658bae2445fff687709644232c739
import json
from pathlib import Path

import pytest

from clutch.providers import AntigravityAdapter, ClaudeAdapter, CodexAdapter


@pytest.mark.parametrize(("name", "adapter"), [("claude", ClaudeAdapter), ("codex", CodexAdapter), ("antigravity", AntigravityAdapter)])
def test_fixture_result(name, adapter):
    raw = (Path(__file__).resolve().parents[1] / "fixtures" / "evidence" / name / "stream.jsonl").read_text()
    lines = [json.loads(line) for line in raw.splitlines()]
    terminal = next(line for line in reversed(lines) if line.get("event", line.get("type")) == ("turn.completed" if name == "codex" else "result"))
    if name == "antigravity":
        terminal = terminal["result"]
    usage = terminal.get("usage", {})
    inputs = usage.get("input_tokens", 0)
    if name == "antigravity":
        inputs += usage.get("cache_read_tokens", 0)
    if name == "claude":
        inputs += usage.get("cache_creation_input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
    result = adapter.parse(object.__new__(adapter), raw)
    assert result.input_tokens == inputs
    assert result.output_tokens == usage["output_tokens"]
    assert result.text
