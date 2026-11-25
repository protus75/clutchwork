---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- mcp-dashboard-resource
- mcp-dashboard-bundle
- mcp-control-and-tickets
- ui-shared-renderers

## Context
- docs/antigravity-plan.md#4. Antigravity MCP App dashboard replacing VS Code views
- docs/antigravity-plan.md#Risks
- clutch/mcp.py
- dev.py
- vscode-clutchwork/media/graph.js
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/media/view.css
- tests/ui_shared_renderers.js
- tests/integration/test_ui_shared_renderers.py
- tests/integration/conftest.py

## Goal / Why
Roadmap row 223 (`mcp-app-dashboard`, `docs/antigravity-plan.md` §4, Risks #2), part 3 of 3. After `mcp-dashboard-resource` and `mcp-dashboard-bundle`, `clutch mcp serve` serves a built dashboard HTML and the `app`-only data tools, but the app only boots and themes itself: it renders no ticket graph, details, steps, Suggestion Box, stats, or help, and cannot open files or launch agent prompts.

After this ticket, `clutch/ui/app.js` renders all six surfaces (Tickets graph with engine liveness, play/stop, priority, runs-before, and admission-gated confirm/reject; Details with artifact links; Recent Steps; Suggestion Box with multi-select triage/dismiss; Stats with a window selector; Help & Lifecycle with `ticket-lifecycle.svg`) through the shared `vscode-clutchwork/media/` renderers and a host adapter that opens files via `com.google.antigravity/toggle-aux-pane` (degrading on `-32601` / `isError`), launches prompts via `app.sendMessage` (including `com.google.antigravity/message` `target: new`), and attaches selection context via `app.updateModelContext` when supported. A Node harness exercises the built bundle end to end.

Rejected simpler approach: re-implementing graph layout, row filtering, and admission checks in `clutch/ui/app.js`. That duplicates logic owned by Python and the shared renderers; the app instead feeds snapshot fields to `renderGraph`, `createTicketsView`, `createDetailView`, and `createBoxView` and enables actions strictly from `row.menu`.

## Boundary contract

### MCP App dashboard surfaces and host adapter
- disposition: extend
- owner: clutch/ui/app.js
- consumers: Antigravity side pane (`aux_pane`) and sidebar (`global`), `tests/mcp_app_dashboard.js`, `tests/integration/test_mcp_app_dashboard.py`
- observable change: `createDashboardApp` wires a host adapter `{callTool, openFile, sendPrompt, openHelp, onFocus}` into `renderGraph`, `createTicketsView`, `createDetailView`, and `createBoxView` and renders the Tickets, Details, Recent Steps, Suggestion Box, Stats, and Help & Lifecycle tabs from `clutch_app_snapshot` and `clutch_app_stats`; actions call `clutch_engine_start`, `clutch_engine_control`, `clutch_ticket_order`, `clutch_app_ticket_confirm`, `clutch_app_ticket_reject`, `clutch_box_triage`, `clutch_box_dismiss`, and `clutch_prompt`; files open through `com.google.antigravity/toggle-aux-pane`; prompts go through `app.sendMessage`; selection goes through `app.updateModelContext`.
- compatibility: `vscode-clutchwork/` files and tests are untouched; the `createDashboardApp` export, IIFE global, and auto-boot guard from `mcp-dashboard-bundle` keep their names.
- acceptance: criteria 1 and 2
- tests: tests/integration/test_mcp_app_dashboard.py, tests/integration/test_ui_shared_renderers.py
- post-merge source of truth: clutch/ui/app.js

## Scope in / Scope out
In:
- `clutch/ui/app.js`:
  - Import `renderGraph`, `createTicketsView`, `createDetailView`, `createBoxView` from `../../vscode-clutchwork/media/{graph,view,detail,box}.js`.
  - Host adapter: `callTool` calls `app.callServerTool` with `{repo}` when set, with no more than 4 calls in flight; `openFile` resolves relative paths against `snap.root` into a `file://` URI and calls `app.request` with method `com.google.antigravity/toggle-aux-pane` and params `{tabType: "fileView", uri}`, catching `-32601` or `result.isError` by disabling file open with a notice instead of throwing; `sendPrompt` fetches text via `clutch_prompt` and calls `app.sendMessage` (adding `_meta: {"com.google.antigravity/message": {"target": "new"}}` for background launch), hidden or disabled when `app.getHostCapabilities()?.message` is absent; selecting a ticket or box item calls `app.updateModelContext` when `app.getHostCapabilities()?.updateModelContext` is present.
  - Tabs: Tickets (`createTicketsView`, liveness from `clutch_engine_control` `ping` plus `snap.engine`, play/stop via `clutch_engine_start` / `clutch_engine_control`, priority and runs-before via `clutch_ticket_order`, confirm/reject via `clutch_app_ticket_confirm` / `clutch_app_ticket_reject` enabled strictly from `row.menu`); Details (`createDetailView` plus links for `ticket.md`, `run.md`, `checks.json`, `review.md`, `diagnosis.json`, `rework.md`, `config.yaml`); Recent Steps (`snap.steps`, `step.path` opens via `openFile`); Suggestion Box (`createBoxView` with multi-select `clutch_box_triage` / `clutch_box_dismiss`); Stats (`clutch_app_stats` with windows `24h`, `7d`, `30d`, `20t`); Help & Lifecycle (`snap.help` topics and links plus inline `ticket-lifecycle.svg`).
  - Agent kickoff buttons (Supervise Drain Loop, Run Roadmap (Drain), Run Roadmap (Serve), Diagnose Stem, Review Drafts) and a repo-path input for `global` launches with no CWD checkout.
- `clutch/ui/dashboard.css`: tab, toolbar, and control styles using the host CSS variables with fallbacks.
- `tests/integration/conftest.py`: add `"test_mcp_app_dashboard.py"` to `REAL_IO_TESTS` and nothing else.
- New Node harness `tests/mcp_app_dashboard.js`: extracts the inline `<script>` body from a built `dashboard.html` path argument, evaluates it in `vm.createContext` with fake `document`, `window`, `globalThis`, and `__CLUTCH_DASHBOARD_NO_AUTOBOOT__: true` (no `node_modules` resolution at test time), and drives `ctx.ClutchDashboardApp.createDashboardApp(...)` with a fake app transport.
- New `tests/integration/test_mcp_app_dashboard.py`: calls `dev.build_ui_bundle(root=<Path(__file__) repo anchor>, out=tmp_path / "dashboard.html")` with real esbuild, serves it through `ClutchMCPServer(ui_html_path=out).dispatch("resources/read", {"uri": "ui://clutch/dashboard.html"})`, checks MIME, size, inlining, and the embedded SVG, and runs `node tests/mcp_app_dashboard.js <out>`.
- Engine-written `# clutch:meta` headers on newly created Python test files under `tests/` updated by Check.

Out:
- `clutch/mcp.py`, `dev.py`, `package.json`, `.gitignore`, and docs or rule files.
- `vscode-clutchwork/`, `clutch/help.py`, `clutch/hostfiles.py`, `clutch/specs/ask/*.md`, `clutch/antigravity.py`.
- Tests in any of the seven hot test files.

## Scope fence
- clutch/ui/app.js
- clutch/ui/dashboard.css
- tests/integration/conftest.py
- tests/integration/test_mcp_app_dashboard.py
- tests/mcp_app_dashboard.js

## Acceptance criteria
1. `tests/integration/test_mcp_app_dashboard.py` builds `dashboard.html` into `tmp_path` via `dev.build_ui_bundle`, checks the HTML served by `resources/read` has MIME `text/html;profile=mcp-app`, is non-empty and under 10 MiB, contains no `<script src=` or `<link rel="stylesheet" href=`, and embeds `ticket-lifecycle.svg`, then passes `tests/mcp_app_dashboard.js` in Node exercising: `applyDocumentTheme` and `applyHostStyleVariables` on connect and `onhostcontextchanged`; `clutch_app_snapshot` and `clutch_app_stats` calls; all six views; `com.google.antigravity/toggle-aux-pane` file opening with graceful `-32601` and `isError` handling; `app.sendMessage` for the current conversation and with `_meta["com.google.antigravity/message"].target == "new"`, hidden or disabled when the `message` capability is absent; `app.updateModelContext` on selection; and admission-gated `clutch_app_ticket_confirm`, `clutch_app_ticket_reject`, `clutch_ticket_order`, `clutch_box_triage`, `clutch_box_dismiss`, `clutch_engine_start`, and `clutch_engine_control` calls. Verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py tests/integration/test_disk_io_skip_list.py`.
2. Shared-renderer and MCP server tests pass unchanged (`vscode-clutchwork/` works identically). Verified by `./dev.py test tests/integration/test_ui_shared_renderers.py tests/integration/test_mcp_read_server.py tests/unit/test_mcp_app_dashboard.py`.

## Verification
```
./dev.py test tests/integration/test_mcp_app_dashboard.py tests/integration/test_disk_io_skip_list.py tests/integration/test_ui_shared_renderers.py tests/integration/test_mcp_read_server.py tests/unit/test_mcp_app_dashboard.py
```

## Definition of rejected
- The built dashboard loads external scripts or stylesheets, exceeds 10 MiB, or hand-rolls `postMessage` instead of `@modelcontextprotocol/ext-apps`.
- `clutch/ui/app.js` duplicates graph layout, sorting, filtering, or admission logic owned by Python or `vscode-clutchwork/media/`, or enables an action not present in `row.menu`.
- A failed `toggle-aux-pane` request throws instead of degrading, or `sendMessage` controls show when the `message` capability is absent.
- `vscode-clutchwork/` is modified, or any file outside `## Scope fence` is modified.

## Time budget
- expected: 25m
- stuck: 50m