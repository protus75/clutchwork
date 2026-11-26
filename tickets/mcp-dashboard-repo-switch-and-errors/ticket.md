---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- clutch/ui/app.js
- clutch/ui/dashboard.css
- clutch/mcp.py::_error
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py
- dev.py::build_ui_bundle

## Goal / Why
Fix three operator-blocking UX defects in the Antigravity ClutchWork MCP dashboard (`tickets/mcp-dashboard-repo-switch-and-errors/evidence/dashboard-ux-evidence.txt`):
1. Switching repositories or clicking Refresh while a background poll is in flight silently no-ops (`if (refreshing) return;`) and leaves the old repo's data rendered while the dropdown displays the newly selected repo for up to a minute. Switching repositories must immediately blank out the old repo's view, display a loading state, start the new repo's refresh without waiting for the stale one, and discard any stale response that resolves later.
2. Every `refresh()` awaits `clutch_app_stats` (4.56s on this checkout) even when the Stats section is collapsed by default. Stats must load lazily only when the Stats section is open (and when the user expands it or changes the stats window).
3. Tool error messages render as unstyled red text in `.notice`, drop `structuredContent.paved_road` returned by `clutch/mcp.py::_error`, have no dismiss control, and get wiped on passive background ticks.

## Boundary contract
### MCP dashboard client behavior
- disposition: extend
- owner: clutch/ui/app.js and clutch/ui/dashboard.css
- consumers: Antigravity MCP App dashboard (`ui://clutch/dashboard.html`) built by `dev.py::build_ui_bundle`
- observable change: switching repos immediately clears old view content and shows a loading notice; explicit repo switches and manual Refresh clicks supersede in-flight refreshes via a request generation token while passive interval polls still coalesce; `clutch_app_stats` runs only when the Stats section is open; error notices display `message` and `paved_road` in a styled dismissible banner
- compatibility: all existing MCP tool names, arguments, and `ui_state` persistence keys stay unchanged; passive interval polls still coalesce duplicate in-flight snapshot requests
- acceptance: node harness tests prove immediate blanking + stale-response discard on repo switch, non-blocking manual refresh, lazy stats loading, and styled dismissible error banner with `paved_road`
- tests: `tests/mcp_app_dashboard_switch_errors.js`, `tests/integration/test_mcp_app_dashboard.py`, updated `tests/mcp_app_dashboard.js`, and carried reproducer `tests/regress_mcp_dashboard_switch_errors.py`
- post-merge source of truth: clutch/ui/app.js and clutch/ui/dashboard.css

## Scope in / Scope out
In scope:
- In `clutch/ui/app.js`:
  - Track refresh requests with a monotonic generation counter (`refreshGen`) and distinguish passive polls (`poll: true`, which coalesce when a refresh is already in flight) from explicit refreshes (`force: true` on repo switch, manual Refresh click, `ontoolinput`, and post-mutation refreshes).
  - Discard stale responses whenever the request generation no longer matches `refreshGen` so an in-flight snapshot from a previous repo never overwrites a newly selected repo.
  - Add a helper that immediately blanks the old repo's rendered sections (`ticketsHeader`, `ticketsList`, `detail`, `actions`, `steps`, `boxHeader`, `boxList`, `boxActions`, `stats`, `help`), resets `snap` and `focus`, and displays a visible loading notice (`Loading <repo>...`) when switching repositories (via `repoSelect`, `repoButton`, or `ontoolinput` changing `explicitRepo`).
  - Lazy-load `clutch_app_stats`: call `loadStats()` during `refresh()` only when `sections.stats.open` is `true`, and trigger `loadStats()` when `sections.stats` toggles open or when `windowSelect`/`statsInput` changes while open (guarded by generation/stale check).
  - In `callTool()`, attach `error.pavedRoad = result.structuredContent?.paved_road` on tool errors.
  - Render `.notice` as a sticky, high-visibility `role="alert"` notification banner (`notice.hidden = true` when empty) pinned at the top of `#dashboard` (`position: sticky; top: 0; z-index: 20`) with a warning icon, bold heading/code, full error message, `pavedRoad` remedy line when present, and an explicit Dismiss button; do not clear an explicit error banner on passive background polls — clear it only on Dismiss click, repo switch, or a new explicit user action/refresh.
