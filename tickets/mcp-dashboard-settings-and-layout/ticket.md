---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/mcp.py
- clutch/config.py::Config
- clutch/config.py::Count
- clutch/config.py::Retro
- clutch/config.py::RetroMerges
- clutch/config.py::RetroSettled
- clutch/config.py::RetroSpikes
- clutch/config.py::Scheduler
- clutch/config.py::Parallel
- clutch/config.py::load_config
- clutch/config.py::load_config_text
- clutch/config.py::_check_references
- clutch/ui/app.js
- clutch/ui/dashboard.css
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py
- tests/unit/test_mcp_app_dashboard.py
- tests/unit/test_mcp_tools.py
- tests/unit/test_mcp_repo_resolution.py

## Goal / Why
Give the MCP App dashboard (`clutch/ui/app.js`) layout persistence, periodic polling, plain-English agent action labels, Suggestion Box parity (`Bulk Triage` and `Ask Agent: discuss`), outcome-colored Recent Steps rows, and an inline Settings section for both UI preferences and repo `config.yaml` retro/parallel settings. Today, reopening the dashboard or switching projects resets every section's order, expanded/collapsed state, and height; the dashboard does not poll on an interval; Recent Steps rows only color their icon rather than the full step line; Suggestion Box lacks bulk triage and discuss; and operators have to hand-edit `config.yaml` for retro and parallel toggles.

## Boundary contract

### MCP dashboard UI state tool
- disposition: create
- owner: clutch/mcp.py
- consumers: `clutch/ui/app.js` (MCP App iframe) and `clutch/mcp.py::ClutchMCPServer`
- closest existing: `clutch/mcp.py::ClutchMCPServer.last_repo_path` (persists a single plain-text repo path string under `~/.config/clutch/last-repo`, cannot hold structured JSON dashboard layout and UI preferences)
- earning reason: storage boundary for cross-session dashboard layout and UI preferences (`~/.config/clutch/dashboard-state.json`) exposed over the MCP app-only tool protocol (`visibility: ["app"]`) with an injectable path seam (`ui_state_path`) for unit test isolation
- observable change: `ClutchMCPServer` gains `ui_state_path: Path | None = None` (defaulting to `<XDG_CONFIG_HOME or ~/.config>/clutch/dashboard-state.json`) and registers app-only tool `clutch_app_ui_state` (`action: Literal["get", "set"]`, optional `state: dict[str, object] | None = None`, optional `repo: str | None = None`). `clutch_app_ui_state` does not require a checkout (`repo` is ignored), returns defaults `{order: ["details", "steps", "tickets", "box", "stats", "settings", "help"], open: {"details": true, "steps": true, "tickets": true, "box": false, "stats": false, "settings": false, "help": false}, heights: {}, refreshSeconds: 15, statsWindow: "7d", playAction: "drain"}` when the file is missing, unreadable, or corrupt, merges/validates allowed keys on `set`, and swallows `OSError` on read/write.
- compatibility: additive app-only tool (`_meta.ui.visibility = ["app"]`), invisible to the model; existing tools and `last_repo_path` behavior are unchanged.
- acceptance: `clutch_app_ui_state` get/set round-trips JSON to `ui_state_path`, returns defaults on missing/corrupt/unreadable files, ignores `OSError` on write, and succeeds without a checkout.
- tests: `tests/unit/test_mcp_ui_state_and_config.py`, `tests/unit/test_mcp_app_dashboard.py`, `tests/unit/test_mcp_tools.py`
- post-merge source of truth: clutch/mcp.py

