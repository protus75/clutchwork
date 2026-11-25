---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- docs/roadmap.md#Status
- docs/roadmap.md#1. Release plan
- docs/roadmap.md#2. Analysis: duplication
- docs/roadmap.md#3. Analysis: gaps
- docs/roadmap.md#4. Analysis: drift
- docs/roadmap.md#0.7.0
- docs/roadmap.md#9. Keeping this document true
- clutch/roadmap.py::gates
- clutch/mcp.py::ClutchMCPServer.dispatch
- clutch/antigravity.py::install_plugin
- clutch/antigravity.py::doctor_finding
- clutch/__main__.py::_parser
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks
- tests/unit/test_main_mcp_serve.py::test_serve_before_config

## On-demand
- clutch/docs/host-running.md
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 231 (`release-audit-070`). At the end of 0.7.0, `docs/roadmap.md` sections 2-4 still describe the code as of the 0.5.0 audit, and the 0.7.0 `gate` block checks neither clause of the 0.7.0 ship gate in section 1 (`clutch mcp serve` serves the Antigravity dashboard resource and read/control tools; `clutch host antigravity` installs the plugin and supervising skills). Neither existing verb has a non-blocking gate check: `clutch mcp serve` blocks on stdio without exercising `resources/read` or `tools/list`, and `clutch host antigravity` writes files without verifying the installed manifest, MCP config, logo, and skills.

When this ticket is done:
- `docs/roadmap.md` sections 2-4 describe the code at this ticket's base commit: items fixed by merged work are removed, items still true are marked "recurred in 0.7.0", and `## Status` updates its commit hash and counts where re-measured. (`0.8.0` already carries row 200 `release-audit-080`, so no duplicate audit row is added there.)
- `clutch mcp serve --check` runs a non-blocking check via `clutch/mcp.py::check_server` that exercises `ClutchMCPServer.dispatch("tools/list", {})` and `ClutchMCPServer.dispatch("resources/read", {"uri": DASHBOARD_URI})`, exiting 0 on success and 2 on refusal (for example `dashboard_unavailable` when `clutch/ui/dashboard.html` is missing or empty).
- `clutch host antigravity --verify` installs the plugin via `clutch/antigravity.py::install_plugin` and then checks the written output via `clutch/antigravity.py::verify_plugin` (`plugin.json`, `mcp_config.json` via `doctor_finding`, non-empty `assets/logo.png`, and every skill in `SKILLS`), exiting 0 on success and 2 on refusal.
- The 0.7.0 `gate` block in `docs/roadmap.md` runs both commands (`uv run clutch mcp serve --check` and `uv run clutch host antigravity --plugin-dir .clutch/antigravity-gate --verify`) between `uv run clutch roadmap merged --release 0.7.0` and `./dev.py test`.

Honest limit: `clutch/ui/dashboard.html` is gitignored until built (or packaged by row 229 `mcp-dashboard-in-wheel`), so `uv run clutch mcp serve --check` exits 2 with `dashboard_unavailable` in a checkout where the bundle has not been built yet. That is the ship clause's meaning, not a defect.

## Boundary contract
### MCP server check flag
- disposition: extend
- owner: clutch/__main__.py (`mcp serve` parser and dispatch) and clutch/mcp.py (`check_server`)
- consumers: the 0.7.0 `gate` block via `clutch roadmap gate 0.7.0`, operators verifying an MCP server installation
- observable change: new optional flag `--check` on `clutch mcp serve` (default false); when set, calls `clutch.mcp.check_server` to verify `tools/list` includes `clutch_open_dashboard` and `resources/read` returns `DASHBOARD_URI` with `MCP_APP_MIME` and non-empty text, printing one summary line and exiting 0, or exiting 2 with a refusal on failure without reading stdin
- compatibility: `clutch mcp serve` without `--check` keeps identical stdio behavior, arguments, and exit codes
- acceptance: criteria 1 and 4
- tests: new `tests/unit/test_release_audit_070_gates.py`
- post-merge source of truth: clutch/__main__.py and clutch/mcp.py

### Antigravity plugin install verification flag
- disposition: extend
- owner: clutch/__main__.py (`host antigravity` parser and `handle_antigravity`) and clutch/antigravity.py (`verify_plugin`)
- consumers: the 0.7.0 `gate` block via `clutch roadmap gate 0.7.0`, operators verifying plugin installation
- observable change: new optional flag `--verify` on `clutch host antigravity` (default false); incompatible with `--workspace` (exit 2); when set, runs `install_plugin` and then `verify_plugin` over the target directory, exiting 0 when `plugin.json`, `mcp_config.json` (checked by `doctor_finding`), `assets/logo.png`, and every `SKILLS` entry are valid and non-empty, or exiting 2 with a refusal naming each finding
- compatibility: `clutch host antigravity` without `--verify` keeps identical behavior, outputs, and exit codes
- acceptance: criteria 2 and 4
- tests: new `tests/unit/test_release_audit_070_gates.py`
- post-merge source of truth: clutch/__main__.py and clutch/antigravity.py

