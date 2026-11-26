---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/mcp.py::ClutchMCPServer
- clutch/antigravity.py
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/ui/app.js
- tests/unit/test_mcp_repo_resolution.py
- tests/unit/test_antigravity_plugin.py
- tests/unit/test_antigravity_bundle.py
- tests/mcp_app_dashboard.js

## Goal / Why
Make the ClutchWork MCP server and dashboard automatically follow the user's active Antigravity workspace when switching projects, without manual repository switching.

Antigravity runs one global `clutch mcp serve` process and does not emit MCP `roots/list_changed` notifications or workspace paths in `hostContext`. It does run plugin lifecycle hooks from `hooks.json` (`SessionStart` and `PreInvocation`), passing `workspacePaths` and `cwd` as JSON on stdin. At the same time, `ClutchMCPServer.default_repo()` currently caches `self.last_repo` after the first read and places `self.cwd` ahead of `last-repo`, so the running server never observes workspace switches written to `~/.config/clutch/last-repo`, and `clutch/ui/app.js` has no auto-follow selection in `.repo-select` and keeps stale ticket `focus` across repo changes.

## Boundary contract
### CLI subcommand `clutch mcp hook-repo`
- disposition: create
- closest existing: `clutch mcp serve` in `clutch/__main__.py` and `ClutchMCPServer.checkout` in `clutch/mcp.py`; `mcp serve` speaks stdio JSON-RPC for the long-lived server and `checkout` requires an already-resolved Clutch repo, whereas Antigravity hooks invoke a short-lived one-shot command that reads hook JSON on stdin and must always print `{}` and exit 0
- earning reason: process boundary invoked by Antigravity `SessionStart` and `PreInvocation` lifecycle hooks across both local (`clutch host antigravity`) and portable (`uvx --from clutchwork`) plugin installations
- owner: `clutch/mcp.py` (`record_active_repo_from_hook`, `default_last_repo_path`) and `clutch/__main__.py` (`mcp hook-repo` subcommand)
- consumers: Antigravity plugin `hooks.json` (`SessionStart` and `PreInvocation`) and `ClutchMCPServer.default_repo()`
- observable change: reads JSON from stdin, inspects `workspacePaths` (list of strings) then `cwd` (string), resolves the first existing directory containing `tickets/`, atomically writes `f"{resolved}\n"` to `last_repo_path` (`~/.config/clutch/last-repo`, honoring `XDG_CONFIG_HOME`) only when the stored stripped value differs, fails soft on invalid/empty JSON, missing Clutch repos, or I/O errors, prints `{}` to stdout, and exits 0
- compatibility: additive subcommand under the existing `mcp` group; `clutch mcp serve` and `clutch mcp serve --check` are unchanged
- acceptance: `clutch mcp hook-repo` updates `last-repo` for valid Clutch workspaces, skips redundant writes when unchanged, ignores non-Clutch directories and malformed JSON, and always prints `{}` with exit 0
- tests: unit tests in `tests/unit/test_mcp_auto_project.py` covering hook JSON parsing, write deduplication, fail-soft error handling, and CLI dispatch
- post-merge source of truth: `clutch/mcp.py` and `clutch/__main__.py`

### MCP default repository resolution
- disposition: replace
- owner: `clutch/mcp.py` (`ClutchMCPServer.default_repo`)
- consumers: all `ClutchMCPServer` tools and prompts invoked without an explicit `repo` argument, including the dashboard's `clutch_app_snapshot` and `clutch_open_dashboard`
- observable change: `ClutchMCPServer.default_repo()` re-reads `self.last_repo_path` on every call (removing the stale `self.last_repo` cache) and resolves the first valid directory containing `tickets/` in order `[*self.roots, remembered_last_repo, self.cwd]`
- compatibility: replaces the old `[*self.roots, self.cwd, self.last_repo]` precedence and cached `self.last_repo` attribute; `tests/unit/test_mcp_repo_resolution.py` is updated in the same change and no other consumer relies on `cwd` beating `last-repo`
- acceptance: updating `last_repo_path` on disk while a `ClutchMCPServer` instance is alive immediately changes `default_repo()`, while MCP client `roots` still take highest precedence and `cwd` remains the fallback when `last-repo` is absent or invalid
- tests: unit tests in `tests/unit/test_mcp_repo_resolution.py` and `tests/unit/test_mcp_auto_project.py`
- post-merge source of truth: `clutch/mcp.py`