### MCP dashboard repo config tool
- disposition: create
- owner: clutch/mcp.py
- consumers: `clutch/ui/app.js` (Settings section) and `clutch/mcp.py::ClutchMCPServer`
- closest existing: `clutch/config.py::load_config` and `clutch/config.py::load_config_text` (read-only config validation; no MCP app-only mutation endpoint exists to read or selectively update `retro.*` and `scheduler.parallel.*` in `config.yaml`)
- earning reason: process/storage boundary allowing the sandboxed MCP App iframe to read and safely update an allowlisted subset of `config.yaml` (`retro.*` and `scheduler.parallel.*`) validated fail-closed before writing via `checkout.fs.write`
- observable change: `ClutchMCPServer` registers app-only tool `clutch_app_config` (`action: Literal["get", "set"]`, optional `updates: dict[str, object] | None = None`, optional `repo: str | None = None`). `get` loads config via `load_config` and returns structured current values for `retro` (`enabled`, `merges: {enabled, every}`, `settled: {enabled, every}`, `spikes: {enabled, count}`) and `scheduler` (`parallel: {enabled, max_runs}`). `set` reads raw `config.yaml` via `yaml.safe_load`, accepts only allowlisted keys under `retro` (`enabled`, `merges.enabled`, `merges.every`, `settled.enabled`, `settled.every`, `spikes.enabled`, `spikes.count`) and `scheduler.parallel` (`enabled`, `max_runs`), refuses any unknown key or non-mapping `updates` with `runner.Refusal`, validates the updated mapping against `clutch.config.Config.model_validate` (and `_check_references` / `load_config_text`) failing closed with `runner.Refusal` without writing on invalid values, and writes the updated YAML via `checkout.fs.write`.
- compatibility: additive app-only tool (`_meta.ui.visibility = ["app"]`), invisible to the model; existing `config.yaml` schema and `load_config` behavior are unchanged.
- acceptance: `clutch_app_config` returns current `retro` and `scheduler.parallel` fields on `get`, persists valid allowlisted updates via `checkout.fs.write` without dropping unrelated `config.yaml` keys, and refuses disallowed keys or invalid values without modifying `config.yaml`.
- tests: `tests/unit/test_mcp_ui_state_and_config.py`, `tests/unit/test_mcp_app_dashboard.py`, `tests/unit/test_mcp_tools.py`
- post-merge source of truth: clutch/mcp.py

### MCP dashboard UI layout and controls
- disposition: extend
- owner: clutch/ui/app.js
- consumers: Antigravity MCP App host rendering `ui://clutch/dashboard.html` and `tests/mcp_app_dashboard.js`
- observable change: default section stack order becomes `details`, `steps`, `tickets`, `box`, `stats`, `settings`, `help` (first three open, last four closed); boot loads persisted state via `clutch_app_ui_state({ action: "get" })` and saves via `clutch_app_ui_state({ action: "set", state })` on section toggle, reorder (`▲`/`▼` or drag-and-drop), resize end, or UI setting change; periodic `setInterval` polls `refresh()` every `refreshSeconds` (default `15`, `0` disables, skips overlapping in-flight refreshes); Agent Actions renames `"Diagnose Stem"` to `"Diagnose Ticket"` and `"New conversation "` to `"Run in new chat "` with explanatory `title`; Suggestion Box gains `"Bulk Triage"` button when pending box items > 0 and `"Ask Agent: discuss"` context menu item; Recent Steps `.step-row` elements render children in `[icon, .step-time, .step-stem, .step-text]` order with normal-weight `.step-stem`, compact `22px` row density, full opacity on `:disabled` rows, outline play/stop/rocket icons for `engine_start` (`passed`), `engine_stop` (`failed`), and `preflight`, and semantic outcome classes (`step-muted`, `step-passed`, `step-failed`, `step-warning`) so icon, `.step-time`, and `.step-stem` share the outcome color while `.step-text` is faded (`var(--vscode-descriptionForeground)`); new `"Settings"` section renders UI preferences and `config.yaml` retro/parallel controls plus `Save config.yaml` and `Open config.yaml` buttons.
- compatibility: preserves all existing ticket, detail, steps, stats, and help interactions; keeps both `Drain` and `Serve` start buttons when stopped while ordering the configured `playAction` first.
- acceptance: verified end-to-end against the built single-file bundle by `tests/integration/test_mcp_app_dashboard.py` and `tests/mcp_app_dashboard.js`.
- tests: `tests/mcp_app_dashboard.js`, `tests/integration/test_mcp_app_dashboard.py`
- post-merge source of truth: clutch/ui/app.js

