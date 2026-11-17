"""Normalize Codex JSON lines into evidence events without performing I/O."""

import json
from collections.abc import Callable

from clutch.evidence.schema import Event

NORMALIZER_ID = "codex-stream/1"
INPUT_INCLUDES_CACHED = True


def normalize(stdout: bytes, times_ns: list[int] | None, put_blob: Callable[[bytes], str]) -> list[Event]:
    events = []
    for seq, line in enumerate(stdout.decode("utf-8", errors="replace").splitlines()):
        try:
            native = json.loads(line)
        except ValueError:
            native = {"line": line}
        if not isinstance(native, dict):
            native = {"line": line}
        native_type = native.get("type", "unknown")
        item = native.get("item") or {}
        item_type = item.get("type")
        data = {}
        kind = "unknown"
        if native_type == "thread.started":
            kind = "session_start"
        elif native_type == "item.started" and item_type == "command_execution":
            kind = "tool_call"
            data = {"tool": {"id": item["id"], "class": "shell", "native": item_type}, "args": {"command": item["command"]}}
        elif native_type == "item.completed" and item_type == "command_execution":
            kind = "tool_result"
            data = {"tool": {"id": item["id"], "class": "shell", "native": item_type}, "status": item.get("status"), "output_blob": put_blob(item.get("aggregated_output", "").encode())}
        elif native_type == "item.completed" and item_type == "file_change":
            kind = "file_change"
        elif native_type == "item.completed" and item_type == "agent_message":
            kind = "message"
            data = {"role": "assistant", "text_blob": put_blob(item["text"].encode())}
        elif native_type == "item.completed" and item_type == "reasoning":
            kind = "reasoning"
            if "text" in item:
                data = {"visibility": "summary", "text_blob": put_blob(item["text"].encode())}
            else:
                data = {"visibility": "count_only"}
        elif native_type == "turn.completed":
            kind = "usage"
            usage = native.get("usage") or {}
            total, cached = usage.get("input_tokens"), usage.get("cached_input_tokens")
            uncached = total if not INPUT_INCLUDES_CACHED else (total - cached if total is not None and cached is not None else None)
            data = {
                "tokens": {
                    "input_uncached": uncached,
                    "input_cache_read": cached,
                    "input_cache_write": usage.get("cache_write_input_tokens"),
                    "output_total": usage.get("output_tokens"),
                    "output_reasoning": usage.get("reasoning_output_tokens"),
                    "tokenizer": "openai-o200k",
                }
            }
        elif native_type in ("turn.failed", "error"):
            kind = "error"
        if kind in ("tool_call", "tool_result", "message", "reasoning"):
            native = {**native, "item": {k: v for k, v in item.items() if k not in ("aggregated_output", "text")}}
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
