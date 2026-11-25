---
state: draft
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
- clutch/stats.py::stats_tree
- clutch/observe.py::STEP_KINDS
- tests/integration/test_step_icons.py
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py

## Goal / Why
Bring the Antigravity MCP App dashboard (`clutch/ui/app.js` and `clutch/ui/dashboard.css`) to full UI/UX parity with `vscode-clutchwork` while strictly preserving ClutchWork's thin-wrapper boundary (JavaScript renders snapshot and stats-tree fields, maps closed snapshot values to CSS variables or inline SVG icons via lookup tables, holds only UI state, and invokes MCP tools without deriving rows, sorting, filtering, parsing text, or inventing policy).

Today the MCP App dashboard uses 6 mutually-exclusive tabs (`<nav class="tabs">`), dumps raw `JSON.stringify` into a `<pre>` for Stats, leaves the `Repository path` input permanently expanded at the top, renders Recent Steps as wrapping inline buttons without stems or icons, lacks right-click context menus on ticket and Suggestion Box rows, places a stray `config.yaml` button and 6 unconditional artifact buttons inside Details, and leaves `vscode-clutchwork/media/view.css`'s `--vscode-*` variables undefined in Antigravity so graph lanes, badges, and row colors fall back unevenly. Replacing that layout with VS Code-style stacked collapsible `<details>` sidebar sections, full-width Recent Steps rows with semantic SVG icons and stems, mapped `--vscode-*` theme tokens for dark and light themes, cursor-anchored right-click context menus driven by `row.menu`, formatted `stats_tree` rows, a collapsed-by-default repo switcher, and a compact top header bar makes the Antigravity dashboard match `vscode-clutchwork` visually and ergonomically.

