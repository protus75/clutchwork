---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/ui/app.js
- clutch/ui/dashboard.css
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/media/graph.js
- vscode-clutchwork/media/view.css
- vscode-clutchwork/extension.js
- clutch/mcp.py::Stats
- clutch/mcp.py::ClutchMCPServer.call_tool
- clutch/stats.py::stats_tree
- clutch/observe.py::STEP_KINDS
- tests/integration/test_step_icons.py
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py
- tests/unit/test_dev_ui_bundle.py
- tests/unit/test_mcp_app_dashboard.py

## Goal / Why
Bring the Antigravity MCP App dashboard (`clutch/ui/app.js` and `clutch/ui/dashboard.css`) to full UI/UX parity with `vscode-clutchwork` while strictly preserving ClutchWork's thin-wrapper boundary (JavaScript renders snapshot and stats-tree fields, maps closed snapshot values to CSS variables or inline SVG icons via lookup tables, holds only UI state, and invokes MCP tools without deriving rows, sorting, filtering, parsing text, or inventing policy).

Today the MCP App dashboard uses 6 mutually-exclusive tabs (`<nav class="tabs">`), dumps raw `JSON.stringify` into a `<pre>` for Stats, leaves the `Repository path` input permanently expanded at the top, renders Recent Steps as wrapping inline buttons without stems or icons, lacks right-click context menus on ticket and Suggestion Box rows, places a stray `config.yaml` button and 6 unconditional artifact buttons inside Details, and leaves `vscode-clutchwork/media/view.css`'s `--vscode-*` variables undefined in Antigravity so graph lanes, badges, and row colors fall back unevenly. Replacing that layout with VS Code-style stacked collapsible `<details>` sidebar sections, full-width Recent Steps rows with semantic SVG icons and stems, mapped `--vscode-*` theme tokens for dark and light themes, cursor-anchored right-click context menus driven by `row.menu`, formatted `stats_tree` rows, a collapsed-by-default repo switcher, and a compact top header bar makes the Antigravity dashboard match `vscode-clutchwork` visually and ergonomically.

