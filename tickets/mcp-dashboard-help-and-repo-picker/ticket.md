---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- mcp-dashboard-settings-and-layout

## Context
- clutch/mcp.py
- clutch/help.py::help_pick
- clutch/observe.py::help_payload
- clutch/observe.py::snapshot
- clutch/ui/app.js
- clutch/ui/dashboard.css
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py
- tests/unit/test_mcp_repo_resolution.py

## Goal / Why
Make the MCP App dashboard's Help & Lifecycle section readable, give operators a 1-click repository picker in the top bar, and bound default `.section-body` heights with selection-free resizer dragging. Today, Help & Lifecycle dumps raw `Object.entries(snap.help)` internal dotted keys (`box.bug_report:`, `command.clutch.askDrainLoop:`, ...) with VS Code-only extension buttons and appends the Ticket Lifecycle SVG at the bottom; switching repositories requires clicking a hidden-state folder icon and typing the full checkout path every time; and `.section-body` has no default height cap, so sections with hundreds of Suggestion Box or merged ticket rows expand to thousands of pixels, pushing `.section-resizer` off-screen, while dragging a resizer highlights adjacent text.

## Boundary contract

### MCP dashboard UI state tool
- disposition: extend
- owner: clutch/mcp.py
- consumers: `clutch/ui/app.js` (MCP App iframe) and `clutch/mcp.py::ClutchMCPServer`
- observable change: `clutch_app_ui_state` `get` includes `recentRepos: list[str]` (up to 10 existing ClutchWork checkouts containing `tickets/`, deduplicated with most-recently-used first, defaulting to `[]` when missing/unreadable/corrupt, and pruning any stored entry that is no longer a directory containing `tickets/`). Every successful `ClutchMCPServer.checkout()` updates `recentRepos` in `ui_state_path` by moving `str(root.resolve())` to index 0, deduplicating, pruning non-existent or non-checkout paths, capping at 10, preserving all other persisted UI state fields, and swallowing `OSError`. Calling `clutch_app_ui_state` `set` preserves the persisted `recentRepos` list without overwriting or dropping it.
- compatibility: additive `recentRepos` field on `clutch_app_ui_state` `get`; existing UI state keys (`order`, `open`, `heights`, `refreshSeconds`, `statsWindow`, `playAction`, `saved`) and `last_repo_path` behavior are preserved.
- acceptance: MRU ordering, deduplication, pruning of missing/non-checkout paths, cap at 10, preservation across `clutch_app_ui_state` `set` calls, `OSError` swallowing, and `ui_state_path` isolation are verified by `tests/unit/test_mcp_recent_repos.py` and `tests/unit/test_mcp_ui_state_and_config.py`.
- tests: `tests/unit/test_mcp_recent_repos.py`, `tests/unit/test_mcp_ui_state_and_config.py`
- post-merge source of truth: clutch/mcp.py

### MCP dashboard Help & Lifecycle, top-bar repo picker, and bounded section resizing
- disposition: extend
- owner: clutch/ui/app.js
- consumers: Antigravity MCP App host rendering `ui://clutch/dashboard.html` and `tests/mcp_app_dashboard.js`
- observable change: Help & Lifecycle renders the cloned Ticket Lifecycle SVG (`body > div[hidden] svg`) first inside a `.lifecycle-diagram` wrapper, followed by categorized human-readable topics built from `snap.helpPick` rather than `Object.entries(snap.help)`: separator entries (`item.kind === "separator"`) render `.help-group-heading` headings (omitting headings whose group has no rendered rows); topic entries (`item.topic`) skip VS Code-only entries (`item.command` set, or `item.topic` starting with `"view."` or `"command."`, or `snap.help[item.topic]?.link?.label === "VS Code extension"`) and render `.help-row` rows showing `item.label`, description (`snap.help[item.topic]?.what` falling back to `item.detail` or `item.description`), and a link opening `snap.help[item.topic]?.link` (`button` via `openFile` for `link.path`, `<a target="_blank">` for `link.url`). The top bar replaces the folder toggle button with a visible compact `<select class="repo-select">` populated from `recentRepos` (plus `snap.root` if not yet listed) showing each repo's basename with full path in `title`, plus an `Other path...` option (`value="__other__"`) that reveals `.repo-switcher`; selecting a repo sets `explicitRepo`, hides `.repo-switcher`, and calls `refresh()`. In `clutch/ui/dashboard.css`, `.section-body` receives bounded default heights (`height: 200px; overflow: auto;` with per-section defaults `[data-section="tickets"] > .section-body { height: 280px; }`, `[data-section="details"] > .section-body { height: 180px; }`, `[data-section="steps"] > .section-body { height: 160px; }`) that inline `body.style.height` from `ui_state.heights` still overrides, and `.section-resizer` sets `height: 6px; cursor: ns-resize; user-select: none; touch-action: none;`; on `pointerdown`, the resizer sets `document.body.style.userSelect = "none"`, calls `resizer.setPointerCapture?.(e.pointerId)`, and restores `document.body.style.userSelect` on `pointerup`.
- compatibility: preserves all existing dashboard sections, Settings, Stats, Recent Steps, Suggestion Box, Tickets, and Details interactions, user-resized heights persisted in `ui_state.heights`, and manual path entry via `.repo-switcher` when `Other path...` is selected or when no checkout is active.
- acceptance: verified end-to-end against the built single-file bundle by `tests/integration/test_mcp_app_dashboard.py` and `tests/mcp_app_dashboard.js`.
- tests: `tests/mcp_app_dashboard.js`, `tests/integration/test_mcp_app_dashboard.py`
- post-merge source of truth: clutch/ui/app.js

