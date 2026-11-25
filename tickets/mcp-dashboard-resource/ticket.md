---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- mcp-control-and-tickets

## Context
- docs/antigravity-plan.md#4. Antigravity MCP App dashboard replacing VS Code views
- docs/antigravity-plan.md#Risks
- clutch/mcp.py
- clutch/observe.py
- clutch/stats.py
- tests/unit/test_mcp_protocol.py
- tests/unit/test_mcp_tools.py
- tests/unit/test_mcp_control_and_tickets.py
- tests/integration/test_engine_text_verbs.py

## On-demand
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 223 (`mcp-app-dashboard`, `docs/antigravity-plan.md` §4, Risks #2), part 1 of 3. After `mcp-control-and-tickets`, `clutch mcp serve` exposes read, ticket, Suggestion Box, and engine-control tools, but it has no MCP App UI resource or dashboard tools that Antigravity can render in its side pane (`aux_pane`) or global sidebar (`global`).

After this ticket, `clutch/mcp.py` advertises the `resources` capability, serves `ui://clutch/dashboard.html` (`mimeType: text/html;profile=mcp-app`, `_meta.ui.prefersBorder: false`) through `resources/list` and `resources/read` from an injectable `ui_html_path`, and adds `clutch_open_dashboard` (declaring `ui.resourceUri` and `com.google.antigravity/ui` `aux_pane` and `global` entrypoints, returning a compact summary well under Antigravity's 1 MiB trajectory cap) plus the `visibility: ["app"]` data tools `clutch_app_snapshot` and `clutch_app_stats`. The `mcp serve` help and doc rows describe the new resource and tools. Building the HTML bundle is `mcp-dashboard-bundle`; the dashboard surfaces are `mcp-dashboard-surfaces`.

Rejected simpler approach: returning the full `observe.snapshot` payload from `clutch_open_dashboard`. That bloats conversation trajectories and hits Antigravity's 1 MiB `CallToolResult` cap, so the app fetches data through `app`-only tools.

## Boundary contract

### MCP App UI resource and dashboard tools
- disposition: extend
- owner: clutch/mcp.py
- consumers: Antigravity MCP host (`aux_pane`, `global`, inline views), `clutch/ui/dashboard.html`, `tests/unit/test_mcp_protocol.py`, `tests/unit/test_mcp_tools.py`, `tests/unit/test_mcp_control_and_tickets.py`, `tests/unit/test_mcp_app_dashboard.py`
- observable change: `initialize` adds `resources` (`listChanged: False`) to `capabilities`; `resources/list` returns `ui://clutch/dashboard.html` with `mimeType` `text/html;profile=mcp-app` and `_meta.ui.prefersBorder` False; `resources/read` validates the URI (`InvalidParams` otherwise), reads `self.ui_html_path` (injectable on `ClutchMCPServer.__init__`, default `Path(__file__).parent / 'ui' / 'dashboard.html'`), raises `DomainError` code `dashboard_unavailable` when missing or empty, and returns one `contents` entry with the HTML text; `tools/list` adds `clutch_open_dashboard` (with `_meta.ui.resourceUri` and `com.google.antigravity/ui` entrypoints `aux_pane` and `global` titled `ClutchWork`) plus `clutch_app_snapshot` and `clutch_app_stats` with `_meta.ui.visibility` `["app"]`; `clutch_open_dashboard` accepts optional `repo` and `tab` and returns `ready: False` for `{}` without a CWD checkout, a compact summary when resolved, and `invalid_repo` for an explicit invalid repo.
- compatibility: all 22 tools from `mcp-control-and-tickets` and all 10 MCP Prompts keep their exact schemas and behavior; only the expected capability and tool sets in the existing MCP unit tests change.
- acceptance: criteria 1, 2, 3, and 5
- tests: tests/unit/test_mcp_app_dashboard.py, tests/unit/test_mcp_protocol.py, tests/unit/test_mcp_tools.py, tests/unit/test_mcp_control_and_tickets.py
- post-merge source of truth: clutch/mcp.py

### mcp serve help and command docs
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/integration/test_help.py`
- observable change: `mcp` / `mcp serve` CLI help, the `mcp serve` row in `clutch/docs/host-running.md`, and the `mcp serve` row in `docs/how-clutch-works.md` §2.1 name the `ui://clutch/dashboard.html` MCP App resource and the `clutch_open_dashboard`, `clutch_app_snapshot`, and `clutch_app_stats` tools.
- compatibility: CLI argv and table column-1 verb names are unchanged; `clutch/hostfiles.py` is untouched.
- acceptance: criterion 4
- tests: tests/unit/test_main_help.py, tests/unit/test_host_running.py, tests/integration/test_help.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
In:
- `clutch/mcp.py`:
  - Constants `DASHBOARD_URI = "ui://clutch/dashboard.html"`, `MCP_APP_MIME = "text/html;profile=mcp-app"`, `DEFAULT_DASHBOARD_HTML = Path(__file__).parent / "ui" / "dashboard.html"`.
  - `ui_html_path: Path | None = None` on `ClutchMCPServer.__init__`, defaulting to `DEFAULT_DASHBOARD_HTML`.
  - `"resources": {"listChanged": False}` in `initialize` `capabilities`.
  - `resources/list` returning the `DASHBOARD_URI` entry (`mimeType: MCP_APP_MIME`, `_meta: {"ui": {"prefersBorder": False}}`); `resources/read` validating `params.get("uri") == DASHBOARD_URI` (`InvalidParams` otherwise), reading `self.ui_html_path` (raising `DomainError` code `dashboard_unavailable` with paved road `build the dashboard UI bundle before opening the dashboard (see docs/how-clutch-works.md)` when unreadable or empty), and returning `{"contents": [{"uri": DASHBOARD_URI, "mimeType": MCP_APP_MIME, "text": html}]}`.
  - Pydantic schema `Dashboard(Repo)` (`extra="forbid"`) with `tab: Literal["tickets", "steps", "box", "stats", "help"] = "tickets"` and optional `repo`.
  - Register `clutch_open_dashboard` with `_meta: {"ui": {"resourceUri": DASHBOARD_URI}, "com.google.antigravity/ui": {"entrypoints": [{"type": "aux_pane", "title": "ClutchWork"}, {"type": "global", "title": "ClutchWork"}]}}`, and `clutch_app_snapshot` (schema `Snapshot`) and `clutch_app_stats` (schema `Stats`) with `_meta: {"ui": {"visibility": ["app"]}}`.
  - `clutch_open_dashboard`: when `args.repo is None` and `(self.cwd / "tickets")` is not a directory, return `{"repo": None, "tab": args.tab, "ready": False, "version": version("clutchwork"), "message": "Supply a ClutchWork checkout path to load the dashboard."}` without error; otherwise resolve `self.checkout(args.repo)`, compute `observe.snapshot(ctx, merged_limit=cfg.snapshot_merged_limit)`, and return the compact summary (`repo`, `tab`, `ready: True`, `counts`, `engine`, `runningStem`, `blockedCount`, `pendingBox`, `version`) plus one-line text, omitting `rows`, `box`, `steps`, and `help`.
  - Route `clutch_app_snapshot` to `observe.snapshot` and `clutch_app_stats` to the same `stats.window_start` / `stats.collect_stats` / `stats.stats_tree` helper used by `clutch_stats`.
  - No user-facing message in `clutch/mcp.py` names `dev.py`, so `tests/integration/test_engine_text_verbs.py` keeps passing.
- `tests/unit/test_mcp_protocol.py`: change only the expected `capabilities` set from `{"tools", "prompts"}` to `{"tools", "prompts", "resources"}`.
- `tests/unit/test_mcp_tools.py`: change only `test_schemas_and_prompts`'s expected `tools/list` name set to add `clutch_open_dashboard`, `clutch_app_snapshot`, and `clutch_app_stats` (25 tools).
- `tests/unit/test_mcp_control_and_tickets.py`: if it asserts exact tool sets, change only those expected sets to add the three new tools.
- New `tests/unit/test_mcp_app_dashboard.py` (`tmp_path`, `io.StringIO`, and fakes only; no repo file reads, no subprocesses) covering the capability, `resources/list`, `resources/read` (happy path, unknown URI `-32602`, missing and empty file `dashboard_unavailable`), `tools/list` `_meta`, `clutch_open_dashboard` (`{}` with and without a checkout CWD, explicit invalid `repo`, compact payload), `clutch_app_snapshot`, and `clutch_app_stats` (including `invalid_window`).
- `clutch/__main__.py`, `clutch/docs/host-running.md`, `docs/how-clutch-works.md`: update `mcp` / `mcp serve` help and the `mcp serve` rows (§2.1 in `docs/how-clutch-works.md`) to name the dashboard resource and tools.
- Engine-written `# clutch:meta` headers on newly created Python test files under `tests/` updated by Check.

Out:
- `dev.py`, `package.json`, `.gitignore`, and any `clutch/ui/` file (`mcp-dashboard-bundle`, `mcp-dashboard-surfaces`).
- `vscode-clutchwork/`, `clutch/help.py`, `clutch/hostfiles.py`, `clutch/specs/ask/*.md`, `README.md`.
- Tests in any of the seven hot test files.

## Scope fence
- clutch/mcp.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_mcp_protocol.py
- tests/unit/test_mcp_tools.py
- tests/unit/test_mcp_control_and_tickets.py
- tests/unit/test_mcp_app_dashboard.py

## Acceptance criteria
1. `tests/unit/test_mcp_protocol.py` and `tests/unit/test_mcp_app_dashboard.py` check `initialize` returns `resources` with `listChanged: False` in `capabilities`, `resources/list` returns `ui://clutch/dashboard.html` with `mimeType` `text/html;profile=mcp-app` and `_meta.ui.prefersBorder` False, and `resources/read` returns the HTML from `ui_html_path`, ruling out an unknown URI succeeding (asserts `-32602`) and a missing or empty file crashing (asserts `DomainError` code `dashboard_unavailable`). Verified by `./dev.py test tests/unit/test_mcp_protocol.py tests/unit/test_mcp_app_dashboard.py`.
2. `tests/unit/test_mcp_tools.py`, `tests/unit/test_mcp_control_and_tickets.py`, and `tests/unit/test_mcp_app_dashboard.py` check `tools/list` exposes 25 tools, `clutch_open_dashboard` carries `_meta.ui.resourceUri` `ui://clutch/dashboard.html` and the `aux_pane` and `global` `ClutchWork` entrypoints, and `clutch_app_snapshot` and `clutch_app_stats` carry `_meta.ui.visibility` `["app"]`. Verified by `./dev.py test tests/unit/test_mcp_tools.py tests/unit/test_mcp_control_and_tickets.py tests/unit/test_mcp_app_dashboard.py`.
3. `tests/unit/test_mcp_app_dashboard.py` checks `clutch_open_dashboard` with `{}` in a checkout CWD returns `structuredContent` with `repo`, `tab`, `ready: True`, `counts`, `engine`, `runningStem`, `blockedCount`, `pendingBox`, `version` and without `rows`, `box`, `steps`, or `help`; with `{}` in a CWD lacking `tickets/` returns `ready: False`, `repo: None`, not `isError`; returns `isError: True` with `code: invalid_repo` for an explicit invalid `repo`; and routes `clutch_app_snapshot` to `observe.snapshot` and `clutch_app_stats` to `stats.collect_stats` / `stats.stats_tree`, including `invalid_window` refusal. Verified by `./dev.py test tests/unit/test_mcp_app_dashboard.py`.
4. `mcp` / `mcp serve` help in `clutch/__main__.py`, the `mcp serve` row in `clutch/docs/host-running.md`, and the §2.1 `mcp serve` row in `docs/how-clutch-works.md` name the dashboard resource and tools and pass `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/integration/test_help.py`.
5. Existing MCP server and engine-text tests pass and `clutch/mcp.py` meets its 90% `test-gate.toml` unit coverage floor. Verified by `./dev.py test tests/integration/test_mcp_read_server.py tests/unit/test_main_mcp_serve.py tests/integration/test_engine_text_verbs.py`.

## Verification
```
./dev.py test tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_protocol.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_control_and_tickets.py tests/unit/test_main_mcp_serve.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/integration/test_help.py tests/integration/test_mcp_read_server.py tests/integration/test_engine_text_verbs.py
```

## Definition of rejected
- `clutch_open_dashboard` embeds `rows`, `box`, `steps`, or `help` in its `CallToolResult`, or fails when invoked with `{}` without a checkout CWD.
- `clutch_app_snapshot` or `clutch_app_stats` omits `_meta.ui.visibility` `["app"]`, or `initialize` omits the `resources` capability.
- Any existing MCP tool or prompt changes schema or behavior, or a message in `clutch/mcp.py` names `dev.py`.
- Any file outside `## Scope fence` is modified, or `clutch/mcp.py` drops below its 90% unit coverage floor.

## Time budget
- expected: 20m
- stuck: 40m