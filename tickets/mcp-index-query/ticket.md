---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- mcp-read-server
- mcp-app-dashboard
- index-query-verb
- index-fts-duplicate-selector

## Context
- docs/antigravity-plan.md#3. Clutch MCP server vs. direct CLI boundary
- docs/antigravity-plan.md#Open decisions
- clutch/mcp.py
- clutch/index.py::QueryHit
- clutch/index.py::QueryResult
- clutch/index.py::query
- clutch/index.py::IndexCreator
- clutch/index.py::default_creator
- tests/unit/test_mcp_tools.py

## On-demand
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 227 (`mcp-index-query`, `docs/antigravity-plan.md` §3, Open decision #5; `docs/roadmap.md` §6, decision 26). `clutch index query` already searches indexed repository chunks read-only via `clutch.index.query`, and `clutch mcp serve` exposes typed observation and mutation tools, but agents running over MCP have no tool to query the project index and must fall back to shell commands or multi-step greps.

After this ticket:
- `clutch mcp serve` exposes the model-visible, read-only `clutch_index_query` tool calling `clutch.index.query` over `<state_dir>/index.duckdb` with `read_only=True` and zero writer or commit lock contention.
- Successful queries (`found` or `no_match`) return typed `structuredContent` with `outcome`, `mode`, `hits` (each carrying `selector`, `path`, `kind`, `purpose`, `relates`, `owner`, `score`), and `findings`, plus JSON text in `content`.
- Non-match failure outcomes (`invalid_input`, `no_index`, `index_unreadable`, `fulltext_unavailable`) map to structured MCP `isError: True` tool errors carrying `code`, `message`, and `paved_road` consistent with `clutch index query`.
- `clutch/__main__.py` (`mcp serve` help), `clutch/docs/host-running.md`, and `docs/how-clutch-works.md` §2.1 reflect project index querying on `mcp serve`.

Rejected simpler approach: shelling out to `clutch index query` as a subprocess or duplicating DuckDB SQL queries inside `clutch/mcp.py`. Shelling out reintroduces subprocess and `PATH` overhead plus fragile text parsing, while duplicating SQL splits the query contract across two owners instead of reusing `clutch.index.query`.

## Boundary contract

### MCP index query tool
- disposition: extend
- owner: clutch/mcp.py
- consumers: MCP clients (Antigravity agent sessions), `tests/unit/test_mcp_tools.py`, `tests/unit/test_mcp_app_dashboard.py`, `tests/unit/test_mcp_control_and_tickets.py`, `tests/unit/test_mcp_index_query.py`
- observable change: adds `IndexQuery(Repo)` (`text: str`, `limit: int = 10`, `extra="forbid"`) and registers `clutch_index_query` in `TOOLS` (bringing `tools/list` from 25 to 26 tools after `mcp-app-dashboard`, model-visible with no `visibility: ["app"]` restriction); adds optional `creator=index.default_creator` parameter on `ClutchMCPServer.__init__`; `call_tool` invokes `clutch.index.query(cfg, checkout.repo, args.text, fs=fs, exec_=checkout.exec_, env=child_env(self.env, cfg, serving=None), creator=self.creator, limit=args.limit, connect=self.connect)` without taking any writer or commit lock; on `outcome in ("found", "no_match")` returns `structuredContent` with `outcome`, `mode`, `hits` (each item containing `path`, `kind`, `selector`, `purpose`, `relates`, `owner`, `score`), and `findings`; on `invalid_input`, `no_index`, `index_unreadable`, or `fulltext_unavailable` raises `runner.Refusal(message, paved_road, code=result.outcome)` projected by `dispatch` into `isError: True` with `structuredContent: {"code", "message", "paved_road"}`.
- compatibility: all 25 tools from `mcp-app-dashboard`, `ui://clutch/dashboard.html`, and all 10 MCP Prompts preserve their exact schemas and behavior; `tests/unit/test_mcp_tools.py` (and `tests/unit/test_mcp_app_dashboard.py` if it asserts exact tool count or names) update their expected `tools/list` set to 26 tools.
- acceptance: criteria 1, 2, 3, and 4
- tests: tests/unit/test_mcp_index_query.py, tests/unit/test_mcp_tools.py, tests/unit/test_mcp_control_and_tickets.py, tests/unit/test_mcp_app_dashboard.py
- post-merge source of truth: clutch/mcp.py

### CLI help and command documentation
- disposition: extend
- owner: clutch/__main__.py, clutch/docs/host-running.md, docs/how-clutch-works.md
- consumers: operators, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/integration/test_help.py`
- observable change: updates `clutch/__main__.py` `mcp serve` `reads=` help text to include the project index, and updates the `| \`mcp serve\` |` rows in `clutch/docs/host-running.md` and `docs/how-clutch-works.md` §2.1 to mention project index search among read tools.
- compatibility: CLI argv, exit codes, and table column-1 verb names are unchanged.
- acceptance: criterion 5
- tests: tests/unit/test_main_help.py, tests/unit/test_host_running.py, tests/integration/test_help.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
In:
- `clutch/mcp.py`:
  - Import `index` from `clutch`.
  - Add Pydantic `BaseModel` schema `IndexQuery(Repo)` (`extra="forbid"` inherited from `Repo`) with `text: str` and `limit: int = 10`.
  - Register `"clutch_index_query": IndexQuery` in `TOOLS` (model-visible, no `_meta` app-only restriction).
  - Add optional `creator=index.default_creator` parameter to `ClutchMCPServer.__init__` and store `self.creator = creator`.
  - Handle `clutch_index_query` in `ClutchMCPServer.call_tool`: run `asyncio.run(index.query(cfg, checkout.repo, args.text, fs=fs, exec_=checkout.exec_, env=child_env(self.env, cfg, serving=None), creator=self.creator, limit=args.limit, connect=self.connect))` without acquiring any writer or commit lock. On `result.outcome in ("found", "no_match")`, return `result` (serialized by `_json` to `{"outcome", "mode", "hits": [{"path", "kind", "selector", "purpose", "relates", "owner", "score"}], "findings"}`). On any other outcome (`invalid_input`, `no_index`, `index_unreadable`, `fulltext_unavailable`), raise `runner.Refusal(message, paved_road, code=result.outcome)` using `result.findings[-1] if result.findings else result.outcome` and remedies matching `clutch/__main__.py::_run_index_query` (`invalid_input`: `"provide non-blank text and a limit from 1 to 50"`, `no_index`: `"run clutch index build"`, `index_unreadable`: `"retry after refresh or run clutch index build"`, `fulltext_unavailable`: `"run clutch index build with full-text search available"`). Keep all user-facing text and paved roads in `clutch/mcp.py` free of `./dev.py` / `dev.py` references.
- `clutch/__main__.py`, `clutch/docs/host-running.md`, `docs/how-clutch-works.md`:
  - Update `mcp serve` `reads=` help text in `clutch/__main__.py` to mention the project index.
  - Update the `| \`mcp serve\` |` rows in `clutch/docs/host-running.md` and `docs/how-clutch-works.md` §2.1 to mention project index querying among read tools.
- `tests/unit/test_mcp_tools.py`:
  - Update only `test_schemas_and_prompts`'s expected `tools/list` name set to include `"clutch_index_query"` (26 tools total after `mcp-app-dashboard`); nothing else in the file changes.
- `tests/unit/test_mcp_app_dashboard.py`:
  - If `test_mcp_app_dashboard.py` (created by `mcp-app-dashboard`) asserts an exact `tools/list` count or name set, update only that expectation to include `"clutch_index_query"` (26 tools total); nothing else in the file changes.
- New unit test file `tests/unit/test_mcp_index_query.py` (using `tmp_path` and fakes only; zero repo file reads or subprocesses):
  - Verifies `tools/list` includes `clutch_index_query` with `text` required, `limit` optional defaulting to `10`, `repo` optional, `additionalProperties: False`, and no `_meta` app-only visibility restriction.
  - Verifies `tools/call` for `clutch_index_query` calls `clutch.index.query` with `read_only=True` on `connect`, passes `self.creator`, passes `child_env(..., serving=None)` (stripping provider secrets), acquires no lock, and returns `structuredContent` with `outcome`, `mode`, `findings`, and `hits` containing exact typed fields `selector`, `path`, `kind`, `purpose`, `relates` (list of strings), `owner`, and `score` (float) for both `found` and `no_match`.
  - Verifies every refusal outcome (`invalid_input`, `no_index`, `index_unreadable`, `fulltext_unavailable`) returns `isError: True` with matching `structuredContent["code"]`, non-empty `message`, and `paved_road`, and verifies missing `text` or extra unknown arguments raise `InvalidParams`.
  - Verifies explicit invalid `repo` returns `isError: True` with `code: "invalid_repo"`.
  - Keeps `clutch/mcp.py` at or above its 90% `test-gate.toml` unit coverage floor.

Out:
- Modifying `clutch/index.py` (its `query`, `QueryHit`, and `QueryResult` contract is reused unchanged).
- Parquet / VSS sidecar storage changes (deferred to roadmap row 228, `index-parquet-vss-sidecar`).
- Adding tests to any of the seven hot test files (`tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`).

## Scope fence
- clutch/mcp.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_mcp_tools.py
- tests/unit/test_mcp_app_dashboard.py
- tests/unit/test_mcp_index_query.py

## Acceptance criteria
1. `tests/unit/test_mcp_tools.py`, `tests/unit/test_mcp_control_and_tickets.py`, `tests/unit/test_mcp_app_dashboard.py`, and `tests/unit/test_mcp_index_query.py` check `tools/list` exposes all 26 tools including `clutch_index_query` with schema requiring `text`, defaulting `limit` to `10`, forbidding extra properties, and omitting app-only `_meta` visibility (ruling out hiding `clutch_index_query` from models or dropping any existing tool). Verified by `./dev.py test tests/unit/test_mcp_tools.py tests/unit/test_mcp_control_and_tickets.py tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_index_query.py`.
2. `tests/unit/test_mcp_index_query.py` checks `tools/call` for `clutch_index_query` invokes `clutch.index.query` with `connect(..., read_only=True)` and `self.creator`, returns `isError` absent/false and `structuredContent` with `outcome == "found"`, `mode`, `findings`, and `hits` entries carrying all seven fields (`selector`, `path`, `kind`, `purpose`, `relates` as a JSON list of strings, `owner`, `score` as a float), and handles `outcome == "no_match"` with `hits == []` (ruling out empty/dropped hit fields, non-read-only connections, or returning `isError: True` on `no_match`). Verified by `./dev.py test tests/unit/test_mcp_index_query.py`.
3. `tests/unit/test_mcp_index_query.py` checks `clutch_index_query` maps `invalid_input` (blank text or out-of-range limit), `no_index`, `index_unreadable`, and `fulltext_unavailable` to `isError: True` with `structuredContent` carrying `code == outcome`, non-empty `message`, and the matching `paved_road` (ruling out returning `isError` false or losing the paved road), strips provider secrets via `child_env(..., serving=None)` (ruling out passing raw `self.env` to embed commands), and rejects missing `text` or extra arguments with `InvalidParams` and invalid `repo` with `code: "invalid_repo"`. Verified by `./dev.py test tests/unit/test_mcp_index_query.py`.
4. `tests/unit/test_mcp_index_query.py` checks `clutch_index_query` acquires no writer or commit lock (succeeding even while a live writer lock file exists in `state_dir`, ruling out lock contention) and `clutch/mcp.py` meets its 90% `test-gate.toml` unit coverage floor. Verified by `./dev.py test tests/unit/test_mcp_index_query.py tests/unit/test_mcp_protocol.py`.
5. `clutch/__main__.py` (`mcp serve` help), `clutch/docs/host-running.md` (`| \`mcp serve\` |`), and `docs/how-clutch-works.md` (§2.1 `| \`mcp serve\` |`) document project index querying on `mcp serve`, and no user-facing string in `clutch/mcp.py` names `./dev.py`. Verified by `./dev.py test tests/unit/test_main_mcp_serve.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/integration/test_help.py tests/integration/test_engine_text_verbs.py`.

## Verification
```
./dev.py test tests/unit/test_mcp_index_query.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_control_and_tickets.py tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_protocol.py tests/unit/test_main_mcp_serve.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/integration/test_help.py tests/integration/test_engine_text_verbs.py
```

## Definition of rejected
- `clutch_index_query` opens `<state_dir>/index.duckdb` read-write, acquires a writer or commit lock, shells out to a subprocess, or duplicates SQL query logic instead of calling `clutch.index.query`.
- `clutch_index_query` omits any of `selector`, `path`, `kind`, `purpose`, `relates`, `owner`, or `score` from `structuredContent["hits"]`, returns `isError: True` on `no_match`, or hides `invalid_input` / `no_index` / `index_unreadable` / `fulltext_unavailable` as a successful response.
- Any file outside `## Scope fence` is modified, `clutch/mcp.py` drops below its 90% `test-gate.toml` unit coverage floor, or `tests/unit/test_mcp_index_query.py` reads repo files or spawns subprocesses.

## Time budget
- expected: 15m
- stuck: 30m
