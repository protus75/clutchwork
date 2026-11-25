---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- mcp-control-and-tickets
- ui-shared-renderers

## Context
- docs/antigravity-plan.md#4. Antigravity MCP App dashboard replacing VS Code views
- docs/antigravity-plan.md#Risks
- docs/antigravity-plan.md#Open decisions
- clutch/mcp.py
- vscode-clutchwork/media/graph.js
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/media/view.css
- dev.py
- package.json
- tests/unit/test_mcp_protocol.py
- tests/unit/test_mcp_tools.py
- tests/integration/conftest.py
- tests/ui_shared_renderers.js
- tests/integration/test_ui_shared_renderers.py

## On-demand
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- CLAUDE.md
- AGENTS.md

## Goal / Why
Roadmap row 223 (`mcp-app-dashboard`, `docs/antigravity-plan.md` §4, Risks #2, Open decisions #1). After `mcp-control-and-tickets` and `ui-shared-renderers`, `clutch mcp serve` exposes read, ticket, Suggestion Box, and engine-control tools and the shared browser renderers accept a host adapter, but Antigravity has no MCP App UI resource or dashboard bundle to render in its side pane (`aux_pane`) or global sidebar (`global`).

After this ticket:
- `./dev.py ui-bundle` builds a single self-contained `clutch/ui/dashboard.html` (under 10 MiB, zero external script/style requests under default CSP) from `clutch/ui/app.js`, `clutch/ui/dashboard.css`, the shared `vscode-clutchwork/media/{graph,view,detail,box}.js` renderers, `vscode-clutchwork/media/view.css`, `vscode-clutchwork/media/ticket-lifecycle.svg`, and `@modelcontextprotocol/ext-apps`.
- `clutch/mcp.py` advertises the `resources` capability, serves `ui://clutch/dashboard.html` (`mimeType: "text/html;profile=mcp-app"`, `_meta.ui.prefersBorder: false`) via `resources/list` and `resources/read`, and adds `clutch_open_dashboard` (declaring `ui.resourceUri` and `com.google.antigravity/ui` `aux_pane` and `global` entrypoints while returning a compact summary well under Antigravity's 1 MiB trajectory cap) plus `visibility: ["app"]` data tools `clutch_app_snapshot` and `clutch_app_stats`.
- The MCP App renders all six surfaces (Tickets graph with engine liveness/play/stop/priority/runs-before/confirm/reject controls, Details pane with shared fences and artifact links, Recent Steps, Suggestion Box with multi-select triage/dismiss, Stats, and Help & Lifecycle with `ticket-lifecycle.svg`), syncs theme tokens via `applyDocumentTheme` and `applyHostStyleVariables`, opens files via `com.google.antigravity/toggle-aux-pane` (degrading cleanly on `-32601` / `isError`), launches agent prompts via `app.sendMessage` (including `com.google.antigravity/message` `target: "new"`), and attaches selected context via `app.updateModelContext` when supported.
- `vscode-clutchwork/` continues working unchanged, and `CLAUDE.md` / `AGENTS.md` extend the operator-only client JS exception under the Pure Python rule (repo-rule home) to cover `clutch/ui/`.

Rejected simpler approach: hand-writing a raw `postMessage` bridge or returning the full `observe.snapshot` payload inside `clutch_open_dashboard`. Hand-writing `postMessage` skips the SEP-1865 handshake, auto-resize, and host-context contract owned by `@modelcontextprotocol/ext-apps`, and returning the full snapshot from `clutch_open_dashboard` bloats conversation trajectories and hits Antigravity's 1 MiB `CallToolResult` cap.

## Boundary contract

### MCP App UI resource and dashboard tools
- disposition: extend
- owner: clutch/mcp.py
- consumers: Antigravity MCP host (`aux_pane`, `global`, inline views), `clutch/ui/dashboard.html`, `tests/unit/test_mcp_protocol.py`, `tests/unit/test_mcp_tools.py`, `tests/unit/test_mcp_control_and_tickets.py`, `tests/unit/test_mcp_app_dashboard.py`, `tests/integration/test_mcp_app_dashboard.py`
- observable change: `initialize` adds `"resources": {"listChanged": False}` to `capabilities`; `resources/list` returns `ui://clutch/dashboard.html` (`mimeType: "text/html;profile=mcp-app"`, `_meta: {"ui": {"prefersBorder": False}}`); `resources/read` validates `params["uri"] == "ui://clutch/dashboard.html"` (`InvalidParams` otherwise), reads `self.ui_html_path` (injectable on `ClutchMCPServer.__init__`, defaulting to `Path(__file__).parent / "ui" / "dashboard.html"`), raises `DomainError` (`code: "dashboard_unavailable"`) when missing or empty, and returns `{"contents": [{"uri": "ui://clutch/dashboard.html", "mimeType": "text/html;profile=mcp-app", "text": html}]}`; `tools/list` adds `clutch_open_dashboard` (`_meta: {"ui": {"resourceUri": "ui://clutch/dashboard.html"}, "com.google.antigravity/ui": {"entrypoints": [{"type": "aux_pane", "title": "ClutchWork"}, {"type": "global", "title": "ClutchWork"}]}}`) plus `app`-only `clutch_app_snapshot` and `clutch_app_stats` (`_meta: {"ui": {"visibility": ["app"]}}`); `clutch_open_dashboard` accepts optional `repo` and `tab` so `{}` succeeds on entrypoint launches (returning `ready: False` when `repo` is omitted and CWD has no `tickets/`, or a compact summary omitting `rows`/`box`/`steps`/`help` when resolved, while explicit invalid `repo` still returns `isError: True` with `code: "invalid_repo"`); `clutch_app_snapshot` delegates to `observe.snapshot` and `clutch_app_stats` shares the `stats.window_start` / `stats.collect_stats` / `stats.stats_tree` helper with `clutch_stats`.
- compatibility: all 22 tools from `mcp-control-and-tickets` and all 10 MCP Prompts keep their exact schemas and behavior; `tests/unit/test_mcp_protocol.py`, `tests/unit/test_mcp_tools.py`, and (if asserting exact tool sets) `tests/unit/test_mcp_control_and_tickets.py` update their expected capability/tool sets.
- acceptance: criteria 1, 2, 3, and 6
- tests: tests/unit/test_mcp_app_dashboard.py, tests/unit/test_mcp_protocol.py, tests/unit/test_mcp_tools.py, tests/unit/test_mcp_control_and_tickets.py, tests/integration/test_mcp_app_dashboard.py
- post-merge source of truth: clutch/mcp.py

### Self-contained Antigravity MCP App dashboard bundle
- disposition: create
- owner: clutch/ui/dashboard.html
- closest existing: `vscode-clutchwork/extension.js` (VS Code webview host), `vscode-clutchwork/media/{graph,view,detail,box}.js` (shared DOM/SVG renderers)
- earning reason: independently deployed single-HTML MCP App iframe boundary required by Antigravity's default CSP (`default-src 'none'`) and `@modelcontextprotocol/ext-apps` postMessage transport; `vscode-clutchwork/extension.js` depends on the `vscode` API and cannot run inside an MCP App iframe, while the shared renderers in `vscode-clutchwork/media/` are reused directly rather than duplicated.
- consumers: `clutch/mcp.py` (`resources/read`), Antigravity side pane (`aux_pane`) and sidebar (`global`), `tests/integration/test_mcp_app_dashboard.py`
- observable change: adds `clutch/ui/app.js`, `clutch/ui/dashboard.css`, and generated `clutch/ui/dashboard.html` built by `./dev.py ui-bundle`; wires `@modelcontextprotocol/ext-apps` (`App`, `applyDocumentTheme`, `applyHostStyleVariables`) to `renderGraph`, `createTicketsView`, `createDetailView`, and `createBoxView` plus Recent Steps, Stats, Help & Lifecycle (`ticket-lifecycle.svg`), `com.google.antigravity/toggle-aux-pane`, `app.sendMessage` (current and `target: "new"`), and `app.updateModelContext`.
- compatibility: `vscode-clutchwork/` files and tests are untouched and keep passing identically.
- acceptance: criteria 4, 5, and 6
- tests: tests/unit/test_mcp_app_dashboard.py, tests/integration/test_mcp_app_dashboard.py, tests/integration/test_ui_shared_renderers.py
- post-merge source of truth: clutch/ui/app.js

### Repo UI bundle build task
- disposition: extend
- owner: dev.py
- consumers: developers, `clutch/ui/dashboard.html`, `tests/unit/test_mcp_app_dashboard.py`
- observable change: adds `build_ui_bundle(root=ROOT, run_cmd=subprocess.run) -> Path` and the `./dev.py ui-bundle` subcommand, which bundles `clutch/ui/app.js` with `esbuild` (`--bundle --format=iife --platform=browser --global-name=ClutchDashboardApp`), inlines `vscode-clutchwork/media/view.css`, `clutch/ui/dashboard.css`, `vscode-clutchwork/media/ticket-lifecycle.svg`, and the bundled JS into a single self-contained `clutch/ui/dashboard.html` (escaping `</script>` safely inside the inline script), and exits non-zero with a clear message if `esbuild` or any source asset is missing.
- compatibility: all existing `./dev.py` tasks (`test`, `visual-baseline`, `vscode`, `vscode-package`) preserve their exact behavior.
- acceptance: criteria 4 and 6
- tests: tests/unit/test_mcp_app_dashboard.py, tests/unit/test_dev_testguard.py
- post-merge source of truth: dev.py

### CLI help, command docs, and repo agent-rule exception
- disposition: extend
- owner: clutch/__main__.py, clutch/docs/host-running.md, docs/how-clutch-works.md, CLAUDE.md, AGENTS.md
- consumers: operators, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/integration/test_help.py`
- observable change: updates `mcp` / `mcp serve` CLI help and `| \`mcp serve\` |` rows in `clutch/docs/host-running.md` and `docs/how-clutch-works.md` §2.1 to include the `ui://clutch/dashboard.html` MCP App resource and dashboard tools; adds the `ui-bundle` row to `docs/how-clutch-works.md` §2.2; extends the repo-rule Pure Python exception in both `CLAUDE.md` and `AGENTS.md` (outside the managed block; repo-rule home) to include `clutch/ui/`; and updates the Command surface rule in `CLAUDE.md` (line 132, outside the managed block; repo-rule home; `AGENTS.md` is the curated subset and does not carry that rule) to list `ui-bundle` alongside `test`, `visual-baseline`, `vscode`, and `vscode-package`.
- compatibility: CLI argv and table column-1 verb names remain unchanged; `clutch/hostfiles.py` (`CORE_TEMPLATE`) is untouched.
- acceptance: criterion 7
- tests: tests/unit/test_main_help.py, tests/unit/test_host_running.py, tests/integration/test_help.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
In:
- `clutch/mcp.py`:
  - Define constants `DASHBOARD_URI = "ui://clutch/dashboard.html"`, `MCP_APP_MIME = "text/html;profile=mcp-app"`, and `DEFAULT_DASHBOARD_HTML = Path(__file__).parent / "ui" / "dashboard.html"`.
  - Add `ui_html_path: Path | None = None` parameter on `ClutchMCPServer.__init__` (defaulting to `DEFAULT_DASHBOARD_HTML`).
  - Add `"resources": {"listChanged": False}` to `initialize` `capabilities`.
  - Implement `resources/list` returning the `DASHBOARD_URI` entry (`mimeType: MCP_APP_MIME`, `_meta: {"ui": {"prefersBorder": False}}`) and `resources/read` validating `params.get("uri") == DASHBOARD_URI` (`InvalidParams` otherwise), reading `self.ui_html_path` (raising `DomainError` with `code: "dashboard_unavailable"` if unreadable/empty), and returning `{"contents": [{"uri": DASHBOARD_URI, "mimeType": MCP_APP_MIME, "text": html}]}`.
  - Add Pydantic `BaseModel` (`extra="forbid"`) schema `Dashboard(Repo)` with `tab: Literal["tickets", "steps", "box", "stats", "help"] = "tickets"`.
  - Register `clutch_open_dashboard` (with `_meta: {"ui": {"resourceUri": DASHBOARD_URI}, "com.google.antigravity/ui": {"entrypoints": [{"type": "aux_pane", "title": "ClutchWork"}, {"type": "global", "title": "ClutchWork"}]}}`), `clutch_app_snapshot` (schema `Snapshot`, `_meta: {"ui": {"visibility": ["app"]}}`), and `clutch_app_stats` (schema `Stats`, `_meta: {"ui": {"visibility": ["app"]}}`).
  - Handle `clutch_open_dashboard`: if `args.repo is None` and not `(self.cwd / "tickets").is_dir()`, return compact `{"repo": None, "tab": args.tab, "ready": False, "version": version("clutchwork"), "message": "Supply a ClutchWork checkout path to load the dashboard."}` without error; otherwise resolve `self.checkout(args.repo)`, compute `observe.snapshot(ctx, merged_limit=cfg.snapshot_merged_limit)`, and return a compact summary (`repo`, `tab`, `ready: True`, `counts`, `engine`, `runningStem`, `blockedCount`, `pendingBox`, `version`) plus concise one-line text (omitting `rows`, `box`, `steps`, `help`). Keep all user-facing messages and paved roads in `clutch/mcp.py` (including `dashboard_unavailable` and `ready: False`) free of `./dev.py` / `dev.py` references so `tests/integration/test_engine_text_verbs.py::test_no_engine_text_names_dev_py` passes.
  - Route `clutch_app_snapshot` to `observe.snapshot` and `clutch_app_stats` to the shared stats helper used by `clutch_stats`.
- `package.json` and `pnpm-lock.yaml`:
  - Add `@modelcontextprotocol/ext-apps`, `esbuild`, and `zod` to `devDependencies` (installed via `pnpm add -D`) so `./dev.py ui-bundle` resolves them cleanly.
- `dev.py`:
  - Add `build_ui_bundle(root=ROOT, run_cmd=subprocess.run) -> Path` and the `ui-bundle` subcommand (listed in module docstring and argparse subparsers): invokes local `node_modules/.bin/esbuild` (or `pnpm exec esbuild`) with `--bundle --format=iife --platform=browser --global-name=ClutchDashboardApp` to bundle `clutch/ui/app.js` as a browser IIFE exposing `ClutchDashboardApp.createDashboardApp`, inlines `vscode-clutchwork/media/view.css`, `clutch/ui/dashboard.css`, `vscode-clutchwork/media/ticket-lifecycle.svg`, and the bundled JS (escaping `</script` to `<\/script`) into `clutch/ui/dashboard.html`.
- `clutch/ui/` (`clutch/ui/app.js`, `clutch/ui/dashboard.css`, and generated `clutch/ui/dashboard.html`):
  - `clutch/ui/app.js`: imports `App`, `applyDocumentTheme`, `applyHostStyleVariables` from `@modelcontextprotocol/ext-apps` and `z` from `zod` (or a schema compatible with `app.request`), imports `renderGraph`, `createTicketsView`, `createDetailView`, and `createBoxView` from `../../vscode-clutchwork/media/{graph,view,detail,box}.js`, exports a pure `createDashboardApp(options)` factory (exposed on `ClutchDashboardApp.createDashboardApp` in the IIFE bundle) and guards auto-boot with `if (typeof document !== "undefined" && !globalThis.__CLUTCH_DASHBOARD_NO_AUTOBOOT__)` so the Node harness can load the bundled `<script>` cleanly without triggering browser auto-boot.
  - Registers `app.ontoolinput`, `app.ontoolresult`, and `app.onhostcontextchanged` before `await app.connect()`; applies `applyDocumentTheme` and `applyHostStyleVariables` right after `connect()` and on every `onhostcontextchanged`.
  - Implements the host adapter `{callTool, openFile, sendPrompt, openHelp, onFocus}`:
    - `callTool` calls `app.callServerTool` with `{repo}` when set (serializing/throttling refreshes so no more than 4 calls are in flight).
    - `openFile` resolves relative paths against `snap.root` into a `file://` URI and calls `app.request({method: "com.google.antigravity/toggle-aux-pane", params: {tabType: "fileView", uri}}, ...)`, catching `-32601` or `result.isError` gracefully (disabling file-open notice instead of throwing).
    - `sendPrompt` fetches rendered prompt text via `clutch_prompt` and calls `app.sendMessage` (with `_meta: {"com.google.antigravity/message": {"target": "new"}}` when background launch is selected), hidden/disabled when `app.getHostCapabilities()?.message` is absent.
    - Selecting a ticket or box item calls `app.updateModelContext` when `app.getHostCapabilities()?.updateModelContext` is present.
  - Renders all six surfaces without duplicating domain/layout/admission logic:
    - Tickets tab (`createTicketsView`, engine liveness indicator via `clutch_engine_control` `ping` + `snap.engine`, play/stop via `clutch_engine_start`/`clutch_engine_control`, priority and `runs-before` via `clutch_ticket_order`, admission-gated `confirm`/`reject` via `clutch_app_ticket_confirm`/`clutch_app_ticket_reject` enabled strictly from `row.menu`).
    - Details pane (`createDetailView` plus clickable artifact links for `ticket.md`, `run.md`, `checks.json`, `review.md`, `diagnosis.json`, `rework.md`, `config.yaml`).
    - Recent Steps tab (`snap.steps` with `step.path` click -> `openFile`).
    - Suggestion Box tab (`createBoxView` with multi-select `clutch_box_triage` and `clutch_box_dismiss`).
    - Stats tab (`clutch_app_stats` with window selector `24h`/`7d`/`30d`/`20t`).
    - Help & Lifecycle tab (`snap.help` topics/links + inline `ticket-lifecycle.svg`).
    - Agent kickoff buttons (*"Supervise Drain Loop"*, *"Run Roadmap (Drain)"*, *"Run Roadmap (Serve)"*, *"Diagnose Stem"*, *"Review Drafts"*) and a repo-path input for `global` view launches with no CWD checkout.
  - `clutch/ui/dashboard.css`: layout, tabs, toolbar, and control styles using `--color-background-*`, `--color-text-*`, `--color-border-*`, and `--font-sans` with fallbacks.
  - `clutch/ui/dashboard.html`: generated by running `./dev.py ui-bundle` and committed.
- `clutch/__main__.py`, `clutch/docs/host-running.md`, `docs/how-clutch-works.md`:
  - Update `mcp` / `mcp serve` help in `clutch/__main__.py`, the `| \`mcp serve\` |` row in `clutch/docs/host-running.md`, and the `| \`mcp serve\` |` (§2.1) and `ui-bundle` (§2.2) rows in `docs/how-clutch-works.md`.
- `CLAUDE.md` and `AGENTS.md`:
  - Extend the Pure Python rule's operator-only client JS exception (outside the managed block; repo-rule home) to name `clutch/ui/` alongside `vscode-clutchwork/` in both `CLAUDE.md` and `AGENTS.md`.
  - Update the Command surface rule in `CLAUDE.md` (outside the managed block; repo-rule home) to list `ui-bundle` alongside `test`, `visual-baseline`, `vscode`, and `vscode-package`.
- `tests/unit/test_mcp_protocol.py`: update only line 35's expected `capabilities` set from `{"tools", "prompts"}` to `{"tools", "prompts", "resources"}`; nothing else in the file changes.
- `tests/unit/test_mcp_tools.py`: update only `test_schemas_and_prompts`'s expected `tools/list` name set to include `clutch_open_dashboard`, `clutch_app_snapshot`, and `clutch_app_stats` (25 tools total); nothing else in the file changes.
- `tests/unit/test_mcp_control_and_tickets.py`: if its `tools/list` assertion checks exact equality on model-visible or `app`-only tool sets, update only those expected sets to include `clutch_open_dashboard` (model-visible) and `clutch_app_snapshot`, `clutch_app_stats` (`app`-only); nothing else in the file changes.
- New unit test file `tests/unit/test_mcp_app_dashboard.py` (using `tmp_path`, `io.StringIO`, and fakes only; zero repo file reads or subprocesses): covers `initialize` `resources` capability, `resources/list`, `resources/read` (happy path, unknown URI `-32602`, missing/empty file `dashboard_unavailable`), `tools/list` `_meta` (`resourceUri`, `com.google.antigravity/ui.entrypoints`, `visibility: ["app"]`), `clutch_open_dashboard` (empty `{}` with and without checkout CWD, explicit invalid `repo`, compact payload omitting `rows`/`box`/`steps`/`help`), `clutch_app_snapshot`, `clutch_app_stats`, `dev.build_ui_bundle` (with fake `run_cmd` and `tmp_path`, including `</script>` escaping and missing-source refusal), and keeps `clutch/mcp.py` above its 90% coverage floor.
- `tests/integration/conftest.py`: add `"test_mcp_app_dashboard.py"` to `REAL_IO_TESTS` (and nothing else).
- New Node harness `tests/mcp_app_dashboard.js` and integration test `tests/integration/test_mcp_app_dashboard.py`: verifies the real committed `clutch/ui/dashboard.html` is served by `ClutchMCPServer.dispatch("resources/read", {"uri": "ui://clutch/dashboard.html"})`, has MIME `text/html;profile=mcp-app`, is non-empty and under 10 MiB, contains no external `<script src=` or `<link rel="stylesheet" href=`, embeds `ticket-lifecycle.svg`, and runs `node tests/mcp_app_dashboard.js <path-to-dashboard.html>` which extracts the inline `<script>` body from `clutch/ui/dashboard.html`, evaluates it in Node's `vm.createContext` with fake `document`, `window`, `globalThis`, and `__CLUTCH_DASHBOARD_NO_AUTOBOOT__: true` (requiring zero `node_modules` resolution at test time because `@modelcontextprotocol/ext-apps` is already bundled inside the IIFE), and calls `ctx.ClutchDashboardApp.createDashboardApp(...)` to verify theme binding (`applyDocumentTheme` / `applyHostStyleVariables`), `com.google.antigravity/toggle-aux-pane` file opening and `-32601`/`isError` degradation, `app.sendMessage` (current and `target: "new"`) capability gating, `app.updateModelContext`, `clutch_app_snapshot`/`clutch_app_stats` data fetches, and admission-gated UI actions.
- Engine-written `# clutch:meta` headers on newly created Python test files under `tests/` updated by Check.

Out:
- Modifying `vscode-clutchwork/` or `clutch/help.py` (`vscode-clutchwork/` stays unchanged per Open decision #1).
- Updating `clutch/specs/ask/*.md` (`ask-specs-mcp-supervision`), `clutch/antigravity.py` / `clutch host antigravity` / `README.md` / `clutch/docs/host-contract.md` (`host-antigravity-plugin`), or `clutch/hostfiles.py`.
- Adding tests to any of the seven hot test files (`tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`).

## Scope fence
- clutch/mcp.py
- clutch/ui/
- dev.py
- package.json
- pnpm-lock.yaml
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- CLAUDE.md
- AGENTS.md
- tests/unit/test_mcp_protocol.py
- tests/unit/test_mcp_tools.py
- tests/unit/test_mcp_control_and_tickets.py
- tests/unit/test_mcp_app_dashboard.py
- tests/integration/conftest.py
- tests/integration/test_mcp_app_dashboard.py
- tests/mcp_app_dashboard.js

## Acceptance criteria
1. `tests/unit/test_mcp_protocol.py` and `tests/unit/test_mcp_app_dashboard.py` check `initialize` returns `"resources": {"listChanged": False}` in `capabilities` (not omitting `resources`), `resources/list` returns `ui://clutch/dashboard.html` with `mimeType: "text/html;profile=mcp-app"` and `_meta: {"ui": {"prefersBorder": False}}`, and `resources/read` returns the HTML from `ui_html_path` (ruling out unknown URI returning success by asserting `-32602`, and ruling out missing/empty HTML crashing by asserting `DomainError` with `code: "dashboard_unavailable"`). Verified by `./dev.py test tests/unit/test_mcp_protocol.py tests/unit/test_mcp_app_dashboard.py`.
2. `tests/unit/test_mcp_tools.py`, `tests/unit/test_mcp_control_and_tickets.py`, and `tests/unit/test_mcp_app_dashboard.py` check `tools/list` exposes all 25 tools, `clutch_open_dashboard` carries `_meta.ui.resourceUri == "ui://clutch/dashboard.html"` and `_meta["com.google.antigravity/ui"]["entrypoints"] == [{"type": "aux_pane", "title": "ClutchWork"}, {"type": "global", "title": "ClutchWork"}]`, and `clutch_app_snapshot` and `clutch_app_stats` carry `_meta: {"ui": {"visibility": ["app"]}}` (not exposed without `visibility: ["app"]`). Verified by `./dev.py test tests/unit/test_mcp_tools.py tests/unit/test_mcp_control_and_tickets.py tests/unit/test_mcp_app_dashboard.py`.
3. `tests/unit/test_mcp_app_dashboard.py` checks `clutch_open_dashboard` succeeds with `{}` when CWD is a checkout (returning a compact `structuredContent` with `repo`, `tab`, `ready: True`, `counts`, `engine`, `runningStem`, `blockedCount`, `pendingBox`, `version`, and explicitly ruling out trajectory bloat by asserting `rows`, `box`, `steps`, and `help` are absent), succeeds with `{}` when CWD has no `tickets/` directory (`ready: False`, `repo: None`, not `isError`), returns `isError: True` with `code: "invalid_repo"` for an explicit invalid `repo`, and routes `clutch_app_snapshot` and `clutch_app_stats` to `observe.snapshot` and `stats.collect_stats` / `stats.stats_tree` (including `invalid_window` refusal). Verified by `./dev.py test tests/unit/test_mcp_app_dashboard.py`.
4. `tests/unit/test_mcp_app_dashboard.py` checks `dev.build_ui_bundle` (with `tmp_path` and a fake `run_cmd`) produces a self-contained HTML file inlining CSS, SVG, and escaped JS (ruling out raw `</script>` breaking the script tag and ruling out missing inputs silently writing broken HTML). Verified by `./dev.py test tests/unit/test_mcp_app_dashboard.py tests/unit/test_dev_testguard.py`.
5. `tests/integration/test_mcp_app_dashboard.py` checks the real committed `clutch/ui/dashboard.html` served through `ClutchMCPServer.dispatch("resources/read", {"uri": "ui://clutch/dashboard.html"})` is non-empty, under 10 MiB, contains no external `<script src=` or `<link rel="stylesheet" href=` references, embeds `ticket-lifecycle.svg`, and passes `tests/mcp_app_dashboard.js` in Node exercising: `applyDocumentTheme` and `applyHostStyleVariables` on connect and `onhostcontextchanged`, `clutch_app_snapshot` and `clutch_app_stats` calls, all six views (Tickets, Details, Recent Steps, Suggestion Box, Stats, Help & Lifecycle), `com.google.antigravity/toggle-aux-pane` file opening and graceful `-32601` / `isError` handling, `app.sendMessage` (current conversation and `_meta["com.google.antigravity/message"].target == "new"`) hidden/disabled when `message` capability is absent, `app.updateModelContext` on user selection, and admission-gated `clutch_app_ticket_confirm` / `clutch_app_ticket_reject` / `clutch_ticket_order` / `clutch_box_triage` / `clutch_box_dismiss` / `clutch_engine_start` / `clutch_engine_control` invocations. Verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py tests/integration/test_disk_io_skip_list.py`.
6. Existing shared-renderer, MCP server, and help tests pass unchanged (`vscode-clutchwork/` works identically) and `clutch/mcp.py` meets its 90% `test-gate.toml` unit coverage floor. Verified by `./dev.py test tests/integration/test_ui_shared_renderers.py tests/integration/test_mcp_read_server.py tests/integration/test_help.py tests/unit/test_main_mcp_serve.py`.
7. `clutch/__main__.py` (`mcp` / `mcp serve` help), `clutch/docs/host-running.md` (`| \`mcp serve\` |`), `docs/how-clutch-works.md` (§2.1 `| \`mcp serve\` |` and §2.2 `ui-bundle`), both `CLAUDE.md` and `AGENTS.md` (Pure Python exception naming `clutch/ui/`), and `CLAUDE.md`'s Command surface rule (listing `ui-bundle`) are updated consistently and pass `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/integration/test_help.py`.

## Verification
```
./dev.py test tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_protocol.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_control_and_tickets.py tests/unit/test_main_mcp_serve.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_dev_testguard.py tests/integration/test_mcp_app_dashboard.py tests/integration/test_ui_shared_renderers.py tests/integration/test_help.py tests/integration/test_disk_io_skip_list.py tests/integration/test_mcp_read_server.py
```

## Definition of rejected
- `clutch/ui/dashboard.html` loads external scripts or stylesheets, exceeds 10 MiB, omits `@modelcontextprotocol/ext-apps` (hand-rolls `postMessage`), or duplicates graph layout, sorting, filtering, or admission logic already owned by Python / `vscode-clutchwork/media/`.
- `clutch_open_dashboard` embeds full `rows`, `box`, `steps`, or `help` payloads in its `CallToolResult`, or fails when invoked with `{}` in a global view without a checkout CWD.
- `clutch_app_snapshot` or `clutch_app_stats` omits `_meta: {"ui": {"visibility": ["app"]}}`, or `initialize` omits the `resources` capability.
- `vscode-clutchwork/` is broken or modified outside the fence, or `CLAUDE.md` and `AGENTS.md` disagree on the Pure Python exception.
- Any file outside `## Scope fence` is modified, or `clutch/mcp.py` drops below its 90% `test-gate.toml` unit coverage floor.

## Time budget
- expected: 25m
- stuck: 50m