## Boundary contract
### MCP App Dashboard UI
- disposition: extend
- owner: clutch/ui/app.js
- consumers: dev.py::build_ui_bundle, clutch/mcp.py (ui://clutch/dashboard.html), tests/mcp_app_dashboard.js, tests/integration/test_mcp_app_dashboard.py
- observable change: `createDashboardApp(options)` renders a compact top header bar with inline SVG action icons (Engine status, Start/Stop, Refresh, Open config.yaml, collapsible Repo switcher, and collapsible Agent Actions drawer), stacked collapsible `<details>` sidebar sections (`data-section` in `tickets|details|steps|box|stats|help`) instead of mutually-exclusive tabs, full-width single-line Recent Steps rows with `STEP_KINDS` inline SVG icons + stem + text + right-aligned `timeDisplay`, cursor-anchored floating `.context-menu` popups on right-click of ticket and Suggestion Box rows driven by `row.menu` / `row.priorityChoices` / `row.runsBeforeChoices`, formatted `.stats-list` / `.stats-row` metric rows fetched via `clutch_app_stats` with `{ window, tree: true }` (returning `{ window, tree }` per `clutch/mcp.py::Stats` and `clutch/mcp.py::ClutchMCPServer.call_tool`), and all 16 `--vscode-*` CSS custom properties referenced by `vscode-clutchwork/media/view.css` defined in `clutch/ui/dashboard.css`.
- compatibility: `createDashboardApp(options)` preserves its export signature, host capability gating, theme/style variable binding, `toggle-aux-pane` file opening, `updateModelContext` selection updates, and all existing MCP tool names and argument shapes (`clutch_app_stats` already accepts `tree: bool = False` in `clutch/mcp.py::Stats` and returns `{"window": args.window, "tree": stats.stats_tree(result)}`).
- acceptance: `tests/mcp_app_dashboard.js` run through `./dev.py test tests/integration/test_mcp_app_dashboard.py` verifies simultaneous visibility of stacked `<details>` sections, Recent Steps row structure and full `STEP_KINDS` icon coverage, complete `--vscode-*` variable definitions in `clutch/ui/dashboard.css`, header action icons, context menu gating/actions/dismissal, formatted stats tree rendering, collapsed repo switcher, and header placement of `Open config.yaml`.
- tests: tests/mcp_app_dashboard.js and tests/integration/test_mcp_app_dashboard.py
- post-merge source of truth: clutch/ui/app.js and clutch/ui/dashboard.css

## Scope in / Scope out
**Scope in:**
- `clutch/ui/app.js`:
  - Replace the 6 mutually-exclusive `<nav class="tabs">` / hidden `<section>` panels with vertically stacked collapsible `<details>` sections in a single scrollable sidebar. Use a deterministic markup contract: each `<details>` sets `data-section` (`"tickets"`, `"details"`, `"steps"`, `"box"`, `"stats"`, `"help"`) and its `<summary>` contains `<span class="section-title">` holding the exact section name (`"Tickets"`, `"Details"`, `"Recent Steps"`, `"Suggestion Box"`, `"Stats"`, `"Help & Lifecycle"`) plus a separate `<span class="section-count">` for optional item counts:
    - **Tickets** (`data-section="tickets"`, `open = true` by default): `ticketsHeader`, `ticketsList` (rendered by `createTicketsView`).
    - **Details** (`data-section="details"`, `open = true` by default): live `detailView` (which renders the selected ticket or box item and its snapshot-provided `Open ticket.md` / `Open message file` / `Open ticket/record` links via `vscode-clutchwork/media/detail.js`) plus compact inline action controls strictly gated by `row.menu` (`Confirm`, `Reject`, priority selector + `Set priority`, runs-before multi-select + `Set runs before`) for keyboard/touch accessibility. Remove the stray `config.yaml` button and the 6 unconditional raw artifact buttons (`ticket.md`, `run.md`, `checks.json`, `review.md`, `diagnosis.json`, `rework.md`) from Details.
    - **Recent Steps** (`data-section="steps"`, `open = true` by default): render each step as its own **full-width single-line flex row** (`.step-row`, `display: flex; width: 100%`, never inline wrapping buttons) matching `vscode-clutchwork/extension.js` `StepsTree`: `[colored 14x14 inline SVG icon for step.kind] [step.stem when present] [step.text] [step.timeDisplay right-aligned]`, with `title = step.tooltip` and click handler opening `step.path` when present. Map every key in `clutch.observe.STEP_KINDS` via an inline SVG lookup table with semantic colors (`*_ok` green, `*_failed` red, `engine_lost` amber/warning, `*_start` / `engine_start` / `engine_stop` neutral/accent); unknown `step.kind` renders a warning SVG icon and `cannot draw the clutch snapshot: unknown step kind ${step.kind}`.
    - **Suggestion Box** (`data-section="box"`, `open = false` by default unless `snap.boxCounts.pending > 0` on initial load, preserving user toggle afterward): `boxHeader`, `boxList` (rendered by `createBoxView`), and inline `Triage` / `Dismiss` buttons when rows are selected and all selected rows have `clutchTriage === "on"` / `clutchDismiss === "on"`.
    - **Stats** (`data-section="stats"`, `open = false` by default): window selector (`24h`, `7d`, `30d`, `20t`, default `7d`) + formatted metric tree rendered from `callTool("clutch_app_stats", { window: windowSelect.value, tree: true })` iterating `result.tree` (`label`, `description`, `tooltip`, recursive `children` as nested `<details>` or `.stats-row` divs with `.stats-label` and `.stats-desc` — no `<pre>` / `JSON.stringify` dump).
    - **Help & Lifecycle** (`data-section="help"`, `open = false` by default): help entries with clickable file/URL links + cloned embedded `ticket-lifecycle.svg`.
  - Render a compact top header bar modeled on `vscode-clutchwork`'s sidebar title bar, with crisp 14x14/16x16 inline SVG icons on action buttons:
    - Engine status indicator (`Engine: running` / `Engine: stopped`), `Start drain` and `Start serve` buttons (play SVG icon) when stopped, `Stop` button (stop SVG icon) when running, `Refresh` button (refresh SVG icon), and `Open config.yaml` button (gear/file SVG icon, calling `openFile(snap.configPath)` when `snap?.configPath` is present).
    - Compact Repo switcher toggle button (folder/repo SVG icon) showing the active repo name/path; wrap the `Repository path` `<input>` and `Load repository` `<button>` in a `.repo-switcher` container whose `hidden` property is `true` whenever a repo is loaded (`snap?.root` is truthy and not toggled open) and `false` when toggled open or when no repo is loaded yet.
    - Compact collapsible **Agent Actions** menu/drawer (omitted when `!app.getHostCapabilities()?.message`) containing `Supervise Drain Loop`, `Run Roadmap (Drain)`, `Run Roadmap (Serve)`, `Diagnose Stem`, `Review Drafts`, and the `New conversation` checkbox toggle.
  - Add a floating right-click `.context-menu` positioned at cursor coordinates (`clientX`/`clientY`) and dismissed on outside click, `Escape` keydown, or action click:
    - For BOTH `createTicketsView` and `createBoxView`, `onRowContext` stores the latest row metadata in a `WeakMap` keyed by the row DOM node and attaches a `contextmenu` listener to that row node at most once (guarded by the `WeakMap`).
    - Ticket row `contextmenu`: calls `e.preventDefault()`, reads the latest row entry from the `WeakMap`, lazily calls `ticketsView.setPinned(entry.row.stem)` inside the event handler (after `createTicketsView` has returned), and renders menu items strictly from `row.menu`, `row.priorityChoices`, and `row.runsBeforeChoices`: `Confirm` (`clutchConfirm === "on"` -> `clutch_app_ticket_confirm`), `Reject` (`clutchReject === "on"` -> `clutch_app_ticket_reject`), priority choices from `row.priorityChoices` (`clutchPriority === "on"` -> `clutch_ticket_order`), `Runs before...` choices/submenu from `row.runsBeforeChoices` (`clutchRunsBefore === "on"` -> `clutch_ticket_order`), `Open ticket.md` (`openFile(row.path)`), `Open run.md`, `Open review.md`, `Open diagnosis.json`, and `Diagnose Stem` (when `app.getHostCapabilities()?.message` and `row.menu.clutchAskDiagnose === "on"`).
    - Suggestion Box row `contextmenu`: calls `e.preventDefault()`, reads the latest `{ row, ids }` entry stored by `onRowContext(node, row, ids)` (using the `ids` passed as the third argument by `box.js`), and renders `Triage` (when all target rows for `ids` have `menu.clutchTriage === "on"` -> `clutch_box_triage`), `Dismiss` (when all target rows for `ids` have `menu.clutchDismiss === "on"` -> `clutch_box_dismiss`), `Open message file` (`openFile(row.path)` when `row.path`), and `Open ticket/record` (`openFile(row.link)` when `row.link`).
- `clutch/ui/dashboard.css`:
  - Define every `--vscode-[A-Za-z0-9-]+` custom property referenced by `vscode-clutchwork/media/view.css` (all 16 exact tokens: `--vscode-clutchwork-blocked`, `--vscode-clutchwork-merged`, `--vscode-clutchwork-queued`, `--vscode-descriptionForeground`, `--vscode-editor-background`, `--vscode-editorHoverWidget-border`, `--vscode-font-family`, `--vscode-font-size`, `--vscode-foreground`, `--vscode-list-hoverBackground`, `--vscode-list-inactiveSelectionBackground`, `--vscode-scmGraph-historyItemBaseRefColor`, `--vscode-scmGraph-historyItemRefColor`, `--vscode-scmGraph-historyItemRemoteRefColor`, `--vscode-sideBar-background`, `--vscode-textLink-foreground`) plus semantic icon color variables (`--clutch-icon-passed`, `--clutch-icon-failed`, `--clutch-icon-warning`, `--clutch-icon-muted`) on `:root` with dark and light theme rules (`[data-theme="dark"]` / `[data-theme="light"]`) mapped to Antigravity `--color-*` host variables with crisp semantic fallbacks so graph lanes, status pills, badges, hover/selection rows, and step icons render in full color.
  - Style the compact sidebar layout, collapsible `<details>` section headers (uppercase compact headings, subtle border-bottom, item counts), `.step-row` full-width single-line flex layout (`display: flex; width: 100%`, right-aligned `.step-time`, `.step-stem`, `.step-text`, `.step-icon`), top header bar, collapsible `.repo-switcher`, floating `.context-menu` and submenu using Antigravity CSS variables (`--color-background-*`, `--color-text-*`, `--color-border-*`, `--font-sans`), compact buttons/selects, and `.stats-list` / `.stats-row` formatting.
- `tests/integration/test_mcp_app_dashboard.py`:
  - Import `STEP_KINDS` from `clutch.observe` and pass `json.dumps(list(STEP_KINDS))` as `argv[3]` when invoking `node tests/mcp_app_dashboard.js <bundle_path> <step_kinds_json>` so the JS harness verifies every canonical step kind from Python without copying the vocabulary.
- `tests/mcp_app_dashboard.js`:
  - Extend the fake DOM `Node` to support multiple listeners per event type, parent tracking / `contains()`, `<details>` `open` boolean state, and `hidden` boolean state so `box.js` + `app.js` `contextmenu` handlers, outside clicks, `Escape` dismissal, `<details>` open/closed state, and `.repo-switcher` `hidden` state are exercised deterministically.
  - Locate `vscode-clutchwork/media/view.css` and `clutch/ui/dashboard.css` via `path.resolve(__dirname, "..")`, extract all `--vscode-[A-Za-z0-9-]+` tokens from `view.css`, and assert every extracted token is defined in `dashboard.css`.
  - Parse `STEP_KINDS` from `process.argv[3]` and assert every key in `STEP_KINDS` renders a dedicated `.step-row` with an inline `<svg>` icon (and does not emit `"unknown step kind"`), while an unknown step kind renders a warning `<svg>` and `"cannot draw the clutch snapshot: unknown step kind <kind>"`.
  - Update existing harness assertions for the stacked `<details>` layout, `clutch_app_stats` `{ window, tree: true }` tree payload, top-bar `Open config.yaml`, removal of unconditional Details artifact buttons, header action SVG icons, right-click context menus, formatted stats tree, and collapsed repo switcher.

**Scope out:**
- Do not modify `vscode-clutchwork/`, `clutch/mcp.py`, `clutch/observe.py`, `clutch/stats.py`, or `dev.py`.
- Do not commit the gitignored `clutch/ui/dashboard.html` bundle output.

## Scope fence
- clutch/ui/app.js
- clutch/ui/dashboard.css
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py

## Acceptance criteria
1. Stacked collapsible sidebar sections replace tabs: `./dev.py test tests/integration/test_mcp_app_dashboard.py` passes with assertions in `tests/mcp_app_dashboard.js` confirming that no `<nav class="tabs">` exists, that `<details>` sections with `data-section` `"tickets"`, `"details"`, and `"steps"` all have `open === true` simultaneously on initial render with matching `.section-title` labels (`Tickets`, `Details`, `Recent Steps`) without clicking any tab, and that `<details>` sections with `data-section` `"stats"` and `"help"` start with `open === false` (ruling out mutually-exclusive hidden panels).
2. Recent Steps full-width rows, stems, and full `STEP_KINDS` SVG icon coverage: `tests/integration/test_mcp_app_dashboard.py` passes `list(clutch.observe.STEP_KINDS)` as `argv[3]` to `tests/mcp_app_dashboard.js`, which asserts that every key in `STEP_KINDS` renders a dedicated `.step-row` containing an inline `<svg>` icon, `step.stem` (when present), `step.text`, and `step.timeDisplay` without producing `"unknown step kind"`, that an unknown `step.kind` renders a warning `<svg>` icon and `"cannot draw the clutch snapshot: unknown step kind <kind>"`, and that `clutch/ui/dashboard.css` styles `.step-row` with `display: flex` and `width: 100%` (ruling out inline wrapping buttons, missing stems/icons, or unmapped `STEP_KINDS` entries).
3. Complete `--vscode-*` color variable parity and header icons: `tests/mcp_app_dashboard.js` resolves `vscode-clutchwork/media/view.css` and `clutch/ui/dashboard.css` via `path.resolve(__dirname, "..")`, extracts every `--vscode-[A-Za-z0-9-]+` token from `view.css`, and asserts every extracted token is defined in `dashboard.css` (ruling out undefined VS Code variables in Antigravity), and asserts that top-bar action buttons (`Start drain` / `Stop`, `Refresh`, `Open config.yaml`, and the Repo switcher toggle) each contain an inline `<svg>` icon.
4. Clean top bar and Details hygiene: `tests/mcp_app_dashboard.js` asserts that `Open config.yaml` is rendered in the top header bar (not inside `<details data-section="details">`) and opens `snap.configPath`, that `<details data-section="details">` does not render unconditional `run.md` / `checks.json` / `review.md` / `diagnosis.json` / `rework.md` buttons, and that the `.repo-switcher` container has `hidden === true` when a repo is loaded and `hidden === false` after clicking the repo switcher toggle (ruling out a permanently visible repo input or stray Details buttons).
5. Ticket right-click context menu: `tests/mcp_app_dashboard.js` asserts that dispatching `contextmenu` on a ticket row pins the row and opens `.context-menu` with `Confirm`, `Reject`, priority choices from `row.priorityChoices`, `Runs before` choices from `row.runsBeforeChoices`, `Open ticket.md`, `Open run.md`, `Open review.md`, `Open diagnosis.json`, and `Diagnose Stem` when enabled, invokes `clutch_app_ticket_confirm`, `clutch_app_ticket_reject`, and `clutch_ticket_order` with the expected arguments, omits disabled actions when `row.menu` flags are `"off"`, and closes on `Escape` and outside click (ruling out a missing, ungated, duplicate-listener, or stuck context menu).
6. Suggestion Box right-click context menu: `tests/mcp_app_dashboard.js` asserts that dispatching `contextmenu` on a Suggestion Box row uses the `ids` supplied by `box.js`'s `onRowContext` callback, opens `.context-menu` with `Triage`, `Dismiss`, and `Open message file`, invokes `clutch_box_triage` and `clutch_box_dismiss` with the selected IDs, and omits `Triage`/`Dismiss` when `row.menu` flags are `"off"` (ruling out missing, stale, or ungated box context actions).
7. Formatted Stats tree: `tests/mcp_app_dashboard.js` asserts that `clutch_app_stats` is called with `{ window: "7d", tree: true }`, that `<details data-section="stats">` renders formatted `.stats-row` metric nodes from `result.tree` (including nested child rows and tooltips), and that no `<pre>` JSON dump is rendered inside Stats (ruling out raw `JSON.stringify` output).
8. Bundle build and MCP dashboard tests remain green: `./dev.py test tests/integration/test_mcp_app_dashboard.py tests/unit/test_dev_ui_bundle.py tests/unit/test_mcp_app_dashboard.py` exits 0 with no regressions to theme binding, `toggle-aux-pane` file opening, `updateModelContext`, prompt launching, or inline action controls.

## Verification
```
./dev.py test tests/integration/test_mcp_app_dashboard.py tests/unit/test_dev_ui_bundle.py tests/unit/test_mcp_app_dashboard.py
```

## Definition of rejected
- Any JavaScript code in `clutch/ui/app.js` derives, sorts, filters, or parses domain data or invents menu/policy rules instead of reading snapshot and `stats_tree` fields.
- Recent Steps renders wrapping inline buttons or omits `step.stem` or any `clutch.observe.STEP_KINDS` inline SVG icon.
- Any `--vscode-[A-Za-z0-9-]+` custom property referenced in `vscode-clutchwork/media/view.css` is left undefined in `clutch/ui/dashboard.css`.
- Any stray `config.yaml` button or unconditional 6-artifact button row remains in Details, or the 6 mutually-exclusive tabs remain.
- Stats still renders a raw `JSON.stringify` `<pre>` dump instead of formatted `stats_tree` rows.
- Any file outside `## Scope fence` is modified, or `./dev.py test tests/integration/test_mcp_app_dashboard.py tests/unit/test_dev_ui_bundle.py tests/unit/test_mcp_app_dashboard.py` fails.

## Time budget
- expected: 15m
- stuck: 30m
