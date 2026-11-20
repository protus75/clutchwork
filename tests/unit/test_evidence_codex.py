import json

import pytest

from clutch.evidence.codex import INPUT_INCLUDES_CACHED, NORMALIZER_ID, normalize
from clutch.evidence.schema import Event


def stream(*events):
    return "\n".join(json.dumps(e) if not isinstance(e, str) else e for e in events).encode()


def blob(value):
    return "sha256:" + value.decode()


def test_session_and_time():
    result = normalize(stream({"type": "thread.started"}, {"type": "turn.started"}), [0, 5_000_000], blob)
    assert NORMALIZER_ID == "codex-stream/1"
    assert [e.kind for e in result] == ["session_start", "unknown"]
    assert result[0].native_type == "thread.started"
    assert [e.seq for e in result] == [0, 1]
    assert [e.t_ms for e in result] == [0, 5]
    assert all(Event.model_validate(e.model_dump(by_alias=True)) == e for e in result)
    assert [e.t_ms for e in normalize(stream({"type": "thread.started"}, {"type": "turn.started"}), None, blob)] == [0, 0]


def test_command():
    item = {"id": "cmd-9", "type": "command_execution", "command": "cat x", "aggregated_output": "contents", "status": "completed"}
    call, result = normalize(stream({"type": "item.started", "item": item}, {"type": "item.completed", "item": item}), None, blob)
    assert call.kind == "tool_call"
    assert (call.tool.id, call.tool.class_, call.tool.native) == ("cmd-9", "shell", "command_execution")
    assert call.args == {"command": "cat x"}
    assert result.kind == "tool_result"
    assert result.status == "completed"
    assert result.output_blob == "sha256:contents"
    assert "aggregated_output" not in result.native["item"]


def test_usage():
    event = normalize(stream({"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 7}}), None, blob)[0]
    assert event.kind == "usage"
    assert event.tokens == {
        "input_uncached": 60 if INPUT_INCLUDES_CACHED else 100,
        "input_cache_read": 40,
        "input_cache_write": None,
        "output_total": 7,
        "output_reasoning": None,
        "tokenizer": "openai-o200k",
    }
    absent = normalize(stream({"type": "turn.completed", "usage": {}}), None, blob)[0]
    assert absent.tokens["input_uncached"] is None
    missing_cache = normalize(stream({"type": "turn.completed", "usage": {"input_tokens": 100}}), None, blob)[0]
    assert missing_cache.tokens["input_uncached"] == 100
    full = normalize(
        stream({"type": "turn.completed", "usage": {"input_tokens": 9, "cached_input_tokens": 2, "cache_write_input_tokens": 3, "output_tokens": 4, "reasoning_output_tokens": 1}}), None, blob
    )[0]
    assert full.tokens["input_cache_write"] == 3
    assert full.tokens["output_reasoning"] == 1


def test_unknown_lines():
    objects = [{"type": "other", "x": 7}, {"type": "turn.started"}, "not json", "[]", {"type": "item.started", "item": {"type": "other"}}]
    events = normalize(stream(*objects), None, blob)
    assert len(events) == 5
    assert [e.kind for e in events] == ["unknown"] * 5
    assert [e.native for e in events] == [objects[0], objects[1], {"line": "not json"}, {"line": "[]"}, objects[4]]


@pytest.mark.parametrize(
    ("event", "kind", "visibility", "text_blob"),
    [
        ({"type": "item.completed", "item": {"type": "agent_message", "text": "hello"}}, "message", None, "sha256:hello"),
        ({"type": "item.completed", "item": {"type": "reasoning", "text": "thinking"}}, "reasoning", "summary", "sha256:thinking"),
        ({"type": "item.completed", "item": {"type": "reasoning"}}, "reasoning", "count_only", None),
        ({"type": "item.completed", "item": {"type": "file_change", "changes": ["x"]}}, "file_change", None, None),
        ({"type": "turn.failed", "error": {"message": "bad"}}, "error", None, "sha256:bad"),
        ({"type": "error", "message": "bad"}, "error", None, "sha256:bad"),
    ],
)
def test_other_mappings(event, kind, visibility, text_blob):
    result = normalize(stream(event), None, blob)[0]
    assert (result.kind, result.visibility, result.text_blob) == (kind, visibility, text_blob)
    if kind == "message":
        assert result.role == "assistant"
    if text_blob and kind != "error":
        assert "text" not in result.native["item"]
