---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- clutch/mcp.py
- clutch/ui/app.js
- clutch/ui/dashboard.css
- vscode-clutchwork/media/view.css
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py
- tests/unit/test_mcp_app_dashboard.py
- tests/unit/test_mcp_tools.py

## Goal / Why
Fix seven owner-reported UX parity bugs in the Antigravity MCP App dashboard so it matches the VS Code extension without manual setup, stale workspace state, hover noise, or broken visual hierarchy:

1. **Auto-resolve repository and follow the active Antigravity project:** When `clutch mcp serve` is launched from outside a checkout or when the user switches projects in Antigravity, `ClutchMCPServer` only checks `self.cwd`, ignores MCP `roots/list` and `notifications/roots/list_changed`, and does not remember the last valid checkout; `clutch/ui/app.js` ignores `ontoolresult` and pins every subsequent call to an old repo string. Resolving `roots` -> `cwd` -> `last_repo`, refreshing `roots/list` on `notifications/roots/list_changed`, and keeping auto-resolved `explicitRepo = ""` in `app.js` opens the dashboard immediately on the active project and automatically follows project switches.
2. **Restore exact VS Code default palette colors:** `clutch/ui/dashboard.css` maps `--vscode-clutchwork-merged` to `--color-text-success` (Antigravity green) and `--vscode-clutchwork-blocked` to `--color-text-warning` (Antigravity yellow). Defining VS Code's exact hex colors directly while keeping chrome surface/background/border/text tokens bound to Antigravity theme variables restores semantic color parity across light and dark themes.
3. **Reorderable and resizable stacked sections:** `clutch/ui/app.js` renders plain `<details class="sidebar-section">` blocks without scrollable bodies, drag-resize handles, or reordering controls. Adding `.section-body`, `.section-resizer` drag handles, `<summary>` drag-and-drop, and `▲`/`▼` move buttons restores VS Code sidebar pane resizing and reordering.
4. **Mouse-over Details update, running-ticket fallback, and no hover `updateModelContext` spam:** Right-clicking currently pins rows permanently, `Escape` does not unpin, and hovering over any row calls `app.updateModelContext(...)` (spamming chat context pills). Making hover update `detailView` immediately without calling `updateModelContext`, restoring `snap.runningStem` on `mouseleave`, unpinning on `Escape`, and only attaching model context on explicit click/pin restores VS Code hover/pin semantics cleanly.
5. **Clean action buttons and Agent Actions layout:** Top-bar controls, toolbar buttons, and the `Agent Actions` drawer currently render as a wall of inline text pills butted together. Using compact icon-first top-bar controls with `title`/`aria-label`, concise `Drain`/`Serve`/`Stop` buttons, a vertical column layout for `.agent-actions`, and clear spacing in `.toolbar` makes actions scannable at a glance.
6. **Ticket right-click context menu parity with VS Code:** The current ticket context menu dumps unconditional `Open run.md`/`Open review.md`/`Open diagnosis.json` links (missing on drafts) and raw inline priority/runs-before pickers, and omits `Lint`, `Ask Agent: review`, and `Ask Agent: drafts`. Grouping items with `<hr class="menu-sep">` dividers, collapsible `Run before...`/`Set priority...` pickers, `Lint`, `Confirm (keep)`/`Reject (kill)`, and the `Ask Agent:` entries restores VS Code's context menu.
7. **Header and typography parity with VS Code:** `ticketsHeader` and `boxHeader` currently have no class or id, so they miss `view.css`'s `#header` style and render in large bright text instead of VS Code's muted `11px` header; `body` also lacks `font-size: var(--vscode-font-size, 13px);`. Adding `.view-header` and `body` font-size restores VS Code's typography and compact `22px` row density.

## Boundary contract