### Antigravity plugin bundle (`hooks.json`)
- disposition: extend
- owner: `clutch/antigravity.py` (`hooks_config`, `portable_hooks_config`, `install_plugin`, `portable_bundle_files`, `verify_plugin`) and committed `hooks.json`
- consumers: `clutch host antigravity [--verify]`, `clutch release bump`, `agy plugin install`, and Antigravity's plugin hook loader
- observable change: plugin installation and the portable bundle include `hooks.json` defining `"clutch-active-repo"` for `"SessionStart"` and `"PreInvocation"` with `[{"type": "command", "command": ..., "timeout": 5}]` (using `shlex.quote(str(executable or sys.executable)) + " -m clutch mcp hook-repo"` locally and `"uvx --from clutchwork clutch mcp hook-repo"` in the portable bundle); `verify_plugin()` validates `hooks.json`
- compatibility: extends the existing plugin file set; committed root `hooks.json`, `tests/unit/test_antigravity_plugin.py`, and `tests/unit/test_antigravity_bundle.py` are updated in the same change
- acceptance: `install_plugin` and `portable_bundle_files` emit valid `hooks.json`, root `hooks.json` matches `portable_bundle_files`, and `verify_plugin` rejects missing, empty, or malformed `hooks.json`
- tests: unit tests in `tests/unit/test_mcp_auto_project.py`, `tests/unit/test_antigravity_plugin.py`, `tests/unit/test_antigravity_bundle.py`, and integration test `tests/integration/test_antigravity_bundle.py`
- post-merge source of truth: `clutch/antigravity.py` and `hooks.json`

### MCP dashboard auto-follow selector
- disposition: extend
- owner: `clutch/ui/app.js`
- consumers: Antigravity MCP App dashboard (`ui://clutch/dashboard.html`)
- observable change: `.repo-select` includes an auto-follow option (`value=""`, label `Auto: <basename>` when a repo is active or `Auto (active project)` otherwise) selected whenever `explicitRepo === ""`, omits `repo` on tool calls in auto mode so `refresh()` follows `default_repo()` live, clears `focus` when `snap.root` changes between refreshes, pins `explicitRepo` when a specific repo is selected, and returns to auto-follow when `""` is selected
- compatibility: extends `.repo-select` options by inserting the Auto option at index 0; `tests/mcp_app_dashboard.js` is updated in the same change
- acceptance: dashboard defaults to Auto mode without sending `repo`, switches cleanly and clears stale `focus` when `snap.root` changes, pins on explicit selection, and resumes auto-follow when Auto is reselected
- tests: Node dashboard harness `tests/mcp_app_dashboard.js` run by `tests/integration/test_mcp_app_dashboard.py`
- post-merge source of truth: `clutch/ui/app.js`

## Scope in / Scope out
Scope in:
- `clutch/mcp.py`:
  - Add `default_last_repo_path(env=None) -> Path` (honoring `XDG_CONFIG_HOME`, defaulting to `~/.config/clutch/last-repo`) and reuse it in `ClutchMCPServer.__init__`.
  - Add `record_active_repo_from_hook(stdin, *, last_repo_path=None, env=None, fs=None) -> dict[str, object]`: parse JSON from `stdin` fail-soft; inspect `workspacePaths` (list of strings) then `cwd` (string); find the first existing resolved directory containing `tickets/`; read existing `last_repo_path` (ignoring `OSError`) and atomically write `f"{resolved}\n"` via `fs.write(...)` (`LocalFileSystem()` default) only if the stripped stored value differs; catch write `OSError` fail-soft; always return `{}`.
  - Update `ClutchMCPServer.default_repo()` to re-read `self.last_repo_path` on every call (removing `self.last_repo`), checking `[*self.roots, remembered_last_repo, self.cwd]` and returning the first existing directory containing `tickets/`. Remove the unused `self.last_repo` attribute and assignment in `checkout()`.
