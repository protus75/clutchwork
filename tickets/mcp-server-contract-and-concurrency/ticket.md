---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
- mcp-dashboard-help-and-repo-picker

## Context
- docs/antigravity-plan.md#Target design
- docs/antigravity-plan.md#Risks
- clutch/mcp.py
- clutch/antigravity.py
- clutch/ask.py::KINDS
- clutch/ask.py::TAKES
- clutch/ask.py::DESCRIPTIONS
- clutch/ask.py::resolve_prompt
- clutch/runner.py::submit_engine
- clutch/runner.py::_locked
- clutch/runner.py::triage_or_submit
- clutch/runner.py::run_or_submit_retro
- tests/unit/test_mcp_protocol.py
- tests/unit/test_mcp_tools.py
- tests/unit/test_mcp_control_and_tickets.py
- tests/unit/test_mcp_app_dashboard.py
- tests/unit/test_antigravity_plugin.py
- tests/integration/test_mcp_read_server.py

## Goal / Why
Restore `clutch/mcp.py` and `clutch/antigravity.py` to the `docs/antigravity-plan.md` (§3, §6) contract and eliminate five coupled defects observed in `tickets/mcp-server-contract-and-concurrency/evidence/plan-drift.txt`:
1. `tools/list` omits `_meta.ui.visibility` on `clutch_wait_event` (must be `["model"]`), `clutch_open_dashboard` (must include `["model", "app"]`), and all other model+app tools (must be `["model", "app"]`), using ad-hoc `name.startswith("clutch_app_")` checks instead of declarative tool specs.
2. `serve_stdio` dispatches every request synchronously on a single reader loop, so a long-running `clutch_wait_event` call (up to 300s) blocks `ping`, `clutch_app_snapshot`, `clutch_app_stats`, and all other concurrent MCP requests.
3. `clutch_box_triage` and `clutch_engine_retro` fall through to synchronous multi-minute LLM passes inline inside `clutch mcp serve` when no engine holds the writer lock, violating the §3 non-blocking MCP boundary.
4. `prompts/list` and `prompts/get` omit `"host"`, even though §3 lists `host` as an MCP Prompt and `clutch/ask.py::resolve_prompt` already implements `kind == "host"`.
5. `clutch/antigravity.py::doctor_finding` only accepts `MCP_ARGS` and flags portable installs using `PORTABLE_MCP_ARGS` (`uvx --from clutchwork clutch mcp serve`) with a false-positive drift warning.

## Boundary contract

