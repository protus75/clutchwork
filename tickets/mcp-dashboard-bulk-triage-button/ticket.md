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
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py

## Goal / Why
Add a manual **Bulk Triage** button to the Antigravity MCP dashboard top toolbar (`.top-bar`) when the engine is running and pending Suggestion Box messages exist, so the operator can trigger bulk triage directly from the top bar without expanding and scrolling to the bottom of the collapsible **Suggestion Box** section. Clicking it submits `clutch_box_triage` with `{ ids: [] }`, refreshes the dashboard, and displays submission confirmation (or any tool error) in `.notice`.

## Boundary contract

### Antigravity dashboard toolbar
- disposition: extend
- owner: clutch/ui/app.js
- consumers: Antigravity MCP App dashboard users and `tests/mcp_app_dashboard.js`
- observable change: When the engine is running (`ping.engine && snap.engine`) and `(snap.boxCounts?.pending ?? 0) > 0`, the `.top-bar` toolbar renders a `Bulk Triage` button with an SVG icon. Clicking it calls `clutch_box_triage` with `{ ids: [] }`, refreshes the dashboard, and sets `.notice` to `Triage submitted: <request_id>` when `request_id` is returned (or `Triage submitted` when `submitted` is true without `request_id`, or the error message on failure). When the engine is stopped or `snap.boxCounts?.pending` is 0, `Bulk Triage` is not rendered in `.top-bar`.
- compatibility: Existing `.top-bar` controls (`Drain`, `Serve`, `Stop`, `Refresh`, `Open config.yaml`, repo selector) and existing `Suggestion Box` section `boxActions` controls remain unchanged.
- acceptance: `Bulk Triage` appears in `.top-bar` only while the engine is running with pending box messages, invokes `clutch_box_triage` with `{ ids: [] }`, refreshes, and displays submission confirmation or error in `.notice`.
- tests: `tests/mcp_app_dashboard.js` exercised via `./dev.py test tests/integration/test_mcp_app_dashboard.py`
- post-merge source of truth: clutch/ui/app.js

### MCP box triage tool
- disposition: reuse
- owner: clutch/mcp.py
- consumers: `clutch/ui/app.js` and MCP clients calling `clutch_box_triage`
- observable change: None; `clutch_box_triage` already accepts `ids: []` and optional `repo`, submits a `triage` control request to the running engine, and returns `{submitted: true, request_id}` (or an `engine_not_running` error when stopped).
- compatibility: Tool schema, visibility (`model`, `app`), and error codes remain unchanged.
- acceptance: Dashboard invokes `clutch_box_triage` through `callTool` without modifying `clutch/mcp.py` or `clutch/triage.py`.
- tests: Existing `tests/unit/test_mcp_control_and_tickets.py` and `tests/integration/test_mcp_app_dashboard.py`
- post-merge source of truth: clutch/mcp.py

## Scope in / Scope out
Scope in:
- In `clutch/ui/app.js`:
  - Add a `triage` icon path to `iconPaths` (reusing the existing `triage` SVG path from `shapes`).
  - In `refresh()`, when `running && (snap.boxCounts?.pending ?? 0) > 0`, append an `iconButton("Bulk Triage", "triage", ...)` to `toolbar` that calls `callTool("clutch_box_triage", { ids: [] })`, awaits `refresh()`, and sets `notice.textContent = \`Triage submitted: \${result.request_id}\`` when `result?.request_id` is present (or `"Triage submitted"` if `result?.submitted` is true without a `request_id`). Errors from `callTool` continue to surface in `notice` via `button`'s `showError` handler.
  - When `!running` or `(snap.boxCounts?.pending ?? 0) === 0`, do not render `Bulk Triage` in `toolbar`.
  - Leave existing `boxActions` in `renderActions()` unchanged.
- In `tests/mcp_app_dashboard.js`:
  - Return `{submitted: true, request_id: 'triage-req-1'}` from the mock `callServerTool` for `clutch_box_triage` (and test an error response path).
  - Assert `Bulk Triage` is present in `.top-bar` when the engine is running and `snap.boxCounts.pending > 0`, absent from `.top-bar` when `snap.boxCounts.pending === 0`, and absent from `.top-bar` when the engine is stopped (`engineRunning = false; snap.engine = false`).
  - Assert clicking `.top-bar`'s `Bulk Triage` calls `clutch_box_triage` with `{ ids: [] }`, triggers a refresh, and displays `Triage submitted: triage-req-1` in `.notice`, and that a tool error (`isError: true`) surfaces its message in `.notice`.

Scope out:
- No changes to `clutch/mcp.py`, `clutch/triage.py`, `clutch/serve.py`, `clutch/drain.py`, `clutch/observe.py`, `clutch/help.py`, or `vscode-clutchwork/`.
- Do not commit `clutch/ui/dashboard.html` (it is a gitignored build artifact built by `dev.build_ui_bundle`).
- Do not add plan/roadmap routing to triage.

## Scope fence
- clutch/ui/app.js
- tests/mcp_app_dashboard.js

## Acceptance criteria
1. When the engine is running (`ping.engine && snap.engine`) and `snap.boxCounts.pending > 0`, `.top-bar` contains a `Bulk Triage` button with an SVG icon, rather than appearing only inside the collapsible `Suggestion Box` section, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
2. Clicking `.top-bar`'s `Bulk Triage` invokes `clutch_box_triage` with `{ ids: [] }` via `callTool` (including `repo` when an explicit repository is selected), refreshes the dashboard snapshot, and displays `Triage submitted: triage-req-1` in `.notice` instead of leaving `.notice` blank after `refresh()` clears it, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
3. When `snap.boxCounts.pending === 0` (even while the engine is running) or when the engine is stopped (`engineRunning = false; snap.engine = false`), `Bulk Triage` is not rendered in `.top-bar`, rather than remaining clickable with nothing pending or into an `engine_not_running` refusal, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
4. When `clutch_box_triage` returns an error response (`isError: true`), `.notice` displays the error message instead of silently swallowing the failure or showing a submitted message, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
5. `clutch/ui/dashboard.html` bundles cleanly from `clutch/ui/app.js` with `dev.build_ui_bundle` and passes all existing dashboard checks without regressions, verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.

## Verification
```
./dev.py test tests/integration/test_mcp_app_dashboard.py
```

## Definition of rejected
- `Bulk Triage` is rendered in `.top-bar` when the engine is stopped or when `snap.boxCounts.pending === 0`, or invokes `clutch_box_triage` with non-empty `ids`.
- Clicking `.top-bar`'s `Bulk Triage` leaves `.notice` empty after `refresh()` or fails to surface tool errors in `.notice`.
- Changes leak outside `clutch/ui/app.js` and `tests/mcp_app_dashboard.js`, or break any existing assertion in `tests/mcp_app_dashboard.js`.

## Time budget
- expected: 10m
- stuck: 20m