## Scope in / Scope out

### Scope in
- `clutch/mcp.py`:
  - Add a helper to normalize and prune `recentRepos`: accept only string paths whose `Path(p)` is an existing directory containing a `tickets/` directory, resolve each path, deduplicate preserving first-seen (MRU) order, and cap at 10 entries.
  - Extend `clutch_app_ui_state` `get` to include `"recentRepos"` (pruned list from `ui_state_path`, defaulting to `[]` when missing, unreadable, corrupt, or non-list).
  - Ensure `clutch_app_ui_state` `set` preserves the persisted `recentRepos` list in `ui_state_path` so saving layout or UI preferences does not erase recent repositories.
  - Update `ClutchMCPServer.checkout()` so every successful checkout records `str(root.resolve())` at index 0 of `recentRepos` in `self.ui_state_path` (reading existing JSON if present, preserving other UI state keys, deduplicating, pruning missing/non-checkout paths, capping at 10, creating parent directories, and swallowing `OSError`).
- `clutch/ui/app.js`:
  - Help & Lifecycle section:
    - Render the cloned Ticket Lifecycle SVG (`document.querySelector("body > div[hidden] svg")`) at the top of the `help` container inside `<div class="lifecycle-diagram">`.
    - Replace the `Object.entries(snap.help)` dump with categorized rendering from `snap.helpPick || []` (`snap.helpPick` is already emitted by merged code in `clutch/observe.py::snapshot`).
    - Group items by separator entries (`item.kind === "separator"`). Skip entries that have `item.command` (VS Code-only commands such as `clutch.openSettings`), entries whose `item.topic` starts with `"view."` or `"command."`, and entries whose `snap.help?.[item.topic]?.link?.label === "VS Code extension"`. Omit any separator heading whose group has zero remaining topic items.
    - Render each non-empty group's heading as `.help-group-heading` and each topic entry as `.help-row` containing `.help-label` (`item.label`), `.help-desc` (`snap.help?.[item.topic]?.what || item.detail || item.description || ""`), and the documentation link from `snap.help?.[item.topic]?.link` (button calling `openFile(link.path)` when `link?.path`, or `<a target="_blank" href=link.url>` when `link?.url`).
  - Top-bar 1-click repository picker:
    - Track `recentRepos` initialized from `clutch_app_ui_state({ action: "get" })` on boot and updated in memory on successful `refresh()` (prepending `snap.root`, deduplicating, capping at 10) so the dropdown stays current without an extra RPC.
    - Replace the top-bar folder toggle button (`Switch repository: ...`) with a visible `<select class="repo-select" aria-label="Switch repository">` in `.top-bar`.
    - Populate `.repo-select` with one `<option>` per path in `recentRepos` (including `snap.root` if not yet listed): `option.value = path`, `option.textContent = basename` (`path.replace(/\/+$/, "").split("/").pop() || path`), `option.title = path`, followed by `<option value="__other__">Other path...</option>`. Set `repoSelect.value` to the active repo (`explicitRepo || snap?.root || ""`) when present and `repoSelect.title` to the active path.
    - On `.repo-select` `change`: if value is `"__other__"`, set `repoOpen = true` and reveal `.repo-switcher` (`repoSwitcher.hidden = false`); otherwise set `explicitRepo = repoSelect.value`, `repoOpen = false`, `repoSwitcher.hidden = true`, and call `refresh()`.
    - When `repoButton` ("Load repository") submits a manual path, set `repoOpen = false` before calling `refresh()` so `.repo-switcher` hides after loading.
  - Resizer drag text-selection prevention:
    - In the `.section-resizer` `pointerdown` handler, save the previous `document.body.style.userSelect`, set `document.body.style.userSelect = "none"`, call `resizer.setPointerCapture?.(e.pointerId)`, and restore `document.body.style.userSelect` (to the saved value, e.g. `""`) inside the `pointerup` handler.