### MCP tool metadata and stdio concurrency
- disposition: extend
- owner: clutch/mcp.py
- consumers: Antigravity MCP host, MCP App iframe (`clutch/ui/app.js`), `clutch mcp serve` (`serve_stdio`), and MCP unit/integration tests
- observable change: Replace the flat `TOOLS: dict[str, type[BaseModel]]` values with a frozen `ToolSpec(model, visibility, blocking="fast")` dataclass (keeping the `TOOLS` dict name) where `visibility: tuple[Literal["model", "app"], ...]` and `blocking: Literal["fast", "wait", "submit_only"] = "fast"`. `clutch_wait_event` declares `visibility=("model",), blocking="wait"`; all `clutch_app_*` tools (`clutch_app_snapshot`, `clutch_app_stats`, `clutch_app_ticket_confirm`, `clutch_app_ticket_reject`, `clutch_app_ui_state`, `clutch_app_config`) declare `visibility=("app",)`; `clutch_open_dashboard` declares `visibility=("model", "app")` alongside `resourceUri` and `com.google.antigravity/ui` entrypoints; all other tools declare `visibility=("model", "app")` (with `clutch_box_triage` and `clutch_engine_retro` declaring `blocking="submit_only"`). `tools/list` emits `_meta.ui.visibility` for every tool directly from `ToolSpec`. In `serve_stdio`, `tools/call` requests reuse the `dispatch` param-validation rule synchronously on the reader loop (`name` is a `str` in `TOOLS` and `spec.model.model_validate(params.get("arguments", {}))` succeeds, answering `-32602` immediately in order on invalid params, while preserving the `clutch_app_config` exemption when `arguments` is a `dict` containing `"updates"` so invalid `updates` still return `isError: True` with `code="invalid_config"` rather than `-32602`) and submit only valid `tools/call` executions to worker threads via `concurrent.futures.ThreadPoolExecutor` with a `threading.Lock` serializing `stdout.write` + `stdout.flush`, waiting for all in-flight workers on EOF before returning, and redirecting process `sys.stdout` to `sys.stderr` once around the loop/shutdown so domain `print()` calls remain thread-safe; `initialize`, `notifications/*`, `roots/list` responses, `ping`, `tools/list`, `resources/*`, and `prompts/*` remain ordered and thread-safe on the reader loop.
- compatibility: Keeps `TOOLS` dict keys identical (`set(mcp.TOOLS)` and `delitem` work unchanged), keeps all JSON-RPC method names and tool argument schemas unchanged, and restores `_meta.ui.visibility` compliance with `docs/antigravity-plan.md` §3 while preventing `clutch_wait_event` from blocking concurrent requests.
- acceptance: Every tool in `tools/list` emits `_meta.ui.visibility` matching its `ToolSpec`, and a blocking `clutch_wait_event` in flight on `serve_stdio` does not block a concurrent `ping` (or `clutch_app_snapshot`) request from returning immediately.
- tests: `tests/unit/test_mcp_surface_contract.py`, `tests/unit/test_mcp_control_and_tickets.py`, `tests/unit/test_mcp_app_dashboard.py`, `tests/unit/test_mcp_protocol.py`
- post-merge source of truth: clutch/mcp.py

### MCP non-blocking triage and retro submission
- disposition: replace
- owner: clutch/mcp.py
- consumers: Antigravity supervising agents, MCP App Suggestion Box (`clutch_box_triage`), and `clutch_engine_retro` callers
- observable change: Replaces the old MCP behavior (calling `runner.triage_or_submit` / `runner.run_or_submit_retro`, which ran synchronous multi-minute LLM passes inline when unlocked) with a submit-only MCP boundary: when a live `serve` or `drain` engine holds the writer lock (`LockHeld`), `clutch_box_triage` and `clutch_engine_retro` submit to the engine control inbox via `runner.submit_engine` and return `{"submitted": True, "request_id": request.request_id}`; when a non-engine writer holds the lock, `runner.submit_engine` raises `LockHeld` (`code="lock_held"`); when no writer holds the lock, both tools release the lock immediately and raise `runner.Refusal(..., code="engine_not_running", paved_road="start the engine with clutch_engine_start or run clutch box triage / clutch engine retro from the CLI")`.
- compatibility: Breaking change for MCP callers invoking `clutch_box_triage` or `clutch_engine_retro` while no engine is running (restores `docs/antigravity-plan.md` §3 non-blocking contract); CLI `clutch box triage` and `clutch engine retro` in `clutch/runner.py` remain unchanged and continue to support synchronous runs when stopped; existing MCP unit tests in `tests/unit/test_mcp_control_and_tickets.py` are updated in this ticket.
- acceptance: `clutch_box_triage` and `clutch_engine_retro` refuse with `isError: True` and `code == "engine_not_running"` when no engine holds the lock without invoking inline LLM passes, submit to the engine inbox when `serve`/`drain` holds the lock, and return `code == "lock_held"` when a non-engine writer holds the lock.
- tests: `tests/unit/test_mcp_surface_contract.py`, `tests/unit/test_mcp_control_and_tickets.py`
- post-merge source of truth: clutch/mcp.py