- `clutch/__main__.py`:
  - Add `mcp hook-repo` subcommand under `mcp` using `_command` with full `summary`, `does`, `reads`, `writes`, `lock`, `exits`, and `examples`, and update the `mcp` group description/epilog to mention `hook-repo`.
  - Dispatch `clutch mcp hook-repo` before loading config: call `mcp.record_active_repo_from_hook(sys.stdin, env=env)`, print `json.dumps(result)`, and return `0`.
- `clutch/antigravity.py` and `hooks.json`:
  - Add `HOOK_NAME = "clutch-active-repo"`, `HOOK_TIMEOUT = 5`, `hooks_config(executable=None)`, and `portable_hooks_config()`, generating `{"clutch-active-repo": {"SessionStart": [{"type": "command", "command": ..., "timeout": 5}], "PreInvocation": [{"type": "command", "command": ..., "timeout": 5}]}}` using `shlex.quote(str(executable or sys.executable)) + " -m clutch mcp hook-repo"` for local installs and `"uvx --from clutchwork clutch mcp hook-repo"` for the portable bundle.
  - Write `hooks.json` in both `install_plugin()` and `portable_bundle_files()`.
  - Validate `hooks.json` in `verify_plugin()` (must parse as a JSON object containing `"clutch-active-repo"` with non-empty `"SessionStart"` and `"PreInvocation"` handler lists where every handler has `type == "command"` and a non-empty string `command` containing `"mcp hook-repo"`).
  - Commit the generated portable `hooks.json` at the repository root so `tests/integration/test_antigravity_bundle.py` passes.
- `clutch/ui/app.js`:
  - Track the previous `snap?.root` in `refresh()`; when `snap.root` changes from a non-empty previous root, reset `focus = undefined` before rendering views.
  - Add the Auto option (`value=""`, label `Auto: <basename>` when `snap.root` is set else `Auto (active project)`) as the first option in `.repo-select`, set `repoSelect.value = explicitRepo`, and let selecting `""` clear `explicitRepo = ""` and immediately call `refresh()`.
- Documentation updates for the new subcommand and hook behavior:
  - `README.md`: update `## Antigravity plugin` to include `hooks.json` in the portable plugin file list and note automatic active-project switching.
  - `docs/how-clutch-works.md`: add a `mcp hook-repo` row to the section 2 verb table.
  - `clutch/docs/host-running.md`: add a `mcp hook-repo` row to the verb table.
  - `clutch/docs/host-contract.md`: update `## Antigravity plugin` to note automatic active-project tracking via `hooks.json`.
- Tests:
  - Create `tests/unit/test_mcp_auto_project.py` with unit tests for `record_active_repo_from_hook` (`workspacePaths`, `cwd` fallback, non-Clutch directories, malformed/empty JSON, no-op when unchanged, XDG override), `ClutchMCPServer.default_repo()` live re-read and precedence, `clutch mcp hook-repo` CLI dispatch, and `antigravity` `hooks_config` / `portable_hooks_config` / `install_plugin` / `portable_bundle_files` / `verify_plugin` (including executable paths with spaces).
  - Update `tests/unit/test_mcp_repo_resolution.py` for the `roots > last-repo > cwd` precedence and removal of `self.last_repo`.
  - Update `tests/unit/test_antigravity_plugin.py` (`len(paths) == 7` and `hooks.json` assertion) and `tests/unit/test_antigravity_bundle.py` (`"hooks.json"` in `portable_bundle_files`).
  - Update `tests/mcp_app_dashboard.js` for the Auto option at index 0 of `.repo-select` and add assertions covering auto-follow mode, `snap.root` switching clearing `focus`, pinning a repo, and returning to Auto.

Scope out:
- Do not change `clutch/doctor.py` or `doctor_finding()` beyond leaving existing MCP config checks intact.
- Do not add shell scripts or shell wrappers.
- Do not add tests to hot test files (`test_cli.py`, `test_stages.py`, `test_drain.py`, etc.) or modify `tests/integration/conftest.py`.
- Do not change MCP tool schemas, MCP `roots/list` handling, or VS Code extension files.