## Scope in / Scope out

### Scope in
- `clutch/mcp.py`:
  - Import `yaml` and `Config` (and `_check_references` or `load_config_text`) from `clutch.config`.
  - Add `ui_state_path: Path | None = None` to `ClutchMCPServer.__init__`, defaulting to `(Path(self.env["XDG_CONFIG_HOME"]) if self.env.get("XDG_CONFIG_HOME") else Path.home() / ".config") / "clutch" / "dashboard-state.json"`.
  - Add Pydantic request models `UiState(Repo)` (`action: Literal["get", "set"]`, `state: dict[str, object] | None = None`) and `AppConfig(Repo)` (`action: Literal["get", "set"]`, `updates: dict[str, object] | None = None`).
  - Register `"clutch_app_ui_state": UiState` and `"clutch_app_config": AppConfig` in `TOOLS` (both automatically receive `_meta: {"ui": {"visibility": ["app"]}}` via the `clutch_app_` prefix rule in `tools/list`).
  - Handle `clutch_app_ui_state` in `call_tool` before `self.checkout(args.repo)` so it works even when no checkout is active. Read/write JSON `{order, open, heights, refreshSeconds, statsWindow, playAction}` with schema defaults, best-effort `OSError` handling on read and write, and fallback to defaults on missing or corrupt JSON.
  - Handle `clutch_app_config` in `call_tool` after `self.checkout(args.repo)`. On `get`, return `{retro: {enabled, merges: {enabled, every}, settled: {enabled, every}, spikes: {enabled, count}}, scheduler: {parallel: {enabled, max_runs}}}` from `checkout.config`. On `set`, read `ctx.config_path` via `yaml.safe_load`, apply only the allowlisted `retro.*` and `scheduler.parallel.*` keys (refusing any other key or malformed `updates` with `runner.Refusal(..., code="invalid_config")`), validate the resulting dict with `Config.model_validate(raw, context={"base": ctx.config_path.parent})` and `clutch.config._check_references(ctx.config_path, cfg)` (or `load_config_text`, which invokes both and rejects `retro.enabled: true` when all three retro triggers are disabled, while `Count` enforces `ge=1` on `every`, `count`, and `max_runs`), failing closed with `runner.Refusal(..., code="invalid_config")` without writing on any `ValidationError` or `ConfigError`, write back via `checkout.fs.write(ctx.config_path, ...)`, and return the updated structured config values.
