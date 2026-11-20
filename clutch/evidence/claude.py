"""Normalize Claude stream JSON without performing I/O."""

import json
from collections.abc import Callable

from clutch.evidence.schema import Event

NORMALIZER_ID = "claude-stream/1"
VERIFIED_PROVIDERS = frozenset({"claude"})

_TOOL_CLASSES = {
    "Read": "read",
    "Grep": "search",
    "Glob": "list",
    "Edit": "edit",
    "MultiEdit": "edit",
    "NotebookEdit": "edit",
    "Write": "write",
    "Bash": "shell",
    "WebFetch": "web_fetch",
    "WebSearch": "web_search",
    "Task": "subagent",
    "TodoWrite": "plan",
}


def normalize(stdout: bytes, times_ns: list[int] | None, put_blob: Callable[[bytes], str]) -> list[Event]:
    events = []
    for index, line in enumerate(stdout.decode("utf-8", errors="replace").splitlines()):
        try:
            native = json.loads(line)
        except ValueError:
            native = {"line": line}
        if not isinstance(native, dict):
            native = {"line": line}
        typ = native.get("type", "unknown")
        t_ms = times_ns[index] // 1_000_000 if times_ns is not None else 0

        def emit(kind, native_type, payload, **data):
            events.append(
                Event.model_validate(
                    {
                        "schema": "clutch.evidence.events/1.0",
                        "seq": len(events),
                        "t_ms": t_ms,
                        "kind": kind,
                        "native_type": native_type,
                        "native": payload,
                        **data,
                    }
                )
            )

        if typ == "system" and native.get("subtype") == "init":
            emit("session_start", "system/init", native)
        elif typ == "system" and native.get("subtype") == "thinking_tokens":
            emit("reasoning", "system/thinking_tokens", native, visibility="count_only", tokens=native.get("estimated_tokens"))
        elif typ == "system" and native.get("subtype") == "permission_denied":
            emit("permission_denied", "system/permission_denied", native)
        elif typ in ("assistant", "user") and isinstance(native.get("message"), dict) and isinstance(native["message"].get("content"), list):
            for block in native["message"]["content"]:
                block_type = block.get("type") if isinstance(block, dict) else None
                native_type = f"{typ}/{block_type}"
                if typ == "assistant" and block_type in ("text", "thinking"):
                    field = "text" if block_type == "text" else "thinking"
                    payload = {**native, "message": {**native["message"], "content": [{k: v for k, v in block.items() if k != field}]}}
                    blob = put_blob(block[field].encode())
                    if block_type == "text":
                        emit("message", native_type, payload, role="assistant", text_blob=blob)
                    else:
                        emit("reasoning", native_type, payload, visibility="text", text_blob=blob)
                elif typ == "assistant" and block_type == "tool_use" and all(k in block for k in ("id", "name", "input")):
                    name = block["name"]
                    cls = _TOOL_CLASSES.get(name, "mcp" if name.startswith("mcp__") else "other")
                    payload = {**native, "message": {**native["message"], "content": [block]}}
                    emit("tool_call", native_type, payload, tool={"id": block["id"], "class": cls, "native": name}, args=block["input"])
                elif typ == "user" and block_type == "tool_result" and "tool_use_id" in block:
                    content = block.get("content", "")
                    output = content if isinstance(content, str) else "\n".join(part.get("text", "") for part in content if part.get("type") == "text")
                    payload = {k: v for k, v in native.items() if k != "tool_use_result"}
                    payload["message"] = {**native["message"], "content": [{k: v for k, v in block.items() if k != "content"}]}
                    emit(
                        "tool_result",
                        native_type,
                        payload,
                        tool={"id": block["tool_use_id"], "class": "other", "native": "tool_result"},
                        status="error" if block.get("is_error") else "ok",
                        output_blob=put_blob(output.encode()),
                    )
                else:
                    emit("unknown", native_type, {**native, "message": {**native["message"], "content": [block]}})
        elif typ == "rate_limit_event":
            emit("rate_limit", typ, native)
        elif typ == "result":
            usage = native.get("usage") or {}
            details = usage.get("output_tokens_details") or {}
            payload = {k: v for k, v in native.items() if k != "result"}
            emit(
                "usage",
                typ,
                payload,
                tokens={
                    "input_uncached": usage.get("input_tokens"),
                    "input_cache_read": usage.get("cache_read_input_tokens"),
                    "input_cache_write": usage.get("cache_creation_input_tokens"),
                    "output_total": usage.get("output_tokens"),
                    "output_reasoning": details.get("thinking_tokens"),
                    "tokenizer": "anthropic",
                },
            )
            emit(
                "result",
                typ,
                payload,
                status="success" if native.get("subtype") == "success" and not native.get("is_error") else "error",
                text_blob=put_blob(str(native.get("result", "")).encode()),
                usd=native.get("total_cost_usd"),
            )
        else:
            emit("unknown", typ, native)
    return events
