"""Normalize Gemini stream JSON lines into evidence events without I/O."""

import json
from collections.abc import Callable

from clutch.evidence.schema import Event

NORMALIZER_ID = "gemini-stream/1"
TOOL_CLASSES = {"read_file": "read", "write_file": "write", "run_shell_command": "shell", "update_topic": "plan"}


def normalize(stdout: bytes, times_ns: list[int] | None, put_blob: Callable[[bytes], str]) -> list[Event]:
    events = []
    tools = {}
    chunks = []
    last_error = None
    for seq, line in enumerate(stdout.decode("utf-8", errors="replace").splitlines()):
        try:
            native = json.loads(line)
        except ValueError:
            native = {"line": line}
        if not isinstance(native, dict):
            native = {"line": line}
        native_type = native.get("type", "unknown")
        kind = "unknown"
        data = {}
        if native_type == "init":
            kind = "session_start"
        elif native_type == "message":
            kind = "message"
            if native.get("role") == "assistant":
                chunks.append(native["content"])
            data = {"role": native["role"], "text_blob": put_blob(native["content"].encode())}
            native = {k: v for k, v in native.items() if k != "content"}
        elif native_type == "tool_use":
            kind = "tool_call"
            name, tool_id = native["tool_name"], native["tool_id"]
            tool = {"id": tool_id, "class": TOOL_CLASSES.get(name, "other"), "native": name}
            tools[tool_id] = tool
            data = {"tool": tool, "args": native["parameters"]}
        elif native_type == "tool_result":
            kind = "tool_result"
            tool_id = native["tool_id"]
            tool = tools.get(tool_id, {"id": tool_id, "class": "other", "native": "unknown"})
            data = {"tool": tool, "status": native.get("status"), "output_blob": put_blob(native["output"].encode()) if "output" in native else None}
            native = {k: v for k, v in native.items() if k != "output"}
        elif native_type == "error":
            kind = "error"
            last_error = native.get("message")
            data = {"text_blob": put_blob(str(last_error).encode())}
        elif native_type == "result":
            kind = "result"
            stats = native.get("stats") or {}
            models = stats.get("models") or {}
            success = native.get("status") == "success"
            message = "".join(chunks) if success else (native.get("error") or {}).get("message") or last_error or native.get("status")
            data = {
                "status": "success" if success else "error",
                "text_blob": put_blob(str(message).encode()),
                "model": next(iter(models)) if len(models) == 1 else None,
                "tokens": {
                    "input_uncached": stats.get("input"),
                    "input_cache_read": stats.get("cached"),
                    "input_cache_write": None,
                    "output_total": stats.get("output_tokens"),
                    "output_reasoning": None,
                    "tokenizer": "gemini",
                },
            }
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