### MCP host prompt exposure
- disposition: extend
- owner: clutch/mcp.py
- consumers: Antigravity MCP prompt callers (`prompts/list`, `prompts/get`)
- observable change: `prompts/list` includes `"host"` alongside `ask.KINDS` with optional `repo` and optional `name` arguments (`[{"name": "repo", "required": False}, {"name": "name", "required": False}]`). `prompts/get` accepts `name == "host"`, validates that `arguments` contains only optional string keys in `{"repo", "name"}`, resolves via `self.prompt(checkout, ctx, "host", [], name=args.get("name"))`, and returns the rendered prompt message (mapping `Refusal` to `DomainError`).
- compatibility: Additive MCP prompt entry restoring parity with `docs/antigravity-plan.md` §3 and `clutch/ask.py::resolve_prompt`; all `ask.KINDS` prompt names and argument rules remain unchanged.
- acceptance: `prompts/list` includes `"host"` with optional `repo` and `name` arguments, and `prompts/get` resolves `"host"` via `self.prompt(..., "host", [], name=...)`.
- tests: `tests/unit/test_mcp_surface_contract.py`, `tests/unit/test_mcp_tools.py`, `tests/integration/test_mcp_read_server.py`
- post-merge source of truth: clutch/mcp.py

### Antigravity plugin doctor check
- disposition: extend
- owner: clutch/antigravity.py
- consumers: `clutch host doctor` (`clutch/doctor.py`), `clutch/antigravity.py::verify_plugin`, and users installing via `agy plugin install https://github.com/protus75/clutchwork`
- observable change: `doctor_finding` derives valid MCP server arg tuples from `{tuple(MCP_ARGS), tuple(PORTABLE_MCP_ARGS)}` so both local (`sys.executable -m clutch mcp serve`) and portable (`uvx --from clutchwork clutch mcp serve`) `mcp_config.json` payloads return `None` when the command is a non-blank string whose executable exists.
- compatibility: Strictly relaxes false-positive rejection of `PORTABLE_MCP_ARGS`; all malformed configs, missing executables, and unrecognized arg lists continue to return the drift finding with paved road `clutch host antigravity`.
- acceptance: `doctor_finding` returns `None` for both `install_plugin()` and `portable_bundle_files()` / `portable_mcp_config()` when the configured executable exists, and still reports drift for unrecognized args or missing executables.
- tests: `tests/unit/test_mcp_surface_contract.py`, `tests/unit/test_antigravity_plugin.py`
- post-merge source of truth: clutch/antigravity.py

## Scope in / Scope out

