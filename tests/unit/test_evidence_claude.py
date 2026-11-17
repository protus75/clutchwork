import json

import pytest

from clutch.evidence.claude import NORMALIZER_ID, VERIFIED_PROVIDERS, normalize
from clutch.evidence.schema import Event


def run(*lines, times=None):
    blobs = []

    def put(data):
        blobs.append(data)
        return f"sha256:{len(blobs)}"

    raw = "\n".join(json.dumps(line) if not isinstance(line, str) else line for line in lines).encode()
    return normalize(raw, times, put), blobs


def message(role, *blocks):
    return {"type": role, "message": {"content": list(blocks)}}


def test_blocks_and_init():
    init = {"type": "system", "subtype": "init"}
    blocks = message("assistant", {"type": "text", "text": "hello"}, {"type": "thinking", "thinking": "ponder"}, {"type": "tool_use", "id": "id1", "name": "Bash", "input": {"command": "pwd"}})
    events, blobs = run(init, blocks, times=[0, 5_000_000])
    assert [e.kind for e in events] == ["session_start", "message", "reasoning", "tool_call"]
    assert [e.seq for e in events] == [0, 1, 2, 3]
    assert [e.t_ms for e in events] == [0, 5, 5, 5]
    assert events[1].role == "assistant" and events[1].text_blob == "sha256:1"
    assert events[2].visibility == "text" and events[2].text_blob == "sha256:2"
    assert blobs == [b"hello", b"ponder"]
    assert all(Event.model_validate(e.model_dump(by_alias=True)) == e for e in events)
    assert "hello" not in str(events[1].native) and "ponder" not in str(events[2].native)


@pytest.mark.parametrize(
    ("name", "cls"),
    [
        ("Bash", "shell"),
        ("Read", "read"),
        ("Grep", "search"),
        ("Glob", "list"),
        ("Edit", "edit"),
        ("MultiEdit", "edit"),
        ("NotebookEdit", "edit"),
        ("Write", "write"),
        ("WebFetch", "web_fetch"),
        ("WebSearch", "web_search"),
        ("Task", "subagent"),
        ("TodoWrite", "plan"),
        ("mcp__x__y", "mcp"),
        ("odd", "other"),
    ],
)
def test_tools(name, cls):
    events, _ = run(message("assistant", {"type": "tool_use", "id": "tool-3", "name": name, "input": {"x": 7}}))
    assert events[0].tool.model_dump(by_alias=True) == {"id": "tool-3", "class": cls, "native": name}
    assert events[0].args == {"x": 7}


def test_results():
    events, blobs = run(
        message(
            "user",
            {"type": "tool_result", "tool_use_id": "a", "is_error": True, "content": "bad"},
            {"type": "tool_result", "tool_use_id": "b", "content": [{"type": "text", "text": "one"}, {"type": "text", "text": "two"}]},
        )
    )
    assert [e.status for e in events] == ["error", "ok"]
    assert [e.tool.id for e in events] == ["a", "b"]
    assert [e.output_blob for e in events] == ["sha256:1", "sha256:2"]
    assert blobs == [b"bad", b"one\ntwo"]
    assert "bad" not in str(events[0].native)


def test_usage():
    events, _ = run(
        {"type": "result", "usage": {"input_tokens": 10, "cache_read_input_tokens": 90, "output_tokens": 5}},
        {"type": "result", "usage": {"cache_creation_input_tokens": 8, "output_tokens_details": {"thinking_tokens": 3}}},
    )
    assert [e.kind for e in events] == ["usage", "result", "usage", "result"]
    assert events[0].tokens == {"input_uncached": 10, "input_cache_read": 90, "input_cache_write": None, "output_total": 5, "output_reasoning": None, "tokenizer": "anthropic"}
    assert events[2].tokens["input_cache_write"] == 8 and events[2].tokens["output_reasoning"] == 3
    assert all(e.t_ms == 0 for e in events)


def test_other_lines_and_blocks():
    unknown = {"type": "new", "data": 42}
    events, _ = run(
        {"type": "rate_limit_event"},
        {"type": "system", "subtype": "permission_denied"},
        {"type": "system", "subtype": "thinking_tokens", "estimated_tokens": 17},
        unknown,
        "not json",
        message("assistant", {"type": "future", "data": 4}),
        "42",
    )
    assert [e.kind for e in events] == ["rate_limit", "permission_denied", "reasoning", "unknown", "unknown", "unknown", "unknown"]
    assert events[2].visibility == "count_only" and events[2].tokens == 17
    assert events[3].native == unknown and events[4].native == {"line": "not json"}
    assert events[5].native["message"]["content"] == [{"type": "future", "data": 4}]
    assert events[6].native == {"line": "42"}
    assert NORMALIZER_ID == "claude-stream/1" and VERIFIED_PROVIDERS == frozenset({"claude"})
