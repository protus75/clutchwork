"""Versioned evidence records and their generated schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Engine(Record):
    version: str
    spec: str
    spec_version: str


class Route(Record):
    tier: str
    effort: str
    candidates: list[str]
    chosen: str
    reason: Literal["first", "spill", "failover"]
    config_sha: str


class Provider(Record):
    name: str
    adapter: str
    kind: str
    package: str | None
    cli_version: str | None
    billing: Literal["metered", "subscription", "local"]


class Process(Record):
    argv: list[str]
    env_names: list[str]
    cwd: str
    timeout_s: int
    writes: bool
    isolated: bool
    conduct_file: str | None


class StartRepo(Record):
    main_sha: str
    base_sha: str
    tree_before: str


class Prompt(Record):
    blob: str
    chars: int
    bytes: int


class StartClock(Record):
    wall_start: str
    mono_start_ns: int


class StartModel(Record):
    requested: str


class Start(Record):
    schema_: Literal["clutch.evidence.call/1.0"] = Field(alias="schema")
    id: str
    group: str
    stem: str | None
    run_seq: int | str
    attempt: int
    surface: str
    call: int
    engine: Engine
    route: Route
    provider: Provider
    model: StartModel
    process: Process
    repo: StartRepo | None
    prompt: Prompt
    clock: StartClock


class Exit(Record):
    status: Literal["ok", "nonzero", "killed", "timeout", "spawn_error"]
    code: int | None
    signal: int | None
    failure_class: str | None


class EndClock(Record):
    wall_end: str
    mono_end_ns: int
    wall_ms: int


class Rusage(Record):
    user_s: float
    sys_s: float
    max_rss_kb: int


class Raw(Record):
    stdout: str
    stderr: str
    stdout_times: str
    lines: int
    non_json_lines: int


class EndRepo(Record):
    tree_after: str
    changed_paths: list[str]


class EndModel(Record):
    served: str | None
    served_source: Literal["stream", "none"]


class NativeIds(Record):
    session_id: str | None
    thread_id: str | None


class Parsed(Record):
    text_chars: int
    input_tokens: int | None
    output_tokens: int | None
    usd: float | None


class End(Record):
    schema_: Literal["clutch.evidence.call/1.0"] = Field(alias="schema")
    id: str
    exit: Exit
    clock: EndClock
    rusage: Rusage | None
    raw: Raw
    repo: EndRepo | None
    model: EndModel
    native_ids: NativeIds
    parsed: Parsed


class Tool(Record):
    id: str
    class_: Literal["read", "search", "list", "edit", "write", "shell", "web_fetch", "web_search", "mcp", "subagent", "plan", "other"] = Field(alias="class")
    native: str


class Event(Record):
    schema_: Literal["clutch.evidence.events/1.0"] = Field(alias="schema")
    seq: int
    t_ms: int
    kind: Literal["session_start", "message", "reasoning", "tool_call", "tool_result", "file_change", "usage", "rate_limit", "permission_denied", "error", "result", "unknown"]
    role: str | None = None
    tool: Tool | None = None
    args: dict[str, Any] | None = None
    args_blob: str | None = None
    status: str | None = None
    output_blob: str | None = None
    text_blob: str | None = None
    tokens: dict[str, Any] | int | None = None
    visibility: Literal["text", "summary", "count_only", "none"] | None = None
    native_type: str
    native: dict[str, Any]


class Attempt(Record):
    schema_: Literal["clutch.evidence.attempt/1.0"] = Field(alias="schema")
    stem: str
    run_seq: int
    attempt: int
    base_sha: str
    head_sha: str
    diff_blob: str
    check_outputs: dict[str, str]
    call_keys: list[str]
    outcome: str
    reason: str | None
    findings: list[dict[str, Any]]
    engine_versions: list[str]
    spec_versions: dict[str, str]


def json_schema(record: Literal["start", "end", "event"]) -> dict[str, Any]:
    return {"start": Start, "end": End, "event": Event}[record].model_json_schema()