- In `clutch/ui/dashboard.css`:
  - Style `.notice` as a high-contrast sticky alert banner (`position: sticky; top: 0; z-index: 20`, tinted danger background, strong left accent border, padding, border-radius, word-wrap, flex layout with dismiss button) so errors cannot be overlooked or scrolled away, and distinct `.notice-loading` styling for loading state.
- In `tests/mcp_app_dashboard.js`:
  - Update the single stats-on-boot assertion (line 70) so it opens `section('stats')` before asserting `clutch_app_stats` was called, while keeping every other existing assertion intact.
- Add `tests/mcp_app_dashboard_switch_errors.js` covering repo-switch blanking + stale-response discard, manual Refresh preempting a stuck poll, lazy stats loading, and error banner `paved_road` + dismiss behavior.
- Update `tests/integration/test_mcp_app_dashboard.py` to run `tests/mcp_app_dashboard_switch_errors.js` against the built bundle in addition to `tests/mcp_app_dashboard.js`.
- Add `tests/regress_mcp_dashboard_switch_errors.py` speaking the `regression_result` JSON protocol.

Out of scope:
- Changing Python MCP tool signatures in `clutch/mcp.py` or snapshot payload shape in `clutch/observe.py`.
- Changing `vscode-clutchwork/` files.
- Committing the gitignored build output `clutch/ui/dashboard.html`.

## Scope fence
- clutch/ui/app.js
- clutch/ui/dashboard.css
- tests/mcp_app_dashboard.js
- tests/mcp_app_dashboard_switch_errors.js
- tests/integration/test_mcp_app_dashboard.py
- tests/regress_mcp_dashboard_switch_errors.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_mcp_app_dashboard.py` passes `tests/mcp_app_dashboard_switch_errors.js`, proving that switching `repoSelect` while an earlier `clutch_app_snapshot` promise is still pending: (a) immediately clears the old repo's tickets/steps/details/box DOM text and shows a loading notice rather than leaving old repo rows visible; (b) issues a new `clutch_app_snapshot` for the newly selected repo rather than dropping the switch; and (c) discards the earlier repo's response when it resolves later so the newly selected repo stays rendered.
2. `./dev.py test tests/integration/test_mcp_app_dashboard.py` proves that clicking the manual Refresh button while a background poll is in flight issues a fresh `clutch_app_snapshot` (not silently dropped), while two back-to-back background interval ticks still coalesce to one snapshot call.
3. `./dev.py test tests/integration/test_mcp_app_dashboard.py` proves that `clutch_app_stats` is not called on initial boot when `sections.stats.open` is `false` (ruling out eager 4.6s stats fetches on collapsed sections) and is called once `sections.stats` toggles open.
4. `./dev.py test tests/integration/test_mcp_app_dashboard.py` proves that a tool error returning `{code, message, paved_road}` renders a `role="alert"` `.notice` banner styled with `position: sticky` in `clutch/ui/dashboard.css` displaying the warning icon, `message`, `paved_road`, and a Dismiss button, that a subsequent passive background poll does not clear the error banner, and that clicking Dismiss hides `.notice` (ruling out a bare easily overlooked red line that vanishes on the next poll).
5. `uv run python tests/regress_mcp_dashboard_switch_errors.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `{"regression_result": "defect"}` with non-zero exit on merge base.

## Verification
```
./dev.py test tests/integration/test_mcp_app_dashboard.py
```

## Definition of rejected
- Any change that breaks background poll coalescing in `tests/mcp_app_dashboard.js`.
- Any repo-switch path that leaves the previous repo's tickets, steps, or box items visible while loading the new repo, or allows a stale response to overwrite the newly selected repo.
- Any edit to files outside `## Scope fence`.

## Time budget
- expected: 15m
- stuck: 30m

## Regression
```
uv run python tests/regress_mcp_dashboard_switch_errors.py
```
- carries: tests/regress_mcp_dashboard_switch_errors.py
- carries: tests/mcp_app_dashboard_switch_errors.js
