# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test provider parsed events
# relates: [clutch/evidence/claude.py, clutch/evidence/codex.py, clutch/evidence/gemini.py, clutch/evidence/schema.py, clutch/providers.py]
# owner: engine
# verified: 9a610809
# hash: bbf771652dbb09f62d699e081f4ddb9d137f492edc0b9c216c34380518ba3db0
import json

import pytest

from clutch.evidence import claude, codex, gemini
from clutch.evidence.schema import Event
from clutch.providers import ClaudeAdapter, CliAdapter, CodexAdapter, GeminiAdapter


def stream(*lines):
    return "\n".join(json.dumps(line) for line in lines)


def normalize(module, *lines):
    events = module.normalize(stream(*lines).encode(), None, lambda b: "blob:" + b.decode())
    assert all(Event.model_validate(e.model_dump(by_alias=True)) == e for e in events)
    return events


def parse(cls, *lines):
    return cls.parse(object.__new__(cls), stream(*lines))


def test_claude_result():
    result = {"type": "result", "subtype": "success", "result": "hi", "total_cost_usd": 0.5}
    event = normalize(claude, result)[-1]
    assert (event.status, event.usd, event.text_blob) == ("success", 0.5, "blob:hi")
    result["is_error"] = True
    assert normalize(claude, result)[-1].status == "error"


def test_codex_closing():
    a = {"type": "item.completed", "item": {"type": "agent_message", "text": "a"}}
    b = {"type": "item.completed", "item": {"type": "agent_message", "text": "b"}}
    done = {"type": "turn.completed", "usage": {"input_tokens": 37, "output_tokens": 5}}
    event = normalize(codex, a, b, done)[-1]
    assert (event.status, event.text_blob) == ("success", "blob:b")
    failed = {"type": "turn.failed", "error": {"message": "usage limit reached"}}
    assert normalize(codex, failed, a, b, done)[-1].status == "error"
    assert normalize(codex, done)[-1].text_blob is None
    assert (parse(CodexAdapter, a, done).input_tokens, parse(CodexAdapter, a, done).output_tokens) == (37, 5)
    assert parse(CodexAdapter, a, {"type": "turn.completed", "usage": {}}).input_tokens is None
    with pytest.raises(ValueError, match="no terminal result event"):
        parse(CodexAdapter, a)
    with pytest.raises(ValueError, match="usage limit reached"):
        parse(CodexAdapter, failed, done)
    with pytest.raises(ValueError, match="could not be normalized"):
        parse(CodexAdapter, {"type": "item.started", "item": {"type": "command_execution"}})


def test_gemini_closing():
    chunks = [{"type": "message", "role": "assistant", "content": text} for text in ("DO", "NE")]
    result = {"type": "result", "status": "success", "stats": {"models": {"model-a": {}}}}
    event = normalize(gemini, *chunks, result)[-1]
    assert (event.status, event.text_blob, event.model) == ("success", "blob:DONE", "model-a")
    result["stats"]["models"]["model-b"] = {}
    assert normalize(gemini, *chunks, result)[-1].model is None
    error = {"type": "result", "status": "error", "error": {"message": "bad"}}
    event = normalize(gemini, error)[-1]
    assert (event.status, event.text_blob) == ("error", "blob:bad")
    assert parse(GeminiAdapter, {"type": "error", "message": "bad"}, *chunks, result).text == "DONE"


def test_claude_tolerates_incomplete_lines():
    lines = [
        {"type": "assistant", "message": None},
        {"type": "assistant", "message": False},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "x"}]}},
        {"type": "result", "subtype": "success", "result": "finished"},
    ]
    events = normalize(claude, *lines)
    assert [e.kind for e in events] == ["unknown", "unknown", "unknown", "usage", "result"]
    assert parse(ClaudeAdapter, *lines).text == "finished"


def test_single_parser():
    assert all("parse" not in vars(cls) for cls in (ClaudeAdapter, CodexAdapter, GeminiAdapter))
    with pytest.raises(ValueError, match="no terminal result event"):
        CliAdapter.parse(object.__new__(ClaudeAdapter), "")
