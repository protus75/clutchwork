"""Normalize Antigravity stream JSON lines into evidence events without I/O."""

import json
from collections.abc import Callable

from clutch.evidence.schema import Event

NORMALIZER_ID = "antigravity-stream/1"
VERIFIED_PROVIDERS = frozenset({"antigravity"})
TOOL_CLASSES = {
    "read_file": "read",
    "write_file": "write",
    "edit_file": "edit",
    "run_command": "shell",
    "grep_search": "search",
    "find_by_name": "list",
    "list_dir": "list",
    "search_web": "web_search",
    "read_url_content": "web_fetch",
    "invoke_subagent": "subagent",
}


def _tokens(usage):
    return {
        "input_uncached": usage.get("input_tokens"),
        "input_cache_read": usage.get("cache_read_tokens"),
        "input_cache_write": None,
        "output_total": usage.get("output_tokens"),
        "output_reasoning": usage.get("thinking_tokens"),
        "tokenizer": "antigravity",
    }


def normalize(stdout: bytes, times_ns: list[int] | None, put_blob: Callable[[bytes], str]) -> list[Event]:
    events, tools, chunks = [], {}, []
    init_model = None
    for seq, line in enumerate(stdout.decode("utf-8", errors="replace").splitlines()):
        try:
            native = json.loads(line)
        except ValueError:
            native = {"line": line}
        if not isinstance(native, dict):
            native = {"line": line}
        native_type = native.get("event", "unknown")
        kind, data = "unknown", {}
        if native_type == "init":
            kind = "session_start"
            model = (native.get("init") or {}).get("model")
            if isinstance(model, str) and model:
                init_model = model
        elif native_type == "step_update":
            su = native.get("step_update") or {}
            step_type, state = su.get("step_type"), su.get("state")
            if step_type == "user_input":
                kind, data = "message", {"role": "user"}
            elif step_type == "tool" and state in ("ACTIVE", "DONE"):
                info = su.get("tool_info") or {}
                tool_id = str(su.get("step_index", seq))
                name = su.get("tool_name") or info.get("name") or "unknown"
                tool = {"id": tool_id, "class": TOOL_CLASSES.get(name, "other"), "native": name}
                if state == "ACTIVE":
                    kind = "tool_call"
                    tools[tool_id] = tool
                    args = info.get("parameters")
                    data = {"tool": tool, "args": args if isinstance(args, dict) else {}}
                else:
                    kind = "tool_result"
                    output = info.get("output")
                    data = {
                        "tool": tools.get(tool_id, tool),
                        "status": "error" if su.get("error") or info.get("error") else "success",
                        "output_blob": put_blob(output.encode()) if isinstance(output, str) else None,
                    }
                    native = {**native, "step_update": {**su, "tool_info": {k: v for k, v in info.items() if k != "output"}}}
            elif step_type == "agent_response":
                delta = su.get("text_delta")
                if isinstance(delta, str):
                    kind = "message"
                    chunks.append(delta)
                    data = {"role": "assistant", "text_blob": put_blob(delta.encode())}
                    native = {**native, "step_update": {k: v for k, v in su.items() if k != "text_delta"}}
                elif state == "DONE":
                    kind = "usage"
                    if su.get("usage") is not None:
                        data = {"tokens": _tokens(su["usage"])}
        elif native_type == "result":
            kind = "result"
            res = native.get("result") or {}
            success = res.get("status") == "SUCCESS"
            message = (res.get("response") if isinstance(res.get("response"), str) else "".join(chunks)) if success else (res.get("error") or res.get("status") or "error")
            data = {"status": "success" if success else "error", "text_blob": put_blob(str(message).encode()), "model": init_model, "tokens": _tokens(res.get("usage") or {})}
            native = {**native, "result": {k: v for k, v in res.items() if k != "response"}}
        events.append(
            Event.model_validate(
                {
                    "schema": "clutch.evidence.events/1.0",
                    "seq": seq,
                    "t_ms": times_ns[seq] // 1_000_000 if times_ns is not None else 0,
                    "kind": kind,
                    "native_type": native_type,
                    "native": native,
                    **data,
                }
            )
        )
    return events