### 0.7.0 ship gate block
- disposition: extend
- owner: docs/roadmap.md (`### 0.7.0` `gate` block, parsed by `clutch/roadmap.py::gates`)
- consumers: `clutch roadmap gate 0.7.0`, `clutch roadmap status`, the roadmap driver
- observable change: adds `uv run clutch mcp serve --check` and `uv run clutch host antigravity --plugin-dir .clutch/antigravity-gate --verify` between `uv run clutch roadmap merged --release 0.7.0` and `./dev.py test`, and updates `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks` to exempt `0.6.0` and `0.7.0` from the three-command length check
- compatibility: first, second-to-last (`./dev.py test`), and last (`roadmap accept 0.7.0`) commands keep their positions; other releases' gate blocks are unchanged
- acceptance: criteria 3 and 5
- tests: updated `tests/integration/test_roadmap_gate.py`
- post-merge source of truth: docs/roadmap.md

## Scope in / Scope out
In:
- `clutch/mcp.py`: add `check_server(server: ClutchMCPServer) -> dict[str, object]` that calls `server.dispatch("tools/list", {})` (requiring non-empty `tools` containing `"clutch_open_dashboard"`) and `server.dispatch("resources/read", {"uri": DASHBOARD_URI})` (requiring a content item with `uri == DASHBOARD_URI`, `mimeType == MCP_APP_MIME`, and non-empty `text`), raising `runner.Refusal` on any missing tool, invalid content, or `DomainError`.
- `clutch/antigravity.py`: add `verify_plugin(plugin_dir: Path, *, fs: FileSystem, dir_exists=None, executable_exists=None) -> list[str]` returning a list of failure strings (empty when valid) checking `plugin.json` (JSON object with `name == PLUGIN_NAME`, non-empty `version`, `logo == "assets/logo.png"`, non-empty `suggestedPrompts`), `doctor_finding(plugin_dir, fs=fs, dir_exists=dir_exists, executable_exists=executable_exists) is None`, non-empty `assets/logo.png`, and non-empty `skills/<name>/SKILL.md` for every key in `SKILLS`.
- `clutch/__main__.py`:
  - Add `--check` (`action="store_true"`) to the `mcp serve` parser; in the `args.verb == "mcp"` branch, when `args.check` is true, instantiate `ClutchMCPServer(default_cwd=repo, config_path=args.config, env=env, clock=clock)`, call `mcp.check_server(server)`, print a one-line summary, and return 0 (or return `_fail("mcp serve", ...)` with exit 2 on `runner.Refusal`); update `mcp serve` help (`does`, `exits`, `examples`).
  - Add `--verify` (`action="store_true"`) to the `host antigravity` parser; in `handle_antigravity`, refuse `--verify` combined with `--workspace` (exit 2), and when `args.verify` is true call `antigravity.verify_plugin(target, fs=fs)` after `install_plugin`, raising `runner.Refusal` (exit 2) if findings are non-empty; update `host antigravity` help (`does`, `exits`, `examples`).
- `docs/roadmap.md`:
  - Re-run the six read-only audit passes of sections 2-4 at the base commit: remove items fixed by merged work, mark recurring items `"recurred in 0.7.0"`, and update `## Status` commit hash and counts where re-measured.
  - In `### 0.7.0`'s `gate` block, insert `uv run clutch mcp serve --check` and `uv run clutch host antigravity --plugin-dir .clutch/antigravity-gate --verify` after `uv run clutch roadmap merged --release 0.7.0` and before `./dev.py test`. Keep `./dev.py test` second-to-last and `uv run clutch roadmap accept 0.7.0` last.
  - Do not strike row 231 (the driver strikes it on merge), and do not add a duplicate audit row to `0.8.0` (row 200 `release-audit-080` already exists).
- `clutch/docs/host-running.md` and `docs/how-clutch-works.md`: update only the `mcp serve` and `host antigravity` rows in the verb tables to document `--check` and `--verify`.
- `tests/integration/test_roadmap_gate.py`: in `test_real_roadmap_gate_blocks` only, widen `if release not in ("0.4.0", "0.5.0"):` to `if release not in ("0.4.0", "0.5.0", "0.6.0", "0.7.0"):`; leave all other lines unchanged.
- `tests/unit/test_release_audit_070_gates.py`: new unit test module using `tmp_path` and in-memory fakes only covering `mcp.check_server`, `main(["mcp", "serve", "--check"])`, `antigravity.verify_plugin`, and `main(["host", "antigravity", "--plugin-dir", ..., "--verify"])`.