- `clutch/ui/dashboard.css`:
  - Give `.section-body` a bounded default height (`height: 200px; overflow: auto; min-height: 60px;`) plus per-section defaults `[data-section="tickets"] > .section-body { height: 280px; }`, `[data-section="details"] > .section-body { height: 180px; }`, and `[data-section="steps"] > .section-body { height: 160px; }` so large sections scroll internally and keep `.section-resizer` reachable while inline `body.style.height` from `ui_state.heights` overrides the default.
  - Update `.section-resizer` to `height: 6px; cursor: ns-resize; user-select: none; touch-action: none;`.
  - Add `.lifecycle-diagram` styling with `.lifecycle-diagram svg { width: 100%; height: auto; display: block; }`.
  - Add layout styling for `.help-group-heading`, `.help-row`, `.help-label`, `.help-desc`, and compact `.repo-select` sizing in `.top-bar`.
- Tests:
  - Create `tests/unit/test_mcp_recent_repos.py` verifying `recentRepos` MRU ordering, deduplication when revisiting an earlier repo, pruning of deleted or non-checkout directories, cap at 10 entries, preservation across `clutch_app_ui_state` `set` calls, `OSError` swallowing, and `ui_state_path` isolation under `tmp_path`.
  - Update `tests/unit/test_mcp_ui_state_and_config.py` only if an existing exact-dict assertion on `clutch_app_ui_state` `get` defaults needs `"recentRepos": []` added.
  - Update `tests/mcp_app_dashboard.js` and `tests/integration/test_mcp_app_dashboard.py` (giving the mock `snap` fixture in `tests/mcp_app_dashboard.js` a `helpPick` list covering separators, topic entries, and VS Code-only command entries) to assert:
    - Lifecycle SVG renders as the first child of Help & Lifecycle inside `.lifecycle-diagram`, and `clutch/ui/dashboard.css` defines `.lifecycle-diagram svg` with `width: 100%`, `height: auto`, and `display: block`.
    - Raw dotted `snap.help` keys (such as `box.bug_report:` or `command.clutch.askDrainLoop:`) and `VS Code extension` buttons are not rendered in Help & Lifecycle.
    - Categorized `snap.helpPick` `.help-group-heading` headings and human-readable `.help-row` topic rows (label, description, and path/URL links) render, while VS Code-only `item.command` and `command.*`/`view.*` entries and their empty headings are omitted.
    - `.repo-select` renders in `.top-bar` with options for `recentRepos` (basename text, full path in `title`) plus `Other path...` (`value="__other__"`), selecting a repo sets `repo` on the subsequent `clutch_app_snapshot` call and hides `.repo-switcher`, and selecting `__other__` reveals `.repo-switcher`.
    - `clutch/ui/dashboard.css` defines bounded default `.section-body` height (`height: 200px`), per-section default heights for `tickets` (`280px`), `details` (`180px`), and `steps` (`160px`), and `.section-resizer` rules with `cursor: ns-resize`, `user-select: none`, and `touch-action: none`; and in the JS harness, dispatching `pointerdown` on `.section-resizer` sets `document.body.style.userSelect` to `"none"` and dispatching `pointerup` clears/restores it.

### Scope out
- Changes to `vscode-clutchwork/` (VS Code extension).
- Modifying `clutch/help.py` or `clutch/observe.py` snapshot schemas.
- Changing `last_repo_path` resolution precedence or adding new MCP tools.
- Editing any of the 7 hot integration test files.