### MCP stdio roots discovery and default repository resolution
- disposition: extend
- owner: clutch/mcp.py
- consumers: `clutch mcp serve`, Antigravity MCP host, MCP unit and integration tests
- observable change: `ClutchMCPServer` records whether the client advertised `capabilities.roots` during `initialize` and stores discovered `self.roots: list[Path]`, `self.last_repo: Path | None`, and an injectable `last_repo_path: Path | None = None` (defaulting to `$XDG_CONFIG_HOME/clutch/last-repo` when `XDG_CONFIG_HOME` is non-empty, else `~/.config/clutch/last-repo`). In `serve_stdio`, after receiving `notifications/initialized` or `notifications/roots/list_changed` (when the client advertised `capabilities.roots`), the server emits a fresh server-to-client JSON-RPC request `{"jsonrpc": "2.0", "id": "roots-1", "method": "roots/list"}` (incrementing the counter on subsequent requests) on stdout, and handles incoming JSON-RPC responses (no `"method"`, has `"result"`) by parsing `file://` root URIs into `server.roots`. Every successful `checkout()` records `self.last_repo = root` and best-effort persists it to `self.last_repo_path`. When `args.repo is None`, default repo resolves in order: (1) first `file://` root in `self.roots` containing `tickets/`, (2) `self.cwd` if `(self.cwd / "tickets").is_dir()`, (3) remembered `last_repo` (in-memory or persisted file) if it still exists and contains `tickets/`; only when none matches does `clutch_open_dashboard` return `ready: False` or other tools raise `invalid_repo`.
- compatibility: explicit `repo` arguments, `cwd`-based resolution when no root matches, and all JSON-RPC request/error codes remain unchanged; clients that do not advertise `capabilities.roots` receive no `roots/list` request.
- acceptance: `tests/unit/test_mcp_repo_resolution.py` verifies `roots/list` emission on `initialized` and `roots/list_changed`, response parsing, resolution precedence (`roots` -> `cwd` -> `last_repo`), persistence via `last_repo_path`, and fallback when no candidate is valid.
- tests: `tests/unit/test_mcp_repo_resolution.py`, `tests/unit/test_mcp_app_dashboard.py`, `tests/unit/test_mcp_tools.py`
- post-merge source of truth: `clutch/mcp.py`

