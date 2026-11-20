# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test evidence gemini
# relates: [clutch/evidence/gemini.py, clutch/evidence/schema.py]
# owner: engine
# verified: 0a308920
# hash: 6b3d44bc86700d9e954afc995d2c6d7d4ff1835ad1d563a1365d30550780d159
import json

from clutch.evidence.gemini import NORMALIZER_ID, normalize
from clutch.evidence.schema import Event


def stream(*lines):
    return "\n".join(json.dumps(line) if not isinstance(line, str) else line for line in lines).encode()


def blob(value):
    return "blob:" + value.decode()


def test_session_messages_and_times():
    lines = stream(
        {"type": "init", "session_id": "s"}, {"type": "message", "role": "assistant", "content": "first", "delta": True}, {"type": "message", "role": "assistant", "content": "second", "delta": True}
    )
    events = normalize(lines, [0, 5_000_000, 9_000_000], blob)
    assert NORMALIZER_ID == "gemini-stream/1"
    assert [e.kind for e in events] == ["session_start", "message", "message"]
    assert events[0].native_type == "init"
    assert [e.seq for e in events] == [0, 1, 2]
    assert [e.t_ms for e in events] == [0, 5, 9]
    assert [(e.role, e.text_blob) for e in events[1:]] == [("assistant", "blob:first"), ("assistant", "blob:second")]
    assert all("content" not in e.native for e in events[1:])
    assert all(Event.model_validate(e.model_dump(by_alias=True)) == e for e in events)
    assert [e.t_ms for e in normalize(lines, None, blob)] == [0, 0, 0]


def test_tools_and_results():
    calls = [
        {"type": "tool_use", "tool_id": str(i), "tool_name": name, "parameters": {"value": i}}
        for i, name in enumerate(["run_shell_command", "write_file", "made_up_tool", "read_file", "update_topic"])
    ]
    results = [
        {"type": "tool_result", "tool_id": "0", "status": "success", "output": "out"},
        {"type": "tool_result", "tool_id": "1", "status": "error"},
        {"type": "tool_result", "tool_id": "2", "status": "success", "output": ""},
        {"type": "tool_result", "tool_id": "missing", "status": "error"},
    ]
    events = normalize(stream(*calls, *results), None, blob)
    assert [e.kind for e in events] == ["tool_call"] * 5 + ["tool_result"] * 4
    assert [(e.tool.id, e.tool.class_, e.tool.native) for e in events[:5]] == [
        ("0", "shell", "run_shell_command"),
        ("1", "write", "write_file"),
        ("2", "other", "made_up_tool"),
        ("3", "read", "read_file"),
        ("4", "plan", "update_topic"),
    ]
    assert [e.args for e in events[:5]] == [{"value": i} for i in range(5)]
    assert [e.tool for e in events[5:8]] == [e.tool for e in events[:3]]
    assert (events[8].tool.id, events[8].tool.class_, events[8].tool.native) == ("missing", "other", "unknown")
    assert [e.status for e in events[5:]] == ["success", "error", "success", "error"]
    assert [e.output_blob for e in events[5:]] == ["blob:out", None, "blob:", None]
    assert all("output" not in e.native for e in events[5:])


def test_results():
    success, failure = normalize(
        stream({"type": "result", "status": "success", "stats": {"input_tokens": 100, "cached": 40, "input": 60, "output_tokens": 7, "total_tokens": 120}}, {"type": "result", "status": "error"}),
        None,
        blob,
    )
    assert (success.kind, success.status) == ("result", "success")
    assert success.tokens == {"input_uncached": 60, "input_cache_read": 40, "input_cache_write": None, "output_total": 7, "output_reasoning": None, "tokenizer": "gemini"}
    assert (failure.kind, failure.status) == ("result", "error")
    assert failure.tokens == {"input_uncached": None, "input_cache_read": None, "input_cache_write": None, "output_total": None, "output_reasoning": None, "tokenizer": "gemini"}


def test_unknown_and_error():
    events = normalize(stream({"type": "error", "message": "bad"}, {"type": "future", "value": 3}, "not json", "[]"), None, blob)
    assert [e.kind for e in events] == ["error", "unknown", "unknown", "unknown"]
    assert [e.native for e in events] == [{"type": "error", "message": "bad"}, {"type": "future", "value": 3}, {"line": "not json"}, {"line": "[]"}]
