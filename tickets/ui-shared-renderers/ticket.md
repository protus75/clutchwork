---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- vscode-clutchwork/media/graph.js
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/media/view.css
- vscode-clutchwork/extension.js
- clutch/help.py
- clutch/ioguard.py::blocked_operation
- tests/unit/test_help.py
- tests/integration/test_help.py
- tests/integration/conftest.py
- tests/integration/test_disk_io_skip_list.py
- tests/integration/test_step_view_unknown_kind.py
- tests/integration/test_extension_draw_failure.py
- tests/vscode_draw_failure.js
- docs/antigravity-plan.md#4. Antigravity MCP App dashboard replacing VS Code views

## Goal / Why
`vscode-clutchwork/media/{graph,view,detail,box}.js` and `view.css` currently couple directly to `acquireVsCodeApi()` and `--vscode-*` CSS variables, preventing the upcoming Antigravity MCP App dashboard (`mcp-app-dashboard`) from reusing the same DOM/SVG renderers without duplicating JS logic. Meanwhile, `clutch/help.py` covers the five VS Code extension views (`view.clutch.{tickets,details,steps,box,stats}`) but lacks `view.*` surfaces for the shared dashboard and its Help & Lifecycle view consumed by `mcp-app-dashboard`.

After this ticket:
- `vscode-clutchwork/media/{graph,view,detail,box}.js` expose pure factory/render entrypoints behind a thin host adapter (`callTool`, `openFile`, `sendPrompt`, `openHelp`) and export them for CommonJS/bundler consumers, while keeping VS Code webview auto-mounting (`acquireVsCodeApi()`) and `vscode-clutchwork` behavior identical.
- `vscode-clutchwork/media/view.css` preserves every `--vscode-*` precedence rule while adding `--color-*` and `--font-*` host-style fallbacks for non-VS Code hosts.
- `clutch/help.py` registers shared UI view topics (`view.clutch.dashboard`, `view.clutch.help`, `view.clutch.lifecycle`) alongside the existing `view.clutch.*` surfaces for `mcp-app-dashboard` to consume.

## Boundary contract
### Shared UI host adapter and renderers
- disposition: extend
- owner: vscode-clutchwork/media/graph.js, vscode-clutchwork/media/view.js, vscode-clutchwork/media/detail.js, vscode-clutchwork/media/box.js, vscode-clutchwork/media/view.css
- consumers: vscode-clutchwork/extension.js webviews, tests/vscode_draw_failure.js, and `mcp-app-dashboard`
- observable change: `graph.js` exports `renderGraph`; `view.js`, `detail.js`, and `box.js` export `createTicketsView`, `createDetailView`, and `createBoxView` accepting a host adapter `{ callTool, openFile, sendPrompt, openHelp }` (plus optional `onFocus`, `onRowContext`, and `keyboardTarget` on `createBoxView`), validating those four adapter methods, and auto-mounting with a VS Code adapter only when `acquireVsCodeApi` is defined; `view.css` adds `--color-*`, `--font-*`, and neutral fallbacks after the mapped `--vscode-*` variables while keeping `--clutch-*` graph colors unchanged
- compatibility: VS Code webviews (`extension.js`) and `tests/vscode_draw_failure.js` see identical DOM output, CSS variable resolution (`--vscode-*` wins first), `dataset.vscodeContext` payloads, and `vscode.postMessage` messages (`ready`, `focus`, `open`, `help`, `readme`)
- acceptance: criteria 1 to 4
- tests: tests/integration/test_ui_shared_renderers.py, tests/ui_shared_renderers.js
- post-merge source of truth: vscode-clutchwork/media/graph.js, vscode-clutchwork/media/view.js, vscode-clutchwork/media/detail.js, vscode-clutchwork/media/box.js, vscode-clutchwork/media/view.css

### Shared UI help surfaces
- disposition: extend
- owner: clutch/help.py
- consumers: `clutch view snapshot`, `vscode-clutchwork/extension.js`, `tests/unit/test_help.py`, `tests/integration/test_help.py`, and `mcp-app-dashboard`
- observable change: `TOPICS` gains `view.clutch.dashboard`, `view.clutch.help`, and `view.clutch.lifecycle` under the `view` surface linked to `host-contract.md` `VS Code extension`
- compatibility: all existing `TOPICS`, `COMMANDS` (exact match with `vscode-clutchwork/package.json`), `topic_text`, `help_map`, and `help_pick` entries keep their keys and link targets so `tests/unit/test_help.py` and `tests/integration/test_help.py` pass unchanged
- acceptance: criteria 5 and 6
- tests: tests/unit/test_help_shared_ui.py, tests/unit/test_help.py, tests/integration/test_help.py
- post-merge source of truth: clutch/help.py

