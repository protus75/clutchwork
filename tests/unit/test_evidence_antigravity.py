# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that the Antigravity stream normalizer maps agy events to evidence kinds, tool classes, blobs, token fields and error results.
# relates: [clutch/evidence/antigravity.py]
# owner: clutch/evidence/antigravity.py
# verified: 69d790e1
# hash: 41f73dcde98ea401efc258b24c3d3b984f7886db10b9ddfa379cebfd32abc5c3
import json

from clutch.evidence.antigravity import NORMALIZER_ID, normalize


def test_stream():
    lines = [
        {"event": "init", "init": {"model": "served"}},
        {"event": "step_update", "step_update": {"step_type": "user_input"}},
        {"event": "step_update", "step_update": {"step_type": "tool", "state": "ACTIVE", "step_index": 5, "tool_name": "read_file", "tool_info": {"parameters": {"Path": "x"}}}},
        {"event": "step_update", "step_update": {"step_type": "tool", "state": "DONE", "step_index": 5, "tool_info": {"output": "content"}}},
        {"event": "step_update", "step_update": {"step_type": "agent_response", "text_delta": "hello"}},
        {"event": "step_update", "step_update": {"step_type": "agent_response", "state": "DONE"}},
        {"event": "result", "result": {"status": "SUCCESS", "usage": {"input_tokens": 12, "cache_read_tokens": 5, "output_tokens": 3, "thinking_tokens": 2}}},
    ]
    events = normalize("\n".join(map(json.dumps, lines)).encode(), [1000000] * len(lines), lambda b: "blob:" + b.decode())
    assert NORMALIZER_ID == "antigravity-stream/1"
    assert [e.kind for e in events] == ["session_start", "message", "tool_call", "tool_result", "message", "usage", "result"]
    assert events[2].tool.class_ == "read" and events[3].tool == events[2].tool
    assert events[3].output_blob == "blob:content" and "output" not in events[3].native["step_update"]["tool_info"]
    assert events[4].text_blob == "blob:hello" and events[5].status is None
    assert events[-1].model == "served" and events[-1].text_blob == "blob:hello"
    assert events[-1].tokens == {"input_uncached": 12, "input_cache_read": 5, "input_cache_write": None, "output_total": 3, "output_reasoning": 2, "tokenizer": "antigravity"}
    assert all(e.t_ms == 1 for e in events)
    err = normalize(b'{"event":"result","result":{"status":"ERROR","error":"bad"}}\n[]', None, lambda b: b.decode())
    assert (err[0].status, err[0].text_blob, err[1].kind) == ("error", "bad", "unknown")