### MCP App dashboard UI (auto-follow repo, palette, layout, hover/pin, context menu, typography)
- disposition: extend
- owner: clutch/ui/app.js, clutch/ui/dashboard.css
- consumers: `dev.build_ui_bundle`, `ui://clutch/dashboard.html`, Antigravity MCP App iframe, `tests/mcp_app_dashboard.js`
- observable change: `clutch/ui/app.js` tracks `explicitRepo` separately from the displayed `snap.root` (only passing `{ repo: explicitRepo }` in `callTool()` when the user explicitly entered a repo in the switcher or `ontoolinput` supplied an explicit `repo`, while leaving `explicitRepo = ""` for server auto-resolution so every `refresh()` / `focus` follows the server's active project), handles `app.ontoolresult` (`result?.structuredContent?.repo`), keeps `repoSwitcher.hidden = true` when a repo is loaded unless toggled, and avoids flashing an error notice before `ontoolinput`/`ontoolresult` supplies `repo`. Hovering (`mouseenter`) updates `detailView` immediately without calling `app.updateModelContext`, `mouseleave` restores `snap.runningStem` when unpinned, `Escape` closes the menu and unpins `ticketsView`, right-clicking does not permanently pin a row, and only explicit click/pin calls `app.updateModelContext`. Each `.sidebar-section` wraps content in `.section-body` (`overflow: auto`), includes a `.section-resizer` drag handle (`>= 60px` clamp), and supports reordering via `<summary>` HTML5 drag-and-drop and `▲`/`▼` move buttons. Ticket right-click context menus match VS Code's 4-group layout with `<hr class="menu-sep">` dividers (`Open ticket.md`; collapsible `Run before...`/`Set priority...` + `Lint`; `Confirm (keep)`/`Reject (kill)`; `Ask Agent: diagnose`/`review`/`drafts`). `ticketsHeader` and `boxHeader` carry class `view-header`. `clutch/ui/dashboard.css` defines exact VS Code SCM graph and light/dark step-icon hex colors directly while keeping chrome tokens bound to Antigravity `--color-*` variables, sets `body` `font-size: var(--vscode-font-size, 13px)`, and styles `.view-header`, `.context-menu`/`.menu-sep`, `.top-bar` icon-first buttons, vertical `.agent-actions`, and spaced `.toolbar` actions.
- compatibility: existing dashboard tools, views, Suggestion Box context menus, and Antigravity light/dark chrome bindings remain intact.
- acceptance: `tests/mcp_app_dashboard.js` and `tests/integration/test_mcp_app_dashboard.py` verify the exact CSS palette values, `ontoolresult` and auto-follow `explicitRepo` behavior, hover/mouseleave Details and `updateModelContext` gating, section reordering and resizing, grouped ticket context menu, `.view-header` typography, and updated top-bar/agent-actions layout.
- tests: `tests/mcp_app_dashboard.js`, `tests/integration/test_mcp_app_dashboard.py`
- post-merge source of truth: `clutch/ui/app.js`, `clutch/ui/dashboard.css`

## Scope in / Scope out
**Scope in:**
- `clutch/mcp.py`:
  - Add `last_repo_path: Path | None = None` to `ClutchMCPServer.__init__`; default to `Path(self.env["XDG_CONFIG_HOME"]) / "clutch" / "last-repo"` when `XDG_CONFIG_HOME` is non-empty, else `Path.home() / ".config" / "clutch" / "last-repo"`.
  - Initialize `self.client_supports_roots = False`, `self.roots: list[Path] = []`, and `self.last_repo: Path | None = None`.
  - In `dispatch("initialize", params)`: record `self.client_supports_roots = isinstance(params.get("capabilities"), dict) and "roots" in params["capabilities"]`.
  - In `serve_stdio`:
    - Handle incoming JSON-RPC responses (dict with `jsonrpc == "2.0"`, no `"method"`, and `"result"` present) instead of raising `-32600 Invalid Request`: when the response matches an emitted `roots/list` request id and `result` contains a `"roots"` list, parse `file://` URIs (using `urllib.parse.urlparse` + `unquote`) into `server.roots`.
    - When receiving notification `"notifications/initialized"` or `"notifications/roots/list_changed"` and `server.client_supports_roots` is True, immediately emit a server-to-client JSON-RPC request `{"jsonrpc": "2.0", "id": f"roots-{n}", "method": "roots/list"}` on `stdout` and flush.
  - Add a default repo resolution helper on `ClutchMCPServer` used when `repo is None` (both in `checkout()` and in `call_tool("clutch_open_dashboard", ...)`):
    1. First `file://` root `Path` in `self.roots` where `(root / "tickets").is_dir()`.
    2. `self.cwd` if `(self.cwd / "tickets").is_dir()`.
    3. `self.last_repo` (or the path read from `self.last_repo_path` if `self.last_repo` is None and the file exists) if it is a directory containing `tickets/`.
    4. Otherwise return `None` (`clutch_open_dashboard` returns `ready: False`; `checkout()` raises `runner.Refusal(..., code="invalid_repo")`).
  - On every successful `checkout()`, set `self.last_repo = root` and best-effort persist `str(root)` to `self.last_repo_path` (creating parent dirs; ignore `OSError` so read-only environments never fail a tool call).
- `clutch/ui/app.js`:
  - Track `explicitRepo` separately from the displayed `snap.root`. Only pass `{ repo: explicitRepo }` in `callTool()` when the user explicitly entered a repo in the repo switcher (clearing `explicitRepo` if they submit an empty string) or `ontoolinput` passed an explicit `repo`. When auto-resolved by the server, leave `explicitRepo = ""` so every `refresh()` (including `window` `focus`) resolves against the server's current active workspace root and automatically switches when the user switches projects.
  - Handle `app.ontoolresult` to read `result?.structuredContent?.repo`: update `repoInput.value` for display, clear any stale repo error notice, and trigger `refresh()` if `connected` (while still forwarding to `options.ontoolresult?.(result)` and keeping `explicitRepo` unset unless explicitly chosen).
  - In `refresh()`, sync `repoInput.value = explicitRepo || snap.root || ""` without setting `explicitRepo` from `snap.root`, clear `notice.textContent` on successful refresh, and keep `repoSwitcher.hidden = !!snap.root && !repoOpen`.
  - Avoid flashing an error notice on initial boot before `ontoolinput`/`ontoolresult` has had a chance to supply `repo` when the initial unpinned `clutch_app_snapshot` fails with `invalid_repo`.
  - Fix hover/pin and model-context behavior:
    - Ensure `mouseenter` on ticket/box rows updates `detailView` immediately without clicking, and `mouseleave` restores `snap.runningStem` when nothing is pinned.
    - Do NOT call `app.updateModelContext(...)` inside `onFocus` / `mouseenter`; only attach model context on an explicit user click/pin (e.g. a click listener on ticket/box rows).
    - Pressing `Escape` calls both `closeMenu()` and `ticketsView.setPinned(undefined)`.
    - Opening the context menu on right-click (`contextmenu`) does NOT permanently pin the row (`ticketsView.setPinned(row.stem)` removed; show details/menu for the right-clicked row without leaving it pinned after the menu closes).
  - Match VS Code's ticket right-click context menu structure with `<hr class="menu-sep">` dividers between non-empty groups:
    - Group 1: `Open ticket.md` (using `row.path`; remove the unconditional `Open run.md`, `Open review.md`, `Open diagnosis.json` items).
    - Group 2 (order & checks):
      - `Run before...` (when `row.menu.clutchRunsBefore === "on"` — clicking expands/toggles the inline checkbox picker + `Set runs before` button instead of rendering checkboxes expanded by default).
      - `Set priority...` (when `row.menu.clutchPriority === "on"` — clicking expands/toggles the P0–P3 choice buttons instead of rendering them expanded by default).
      - `Lint` (when `row.menu.clutchLint === "on"` — calls `clutch_ticket_lint({ stems: [row.stem] })` and displays the lint summary in `notice`).
    - Group 3 (verdicts):
      - `Confirm (keep)` (when `row.menu.clutchConfirm === "on"` -> `clutch_app_ticket_confirm`).
      - `Reject (kill)` (when `row.menu.clutchReject === "on"` -> `clutch_app_ticket_reject`).
    - Group 4 (agent prompts, when `app.getHostCapabilities()?.message`):
      - `Ask Agent: diagnose` (when `row.menu.clutchAskDiagnose === "on"` -> `sendPrompt("diagnose", [row.stem])`).
      - `Ask Agent: review` (when `row.menu.clutchAskReview === "on"` -> `sendPrompt("review", [row.stem])`).
      - `Ask Agent: drafts` (when `row.menu.clutchAskDrafts === "on"` -> `sendPrompt("drafts", [])`).
  - Give `ticketsHeader` and `boxHeader` class `"view-header"`.
  - For each `.sidebar-section`:
    - Wrap its body children inside `<div class="section-body">`.
    - Append `<div class="section-resizer"></div>` at the bottom of the section; on `pointerdown`/`mousedown`, track vertical drag via `pointermove`/`mousemove` and `pointerup`/`mouseup` to set `.section-body`'s `style.height` (clamped to `>= 60px`).
    - Make `<summary>` draggable (`draggable = true`) and handle `dragstart`, `dragover` (`preventDefault()`), and `drop` to reorder the dragged `.sidebar-section` before or after the drop target section.
    - Add explicit up (`▲`) and down (`▼`) move buttons inside `<summary>` (in a `.section-controls` container) whose click handlers call `e.stopPropagation()` and `e.preventDefault()` so clicking them reorders the section among `.sidebar-section` siblings without toggling `<details>`.
  - Update `.top-bar` controls to be compact and icon-first:
    - Engine status indicator clearly separated from concise action buttons `Drain` / `Serve` (when stopped) or `Stop` (when running).
    - Icon-only buttons with `title` and `aria-label` for Refresh (`Refresh`), Config (`Open config.yaml`), and Repository (`Switch repository: ${snap.root || "none"}`).
- `clutch/ui/dashboard.css`:
  - Define exact VS Code default SCM graph and icon palette colors directly:
    - `--vscode-clutchwork-merged: #B180D7;`
    - `--vscode-clutchwork-queued: #3794FF;`
    - `--vscode-clutchwork-blocked: #EA5C00;`
    - `:root` / `[data-theme="light"]`: `--clutch-icon-passed: #388A34;`, `--clutch-icon-failed: #E51400;`, `--clutch-icon-warning: #BF8803;`
    - `[data-theme="dark"]`: `--clutch-icon-passed: #73C991;`, `--clutch-icon-failed: #F14C4C;`, `--clutch-icon-warning: #CCA700;`
  - Do NOT map `--vscode-clutchwork-merged` to `--color-text-success` or `--vscode-clutchwork-blocked` to `--color-text-warning`.
  - Keep surface/background/border/text tokens bound to Antigravity `--color-background-*`, `--color-text-*`, `--color-border-*`.
  - Set `body` `font-size: var(--vscode-font-size, 13px);` and add `.view-header { padding: 2px 8px 4px; color: var(--vscode-descriptionForeground); font-size: 11px; }`.
  - Style `.context-menu` (`background: var(--color-background-secondary, #252526); border-radius: 6px; padding: 4px 0; font-size: 13px;`), `.context-menu button` (`padding: 5px 14px; width: 100%; border-radius: 0;`), and `.menu-sep { border: 0; border-top: 1px solid var(--color-border-primary, #454545); margin: 4px 0; }`.
  - Style `.section-body` (`overflow: auto; min-height: 60px;`), `.section-resizer` (`height: 6px; cursor: ns-resize;`), and `.section-controls` / move buttons inside `.sidebar-section > summary`.
  - Style `.top-bar` (`gap: 6px`, button `padding: 4px 8px`, visible distinct button surface/border), `.agent-actions` (vertical column layout `display: flex; flex-direction: column; gap: 4px; padding: 6px 4px;` with full-width left-aligned buttons `padding: 5px 8px`), and `.toolbar` (`gap: 6px; padding: 4px 0;` and `padding: 4px 10px` on buttons).
- `tests/unit/test_mcp_repo_resolution.py` (new): unit tests using `tmp_path` only covering `roots/list` handshake on `initialized` and `notifications/roots/list_changed`, response parsing, `roots` -> `cwd` -> `last_repo` precedence, `last_repo_path` persistence, and fallback when no valid checkout exists.
- `tests/unit/test_mcp_app_dashboard.py` and `tests/unit/test_mcp_tools.py`: pass `last_repo_path=tmp_path / "last-repo"` in `test_dashboard_tools` and `test_prompt_domain_and_validation` so existing unit tests never read or clobber a developer's `$HOME/.config/clutch/last-repo`.
- `tests/mcp_app_dashboard.js` and `tests/integration/test_mcp_app_dashboard.py`:
  - Update top-bar button lookups for the new icon-only `title`/`aria-label` buttons (`Refresh`, `Open config.yaml`, `Switch repository: ...`) and concise `Drain`/`Serve`/`Stop` labels, update ticket context menu assertions for the new grouped items (`Open ticket.md`, collapsible `Run before...`/`Set priority...`, `Lint`, `Confirm (keep)`, `Reject (kill)`, `Ask Agent: diagnose`/`review`/`drafts`, `<hr class="menu-sep">`, and absence of unconditional `Open run.md`/`Open review.md`/`Open diagnosis.json`), and update the ticket `updateModelContext` assertion to click a ticket row instead of relying on right-click pinning.
  - Add assertions verifying: exact VS Code hex values in `dashboard.css` (and absence of `--color-text-success`/`--color-text-warning` mappings for merged/blocked), `ontoolresult` repo sync without setting `explicitRepo` (so subsequent `refresh()` leaves `repo` omitted and follows server root switches), `mouseenter` updating Details without calling `updateModelContext` and `mouseleave` restoring `snap.runningStem`, `Escape` unpinning, section reordering via move buttons and drag-and-drop, `.section-resizer` height resizing (clamped `>= 60px`), `.view-header` class on headers, and `.agent-actions` / `.context-menu` / `.menu-sep` CSS rules.
- `tests/regression/mcp_dashboard_ux_parity.py` (new): regression reproducer speaking the `regression_result` JSON protocol.

**Scope out:**
- No edits to `vscode-clutchwork/` or any of the 7 hot test files.
- No edits to `clutch/docs/` or `docs/`.
- No committing of gitignored `clutch/ui/dashboard.html`.

## Scope fence
- clutch/mcp.py
- clutch/ui/app.js
- clutch/ui/dashboard.css
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py
- tests/unit/test_mcp_app_dashboard.py
- tests/unit/test_mcp_tools.py
- tests/unit/test_mcp_repo_resolution.py
- tests/regression/mcp_dashboard_ux_parity.py

## Acceptance criteria
1. `serve_stdio` emits `{"jsonrpc": "2.0", "id": "roots-1", "method": "roots/list"}` after `notifications/initialized` and emits a fresh `roots/list` request on `notifications/roots/list_changed` when `initialize` advertises `capabilities.roots`, parses `file://` root URIs from the client's JSON-RPC response into `server.roots` (not rejecting the response with `-32600`), and emits no `roots/list` request when `capabilities.roots` is absent; verified by `./dev.py test tests/unit/test_mcp_repo_resolution.py tests/unit/test_mcp_protocol.py`.
2. When `args.repo is None`, `ClutchMCPServer` resolves the checkout in order `roots` -> `cwd` -> persisted/in-memory `last_repo` (recording every successful `checkout()` to `self.last_repo` and `self.last_repo_path`), returning `ready: False` / `invalid_repo` only when none contains `tickets/` (not failing when `cwd` lacks `tickets/` or sticking on an old `cwd`/`last_repo` when `self.roots` switches to a different checkout); verified by `./dev.py test tests/unit/test_mcp_repo_resolution.py tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_tools.py`.
3. `clutch/ui/dashboard.css` defines `--vscode-clutchwork-merged: #B180D7`, `--vscode-clutchwork-queued: #3794FF`, `--vscode-clutchwork-blocked: #EA5C00`, dark icon colors (`#73C991`, `#F14C4C`, `#CCA700`), and light icon colors (`#388A34`, `#E51400`, `#BF8803`), and does NOT map `--vscode-clutchwork-merged` to `--color-text-success` or `--vscode-clutchwork-blocked` to `--color-text-warning`, while keeping chrome surface/background/border/text tokens bound to Antigravity `--color-*` variables, setting `body` `font-size: var(--vscode-font-size, 13px)`, and styling `.view-header`, `.menu-sep`, and vertical `.agent-actions` (`flex-direction: column`); verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
4. `clutch/ui/app.js` picks up `result.structuredContent.repo` in `app.ontoolresult`, keeps `explicitRepo = ""` during server auto-resolution so subsequent `refresh()`/`focus` calls omit `repo` and follow server root switches (passing `repo` only when explicitly entered in the switcher or passed via `ontoolinput`), keeps `repoSwitcher.hidden = true` when a repo is loaded unless toggled, does not flash an error notice before `ontoolinput`/`ontoolresult` supplies `repo`, applies class `view-header` to `ticketsHeader` and `boxHeader`, and renders icon-only `title`/`aria-label` top-bar buttons plus concise `Drain`/`Serve`/`Stop` buttons; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
5. Hovering (`mouseenter`) a ticket row updates `detailView` immediately without calling `app.updateModelContext`, `mouseleave` on the tickets list restores `snap.runningStem` when unpinned, `Escape` unpins `ticketsView`, right-clicking does not permanently pin a row, and only explicit clicking calls `app.updateModelContext`; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
6. Right-clicking a ticket renders VS Code's 4-group context menu separated by `<hr class="menu-sep">` (`Open ticket.md` without unconditional `Open run.md`/`Open review.md`/`Open diagnosis.json`; collapsible `Run before...` and `Set priority...` pickers plus `Lint` calling `clutch_ticket_lint`; `Confirm (keep)` and `Reject (kill)`; `Ask Agent: diagnose`, `Ask Agent: review`, and `Ask Agent: drafts` gated by `row.menu` and `message` capability); verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
7. Each `.sidebar-section` in `clutch/ui/app.js` wraps content in `.section-body`, resizes `.section-body` height (clamped to `>= 60px`, not unbounded/negative) via `.section-resizer` drag events, and reorders sections via both `<summary>` HTML5 drag-and-drop and `▲`/`▼` move buttons without toggling `<details>`; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
8. The regression reproducer exits 0 with `{"regression_result": "pass"}` on the fixed branch and exits non-zero with `{"regression_result": "defect"}` on the merge base; verified by `uv run python tests/regression/mcp_dashboard_ux_parity.py`.

## Verification
```
./dev.py test tests/unit/test_mcp_repo_resolution.py tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_protocol.py tests/integration/test_mcp_app_dashboard.py
```

## Definition of rejected
- Any `clutch/ui/dashboard.css` rule maps `--vscode-clutchwork-merged` to `--color-text-success` or `--vscode-clutchwork-blocked` to `--color-text-warning`, or drops Antigravity `--color-*` chrome bindings.
- Any unit test reads or writes `$HOME/.config/clutch/last-repo` instead of using `tmp_path` via `last_repo_path`.
- Hovering (`mouseenter`) a ticket or box row calls `app.updateModelContext`.
- Any edit occurs outside the declared `## Scope fence` or modifies any of the 7 hot test files.

## Time budget
- expected: 25m
- stuck: 50m

## Regression
```
uv run python tests/regression/mcp_dashboard_ux_parity.py
```
- carries: tests/regression/mcp_dashboard_ux_parity.py