## Scope in / Scope out
Scope in:
- `vscode-clutchwork/media/graph.js`: keep global `renderGraph(graph, dotColor, colors)` and export `{ renderGraph, SWIMLANE_HEIGHT, SWIMLANE_WIDTH }` via `module.exports` when `typeof module === 'object' && module.exports`.
- `vscode-clutchwork/media/view.js`: extract `createTicketsView({ header, list, host, renderGraph, colors })` (resolving the graph renderer as `options.renderGraph || (typeof renderGraph === 'function' ? renderGraph : require('./graph.js').renderGraph)` so `require` is never called when a global `renderGraph` exists, as in `tests/vscode_draw_failure.js`'s `vm.runInNewContext` and VS Code `<script>` webviews; defaulting `colors` to `DEFAULT_COLORS`) returning `{ render, showError, getFocus, setPinned }`. Validate that `host` provides functions `callTool`, `openFile`, `sendPrompt`, and `openHelp` (throwing `TypeError` otherwise); route row double-click to `host.openFile(r.path)`, error setup-help link click to `host.openHelp()`, focus updates to `host.onFocus?.(stem)`, and optional context decoration to `host.onRowContext?.(rowEl, row)`. Catch render errors inside `render(snap)` and call `showError(\`cannot draw the clutch snapshot: \${error.message}\`)`. Export `{ createTicketsView, DEFAULT_COLORS }` via `module.exports` when CommonJS is present, and keep auto-mounting only inside `if (typeof acquireVsCodeApi === 'function')` using a VS Code host adapter (`openFile`, `openHelp`, `onFocus`, `onRowContext`, plus rejecting `callTool`/`sendPrompt` stubs), `window.addEventListener('message', ...)`, and `vscode.postMessage({ type: 'ready' })`.
- `vscode-clutchwork/media/detail.js`: extract `createDetailView({ detail, host })` returning `{ render, showError }`. Validate `host` (`callTool`, `openFile`, `sendPrompt`, `openHelp`); route artifact/ticket/message links to `host.openFile(path)`, `"Learn more"` links to `host.openHelp(topic)`, and error setup-help link to `host.openHelp()`. Catch render errors inside `render(snap, focus)` and call `showError(\`cannot draw the clutch snapshot: \${error.message}\`)`. Export `{ createDetailView }` via `module.exports` when CommonJS is present, and auto-mount only when `typeof acquireVsCodeApi === 'function'`.
- `vscode-clutchwork/media/box.js`: extract `createBoxView({ header, list, host, colors, keyboardTarget })` (defaulting `colors` to `DEFAULT_COLORS` and `keyboardTarget` to `typeof window !== 'undefined' ? window : null`, registering `'keydown'` on `keyboardTarget` without overwriting `'message'` on `window`) returning `{ render, showError, getFocus, getSelected }`. Validate `host` (`callTool`, `openFile`, `sendPrompt`, `openHelp`); route row double-click to `host.openFile(r.path)`, error setup-help link to `host.openHelp()`, focus updates to `host.onFocus?.(id)`, and optional context decoration to `host.onRowContext?.(node, row, ids)`. Catch render errors inside `render(snap)` and call `showError(\`cannot draw the clutch snapshot: \${error.message}\`)`. Export `{ createBoxView, DEFAULT_COLORS }` via `module.exports` when CommonJS is present, and auto-mount only when `typeof acquireVsCodeApi === 'function'`.
- `vscode-clutchwork/media/view.css`: retain `--clutch-merged`, `--clutch-queued`, and `--clutch-blocked` in `:root` with their existing `--vscode-clutchwork-*`, `--vscode-scmGraph-*`, and hex fallbacks unchanged; retain all existing selectors and layout rules; update only the host theme variables below so each `--vscode-*` variable stays first and falls back to its mapped `--color-*` / `--font-*` token and neutral final fallback:
  | VS Code variable | Fallback chain |
  |---|---|
  | `--vscode-font-family` | `var(--vscode-font-family, var(--font-sans, system-ui, -apple-system, sans-serif))` |
  | `--vscode-font-size` | `var(--vscode-font-size, var(--font-text-sm-size, 13px))` |
  | `--vscode-foreground` | `var(--vscode-foreground, var(--color-text-primary, inherit))` |
  | `--vscode-descriptionForeground` | `var(--vscode-descriptionForeground, var(--color-text-secondary, #71717a))` |
  | `--vscode-list-hoverBackground` | `var(--vscode-list-hoverBackground, var(--color-background-secondary, rgba(128, 128, 128, 0.12)))` |
  | `--vscode-sideBar-background` / `--vscode-editor-background` (`.graph` stroke) | `var(--vscode-sideBar-background, var(--vscode-editor-background, var(--color-background-primary, transparent)))` |
  | `--vscode-list-inactiveSelectionBackground` | `var(--vscode-list-inactiveSelectionBackground, var(--color-background-tertiary, rgba(128, 128, 128, 0.2)))` |
  | `--vscode-editorHoverWidget-border` | `var(--vscode-editorHoverWidget-border, var(--color-border-primary, rgba(128, 128, 128, 0.3)))` |
  | `--vscode-textLink-foreground` | `var(--vscode-textLink-foreground, var(--color-text-accent, #3794ff))` |
  | `--vscode-editor-background` (`.badge` color) | `var(--vscode-editor-background, var(--color-background-primary, #1e1e1e))` |
- `clutch/help.py`: add `"clutch.dashboard": "Shows the ClutchWork dashboard."`, `"clutch.help": "Shows help topics and documentation links."`, and `"clutch.lifecycle": "Shows the ticket lifecycle diagram."` to the `view` `_add(...)` dictionary (doc `"host-contract.md"`, heading `"VS Code extension"`), keeping `COMMANDS` and all existing topics unchanged; `mcp-app-dashboard` will consume these topics in the shared dashboard.
- `tests/unit/test_help_shared_ui.py`: new unit test file verifying `view.clutch.dashboard`, `view.clutch.help`, and `view.clutch.lifecycle` exist in `TOPICS`, produce single-line `text`/`what` entries via `help_map` with fake docs, and appear under the `view` separator in `help_pick`.
- `tests/ui_shared_renderers.js`: new Node test script verifying: (a) CommonJS imports and `createTicketsView`, `createDetailView`, `createBoxView`, and `renderGraph` behavior with a mock `{ callTool, openFile, sendPrompt, openHelp, onFocus, onRowContext }` adapter (missing adapter methods throw `TypeError`; row click/hover/dblclick/multi-select/learn-more/error-link trigger the expected adapter callbacks without `acquireVsCodeApi`); and (b) VS Code webview compatibility in a `vm` context with `acquireVsCodeApi` and `renderGraph` across valid, invalid, and error messages for `view.js`, `detail.js`, and `box.js`.
- `tests/integration/test_ui_shared_renderers.py`: new integration test file (no `disk_io_skip` marker) that spawns `node` via `subprocess.run` (matching `tests/integration/test_step_view_unknown_kind.py`) to run `tests/ui_shared_renderers.js` and `tests/vscode_draw_failure.js` across its view/scenario matrix, and asserts `vscode-clutchwork/media/view.css` retains `--clutch-*` unchanged and maps each variable in the table above with `--vscode-*` first and its `--color-*` / `--font-*` fallback.
- `tests/integration/conftest.py`: add `"test_ui_shared_renderers.py"` to `REAL_IO_TESTS` (matching `test_step_view_unknown_kind.py`) because executing the shipped JavaScript files requires spawning a real `node` subprocess (`clutch.ioguard` blocks `subprocess.Popen` otherwise, and no in-memory Python fake executes JavaScript), and leaving `test_ui_shared_renderers.py` unmarked satisfies `tests/integration/test_disk_io_skip_list.py`.
- Engine-written `# clutch:meta` header lines on newly created or edited files under `tests/` (`tests/unit/test_help_shared_ui.py`, `tests/integration/test_ui_shared_renderers.py`, `tests/integration/conftest.py`) updated by Check's meta step.

Scope out:
- `vscode-clutchwork/extension.js`, `vscode-clutchwork/package.json`, the extension README, and `tests/vscode_draw_failure.js`.
- `clutch/ui/dashboard.html`, `@modelcontextprotocol/ext-apps`, and `./dev.py ui-bundle` (`mcp-app-dashboard`).
- `clutch/observe.py`, `clutch/__main__.py`, and all host guide, architecture, and roadmap documentation.
- Existing test files `tests/unit/test_help.py`, `tests/integration/test_help.py`, `tests/integration/test_extension_draw_failure.py`, and all seven hot test files (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `test_cli.py`, `test_watch.py`, `serve_rig.py`).

## Scope fence
- vscode-clutchwork/media/graph.js
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/media/view.css
- clutch/help.py
- tests/unit/test_help_shared_ui.py
- tests/ui_shared_renderers.js
- tests/integration/test_ui_shared_renderers.py
- tests/integration/conftest.py

## Acceptance criteria
1. `createTicketsView`, `createDetailView`, and `createBoxView` throw `TypeError` when any of `callTool`, `openFile`, `sendPrompt`, or `openHelp` is missing from `host`, rather than silently failing later at click time; checked by `./dev.py test tests/integration/test_ui_shared_renderers.py`.
2. With `acquireVsCodeApi` undefined and a mock `{ callTool, openFile, sendPrompt, openHelp, onFocus, onRowContext }` adapter, `createTicketsView`, `createDetailView`, and `createBoxView` render snapshots, invoke `openFile` on row/link clicks, invoke `openHelp(topic)` on `"Learn more"` links and `openHelp()` on `"Open setup help"`, invoke `onFocus` on hover/pin/selection, and `renderGraph` produces an SVG `<svg class="graph">` without touching `window` or `acquireVsCodeApi`; checked by `./dev.py test tests/integration/test_ui_shared_renderers.py`.
3. Under a stubbed `acquireVsCodeApi()` environment (`tests/ui_shared_renderers.js` VM check and `tests/vscode_draw_failure.js`), `view.js`, `detail.js`, and `box.js` produce the same `ready`, `focus`, `open`, `help`, and `readme` messages, `dataset.vscodeContext` payloads, and `cannot draw the clutch snapshot:` / `snapshot failed:` error outputs as before; checked by `./dev.py test tests/integration/test_ui_shared_renderers.py`.
4. In `vscode-clutchwork/media/view.css`, `--clutch-merged`, `--clutch-queued`, and `--clutch-blocked` keep their existing `--vscode-clutchwork-*` / `--vscode-scmGraph-*` / hex values, and each of the ten mapped `--vscode-*` entries in the Scope in table keeps `--vscode-*` first followed by its mapped `--color-*` or `--font-*` fallback before the literal fallback; checked by `./dev.py test tests/integration/test_ui_shared_renderers.py`.
5. `clutch/help.py` includes `view.clutch.dashboard`, `view.clutch.help`, and `view.clutch.lifecycle` in `TOPICS`, `help_map` resolves them with single-line non-empty descriptions, and `help_pick` lists them under the `view` separator; checked by `./dev.py test tests/unit/test_help_shared_ui.py tests/unit/test_help.py tests/integration/test_help.py`.
6. Existing extension, help, and disk-io-skip tests pass unchanged; checked by `./dev.py test tests/unit/test_help_snapshot.py tests/integration/test_extension_argv.py tests/integration/test_step_icons.py tests/integration/test_step_view_unknown_kind.py tests/integration/test_disk_io_skip_list.py`.

## Verification
```
./dev.py test tests/unit/test_help.py tests/unit/test_help_snapshot.py tests/unit/test_help_shared_ui.py tests/integration/test_ui_shared_renderers.py tests/integration/test_help.py tests/integration/test_extension_argv.py tests/integration/test_step_icons.py tests/integration/test_step_view_unknown_kind.py tests/integration/test_disk_io_skip_list.py
```

## Definition of rejected
- Any `vscode-clutchwork/media/{view,detail,box}.js` file still calls `acquireVsCodeApi()` unconditionally at module load, breaking import in non-VS Code environments.
- Any `create*View` factory omits validation of `callTool`, `openFile`, `sendPrompt`, or `openHelp`.
- Any existing VS Code webview behavior, CSS precedence (`--vscode-*` first), `dataset.vscodeContext` shape, or `tests/vscode_draw_failure.js` scenario fails.
- `clutch/help.py` alters `COMMANDS` keys or breaks `tests/unit/test_help.py` or `tests/integration/test_help.py`.
- `tests/integration/test_ui_shared_renderers.py` carries `pytest.mark.disk_io_skip` or fails with `IntegrationIOBlocked`.
- Any file outside the Scope fence changes.

## Time budget
- expected: 15m
- stuck: 30m