Out:
- Fixing code or doc drift discovered during the sections 2-4 audit; file each finding with `clutch box suggest` instead of folding it into this diff.
- Editing `CLUTCH_PLAN.md`, other plan documents under `docs/`, section 9, or any roadmap row other than sections 2-4, `## Status`, and the 0.7.0 `gate` block.
- Renumbering roadmap rows or striking row 231.
- Adding a standing test pinning roadmap row text or exact gate-block commands.
- Building or packaging `clutch/ui/dashboard.html` (owned by row 229 `mcp-dashboard-in-wheel`).

## Scope fence
- clutch/mcp.py
- clutch/antigravity.py
- clutch/__main__.py
- docs/roadmap.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/integration/test_roadmap_gate.py
- tests/unit/test_release_audit_070_gates.py

## Acceptance criteria
1. `clutch/mcp.py::check_server` and `main(["mcp", "serve", "--check"])` return 0 without calling `serve_stdio` when `ui_html_path` is a non-empty HTML file and `tools/list` includes `clutch_open_dashboard`, and return 2 (not 0) when `ui_html_path` is missing or empty (`dashboard_unavailable`) or `clutch_open_dashboard` is absent; `main(["mcp", "serve"])` without `--check` still invokes `serve_stdio`. Checked by `./dev.py test tests/unit/test_release_audit_070_gates.py tests/unit/test_main_mcp_serve.py`.
2. `clutch/antigravity.py::verify_plugin` returns `[]` for a valid `install_plugin` directory and non-empty findings (not `[]`) when `plugin.json`, `mcp_config.json`, `assets/logo.png`, or any `SKILLS` file is missing, empty, or invalid; `main(["host", "antigravity", "--plugin-dir", ..., "--verify"])` returns 0 on valid install and 2 (not 0) on verification failure or when combined with `--workspace`. Checked by `./dev.py test tests/unit/test_release_audit_070_gates.py tests/unit/test_antigravity_plugin.py`.
3. `clutch.roadmap.gates(text)["0.7.0"]` parses with `uv run clutch roadmap merged --release 0.7.0` first, `uv run clutch mcp serve --check` and `uv run clutch host antigravity --plugin-dir .clutch/antigravity-gate --verify` in the middle, `./dev.py test` second-to-last (once), and `uv run clutch roadmap accept 0.7.0` last, and every `uv run clutch` command parses via `cli._parser().parse_args`. Checked by `./dev.py test tests/integration/test_roadmap_gate.py tests/integration/test_roadmap_table.py`.
4. CLI help and examples for `mcp serve` and `host antigravity` name `--check` and `--verify` and parse cleanly, and the `mcp serve` and `host antigravity` rows in `clutch/docs/host-running.md` and `docs/how-clutch-works.md` name them. Checked by `./dev.py test tests/unit/test_main_help.py` and reviewer inspection of `git diff main...HEAD -- clutch/docs/host-running.md docs/how-clutch-works.md`.
5. Every item remaining in `docs/roadmap.md` sections 2-4 is confirmed true at the base commit and marked `"recurred in 0.7.0"` where it recurred, and no item is removed unless merged work fixed it; `docs/roadmap.md` parses cleanly with unique numbers and stems. Checked by reviewer inspection of `git diff main...HEAD -- docs/roadmap.md` and `./dev.py test tests/integration/test_roadmap_table.py tests/unit/test_roadmap_table.py`.

## Verification
```
./dev.py test tests/unit/test_release_audit_070_gates.py tests/unit/test_main_mcp_serve.py tests/unit/test_antigravity_plugin.py tests/unit/test_main_help.py tests/unit/test_roadmap_table.py tests/integration/test_roadmap_gate.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
The branch is thrown away if it edits any file outside the fence, breaks `clutch mcp serve` or `clutch host antigravity` without the new flags, lets `--check` or `--verify` exit 0 on a missing dashboard or broken plugin output, strikes row 231, renumbers roadmap rows, edits another plan or `CLUTCH_PLAN.md`, adds a standing test pinning roadmap row or gate text, changes `test_roadmap_gate.py` beyond exempting `0.6.0` and `0.7.0`, or removes a sections 2-4 audit item without a merged change that fixed it.

## Time budget
- expected: 30m
- stuck: 60m