## Scope fence
- clutch/mcp.py
- clutch/__main__.py
- clutch/antigravity.py
- hooks.json
- clutch/ui/app.js
- README.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- tests/unit/test_mcp_auto_project.py
- tests/unit/test_mcp_repo_resolution.py
- tests/unit/test_antigravity_plugin.py
- tests/unit/test_antigravity_bundle.py
- tests/mcp_app_dashboard.js

## Acceptance criteria
1. `record_active_repo_from_hook` picks the first existing directory containing `tickets/` from `workspacePaths` before `cwd`, atomically writes `f"{resolved}\n"` to `last_repo_path` only when the stored value differs, and returns `{}` without raising on invalid JSON, non-Clutch directories, or unwritable paths (ruling out crashing, overwriting with a non-Clutch dir, or rewriting identical bytes), verified by `./dev.py test tests/unit/test_mcp_auto_project.py`.
2. `clutch mcp hook-repo` runs without loading `config.yaml`, prints `{}` to stdout, exits 0, and has complete `_command` help and parseable examples under the `mcp` group (ruling out missing help fields or nonzero exit on bad stdin), verified by `./dev.py test tests/unit/test_mcp_auto_project.py tests/unit/test_main_help.py`.
3. `ClutchMCPServer.default_repo()` re-reads `self.last_repo_path` on every call with precedence `roots` > `last-repo` > `cwd`, immediately observing external updates written to `last_repo_path` while keeping client `roots` highest and `cwd` as fallback (ruling out stale caching or `cwd` shadowing `last-repo`), verified by `./dev.py test tests/unit/test_mcp_repo_resolution.py tests/unit/test_mcp_auto_project.py`.
4. `clutch/antigravity.py` emits `hooks.json` with `"clutch-active-repo"` handlers for `"SessionStart"` and `"PreInvocation"` (shell-quoting local executables with spaces and using `uvx --from clutchwork clutch mcp hook-repo` in the portable bundle), writes it in `install_plugin()` and `portable_bundle_files()`, validates it in `verify_plugin()`, and matches committed root `hooks.json` (ruling out missing/malformed `hooks.json` or bundle drift), verified by `./dev.py test tests/unit/test_mcp_auto_project.py tests/unit/test_antigravity_plugin.py tests/unit/test_antigravity_bundle.py tests/unit/test_release_audit_070_gates.py tests/integration/test_antigravity_bundle.py`.
5. The MCP dashboard `.repo-select` defaults to Auto mode (`value=""`, omitting `repo` on tool calls), clears `focus` when `snap.root` changes between refreshes, pins `explicitRepo` on explicit selection, and returns to auto-follow when Auto is reselected (ruling out sticky `explicitRepo` or stale ticket details after a repo switch), verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
6. Documentation for `mcp hook-repo` and `hooks.json` is updated in `README.md`, `docs/how-clutch-works.md`, `clutch/docs/host-running.md`, and `clutch/docs/host-contract.md`, and existing Antigravity documentation checks continue to pass, verified by `./dev.py test tests/integration/test_antigravity_plugin.py`.

## Verification
```
./dev.py test tests/unit/test_mcp_auto_project.py tests/unit/test_mcp_repo_resolution.py tests/unit/test_antigravity_plugin.py tests/unit/test_antigravity_bundle.py tests/unit/test_main_help.py tests/unit/test_main_mcp_serve.py tests/unit/test_release_audit_070_gates.py tests/unit/test_release_plugin_bundle.py tests/integration/test_antigravity_bundle.py tests/integration/test_antigravity_plugin.py tests/integration/test_mcp_app_dashboard.py
```

## Definition of rejected
- Any `clutch mcp hook-repo` failure case prints non-JSON or exits non-zero, risking blocked Antigravity turns.
- `ClutchMCPServer.default_repo()` still caches `last_repo` in memory or lets `self.cwd` shadow a valid `last_repo_path`.
- Any shell script is added or `shell=True` is introduced.
- Committed `hooks.json` disagrees with `portable_bundle_files()` or `verify_plugin()` accepts missing/corrupt `hooks.json`.
- Any file outside `## Scope fence` is modified, or existing tests fail.

## Time budget
- expected: 15m
- stuck: 30m