## Boundary contract
### MCP App Dashboard UI
- disposition: extend
- owner: clutch/ui/app.js
- consumers: dev.py::build_ui_bundle, clutch/mcp.py (ui://clutch/dashboard.html), tests/mcp_app_dashboard.js, tests/integration/test_mcp_app_dashboard.py
- observable change: `createDashboardApp(options)` renders a compact top header bar with inline SVG action icons (Engine status, Start/Stop, Refresh, Open config.yaml, collapsible Repo switcher, and collapsible Agent Actions drawer), stacked collapsible `<details>` sidebar sections (Tickets, Details, Recent Steps, Suggestion Box, Stats, Help & Lifecycle) instead of mutually-exclusive tabs, full-width single-line Recent Steps rows with `STEP_KINDS` inline SVG icons + stem + text + right-aligned `timeDisplay`, cursor-anchored floating `.context-menu` popups on right-click of ticket and Suggestion Box rows driven by `row.menu` / `row.priorityChoices` / `row.runsBeforeChoices`, formatted `.stats-list` / `.stats-row` metric rows fetched via `clutch_app_stats` with `{ window, tree: true }`, and full `--vscode-*` CSS variable mappings in `clutch/ui/dashboard.css`.
- compatibility: `createDashboardApp(options)` preserves its export signature, host capability gating, theme/style variable binding, `toggle-aux-pane` file opening, `updateModelContext` selection updates, and all existing MCP tool names and argument shapes (`clutch_app_stats` already accepts `tree: true` in `clutch/mcp.py`).
- acceptance: `tests/mcp_app_dashboard.js` run through `./dev.py test tests/integration/test_mcp_app_dashboard.py` verifies simultaneous visibility of stacked sections, Recent Steps row structure and icons, complete `--vscode-*` variable definitions in `clutch/ui/dashboard.css`, header action icons, context menu gating/actions/dismissal, formatted stats tree rendering, collapsed repo switcher, and header placement of `Open config.yaml`.
- tests: tests/mcp_app_dashboard.js (executed by tests/integration/test_mcp_app_dashboard.py)
- post-merge source of truth: clutch/ui/app.js and clutch/ui/dashboard.css

## Scope in / Scope out
**Scope in:**
- `clutch/ui/app.js`:
  - Replace the 6 mutually-exclusive `<nav class="tabs">` / hidden `<section>` panels with vertically stacked collapsible `<details>` sections in a single scrollable sidebar:
    - **Tickets** (`open` by default): `ticketsHeader`, `ticketsList` (rendered by `createTicketsView`).
    - **Details** (`open` by default): live `detailView` (which renders the selected ticket or box item and its snapshot-provided `Open ticket.md` / `Open message file` / `Open ticket/record` links via `vscode-clutchwork/media/detail.js`) plus compact inline action controls strictly gated by `row.menu` (`Confirm`, `Reject`, priority selector + `Set priority`, runs-before multi-select + `Set runs before`) for keyboard/touch accessibility. Remove the stray `config.yaml` button and the 6 unconditional raw artifact buttons (`ticket.md`, `run.md`, `checks.json`, `review.md`, `diagnosis.json`, `rework.md`) from Details.
    - **Recent Steps** (`open` by default): render each step as its own **full-width single-line flex row** (`.step-row`, `display: flex; width: 100%`, never inline wrapping buttons) matching `vscode-clutchwork/extension.js` `StepsTree`: `[colored 14x14 inline SVG icon for step.kind] [step.stem when present] [step.text] [step.timeDisplay right-aligned]`, with `title = step.tooltip` and click handler opening `step.path` when present. Map every `STEP_KINDS` entry (`meta_*`, `review_visual_*`, `resolve_*`, `acceptance_*`, `preflight_*`, `retro_check_*`, `requisition_review_*`, `stage_*`, `author_*`, `engine_start`, `engine_stop`, `engine_lost`, `implement_*`, `review_*`, `diagnose_*`, `rework_*`, `retro_*`, `check_*`, `merge_*`, `triage_*`) via an inline SVG lookup table with semantic colors (`*_ok` green, `*_failed` red, `engine_lost` amber/warning, `*_start` / `engine_start` / `engine_stop` neutral/accent); unknown `step.kind` renders a warning SVG icon and `cannot draw the clutch snapshot: unknown step kind ${step.kind}`.
    - **Suggestion Box** (collapsible `<details>`, starts collapsed unless `snap.boxCounts.pending > 0` on initial load, preserving user toggle afterward): `boxHeader`, `boxList` (rendered by `createBoxView`), and inline `Triage` / `Dismiss` buttons when rows are selected and all selected rows have `clutchTriage === "on"` / `clutchDismiss === "on"`.
    - **Stats** (collapsed by default): window selector (`24h`, `7d`, `30d`, `20t`, default `7d`) + formatted metric tree rendered from `callTool("clutch_app_stats", { window: windowSelect.value, tree: true })` iterating `result.tree` (`label`, `description`, `tooltip`, recursive `children` as nested `<details>` or `.stats-row` divs with `.stats-label` and `.stats-desc` — no `<pre>` / `JSON.stringify` dump).
    - **Help & Lifecycle** (collapsed by default): help entries with clickable file/URL links + cloned embedded `ticket-lifecycle.svg`.
  - Render a compact top header bar modeled on `vscode-clutchwork`'s sidebar title bar, with crisp 14x14/16x16 inline SVG icons on action buttons:
    - Engine status indicator (`Engine: running` / `Engine: stopped`), `Start drain` and `Start serve` buttons (play SVG icon) when stopped, `Stop` button (stop SVG icon) when running, `Refresh` button (refresh SVG icon), and `Open config.yaml` button (gear/file SVG icon, calling `openFile(snap.configPath)` when `snap?.configPath` is present).
    - Compact Repo switcher toggle button (folder/repo SVG icon) showing the active repo name/path; the `Repository path` input and `Load repository` button stay collapsed when a repo is loaded and open on toggle click (or automatically when no repo is loaded).
    - Compact collapsible **Agent Actions** menu/drawer (omitted when `!app.getHostCapabilities()?.message`) containing `Supervise Drain Loop`, `Run Roadmap (Drain)`, `Run Roadmap (Serve)`, `Diagnose Stem`, `Review Drafts`, and the `New conversation` checkbox toggle.
  - Add a floating right-click `.context-menu` positioned at cursor coordinates (`clientX`/`clientY`) and dismissed on outside click, `Escape` keydown, or action click:
    - Ticket row `contextmenu` (wired via `onRowContext` passed to `createTicketsView`): calls `preventDefault()`, pins/selects the ticket row, and renders items strictly from `row.menu`, `row.priorityChoices`, and `row.runsBeforeChoices`: `Confirm` (`clutchConfirm === "on"` -> `clutch_app_ticket_confirm`), `Reject` (`clutchReject === "on"` -> `clutch_app_ticket_reject`), priority choices from `row.priorityChoices` (`clutchPriority === "on"` -> `clutch_ticket_order`), `Runs before...` choices/submenu from `row.runsBeforeChoices` (`clutchRunsBefore === "on"` -> `clutch_ticket_order`), `Open ticket.md` (`openFile(row.path)`), `Open run.md`, `Open review.md`, `Open diagnosis.json`, and `Diagnose Stem` (when `app.getHostCapabilities()?.message` and `row.menu.clutchAskDiagnose === "on"`).
    - Suggestion Box row `contextmenu` (wired via `onRowContext` passed to `createBoxView`, using a `WeakMap` so a single `contextmenu` listener is attached per DOM node without duplicating across `update()` calls): calls `preventDefault()`, uses the current multi-selection if the clicked row is already selected or selects that row, and renders `Triage` (when all target rows have `clutchTriage === "on"` -> `clutch_box_triage`), `Dismiss` (when all target rows have `clutchDismiss === "on"` -> `clutch_box_dismiss`), `Open message file` (`openFile(row.path)` when `row.path`), and `Open ticket/record` (`openFile(row.link)` when `row.link`).
- `clutch/ui/dashboard.css`:
  - Define every `--vscode-*` CSS custom property referenced by `vscode-clutchwork/media/view.css` (`--vscode-clutchwork-merged`, `--vscode-clutchwork-queued`, `--vscode-clutchwork-blocked`, `--vscode-scmGraph-historyItemRemoteRefColor`, `--vscode-scmGraph-historyItemRefColor`, `--vscode-scmGraph-historyItemBaseRefColor`, `--vscode-font-family`, `--vscode-font-size`, `--vscode-foreground`, `--vscode-descriptionForeground`, `--vscode-list-hoverBackground`, `--vscode-list-inactiveSelectionBackground`, `--vscode-sideBar-background`, `--vscode-editor-background`, `--vscode-editorHoverWidget-border`, `--vscode-textLink-foreground`) plus semantic icon color variables (`--clutch-icon-passed`, `--clutch-icon-failed`, `--clutch-icon-warning`, `--clutch-icon-muted`) on `:root` with dark and light theme rules (`[data-theme="dark"]` / `[data-theme="light"]`) mapped to Antigravity `--color-*` host variables with crisp semantic fallbacks so graph lanes, status pills, badges, hover/selection rows, and step icons render in full color.
  - Style the compact sidebar layout, collapsible `<details>` section headers (uppercase compact headings, subtle border-bottom, item counts), `.step-row` full-width single-line flex layout (with right-aligned `.step-time`, `.step-stem`, `.step-text`, `.step-icon`), top header bar, collapsible repo switcher, floating `.context-menu` and submenu using Antigravity CSS variables (`--color-background-*`, `--color-text-*`, `--color-border-*`, `--font-sans`), compact buttons/selects, and `.stats-list` / `.stats-row` formatting.
- `tests/mcp_app_dashboard.js`:
  - Extend the fake DOM `Node` to support multiple listeners per event type, parent tracking / `contains()`, and `<details>` `open` state so `box.js` + `app.js` `contextmenu` handlers, outside clicks, and `Escape` dismissal are exercised directly.
  - Update existing harness assertions for the stacked `<details>` layout, `clutch_app_stats` `{ window, tree: true }` tree payload, top-bar `Open config.yaml`, and removal of unconditional Details artifact buttons, and add assertions for Recent Steps row layout/stems/icons, `--vscode-*` CSS variable coverage in `clutch/ui/dashboard.css`, header action SVG icons, right-click context menus, formatted stats tree, and collapsed repo switcher.

**Scope out:**
- Do not modify `vscode-clutchwork/`, `clutch/mcp.py`, `clutch/observe.py`, `clutch/stats.py`, `dev.py`, or `tests/integration/test_mcp_app_dashboard.py`.
- Do not commit the gitignored `clutch/ui/dashboard.html` bundle output.

## Scope fence
- clutch/ui/app.js
- clutch/ui/dashboard.css
- tests/mcp_app_dashboard.js

## Acceptance criteria
1. Stacked collapsible sidebar sections replace tabs: `./dev.py test tests/integration/test_mcp_app_dashboard.py` passes with assertions in `tests/mcp_app_dashboard.js` confirming that no `<nav class="tabs">` exists, that Tickets, Details, and Recent Steps `<details>` sections all have `open === true` simultaneously on initial render without clicking any tab, and that Stats and Help & Lifecycle start with `open === false` (ruling out mutually-exclusive hidden panels).
2. Recent Steps full-width rows, stems, and SVG icons: `tests/mcp_app_dashboard.js` asserts that each step in `snap.steps` renders as its own dedicated `.step-row` element containing an inline `<svg>` icon for `step.kind`, `step.stem` (when present), `step.text`, and `step.timeDisplay`, that an unknown `step.kind` renders a warning icon and `cannot draw the clutch snapshot: unknown step kind <kind>`, and that `clutch/ui/dashboard.css` styles `.step-row` with `display: flex` and `width: 100%` (ruling out inline wrapping buttons or missing stems/icons).
3. Complete `--vscode-*` color variable parity and header icons: `tests/mcp_app_dashboard.js` parses all `--vscode-*` custom properties referenced in `vscode-clutchwork/media/view.css` and asserts every single one is defined in `clutch/ui/dashboard.css` (ruling out undefined VS Code variables in Antigravity), and asserts that top-bar action buttons (`Start drain` / `Stop`, `Refresh`, `Open config.yaml`, and the Repo switcher toggle) each contain an inline `<svg>` icon.
4. Clean top bar and Details hygiene: `tests/mcp_app_dashboard.js` asserts that `Open config.yaml` is rendered in the top header bar (not inside Details) and opens `snap.configPath`, that Details does not render unconditional `run.md` / `checks.json` / `review.md` / `diagnosis.json` / `rework.md` buttons, and that the `Repository path` input is hidden when a repo is loaded and revealed only when the repo switcher toggle is clicked (ruling out a permanently visible repo input or stray Details buttons).
5. Ticket right-click context menu: `tests/mcp_app_dashboard.js` asserts that dispatching `contextmenu` on a ticket row opens `.context-menu` with `Confirm`, `Reject`, priority choices from `row.priorityChoices`, `Runs before` choices from `row.runsBeforeChoices`, `Open ticket.md`, `Open run.md`, `Open review.md`, `Open diagnosis.json`, and `Diagnose Stem` when enabled, invokes `clutch_app_ticket_confirm`, `clutch_app_ticket_reject`, and `clutch_ticket_order` with the expected arguments, omits disabled actions when `row.menu` flags are `"off"`, and closes on `Escape` and outside click (ruling out a missing, ungated, or stuck context menu).
6. Suggestion Box right-click context menu: `tests/mcp_app_dashboard.js` asserts that dispatching `contextmenu` on a Suggestion Box row opens `.context-menu` with `Triage`, `Dismiss`, and `Open message file`, invokes `clutch_box_triage` and `clutch_box_dismiss` with the selected IDs, and omits `Triage`/`Dismiss` when `row.menu` flags are `"off"` (ruling out missing or ungated box context actions).
7. Formatted Stats tree: `tests/mcp_app_dashboard.js` asserts that `clutch_app_stats` is called with `{ window: "7d", tree: true }`, that the Stats section renders formatted `.stats-row` metric nodes from `result.tree` (including nested child rows and tooltips), and that no `<pre>` JSON dump is rendered inside Stats (ruling out raw `JSON.stringify` output).
8. Bundle build and MCP dashboard tests remain green: `./dev.py test tests/integration/test_mcp_app_dashboard.py tests/unit/test_dev_ui_bundle.py tests/unit/test_mcp_app_dashboard.py` exits 0 with no regressions to theme binding, `toggle-aux-pane` file opening, `updateModelContext`, prompt launching, or inline action controls.

## Verification
```
./dev.py test tests/integration/test_mcp_app_dashboard.py tests/unit/test_dev_ui_bundle.py tests/unit/test_mcp_app_dashboard.py
```

## Definition of rejected
- Any JavaScript code in `clutch/ui/app.js` derives, sorts, filters, or parses domain data or invents menu/policy rules instead of reading snapshot and `stats_tree` fields.
- Recent Steps renders wrapping inline buttons or omits `step.stem` or `STEP_KINDS` inline SVG icons.
- Any `--vscode-*` custom property referenced in `vscode-clutchwork/media/view.css` is left undefined in `clutch/ui/dashboard.css`.
- Any stray `config.yaml` button or unconditional 6-artifact button row remains in Details, or the 6 mutually-exclusive tabs remain.
- Stats still renders a raw `JSON.stringify` `<pre>` dump instead of formatted `stats_tree` rows.
- Any file outside `## Scope fence` is modified, or `./dev.py test tests/integration/test_mcp_app_dashboard.py tests/unit/test_dev_ui_bundle.py tests/unit/test_mcp_app_dashboard.py` fails.

## Time budget
- expected: 15m
- stuck: 30m
