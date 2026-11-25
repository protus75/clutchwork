---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
- events-once-cursor

## Context
- docs/antigravity-plan.md#3. Clutch MCP server vs. direct CLI boundary
- docs/antigravity-plan.md#Risks
- docs/antigravity-plan.md#Open decisions
- clutch/runner.py::Refusal
- clutch/events.py::wait_once
- clutch/observe.py::snapshot
- clutch/status.py::project
- clutch/stats.py
- clutch/roadmap.py::status
- clutch/evidence/store.py::EvidenceStore
- clutch/evidence/views.py::show_lines
- clutch/context.py
- clutch/ask.py
- tests/unit/test_main_help.py
- tests/unit/test_host_running.py
- tests/unit/test_readme.py
- tests/unit/test_tickets_tolerant_reader.py
- tests/unit/test_context_suggest_verb.py
- tests/unit/test_main_prompt_host.py

## On-demand
- clutch/__main__.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- README.md

## Goal / Why
Roadmap row 220 (`mcp-read-server`, `docs/antigravity-plan.md` §3, Risks #2 and #5, Open decisions #2). Agents supervising ClutchWork in Antigravity currently invoke `clutch` CLI subprocesses in sandboxed shells where `~/.local/bin` may be missing from `PATH`, commands require approval prefixes, and outputs like `view status` and `roadmap status` require fragile text parsing.

After this ticket:
- `clutch/mcp.py` implements a pure-Python stdio JSON-RPC 2.0 MCP server using existing `pydantic` schemas (zero new core dependencies) and injectable I/O, clock, sleep, git, exec, and DuckDB connection seams so it is unit-testable under `clutch.testguard`.
- `clutch mcp serve` launches the stdio server regardless of whether the invocation CWD is a Clutch checkout.
- The server exposes the nine read-only tools (`clutch_snapshot`, `clutch_status`, `clutch_stats`, `clutch_roadmap_status`, `clutch_wait_event`, `clutch_evidence_captures`, `clutch_evidence_show`, `clutch_context_suggest`, `clutch_prompt`) and MCP Prompts (`prompts/list`, `prompts/get`) for `clutch/specs/ask/*.md`, each routing an optional `repo` path (defaulting to CWD and validated as an existing directory containing `tickets/`).
- `Refusal` and domain errors map to structured MCP tool errors (`isError: true` with `structuredContent` holding `code`, `message`, and `paved_road`), and `clutch_status` includes the running `clutchwork` package version so stale server processes after an upgrade are visible immediately.

Rejected simpler approach: shelling out to `clutch` CLI subcommands inside an MCP wrapper or adding the third-party `mcp` PyPI SDK. Subprocesses reintroduce sandbox `PATH` and text-scraping fragility (`docs/antigravity-plan.md` §3), while adding the `mcp` SDK adds core dependency weight and obscures direct `_meta` control (`Open decisions #2`).

## Boundary contract

### Structured `Refusal` attributes
- disposition: extend
- owner: clutch/runner.py
- consumers: `clutch/mcp.py`, `clutch/__main__.py`
- observable change: `Refusal.__init__(self, message: str, paved_road: str, *, code: str = "refusal")` stores `self.message = message`, `self.paved_road = paved_road`, and `self.code = code` while preserving `super().__init__(f"{message} -- {paved_road}")`.
- compatibility: additive; all existing 2-argument `Refusal(message, paved_road)` callers and `str(exc)` formatting remain identical.
- acceptance: criterion 3
- tests: tests/unit/test_mcp_tools.py
- post-merge source of truth: clutch/runner.py

### Shared stats collection
- disposition: extend
- owner: clutch/stats.py
- consumers: `clutch/__main__.py::_stats`, `clutch/mcp.py`
- observable change: adds `async def collect_stats(checkout, events, now, window)` loading ticket `kind` via `tickets.read_tolerant` and `checks.json` invoices via `checkout.git._run(checkout.repo, "show", ...)` before calling `project_stats(...)`, and delegates `clutch/__main__.py::_stats` to it without duplicating collection logic.
- compatibility: `clutch/__main__.py::_stats` preserves its exact signature and behavior (including existing `stats.project_stats` monkeypatching in `tests/unit/test_tickets_tolerant_reader.py`).
- acceptance: criterion 2 and criterion 6
- tests: tests/unit/test_mcp_tools.py, tests/unit/test_tickets_tolerant_reader.py
- post-merge source of truth: clutch/stats.py

### Shared context suggestion by stem
- disposition: extend
- owner: clutch/context.py
- consumers: `clutch/__main__.py::_run_context_suggest`, `clutch/mcp.py`
- observable change: adds `suggest_for_stem(state_dir: Path, root: Path, stem: str, *, fs, connect=duckdb.connect) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]` validating the stem, reading `tickets/<stem>/ticket.md`, validating `Goal / Why` and `Scope fence`, querying `<state_dir>/index.duckdb` via `connect(..., read_only=True)`, and raising `runner.Refusal(..., code=...)` for `invalid_stem`, `missing_ticket`, `missing_section`, `no_index`, and `index_unreadable`; `clutch/__main__.py::_run_context_suggest` delegates to it.
- compatibility: `clutch/__main__.py::_run_context_suggest` keeps its exact signature, stdout, stderr messages, and exit codes (0, 1, 2).
- acceptance: criterion 2, criterion 3, and criterion 6
- tests: tests/unit/test_mcp_tools.py, tests/unit/test_context_suggest_verb.py, tests/unit/test_context_suggest_require.py
- post-merge source of truth: clutch/context.py

### Shared prompt resolution
- disposition: extend
- owner: clutch/ask.py
- consumers: `clutch/__main__.py::handle_prompt`, `clutch/mcp.py`
- observable change: adds `resolve_prompt(kind: str, stems: Sequence[str], *, name: str | None = None, config: Config, repo: Path, running_stems: Callable[[], Collection[str]] = ..., draft_stems: Callable[[], Sequence[str]] = ...) -> tuple[str, dict | None]` encapsulating `list` (returning `catalog` payload), `host`, `drafts`, `box`, `none`-taking, and `stem`-taking resolution (including `diagnose` -> `running` when the stem is live) and raising `runner.Refusal(..., code=...)` on invalid kind/stem/arguments or missing ticket/host prompt; `clutch/__main__.py::handle_prompt` delegates to it.
- compatibility: `KINDS`, `DESCRIPTIONS`, `TAKES`, `render`, `catalog`, and `render_host` signatures and outputs remain unchanged; `clutch prompt` CLI output and exit codes remain identical.
- acceptance: criterion 2, criterion 3, criterion 4, and criterion 6
- tests: tests/unit/test_mcp_tools.py, tests/unit/test_main_prompt_host.py, tests/unit/test_ask_host_prompts.py
- post-merge source of truth: clutch/ask.py

### Read-only stdio MCP server
- disposition: create
- owner: clutch/mcp.py
- consumers: `clutch/__main__.py::handle_mcp_serve`, Antigravity and MCP clients, future `mcp-control-and-tickets` and `mcp-app-dashboard`
- closest existing: `clutch/observe.py` and `clutch/__main__.py` only expose CLI text/JSON handlers rather than a JSON-RPC 2.0 protocol loop, tool schemas, or MCP prompt endpoints.
- earning reason: Antigravity MCP integration introduces an external stdio JSON-RPC 2.0 protocol boundary reused across `mcp-read-server`, `mcp-control-and-tickets`, and `mcp-app-dashboard`.
- observable change: provides line-delimited JSON-RPC 2.0 stdio transport (`serve_stdio`, `ClutchMCPServer`) handling `initialize`, `notifications/*` (no response emitted), `ping`, `tools/list`, `tools/call`, `prompts/list`, and `prompts/get`; validates tool arguments with Pydantic `BaseModel` schemas (`extra="forbid"`), validates `repo` (default CWD, must exist and contain `tickets/`), exposes the 9 read-only tools returning concise text `content` plus typed `structuredContent`, exposes `prompts/list` / `prompts/get` for `ask.KINDS` (`clutch/specs/ask/*.md`), includes `importlib.metadata.version("clutchwork")` in `clutch_status`, and maps `Refusal`, `ConfigError`, `JournalCorruption`, `GitError`, and domain `ValueError` failures in tool calls to `isError: true` with `structuredContent: {"code": ..., "message": ..., "paved_road": ...}`.
- compatibility: additive; zero new core dependencies in `pyproject.toml`.
- acceptance: criteria 1, 2, 3, and 4
- tests: tests/unit/test_mcp_protocol.py, tests/unit/test_mcp_tools.py, tests/integration/test_mcp_read_server.py
- post-merge source of truth: clutch/mcp.py

### `clutch mcp serve` CLI and verb docs
- disposition: extend
- owner: clutch/__main__.py, clutch/docs/host-running.md, docs/how-clutch-works.md, README.md
- consumers: Antigravity MCP config, operators, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_readme.py`
- observable change: adds top-level `mcp` command group and `serve` subcommand via `_command(...)` in `clutch/__main__.py`, dispatches `mcp serve` before `load_config(...)` in `main()` so starting outside a Clutch checkout succeeds, forwards optional `--config` and `cwd` into `mcp.serve_stdio(...)`, and documents `mcp serve` in `clutch/docs/host-running.md` (verb table row), `docs/how-clutch-works.md` section 2.1 (verb table row), and `README.md` (`# Observing`).
- compatibility: all existing CLI groups, verbs, and `_status` / `_stats` / `_run_context_suggest` entrypoints keep their signatures and behavior.
- acceptance: criteria 5, 6, and 7
- tests: tests/unit/test_main_mcp_serve.py, tests/unit/test_main_help.py, tests/unit/test_host_running.py, tests/unit/test_readme.py, tests/integration/test_mcp_read_server.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/runner.py`: store `self.message`, `self.paved_road`, and `self.code` (default `"refusal"`) on `Refusal.__init__`. Nothing else in `clutch/runner.py` changes.
- `clutch/stats.py`: add `async def collect_stats(checkout, events, now, window)` loading ticket kinds and `checks.json` invoices and returning `project_stats(...)`.
- `clutch/context.py`: add `suggest_for_stem(state_dir, root, stem, *, fs, connect=duckdb.connect)` raising `runner.Refusal(..., code=...)` on invalid stem, missing/unreadable ticket, missing/blank `Goal / Why` or `Scope fence`, `no_index`, or `index_unreadable`.
- `clutch/ask.py`: add `resolve_prompt(...)` handling `list`, `host`, `drafts`, `box`, `none`, and `stem` prompts (including `diagnose` -> `running` live check) and raising `runner.Refusal(..., code=...)` on refusal conditions.
- `clutch/mcp.py`: implement pure-Python stdio JSON-RPC 2.0 MCP server (`ClutchMCPServer`, `serve_stdio`, tool/prompt registries and Pydantic input schemas) with injectable `stdin`, `stdout`, `default_cwd`, `config_path`, `env`, `clock`, `sleep`, `monotonic`, `exec_factory`, `git_factory`, and `connect` seams:
  - JSON-RPC 2.0 framing: ignore blank lines; emit no response for notifications (requests without `"id"`); return `-32700` on invalid JSON, `-32600` on invalid request envelope, `-32601` on unknown method, `-32602` on invalid params (unknown tool/prompt name or Pydantic `ValidationError`), and `-32603` on unexpected internal exception.
  - `initialize` returns `protocolVersion` (negotiated from supported versions or `"2025-03-26"`), `capabilities: {"tools": {"listChanged": False}, "prompts": {"listChanged": False}}`, and `serverInfo: {"name": "clutchwork", "version": <package_version>}`. `ping` returns `{}`.
  - `repo` routing: optional `repo: str | None = None` on every tool and prompt argument; defaults to `default_cwd`, rejects blank strings or directories missing `tickets/` with `Refusal(..., code="invalid_repo")`, and loads `config.yaml` (using `config_path` when `repo` is omitted or resolves to `default_cwd`).
  - Tools (`tools/list`, `tools/call`):
    1. `clutch_snapshot(repo=None, all_merged=False)` -> `observe.snapshot(ctx, merged_limit=None if all_merged else config.snapshot_merged_limit)` (with `GIT_OPTIONAL_LOCKS=0`).
    2. `clutch_status(repo=None, short=False)` -> `status.project(...)` + `size_warning(...)` + `version: importlib.metadata.version("clutchwork")` (JSON-normalized `structuredContent` plus `status.render(..., short=short)` text).
    3. `clutch_stats(repo=None, window="7d", tree=False)` -> `stats.window_start` + `stats.collect_stats` (wrapping `stats_tree` in `{"window": window, "tree": ...}` when `tree=True`, mapping bad window `ValueError` to structured refusal `code="invalid_window"`).
    4. `clutch_roadmap_status(repo=None)` -> `roadmap.status(checkout)` returning `{"lines": lines}`.
    5. `clutch_wait_event(repo=None, cursor=None, timeout_seconds=300.0)` -> `events.wait_once(config.state_dir, cursor=cursor, timeout=timeout_seconds, sleep=..., clock=...)` returning `{"cursor": next_cursor, "events": lines, "timed_out": timed_out}` (mapping `ValueError` to `code="invalid_cursor_or_timeout"`).
    6. `clutch_evidence_captures(repo=None, stem, attempt=None, name=None)` -> `EvidenceStore.captures` or `EvidenceStore.get_capture` (refusing `name` without `attempt` and mapping `ValueError`, `CaptureNotFound`, `CaptureUnreadable`, `OSError` to structured `Refusal` errors).
    7. `clutch_evidence_show(repo=None, call_key)` -> `EvidenceStore.read_record` (`start`, optional `end`), `read_normalized`, `views.show_lines`, mapping missing/unreadable/corrupt evidence to structured `Refusal` errors.
    8. `clutch_context_suggest(repo=None, stem)` -> `context.suggest_for_stem(...)` returning `{"stem": stem, "files": [...], "chunks": [...]}`.
    9. `clutch_prompt(repo=None, kind, stems=[], name=None)` -> `ask.resolve_prompt(...)` returning rendered prompt text (or `catalog` items when `kind == "list"`).
  - Tool error mapping: `Refusal`, `ConfigError`, `JournalCorruption`, `GitError`, `UnknownBoxId` inside `tools/call` return JSON-RPC result with `isError: True`, concise text `content`, and `structuredContent: {"code": ..., "message": ..., "paved_road": ...}`.
  - Prompts (`prompts/list`, `prompts/get`): list all `ask.KINDS` (`clutch/specs/ask/*.md`) with descriptions from `ask.DESCRIPTIONS` and declared `arguments` (`repo` optional on all; `stem` required when `ask.TAKES[kind] == "stem"`; `ids` required when `ask.TAKES[kind] == "box"`), and render via `ask.resolve_prompt(...)` in `prompts/get` (mapping domain errors on `prompts/get` to JSON-RPC `-32602` / `-32000` with `data: {"code", "message", "paved_road"}`).
- `clutch/__main__.py`:
  - Add `mcp` command group and `mcp serve` subcommand using `_command(...)` with complete `summary`, `does`, `reads`, `writes`, `lock`, `exits`, and `examples`.
  - Dispatch `mcp serve` in `main()` before `load_config(args.config, cwd=repo)` so `clutch mcp serve` starts even when CWD has no `config.yaml`, forwarding `default_cwd=repo`, `config_path=args.config`, `env=env`, and `clock=clock` to `mcp.serve_stdio(...)` and returning `0` on `KeyboardInterrupt`.
  - Delegate `_stats`, `_run_context_suggest`, and `handle_prompt` to `stats.collect_stats`, `context.suggest_for_stem`, and `ask.resolve_prompt` while preserving their existing signatures, output, and exit codes. Keep `_status` intact so existing monkeypatches on `clutch.__main__.project` remain valid.
- `clutch/docs/host-running.md`: add `| \`mcp serve\` | Yes | Run the read-only stdio JSON-RPC 2.0 MCP server (reads \`repo\` per call or CWD). |` to the verb table.
- `docs/how-clutch-works.md`: add `| \`mcp serve\` | no | Run the pure-Python stdio JSON-RPC 2.0 MCP server exposing read-only observation, event wakeup, evidence, context, and prompt tools and MCP Prompts. |` to the section 2.1 Verbs table.
- `README.md`: add `uv run clutch mcp serve  # run the stdio MCP server` under `# Observing` (keeping all links `https://` and no `./dev.py` above `## Developing clutch`).
- New unit test files `tests/unit/test_mcp_protocol.py`, `tests/unit/test_mcp_tools.py`, and `tests/unit/test_main_mcp_serve.py` using `tmp_path`, `io.StringIO`, and in-memory fakes only (zero real subprocesses, network, or repo file reads).
- New integration test file `tests/integration/test_mcp_read_server.py` reading tracked files only via `Path(__file__).resolve().parents[2]` (zero disk writes, processes, network, or on-disk DuckDB; no `REAL_IO_TESTS` entry).
- Engine-written `# clutch:meta` header lines on newly created files under `tests/` updated by Check's meta step.

Scope out:
- Mutating MCP tools (`ticket_*`, `box_*`, `engine_*`) — deferred to `mcp-control-and-tickets`.
- MCP App UI resource (`ui://clutch/dashboard.html`), `clutch_open_dashboard`, `com.google.antigravity/ui` entrypoints, and `visibility: ["app"]`-only tools — deferred to `mcp-app-dashboard`.
- Updating `clutch/specs/ask/*.md` (`ask-specs-mcp-supervision`), `clutch/help.py` (`ui-shared-renderers`), `vscode-clutchwork/`, or adding dependencies to `pyproject.toml`.
- Adding tests to any of the seven hot test files (`tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`) or existing test files.

## Scope fence
- clutch/runner.py
- clutch/stats.py
- clutch/context.py
- clutch/ask.py
- clutch/mcp.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_mcp_protocol.py
- tests/unit/test_mcp_tools.py
- tests/unit/test_main_mcp_serve.py
- tests/integration/test_mcp_read_server.py

## Acceptance criteria
1. `tests/unit/test_mcp_protocol.py`: `serve_stdio` reads line-delimited JSON-RPC 2.0 requests from an in-memory `stdin`, emits nothing on blank lines or `notifications/initialized`, handles `initialize` (returning `serverInfo.version == importlib.metadata.version("clutchwork")` and `capabilities` with `tools` and `prompts`) and `ping` (`{}`), returns JSON-RPC `-32700` on malformed JSON, `-32600` on non-object or wrong `jsonrpc` version, `-32601` on unknown method, and `-32602` on unknown tool/prompt name or invalid Pydantic arguments (never silently succeeding or crashing the loop on bad input), and exits cleanly on EOF. Verified by `./dev.py test tests/unit/test_mcp_protocol.py`.
2. `tests/unit/test_mcp_tools.py`: `tools/list` returns all nine tool schemas (`clutch_snapshot`, `clutch_status`, `clutch_stats`, `clutch_roadmap_status`, `clutch_wait_event`, `clutch_evidence_captures`, `clutch_evidence_show`, `clutch_context_suggest`, `clutch_prompt`), and `tools/call` exercises each tool against `tmp_path` + in-memory seams returning non-empty `content` text and typed `structuredContent`: `clutch_snapshot` respects `all_merged` and sets `GIT_OPTIONAL_LOCKS=0`; `clutch_status` includes `version` matching `importlib.metadata.version("clutchwork")`, `evidence_warning`, and omits `scorecard` only when `short=True`; `clutch_stats` returns stats or `{"window": ..., "tree": ...}` when `tree=True`; `clutch_roadmap_status` returns `lines`; `clutch_wait_event` passes `cursor` and `timeout_seconds` to `events.wait_once` using injected `sleep`/`clock` seams without calling `time.sleep`; `clutch_evidence_captures` lists pairs or reads a named capture; `clutch_evidence_show` returns `start`, `end`, `normalized`, and `lines`; `clutch_context_suggest` queries via the injected `connect` seam; `clutch_prompt` renders `author`, switches `diagnose` to `running` when live, resolves `drafts`, renders `box`, and lists `catalog` on `kind="list"` (never returning stale or empty placeholder content). Verified by `./dev.py test tests/unit/test_mcp_tools.py`.
3. `tests/unit/test_mcp_tools.py`: `repo` defaults to `default_cwd` when omitted and routes to an explicit `repo` path when supplied even when `default_cwd` is not a Clutch checkout; a missing directory, directory without `tickets/`, blank `repo=""`, missing `config.yaml`, invalid `window`, invalid `wait_event` cursor/timeout, missing `attempt` with `name`, unknown capture/call key, `no_index`, or unknown prompt returns `isError: true` with `structuredContent` containing non-empty `code`, `message`, and `paved_road` (never raising an uncaught traceback or returning `isError: false`). Verified by `./dev.py test tests/unit/test_mcp_tools.py`.
4. `tests/unit/test_mcp_tools.py`: `prompts/list` returns all 10 `ask.KINDS` entries with their `required` arguments (`stem` for `diagnose`/`running`/`review`/`author`, `ids` for `box`, optional `repo` on all), and `prompts/get` returns `messages[0]["content"]["text"]` matching `ask.render` (never missing `$stem`/`$state_dir` substitutions) and returns a JSON-RPC error on an unknown prompt name or missing required argument. Verified by `./dev.py test tests/unit/test_mcp_tools.py`.
5. `tests/unit/test_main_mcp_serve.py`: `_parser().parse_args(["mcp", "serve"])` sets `verb == "mcp"` and `mcp_verb == "serve"`; `main(["mcp", "serve"], cwd=empty_tmp_path, ...)` invokes `mcp.serve_stdio` without calling `load_config` on `empty_tmp_path` and exits `0` (also returning `0` on `KeyboardInterrupt`), while `main(["--config", str(cfg), "mcp", "serve"], cwd=tmp_path, ...)` forwards `config_path=cfg`. Verified by `./dev.py test tests/unit/test_main_mcp_serve.py`.
6. Existing CLI help, run-guide parity, README, stats, context-suggest, prompt, and status tests pass unchanged (`./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_context_suggest_verb.py tests/unit/test_context_suggest_require.py tests/unit/test_tickets_tolerant_reader.py tests/unit/test_main_prompt_host.py tests/unit/test_ask_host_prompts.py tests/unit/test_stale_running.py tests/unit/test_status_overdue.py tests/unit/test_main_view_group.py tests/integration/test_help.py` exits `0`).
7. `clutch/docs/host-running.md`, `docs/how-clutch-works.md` section 2.1, and `README.md` document `mcp serve`, and `tests/integration/test_mcp_read_server.py` verifies `prompts/list` covers every `clutch/specs/ask/*.md` file and `prompts/get` renders real `drain-loop` and `author` prompts read-only under `clutch.ioguard` (`./dev.py test tests/integration/test_mcp_read_server.py` exits `0`).

## Verification
```
./dev.py test tests/unit/test_mcp_protocol.py tests/unit/test_mcp_tools.py tests/unit/test_main_mcp_serve.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_context_suggest_verb.py tests/unit/test_context_suggest_require.py tests/unit/test_tickets_tolerant_reader.py tests/unit/test_main_prompt_host.py tests/unit/test_ask_host_prompts.py tests/unit/test_stale_running.py tests/unit/test_status_overdue.py tests/unit/test_main_view_group.py tests/integration/test_mcp_read_server.py tests/integration/test_help.py
```

## Definition of rejected
- `clutch mcp serve` refuses to start when CWD has no `config.yaml` or `tickets/` directory, or spawns `clutch` CLI subprocesses inside `clutch/mcp.py`.
- Any tool mutates repository files, journal, lockfiles, or index, or accepts a `repo` path missing `tickets/`.
- `Refusal` exceptions in `tools/call` omit `code`, `message`, or `paved_road`, or `clutch_status` omits the running `clutchwork` package version.
- Any new core dependency is added to `pyproject.toml`, any file outside `## Scope fence` is modified, or `clutch/mcp.py`, `clutch/context.py`, `clutch/stats.py`, `clutch/ask.py`, `clutch/runner.py`, or `clutch/__main__.py` fails its `test-gate.toml` unit coverage threshold.

## Time budget
- expected: 25m
- stuck: 50m