## Scope fence
- clutch/mcp.py
- clutch/ui/app.js
- clutch/ui/dashboard.css
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py
- tests/unit/test_mcp_recent_repos.py
- tests/unit/test_mcp_ui_state_and_config.py

## Acceptance criteria
1. Every successful `ClutchMCPServer.checkout()` records `str(root.resolve())` at index 0 of `recentRepos` in `ui_state_path` (deduplicated, MRU-ordered, capped at 10, pruning paths whose directory or `tickets/` subdirectory no longer exists, preserving other UI state keys, and swallowing `OSError`), `clutch_app_ui_state` `get` returns `recentRepos` (`[]` on missing/corrupt file, not omitting the key or raising), `clutch_app_ui_state` `set` preserves `recentRepos` (not wiping it to `[]`), and unit tests isolate state under `tmp_path`; verified by `./dev.py test tests/unit/test_mcp_recent_repos.py tests/unit/test_mcp_ui_state_and_config.py`.
2. In the built MCP dashboard bundle, Help & Lifecycle renders the Ticket Lifecycle SVG inside `.lifecycle-diagram` as the first element of the help container (not appended at the bottom after help entries), and `clutch/ui/dashboard.css` styles `.lifecycle-diagram svg` with `width: 100%`, `height: auto`, and `display: block`; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
3. Help & Lifecycle renders categorized `.help-group-heading` headings and `.help-row` entries from `snap.helpPick` showing `item.label`, human-readable description (`snap.help[item.topic].what` or `item.detail`/`item.description`), and working path/URL links, while omitting raw dotted `snap.help` keys (`box.bug_report:`, `command.clutch.askDrainLoop:`), `VS Code extension` buttons, `item.command` entries, and empty `view`/`command` group headings; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
4. `.top-bar` renders a visible `<select class="repo-select">` populated from `recentRepos` (plus `snap.root` if absent) displaying each repo's basename with full path in `title`, plus `Other path...` (`value="__other__"`), rather than the hidden-only folder toggle button; selecting a repo triggers `refresh()` with `repo` set to that path and keeps `.repo-switcher` hidden, while selecting `__other__` reveals `.repo-switcher`; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
5. `clutch/ui/dashboard.css` bounds `.section-body` with a default `height: 200px` (`overflow: auto`, not unbounded auto height) plus per-section defaults (`tickets: 280px`, `details: 180px`, `steps: 160px`), styles `.section-resizer` with `cursor: ns-resize`, `user-select: none`, and `touch-action: none`, and dragging `.section-resizer` sets `document.body.style.userSelect = "none"` on `pointerdown` (not leaving text selectable during drag) and restores it on `pointerup`; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.

## Verification
```
./dev.py test tests/unit/test_mcp_recent_repos.py tests/unit/test_mcp_ui_state_and_config.py tests/unit/test_mcp_repo_resolution.py tests/integration/test_mcp_app_dashboard.py
```

## Definition of rejected
- Any unit test reads or writes `~/.config/clutch/dashboard-state.json` instead of an isolated `tmp_path` file.
- `clutch_app_ui_state` `set` overwrites or drops `recentRepos`, or `recentRepos` retains non-existent paths or exceeds 10 entries.
- Help & Lifecycle renders raw dotted `snap.help` keys (e.g. `box.bug_report:`, `command.clutch.`), `VS Code extension` buttons, or places the lifecycle SVG below the help list.
- Switching repos via `.repo-select` fails to pass the selected repo to `clutch_app_snapshot` or fails to reveal `.repo-switcher` when `Other path...` is selected.
- `.section-body` remains unbounded by default, or dragging `.section-resizer` leaves `document.body.style.userSelect` unset during drag or stuck at `"none"` after `pointerup`.
- Any of the 7 hot integration test files is modified.

## Time budget
- expected: 15m
- stuck: 30m
- reason: `recentRepos` persistence in `clutch/mcp.py` and the Help & Lifecycle, `.repo-select`, and bounded section resizing updates in `clutch/ui/app.js` and `clutch/ui/dashboard.css` share the `clutch_app_ui_state` contract and are verified together against the built bundle in `tests/integration/test_mcp_app_dashboard.py`