- `clutch/ui/app.js`:
  - Change default section creation order to: `details` ("Details", open: true), `steps` ("Recent Steps", open: true), `tickets` ("Tickets", open: true), `box` ("Suggestion Box", open: false), `stats` ("Stats", open: false), `settings` ("Settings", open: false), `help` ("Help & Lifecycle", open: false).
  - On boot after `app.connect()`, call `clutch_app_ui_state({ action: "get" })` and apply persisted `order`, `open`, `heights`, `refreshSeconds`, `statsWindow`, and `playAction` (without letting the first `refresh()` overwrite a persisted `open.box` preference; only auto-open `box` when `open.box` was not saved).
  - Persist `{order, open, heights, refreshSeconds, statsWindow, playAction}` via `clutch_app_ui_state({ action: "set", state })` whenever the user toggles a section (`toggle` event after hydration), reorders sections (`▲`/`▼` or drag-and-drop), finishes resizing a section (`pointerup`), or changes a UI setting (`refreshSeconds`, `statsWindow`, `playAction`).
  - Schedule `setInterval` polling based on `refreshSeconds` (default `15`, `0` disables polling; clear/reset timer on change; guard `refresh()` so overlapping refreshes skip when one is already in flight).
  - Order the stopped-engine play buttons according to `playAction` (`drain` first when `"drain"`, `serve` first when `"serve"`) while keeping both buttons available.
  - Rename Agent Actions `"Diagnose Stem"` to `"Diagnose Ticket"` and `"New conversation "` checkbox label to `"Run in new chat "` with `title="When checked, sends the action to a new background Antigravity conversation instead of the current chat."`.
  - In Suggestion Box: add `"Bulk Triage"` button when `(snap.boxCounts?.pending ?? 0) > 0` calling `mutate("clutch_box_triage", { ids: [] })`; add `"Ask Agent: discuss"` in `boxContext` when `app.getHostCapabilities()?.message` calling `sendPrompt("box", ids)`.
  - In `shapes`, `stepIcons`, and `stepRow(step)`:
    - Map `engine_start` to color `"passed"` (green) with outline play triangle path `M4 2v12l9-6L4 2zm1.5 2.7L10.4 8l-4.9 3.3V4.7z`, `engine_stop` to color `"failed"` (red) with outline stop square path `M3 3h10v10H3V3zm1.5 1.5v7h7v-7h-7z`, and `engine_lost` to color `"warning"` (amber).
    - Update `shapes.preflight` to a rocket SVG path (matching VS Code's `rocket` Codicon).
    - Render `stepRow(step)` children in order `[icon, .step-time, .step-stem (when step.stem is present), .step-text]` and attach a semantic outcome class on `.step-row` matching the step's color token (`step-muted`, `step-passed`, `step-failed`, `step-warning`, with unknown step kinds using `step-warning`).
  - Render the `"Settings"` section with labeled controls for UI preferences (`Refresh seconds`, `Stats window`, `Default play action`) and repo `config.yaml` settings (`Retro enabled`, `Retro merges enabled` + `every`, `Retro settled enabled` + `every`, `Retro spikes enabled` + `count`, `Parallel enabled` + `max runs`), plus `Save config.yaml` (calling `clutch_app_config({ action: "set", updates })`) and `Open config.yaml` (calling `openFile(snap?.configPath)`). Populate config inputs from `clutch_app_config({ action: "get" })` during `refresh()`.
- `clutch/ui/dashboard.css`:
  - Update Recent Steps row styling: add `.step-row:disabled { opacity: 1; cursor: default; }` so non-clickable step rows (`Preflight`, `serve started`, `serve stopped`) are not dimmed by `button:disabled { opacity: .5; }`; remove `font-weight: bold` from `.step-stem`; remove `margin-left: auto` from `.step-time`; remove `.step-time` from the muted `var(--vscode-descriptionForeground)` selector so `.step-time` inherits the row's outcome color; set `.step-text` to `color: var(--vscode-descriptionForeground);`; keep compact `22px` row density on `.step-row`; and add semantic outcome color rules for `.step-row.step-muted` (`color: var(--vscode-foreground);`), `.step-row.step-passed` (`color: var(--clutch-icon-passed);`), `.step-row.step-failed` (`color: var(--clutch-icon-failed);`), and `.step-row.step-warning` (`color: var(--clutch-icon-warning);`).
  - Add clean layout rules for the Settings section controls (`.settings-group`, `.settings-row`, inline checkbox/number/select alignment).
- Tests:
  - Create `tests/unit/test_mcp_ui_state_and_config.py` covering `clutch_app_ui_state` (defaults on missing/corrupt file, get/set round-trip, `OSError` swallowed on read/write, works without a checkout) and `clutch_app_config` (`get` structure, `set` allowlisted update preserving unrelated keys, refusal on disallowed key, refusal on invalid value / invalid retro trigger combination without modifying `config.yaml`).
  - Update `tests/unit/test_mcp_app_dashboard.py` (update tool count `26 -> 28`, check `_meta` on `clutch_app_ui_state` and `clutch_app_config`, pass `ui_state_path=tmp_path / "ui-state.json"`).
  - Update `tests/unit/test_mcp_tools.py` (add `"clutch_app_ui_state"` and `"clutch_app_config"` to the expected `tools/list` name set, pass `ui_state_path=tmp_path / "ui-state.json"`).
  - Update `tests/unit/test_mcp_repo_resolution.py` (pass `ui_state_path=tmp_path / "ui-state.json"` when constructing `ClutchMCPServer` / `serve_stdio`).
  - Update `tests/mcp_app_dashboard.js` and `tests/integration/test_mcp_app_dashboard.py` to verify default section order (`details, steps, tickets, box, stats, settings, help`), layout persistence (`clutch_app_ui_state` get on boot and set on toggle/reorder/resize/settings change), `"Diagnose Ticket"` and `"Run in new chat "` with tooltip, `"Bulk Triage"` and `"Ask Agent: discuss"`, Recent Steps child order (`icon`, `.step-time`, `.step-stem`, `.step-text`), `.step-row.step-passed` (including `engine_start`), `.step-row.step-failed` (including `engine_stop`), `.step-row.step-muted`, and `.step-row.step-warning` classes, `.step-row:disabled { opacity: 1` in `dashboard.css`, non-bold `.step-stem`, `.step-time` without `margin-left: auto`, and `.step-text` muted color in `dashboard.css`, Settings controls calling `clutch_app_config`, and `refreshSeconds` polling timer (schedule, skip overlap, reset on change, disable at `0`).

### Scope out
- Changes to `vscode-clutchwork/` (VS Code extension).
- Exposing other `config.yaml` sections beyond `retro.*` and `scheduler.parallel.*` in `clutch_app_config`.
- Changing `Dashboard.tab` or adding new model-visible MCP tools.
- Editing any of the 7 hot integration test files.

## Scope fence
- clutch/mcp.py
- clutch/ui/app.js
- clutch/ui/dashboard.css
- tests/mcp_app_dashboard.js
- tests/integration/test_mcp_app_dashboard.py
- tests/unit/test_mcp_app_dashboard.py
- tests/unit/test_mcp_tools.py
- tests/unit/test_mcp_repo_resolution.py
- tests/unit/test_mcp_ui_state_and_config.py

## Acceptance criteria
1. `clutch_app_ui_state` is registered as an app-only tool (`_meta == {"ui": {"visibility": ["app"]}}`), works without an active checkout, returns defaults `{order, open, heights, refreshSeconds: 15, statsWindow: "7d", playAction: "drain"}` when `ui_state_path` is missing or contains invalid JSON (not raising an error), round-trips `set` -> `get` to `ui_state_path`, and swallows `OSError` on read/write; verified by `./dev.py test tests/unit/test_mcp_ui_state_and_config.py tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_tools.py`.
2. `clutch_app_config` is registered as an app-only tool (`_meta == {"ui": {"visibility": ["app"]}}`), returns current `retro` (`enabled`, `merges.enabled`, `merges.every`, `settled.enabled`, `settled.every`, `spikes.enabled`, `spikes.count`) and `scheduler.parallel` (`enabled`, `max_runs`) values on `get`, applies only allowlisted keys on `set` while preserving unrelated `config.yaml` keys, and returns an error (`isError: True`, `Refusal`) without modifying `config.yaml` when given a non-allowlisted key or an invalid value (such as `max_runs: 0` refused by `Count` `ge=1`, or `retro.enabled: true` with all triggers disabled refused by `clutch/config.py::_check_references`); verified by `./dev.py test tests/unit/test_mcp_ui_state_and_config.py`.
3. Unit tests constructing `ClutchMCPServer` in `tests/unit/test_mcp_app_dashboard.py`, `tests/unit/test_mcp_tools.py`, `tests/unit/test_mcp_repo_resolution.py`, and `tests/unit/test_mcp_ui_state_and_config.py` pass `ui_state_path` under `tmp_path` so unit tests never read or write `~/.config/clutch/dashboard-state.json`; verified by `./dev.py test tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_repo_resolution.py tests/unit/test_mcp_ui_state_and_config.py`.
4. The built MCP dashboard bundle renders sections in default order `details`, `steps`, `tickets`, `box`, `stats`, `settings`, `help` (not `tickets` first), with `details`, `steps`, `tickets` open and `box`, `stats`, `settings`, `help` closed; loads saved layout via `clutch_app_ui_state({ action: "get" })` on boot and persists via `clutch_app_ui_state({ action: "set", state })` on section toggle, reorder (`▲`/`▼` and drag-and-drop), resize end, and UI preference change; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
5. The dashboard schedules periodic `refresh()` polling at `refreshSeconds * 1000` ms (default `15`), skips overlapping refreshes when one is already in flight, resets the timer when `refreshSeconds` changes, and clears polling when `refreshSeconds` is `0`; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
6. Agent Actions labels `"Diagnose Ticket"` (not `"Diagnose Stem"`) and `"Run in new chat "` (not `"New conversation "`) with `title="When checked, sends the action to a new background Antigravity conversation instead of the current chat."`; Suggestion Box shows `"Bulk Triage"` when pending box items > 0 (calling `clutch_box_triage` with `ids: []`) and `"Ask Agent: discuss"` in its context menu (calling `clutch_prompt` with `kind: "box"` and `stems: ids`); and the `"Settings"` section renders UI preference controls plus `config.yaml` retro/parallel controls with `Save config.yaml` (calling `clutch_app_config({ action: "set", updates })`) and `Open config.yaml`; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
7. Recent Steps `.step-row` elements render children in `[icon, .step-time, .step-stem, .step-text]` order (with `.step-time` immediately after the icon, not right-aligned at the end), carry the semantic outcome class (`step-muted` for non-engine `*_start`, `step-passed` for `*_ok` and `engine_start`, `step-failed` for `*_failed` and `engine_stop`, and `step-warning` for `engine_lost`/unknown — not plain `.step-row` without an outcome class, and not `step-muted` for `engine_start`/`engine_stop`), use outline play/stop paths for `engine_start`/`engine_stop` and a rocket path for `preflight`, and `clutch/ui/dashboard.css` defines `.step-row:disabled { opacity: 1; cursor: default; }`, `.step-row.step-muted`, `.step-row.step-passed`, `.step-row.step-failed`, and `.step-row.step-warning` color rules, omits `font-weight: bold` on `.step-stem` and `margin-left: auto` on `.step-time`, lets `.step-time` inherit the row color, and sets `.step-text` to `var(--vscode-descriptionForeground)`; verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.

## Verification
```
./dev.py test tests/unit/test_mcp_ui_state_and_config.py tests/unit/test_mcp_app_dashboard.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_repo_resolution.py tests/unit/test_mcp_control_and_tickets.py tests/integration/test_mcp_app_dashboard.py
```

## Definition of rejected
- Any unit test reads or writes `~/.config/clutch/dashboard-state.json` instead of an isolated `tmp_path` file.
- `clutch_app_config` writes to `config.yaml` when given a non-allowlisted key or an invalid config value, or drops unrelated keys from `config.yaml`.
- `clutch_app_ui_state` fails with `invalid_repo` when no checkout is active, or exposes either new tool to the model instead of `visibility: ["app"]`.
- Reopening the dashboard with persisted `clutch_app_ui_state` loses saved section order, expanded/collapsed state, heights, or UI preferences.
- Any of the 7 hot integration test files is modified.

## Time budget
- expected: 20m
- stuck: 40m
- reason: server tools (`clutch_app_ui_state`, `clutch_app_config`) and dashboard UI layout/settings wiring share one contract and are verified together against the built single-file bundle in `tests/integration/test_mcp_app_dashboard.py`
