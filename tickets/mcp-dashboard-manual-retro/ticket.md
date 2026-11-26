---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/ui/app.js
- clutch/mcp.py::TOOLS
- clutch/mcp.py::_submit_only
- clutch/retro.py::project_window
- clutch/retro.py::select_trigger
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py

## Goal / Why
Add a manual **Run Retro** button to the Antigravity MCP dashboard top toolbar when the engine is running, so the operator can trigger a forced retro directly from the plugin without dropping to the CLI or asking an agent to call `clutch_engine_retro`. Triggering retro through `clutch_engine_retro` already advances the retro window on completion (`project_window`), resetting the automatic merge, settled, and spike counts for the next window.

## Boundary contract

### Antigravity dashboard toolbar
- disposition: extend
- owner: clutch/ui/app.js
- consumers: Antigravity MCP App dashboard users and `tests/mcp_app_dashboard.js`
- observable change: When the engine is running (`ping.engine && snap.engine`), the `.top-bar` toolbar renders a `Run Retro` button alongside `Stop`. Clicking it calls `clutch_engine_retro`, refreshes the dashboard, and shows submission feedback in `.notice` when `request_id` is returned (or shows the tool error in `.notice` on failure). When the engine is stopped, `Run Retro` is not rendered.
- compatibility: Existing `Drain`, `Serve`, `Stop`, `Refresh`, `Open config.yaml`, and repository selector controls remain unchanged.
- acceptance: `Run Retro` appears only while the engine is running, invokes `clutch_engine_retro`, refreshes, and displays submission confirmation or error in `.notice`.
- tests: `tests/mcp_app_dashboard.js` exercised via `./dev.py test tests/integration/test_mcp_app_dashboard.py`
- post-merge source of truth: clutch/ui/app.js

### MCP engine retro tool
- disposition: reuse
- owner: clutch/mcp.py
- consumers: `clutch/ui/app.js` and MCP clients calling `clutch_engine_retro`
- observable change: None; `clutch_engine_retro` already accepts optional `repo`, submits a `retro` control request to the running engine, and returns `{submitted: true, request_id}` (or an `engine_not_running` error when stopped). Completing the forced retro advances `project_window` in `clutch/retro.py`, resetting normal retro count triggers.
- compatibility: Tool schema, visibility (`model`, `app`), and error codes remain unchanged.
- acceptance: Dashboard invokes `clutch_engine_retro` through `callTool` without modifying `clutch/mcp.py` or `clutch/retro.py`.
- tests: Existing `tests/unit/test_mcp_control_and_tickets.py` and `tests/integration/test_mcp_app_dashboard.py`
- post-merge source of truth: clutch/mcp.py

## Scope in / Scope out
Scope in:
- In `clutch/ui/app.js`:
  - Add a `retro` icon path to `iconPaths` (reusing the existing retro SVG path from `shapes`).
  - In `refresh()`, when `running` is true, append an `iconButton("Run Retro", "retro", ...)` to `toolbar` alongside `Stop` that calls `callTool("clutch_engine_retro")`, awaits `refresh()`, and sets `notice.textContent = \`Retro submitted: \${result.request_id}\`` when `result?.request_id` is present (or `"Retro submitted"` if `result?.submitted` is true without a `request_id`). Errors from `callTool` continue to surface in `notice` via `button`'s `showError` handler.
  - When `running` is false, do not render `Run Retro`.
- In `tests/mcp_app_dashboard.js`:
  - Return `{submitted: true, request_id: 'retro-req-1'}` from the mock `callServerTool` for `clutch_engine_retro` (and test an error response path).
  - Assert `Run Retro` is present in `.top-bar` when the engine is running and absent when the engine is stopped.
  - Assert clicking `Run Retro` calls `clutch_engine_retro`, triggers a refresh, and displays the submitted request confirmation in `.notice`, and that a tool error surfaces in `.notice`.

Scope out:
- No changes to `clutch/mcp.py`, `clutch/retro.py`, `clutch/serve.py`, `clutch/drain.py`, `clutch/observe.py`, `clutch/help.py`, or `vscode-clutchwork/`.
- Do not commit `clutch/ui/dashboard.html` (it is a gitignored build artifact built by `dev.build_ui_bundle`).
- Do not change retro's `forced=True` admission rules or automatic count-reset mechanics (already implemented in `clutch/retro.py`).

## Scope fence
- clutch/ui/app.js
- tests/mcp_app_dashboard.js

## Acceptance criteria
1. When the engine is running (`ping.engine && snap.engine`), `.top-bar` contains a `Run Retro` button with an SVG icon, not omitted or rendered only in `Agent Actions`, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
2. Clicking `Run Retro` invokes `clutch_engine_retro` via `callTool` (passing `repo` when an explicit repository is selected), refreshes the dashboard snapshot, and displays `Retro submitted: retro-req-1` in `.notice` instead of leaving `.notice` blank after `refresh()` clears it, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
3. When the engine is stopped (`engineRunning = false; snap.engine = false`), `Run Retro` is not rendered in `.top-bar`, rather than remaining clickable into an `engine_not_running` refusal, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
4. When `clutch_engine_retro` returns an error response (`isError: true`), `.notice` displays the error message instead of silently swallowing the failure or showing a submitted message, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
5. `clutch/ui/dashboard.html` bundles cleanly from `clutch/ui/app.js` with `dev.build_ui_bundle` and passes all existing dashboard checks without regressions, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.

## Verification
```
./dev.py test tests/integration/test_mcp_app_dashboard.py
```

## Definition of rejected
- `Run Retro` is rendered while the engine is stopped, or invokes any tool other than `clutch_engine_retro`.
- Clicking `Run Retro` leaves `.notice` empty after `refresh()` or fails to surface tool errors in `.notice`.
- Changes leak outside `clutch/ui/app.js` and `tests/mcp_app_dashboard.js`, or break any existing assertion in `tests/mcp_app_dashboard.js`.

## Time budget
- expected: 10m
- stuck: 20m