### Scope in
- `clutch/mcp.py`:
  - Define `@dataclasses.dataclass(frozen=True) class ToolSpec`: `model: type[BaseModel]`, `visibility: tuple[Literal["model", "app"], ...]`, `blocking: Literal["fast", "wait", "submit_only"] = "fast"`.
  - Convert `TOOLS` to `dict[str, ToolSpec]` (preserving all 28 registered tools after `mcp-dashboard-settings-and-layout` and `mcp-dashboard-help-and-repo-picker`):
    - `clutch_wait_event`: `visibility=("model",)`, `blocking="wait"`
    - `clutch_app_snapshot`, `clutch_app_stats`, `clutch_app_ticket_confirm`, `clutch_app_ticket_reject`, `clutch_app_ui_state`, `clutch_app_config`: `visibility=("app",)`
    - `clutch_box_triage`, `clutch_engine_retro`: `visibility=("model", "app")`, `blocking="submit_only"`
    - `clutch_open_dashboard` and all remaining tools: `visibility=("model", "app")`
  - Update `tools/list` to emit `_meta` from `ToolSpec` for every tool (`_meta.ui.visibility = list(spec.visibility)`), adding `resourceUri: DASHBOARD_URI` inside `_meta.ui` and `com.google.antigravity/ui` entrypoints on `clutch_open_dashboard`, with no ad-hoc `name.startswith("clutch_app_")` check.
  - Update `tools/call` model validation to use `TOOLS[name].model.model_validate(...)`.
  - Update `clutch_box_triage` and `clutch_engine_retro` in `call_tool` to use a submit-only helper: try `runner._locked(...)`; if `LockHeld` is raised, submit via `runner.submit_engine(checkout, exc, "triage", ids=args.ids)` or `runner.submit_engine(checkout, exc, "retro")` and return `{"submitted": True, "request_id": request.request_id}`; if the lock is acquired (no writer running), release it immediately and raise `runner.Refusal(..., code="engine_not_running", paved_road="start the engine with clutch_engine_start or run clutch box triage / clutch engine retro from the CLI")`. Never import or invoke `_preflighted_llm`, `_config_reloader`, `runner.triage_or_submit`, or `runner.run_or_submit_retro` inline from MCP.
  - Define `HOST_PROMPT_DESCRIPTION = "Render a host-defined prompt from prompts_dir."` in `clutch/mcp.py` and update `prompts/list` to append `{"name": "host", "description": HOST_PROMPT_DESCRIPTION, "arguments": [{"name": "repo", "required": False}, {"name": "name", "required": False}]}` after `ask.KINDS`.
  - Update `prompts/get` to accept `kind == "host"`, validate `args` keys are a subset of `{"repo", "name"}` with optional string values, call `text, catalog = self.prompt(checkout, ctx, "host", [], name=args.get("name"))` (so omitted or unknown `name` or unset `prompts_dir` surfaces `resolve_prompt`'s `Refusal` as `DomainError(_error(exc))`, while any returned `catalog` falls back to `json.dumps(catalog)`), and return `{"description": HOST_PROMPT_DESCRIPTION, "messages": [{"role": "user", "content": {"type": "text", "text": text or json.dumps(catalog)}}]}`.
  - Update `serve_stdio` to:
    - Capture `out = stdout if stdout is not None else sys.stdout` before entering a single `with redirect_stdout(sys.stderr):` covering the reader loop and thread pool shutdown.
    - Serialize all writes to `out` (`out.write(...)` + `out.flush()`) under a `threading.Lock`.
    - Pre-validate `tools/call` params synchronously on the reader loop by reusing the `dispatch` validation rule (via a shared helper or identical check: verify `name` is a `str` in `TOOLS` and `TOOLS[name].model.model_validate(params.get("arguments", {}))` succeeds, exempting `clutch_app_config` when `isinstance(params.get("arguments"), dict)` and `"updates" in params["arguments"]` so invalid `updates` still return `isError: True` with `code="invalid_config"` rather than `-32602`, and answering `-32602` immediately in order for all other invalid params); submit only valid `tools/call` executions concurrently to a `concurrent.futures.ThreadPoolExecutor` (waiting for all submitted futures on EOF before returning), while keeping `initialize`, `notifications/*`, `roots/list` responses, `ping`, `tools/list`, `resources/*`, and `prompts/*` thread-safe and ordered on the reader loop.
- `clutch/antigravity.py`:
  - Derive `VALID_MCP_ARGS = frozenset({MCP_ARGS, PORTABLE_MCP_ARGS})` and update `doctor_finding` to accept any list `server["args"]` whose `tuple(args)` is in `VALID_MCP_ARGS`.
- Tests:
  - Create `tests/unit/test_mcp_surface_contract.py` verifying:
    - Every tool in `tools/list` emits `_meta.ui.visibility`, `clutch_wait_event` has `["model"]`, every `clutch_app_*` tool has `["app"]`, `clutch_open_dashboard` has `["model", "app"]` + `resourceUri` + entrypoints, and all other tools have `["model", "app"]`.
    - Concurrent `serve_stdio`: using a blocking fake `events.wait_once` gated on a `threading.Event` and a queue-backed or pipe-backed `stdin` stream, send a `clutch_wait_event` request followed immediately by a `ping` request and verify `ping` replies before `clutch_wait_event` is released, then release `clutch_wait_event` and verify its reply arrives cleanly without interleaved JSON lines; also verify a `clutch_app_config` call with invalid `updates` over `serve_stdio` returns a JSON-RPC result with `isError: True` and `structuredContent["code"] == "invalid_config"` (not `-32602`).
    - `clutch_box_triage` and `clutch_engine_retro` refuse with `isError: True` and `code == "engine_not_running"` when no engine holds the lock (never invoking `triage_or_submit` / `run_or_submit_retro`), submit to the engine inbox when `serve` or `drain` holds the lock, and return `code == "lock_held"` when a non-engine writer holds the lock.
    - `prompts/list` includes `"host"` with optional `repo` and `name` arguments, and `prompts/get` resolves `"host"` (and rejects unknown arguments or non-string `name` with `InvalidParams`).
    - `antigravity.doctor_finding` returns `None` for both `install_plugin()` and `portable_bundle_files()` / `portable_mcp_config()` when the executable exists, and still returns a drift finding for invalid arg lists or missing executables.
  - Update `tests/unit/test_mcp_control_and_tickets.py`:
    - Update `test_catalog_and_actor_schema` for declarative `_meta.ui.visibility` on all tools.
    - Update `test_box_triage_idle_and_busy` and `test_retro_idle_and_busy` to assert `code == "engine_not_running"` when unlocked (while preserving `runner.triage_or_submit` / `runner.run_or_submit_retro` submission coverage and `lock_held` for non-engine holders).
    - Update `test_stdio_domain_noise_and_extension_rejection` to index `replies` by JSON-RPC `id` rather than assuming serial arrival order across concurrent `tools/call` workers.
  - Update `tests/unit/test_mcp_app_dashboard.py`:
    - Update `catalog["clutch_open_dashboard"]["_meta"]` expectation to include `"visibility": ["model", "app"]` inside `"ui"`.
  - Update `tests/unit/test_mcp_tools.py`:
    - Update `prompts/list` assertions in `test_schemas_and_prompts` and `test_prompt_argument_catalog` to include `"host"` with `[{"name": "repo", "required": False}, {"name": "name", "required": False}]`.
  - Update `tests/integration/test_mcp_read_server.py`:
    - Update `test_real_prompt_catalog_and_render` to expect `{p.stem for p in (root / "clutch/specs/ask").glob("*.md")} | {"host"}`.
  - Create pure-Python base-compatible regression reproducer `tests/regression/mcp_server_contract_and_concurrency.py` that checks its prerequisites (`clutch/mcp.py` and `clutch/antigravity.py`), verifies `tools/list` emits `_meta.ui.visibility == ["model"]` on `clutch_wait_event` AND writes `antigravity.portable_mcp_config()` into a temporary plugin directory (`mcp_config.json`) and calls `antigravity.doctor_finding(plugin_dir, executable_exists=lambda _: True)` (using only base-existing parameters so the check is deterministic regardless of whether `uvx` is on `PATH`), wrapping execution in `try`/`except` so it always prints strictly one JSON object: `{"regression_result": "pass"}` (exit 0), `{"regression_result": "defect"}` (exit 1), or `{"regression_result": "error"}` (exit 2).

### Scope out
- Changing CLI `clutch box triage` or `clutch engine retro` synchronous behavior in `clutch/runner.py`.
- Adding or removing MCP tools or changing dashboard UI files (`clutch/ui/*`, `vscode-clutchwork/*`).
- Modifying any of the 7 hot integration test files.

## Scope fence
- clutch/mcp.py
- clutch/antigravity.py
- tests/unit/test_mcp_surface_contract.py
- tests/unit/test_mcp_control_and_tickets.py
- tests/unit/test_mcp_app_dashboard.py
- tests/unit/test_mcp_tools.py
- tests/integration/test_mcp_read_server.py
- tests/regression/mcp_server_contract_and_concurrency.py

## Acceptance criteria
1. Every tool returned by `ClutchMCPServer.dispatch("tools/list", {})` includes `_meta.ui.visibility` derived from `ToolSpec` (not `None` or omitted): `clutch_wait_event` has `["model"]`, every `clutch_app_*` tool has `["app"]`, `clutch_open_dashboard` has `["model", "app"]` alongside `resourceUri` and `com.google.antigravity/ui` entrypoints, and all other tools have `["model", "app"]`; verified by `./dev.py test tests/unit/test_mcp_surface_contract.py tests/unit/test_mcp_control_and_tickets.py tests/unit/test_mcp_app_dashboard.py`.
2. In `serve_stdio`, an in-flight blocking `clutch_wait_event` request does not block a concurrent `ping` request from returning immediately before `clutch_wait_event` completes (not waiting for `clutch_wait_event` to finish), and all JSON-RPC stdout lines remain valid uncorrupted JSON with domain `print()` output sent to stderr; verified by `./dev.py test tests/unit/test_mcp_surface_contract.py tests/unit/test_mcp_protocol.py tests/unit/test_mcp_control_and_tickets.py tests/unit/test_mcp_repo_resolution.py`.
3. `clutch_box_triage` and `clutch_engine_retro` refuse with `isError: True` and `structuredContent["code"] == "engine_not_running"` when no engine holds the writer lock (never running synchronous inline LLM passes), submit to the engine inbox returning `{"submitted": True, "request_id": ...}` when `serve` or `drain` holds the lock, and return `code == "lock_held"` when a non-engine writer holds the lock; verified by `./dev.py test tests/unit/test_mcp_surface_contract.py tests/unit/test_mcp_control_and_tickets.py`.
4. `prompts/list` includes `"host"` with optional `repo` and `name` arguments (not omitting `"host"`), and `prompts/get` with `name="host"` resolves via `self.prompt(..., "host", [], name=...)` while rejecting unknown argument keys with `InvalidParams`; verified by `./dev.py test tests/unit/test_mcp_surface_contract.py tests/unit/test_mcp_tools.py tests/integration/test_mcp_read_server.py`.
5. `clutch/antigravity.py::doctor_finding` returns `None` for both `install_plugin()` (`MCP_ARGS`) and `portable_bundle_files()` / `portable_mcp_config()` (`PORTABLE_MCP_ARGS`) when the executable exists (not emitting a false-positive drift warning on portable bundles), while still returning a drift finding for unrecognized args or missing executables; verified by `./dev.py test tests/unit/test_mcp_surface_contract.py tests/unit/test_antigravity_plugin.py tests/unit/test_antigravity_bundle.py`.
6. `uv run python tests/regression/mcp_server_contract_and_concurrency.py` prints `{"regression_result": "pass"}` with exit 0 on the fixed branch and `{"regression_result": "defect"}` with exit 1 on the merge base.

## Verification
```
./dev.py test tests/unit/test_mcp_surface_contract.py tests/unit/test_mcp_protocol.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_control_and_tickets.py tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_repo_resolution.py tests/unit/test_antigravity_plugin.py tests/unit/test_antigravity_bundle.py tests/integration/test_mcp_read_server.py
```

## Definition of rejected
- Any tool in `tools/list` omits `_meta.ui.visibility`, or `clutch_wait_event` advertises `"app"` visibility, or any `clutch_app_*` tool advertises `"model"` visibility.
- `serve_stdio` still blocks `ping` or other concurrent MCP requests while `clutch_wait_event` is waiting, or interleaves partial JSON lines on stdout.
- `clutch_box_triage` or `clutch_engine_retro` executes an inline synchronous LLM pass when no engine is running instead of refusing with `engine_not_running`.
- `prompts/list` omits `"host"` or `prompts/get` rejects `name="host"`.
- `antigravity.doctor_finding` reports drift on `portable_mcp_config()` / `portable_bundle_files()`.
- Any of the 7 hot integration test files is modified.

## Time budget
- expected: 20m
- stuck: 40m

## Regression
```
uv run python tests/regression/mcp_server_contract_and_concurrency.py
```
- carries: tests/regression/mcp_server_contract_and_concurrency.py
