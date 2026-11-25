---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- mcp-dashboard-surfaces
- ask-specs-mcp-supervision

## Context
- docs/antigravity-plan.md#6. Host and machine onboarding
- docs/antigravity-plan.md#Risks
- docs/antigravity-plan.md#Open decisions
- clutch/doctor.py
- clutch/seams.py::FileSystem
- clutch/seams.py::LocalFileSystem
- vscode-clutchwork/media/icon.svg
- tests/unit/test_main_host_group.py
- tests/unit/test_doctor_overdue.py
- tests/unit/test_main_help.py
- tests/unit/test_host_running.py
- tests/integration/test_host_onboarding_doc.py

## On-demand
- clutch/__main__.py
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- README.md

## Goal / Why
Roadmap row 225 (`host-antigravity-plugin`, `docs/antigravity-plan.md` §6, Risks #3 and #5, Open decisions #3). After `mcp-app-dashboard` and `ask-specs-mcp-supervision`, ClutchWork serves the stdio MCP server (`clutch mcp serve`), its MCP App dashboard (`ui://clutch/dashboard.html`), and MCP-first supervising specs (`drain-loop`, `plan-ticket-drain`, `plan-ticket-serve`), but operators have no supported CLI command to install the `clutchwork` Antigravity plugin or workspace skills, no packaged logo asset inside the `clutch` Python wheel, no `host doctor` drift check for the installed plugin's MCP executable, and no Antigravity onboarding documentation.

After this ticket:
- `clutch host antigravity [--plugin-dir PATH] [--workspace]` installs or refreshes the global Antigravity plugin at `~/.gemini/config/plugins/clutchwork/` (or `--plugin-dir PATH`) with `plugin.json`, `mcp_config.json` pinned to `sys.executable -m clutch mcp serve`, `assets/logo.svg` copied from Clutch's packaged `clutch/assets/logo.svg`, and three thin (<40-line) skills (`skills/clutch-drain-loop/SKILL.md`, `skills/clutch-plan-drain/SKILL.md`, `skills/clutch-plan-serve/SKILL.md`) that call `clutch_prompt` at runtime rather than duplicating process rules, and prints a refresh hint mentioning `customization://clutchwork`.
- With `--workspace`, `clutch host antigravity --workspace` writes `.agents/skills/clutch-{drain-loop,plan-drain,plan-serve}/SKILL.md` into the target checkout without touching `CLAUDE.md`, `AGENTS.md`, `routed_conduct_paths`, or `CoreDriftGate` (combining `--workspace` with `--plugin-dir` is refused).
- `clutch host doctor` checks `~/.gemini/config/plugins/clutchwork/` when it exists, verifying `mcp_config.json` matches the expected schema and its `command` executable resolves, emitting a passing `WARN antigravity:` row with paved road `clutch host antigravity` on drift and emitting nothing when absent or current.
- `clutch/docs/host-running.md`, `clutch/docs/host-contract.md`, `docs/how-clutch-works.md`, and `README.md` document `clutch host antigravity`, the Antigravity plugin workflow, and the `host doctor` drift check.

Rejected simpler approach: copying full `drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md` prose into `SKILL.md` files or referencing `vscode-clutchwork/media/icon.svg` directly from `clutch/antigravity.py`. Copying prompt prose violates `AGENTS.md` (*"Keep shipped process prompts in sync"* and *"One authoring process"*) and drifts on every spec edit; reading `vscode-clutchwork/media/icon.svg` breaks non-editable wheel installs because `pyproject.toml` packages only `clutch/`.

## Boundary contract

### Antigravity plugin and workspace skill installer
- disposition: create
- owner: clutch/antigravity.py
- closest existing: `clutch/hostfiles.py` (managed `CLAUDE.md`/`AGENTS.md` conduct block renderer), `clutch/doctor.py` (read-only setup checks)
- earning reason: named external-host plugin bundle boundary (`~/.gemini/config/plugins/clutchwork/` and `.agents/skills/`) with multiple production consumers (`clutch/__main__.py` for installation and `clutch/doctor.py` for drift inspection); `clutch/hostfiles.py` owns git-committed conduct blocks (`CoreDriftGate` / `routed_conduct_paths`) and must remain strictly scoped to `CLAUDE.md` and `AGENTS.md`.
- consumers: `clutch/__main__.py` (`host antigravity`), `clutch/doctor.py` (`check`), `tests/unit/test_antigravity_plugin.py`, `tests/integration/test_antigravity_plugin.py`
- observable change: exposes `PLUGIN_NAME`, `DISPLAY_NAME`, `MCP_SERVER_NAME`, `SUGGESTED_PROMPTS`, `SKILLS`, `DEFAULT_LOGO_PATH`, `default_plugin_dir(env)`, `plugin_manifest(version_str=None)`, `mcp_config(executable=None)`, `install_plugin(*, plugin_dir, fs, executable=None, logo_bytes=None, logo_path=DEFAULT_LOGO_PATH, version_str=None)`, `install_workspace_skills(*, repo, fs)`, and `doctor_finding(plugin_dir, *, fs=None, dir_exists=None, executable_exists=None)`. Writes all files atomically through the `FileSystem` seam, never modifies `~/.gemini/config/config.json`, `CLAUDE.md`, or `AGENTS.md`, and returns a warning string naming `clutch host antigravity` only when `plugin_dir` exists and `mcp_config.json` is missing, malformed, schema-drifted, or points to an unresolvable executable.
- compatibility: additive module; `clutch/hostfiles.py` (`CORE_TEMPLATE`, `routed_conduct_paths`, `stale_core`) is unchanged.
- acceptance: criteria 1, 2, 3, and 5
- tests: tests/unit/test_antigravity_plugin.py, tests/integration/test_antigravity_plugin.py
- post-merge source of truth: clutch/antigravity.py

### Packaged ClutchWork SVG logo asset
- disposition: create
- owner: clutch/assets/logo.svg
- closest existing: `vscode-clutchwork/media/icon.svg`
- earning reason: wheel-packaged asset boundary required so `clutch host antigravity` copies `assets/logo.svg` in installed wheels (`pyproject.toml` packages only `clutch/`, not `vscode-clutchwork/`).
- consumers: `clutch/antigravity.py` (`DEFAULT_LOGO_PATH`), `tests/integration/test_antigravity_plugin.py`
- observable change: adds `clutch/assets/logo.svg` matching `vscode-clutchwork/media/icon.svg` inside the `clutch` package.
- compatibility: `vscode-clutchwork/media/icon.svg` is untouched.
- acceptance: criterion 5
- tests: tests/integration/test_antigravity_plugin.py
- post-merge source of truth: clutch/assets/logo.svg

### CLI host antigravity subcommand
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators, `tests/unit/test_antigravity_plugin.py`, `tests/unit/test_main_help.py`, `tests/unit/test_main_host_group.py`, `tests/unit/test_host_running.py`
- observable change: adds `clutch host antigravity [--plugin-dir PATH] [--workspace]` under the `host` command group via `_command(...)` with full help and examples; runs without requiring `config.yaml` or a lock; refuses combining `--plugin-dir` with `--workspace` (exit 2) and refuses missing/blank `HOME` when neither `--plugin-dir` nor `--workspace` is set (exit 2); prints installed paths and (for plugin installs) the `[ClutchWork](customization://clutchwork)` refresh hint; updates `host` group and `host doctor` help text.
- compatibility: all existing `host` subcommands (`core`, `docs`, `doctor`) keep their exact argv, behavior, and exit codes.
- acceptance: criteria 4 and 6
- tests: tests/unit/test_antigravity_plugin.py, tests/unit/test_main_help.py, tests/unit/test_main_host_group.py, tests/unit/test_host_running.py
- post-merge source of truth: clutch/__main__.py

### Host doctor Antigravity drift warning
- disposition: extend
- owner: clutch/doctor.py
- consumers: `clutch/__main__.py` (`host doctor`), `tests/unit/test_antigravity_plugin.py`, `tests/unit/test_doctor_overdue.py`, `tests/unit/test_main_host_group.py`
- observable change: `doctor.check(...)` calls `antigravity.doctor_finding(antigravity.default_plugin_dir(env))` and appends `Check("antigravity", True, finding, warn=True)` when drifted; emits no row when `HOME` is unset, when `~/.gemini/config/plugins/clutchwork/` does not exist, or when `mcp_config.json` is valid and its executable resolves.
- compatibility: read-only check; never fails `doctor` (always `passed=True, warn=True`) and preserves exact existing rows when no Antigravity plugin is installed or when it is current.
- acceptance: criterion 3
- tests: tests/unit/test_antigravity_plugin.py, tests/unit/test_doctor_overdue.py, tests/unit/test_main_host_group.py
- post-merge source of truth: clutch/doctor.py

### Command and onboarding documentation
- disposition: extend
- owner: clutch/docs/host-running.md, clutch/docs/host-contract.md, docs/how-clutch-works.md, README.md
- consumers: operators, `tests/unit/test_host_running.py`, `tests/integration/test_help.py`, `tests/integration/test_host_onboarding_doc.py`, `tests/integration/test_antigravity_plugin.py`
- observable change: adds `| \`host antigravity\` |` row and updates `| \`host doctor\` |` row in `clutch/docs/host-running.md` and `docs/how-clutch-works.md` §2.1; adds `## Antigravity plugin` and optional `clutch host antigravity` mention in `## Onboarding a host` in `clutch/docs/host-contract.md`; adds `uv run clutch host antigravity` and `## Antigravity plugin` in `README.md`.
- compatibility: keeps `## VS Code extension`, existing `## Onboarding a host` verb ordering (and no code fences/`./dev.py`/`shell=True` in onboarding/operating sections), and all existing `clutch/help.py` heading and verb links intact.
- acceptance: criterion 6
- tests: tests/unit/test_host_running.py, tests/integration/test_help.py, tests/integration/test_host_onboarding_doc.py, tests/integration/test_antigravity_plugin.py
- post-merge source of truth: clutch/docs/host-running.md, clutch/docs/host-contract.md, docs/how-clutch-works.md, README.md

## Scope in / Scope out
In:
- `clutch/assets/logo.svg`:
  - Copy the ClutchWork SVG logo from `vscode-clutchwork/media/icon.svg` into `clutch/assets/logo.svg` so wheel installs ship the logo asset inside the `clutch` package.
- `clutch/antigravity.py`:
  - Define `PLUGIN_NAME = "clutchwork"`, `DISPLAY_NAME = "ClutchWork"`, `MCP_SERVER_NAME = "clutchwork"`, `MCP_ARGS = ("-m", "clutch", "mcp", "serve")`, `DEFAULT_LOGO_PATH = Path(__file__).parent / "assets" / "logo.svg"`, and `SUGGESTED_PROMPTS` matching the three starter prompts in `## Context` §6 (dashboard open, drain-loop supervision, and unattended serve roadmap run).
  - Define `SKILLS` for the three thin wrapper skills:
    - `clutch-drain-loop`: YAML frontmatter (`name: clutch-drain-loop`, `description: ...`), strictly under 40 lines, instructs Antigravity to call `clutch_prompt` with `kind: "drain-loop"` for the canonical spec, binds `clutch_wait_event` and `clutch_open_dashboard`, and duplicates zero process rules (no `/loop`, no copied step-by-step drain-loop rules).
    - `clutch-plan-drain`: YAML frontmatter (`name: clutch-plan-drain`, `description: ...`), strictly under 40 lines, instructs Antigravity to call `clutch_prompt` with `kind: "plan-ticket-drain"`, binds `invoke_subagent`, `clutch_wait_event`, and `clutch_open_dashboard`, and duplicates zero process rules.
    - `clutch-plan-serve`: YAML frontmatter (`name: clutch-plan-serve`, `description: ...`), strictly under 40 lines, instructs Antigravity to call `clutch_prompt` with `kind: "plan-ticket-serve"`, binds `invoke_subagent`, `clutch_wait_event`, and `clutch_open_dashboard`, and duplicates zero process rules.
  - Implement `default_plugin_dir(env: Mapping[str, str] | None = None) -> Path | None`: returns `Path(home) / ".gemini" / "config" / "plugins" / PLUGIN_NAME` when `home := (env.get("HOME") or "").strip()` is non-empty (using `os.environ` only when `env is None`), and `None` when `HOME` is unset or blank.
  - Implement `plugin_manifest(version_str: str | None = None) -> dict[str, object]`: returns Antigravity `plugin.json` dict with only documented top-level fields (`name`, `displayName`, `description`, `version`, `logo: "assets/logo.svg"`, `suggestedPrompts`).
  - Implement `mcp_config(executable: str | Path | None = None) -> dict[str, object]`: returns `{"mcpServers": {MCP_SERVER_NAME: {"command": str(executable or sys.executable), "args": list(MCP_ARGS)}}}`.
  - Implement `install_plugin(*, plugin_dir: Path, fs: FileSystem, executable: str | Path | None = None, logo_bytes: bytes | None = None, logo_path: Path = DEFAULT_LOGO_PATH, version_str: str | None = None) -> list[Path]`: writes `plugin.json`, `mcp_config.json`, `assets/logo.svg` (reading `logo_path` via `fs.read_bytes` when `logo_bytes is None`), and `skills/<name>/SKILL.md` for all three skills atomically via `fs.write`, returning sorted written paths.
  - Implement `install_workspace_skills(*, repo: Path, fs: FileSystem) -> list[Path]`: writes `<repo>/.agents/skills/<name>/SKILL.md` for all three skills atomically via `fs.write`, returning sorted written paths.
  - Implement `doctor_finding(plugin_dir: Path | None, *, fs: FileSystem | None = None, dir_exists: Callable[[Path], bool] | None = None, executable_exists: Callable[[str], bool] | None = None) -> str | None`: returns `None` if `plugin_dir is None` or `not dir_exists(plugin_dir)`; otherwise reads `plugin_dir / "mcp_config.json"` via `fs.read_bytes`, validates JSON object with `mcpServers[MCP_SERVER_NAME]` carrying a non-blank string `command` and `args == list(MCP_ARGS)`, and checks `executable_exists(command)` (defaulting to checking an executable file path via `Path(cmd).is_file() and os.access(cmd, os.X_OK)` for paths with a separator or `shutil.which(cmd)` for bare names). Returns a concise warning naming `clutch host antigravity` on any missing/invalid/drifted/unresolvable state, and `None` when valid.
- `clutch/__main__.py`:
  - Add `antigravity` subcommand under `host_sub` via `_command(...)` with `--plugin-dir` (`type=Path`, `default=None`) and `--workspace` (`action="store_true"`), plus full `summary`, `does`, `reads`, `writes`, `lock`, `exits`, and parseable `examples` (`["clutch host antigravity", "clutch host antigravity --workspace"]`).
  - Update `host` group `description` and `host doctor` `does`/`reads` help text to cover `host antigravity` and the optional Antigravity plugin drift warning.
  - Add `handle_antigravity` in `main(...)`: refuses `--plugin-dir` combined with `--workspace` (`runner.Refusal`); with `--workspace` calls `antigravity.install_workspace_skills(repo=repo, fs=LocalFileSystem())`; otherwise resolves `target = args.plugin_dir or antigravity.default_plugin_dir(env)` (refusing when `target is None` with paved road `--plugin-dir PATH` or setting `HOME`), calls `antigravity.install_plugin(plugin_dir=target, fs=LocalFileSystem())`, prints installed paths, and prints the refresh hint mentioning `[ClutchWork](customization://clutchwork)`.
  - Wire `"antigravity": handle_antigravity` into `handlers["host"]` and add `"antigravity"` to the no-config-required set `(args.verb == "host" and args.host_verb in {"docs", "doctor", "antigravity"})`.
- `clutch/doctor.py`:
  - Import `antigravity` and in `check(...)` append `Check("antigravity", True, finding, warn=True)` when `finding := antigravity.doctor_finding(antigravity.default_plugin_dir(env))` is truthy.
- `clutch/docs/host-running.md`:
  - Add `| \`host antigravity\` | Yes | Install or refresh the ClutchWork Antigravity plugin (`~/.gemini/config/plugins/clutchwork/`, or `--plugin-dir PATH`) or write workspace skills (`--workspace` -> `.agents/skills/`). |` to the verb table.
  - Update the `| \`host doctor\` |` row to mention warning when an installed Antigravity plugin's `mcp_config.json` is drifted or its executable cannot resolve.
- `clutch/docs/host-contract.md`:
  - Add `## Antigravity plugin` right after `## VS Code extension` (preserving `## VS Code extension` unchanged) documenting `clutch host antigravity [--plugin-dir PATH] [--workspace]`, `~/.gemini/config/plugins/clutchwork/`, automatic conduct-file loading via `clutch host core`, toggling `[ClutchWork](customization://clutchwork)` to reload the stdio MCP server after upgrades, and `clutch host doctor` drift detection.
  - Add an optional `clutch host antigravity` note in `## Onboarding a host` without reordering existing verbs or adding code fences, `shell=True`, or `./dev.py`.
- `docs/how-clutch-works.md`:
  - Add `| \`host antigravity [--plugin-dir PATH] [--workspace]\` | no | ... |` to §2.1 Verbs table and update the `| \`host doctor\` |` row to include the Antigravity plugin drift warning.
- `README.md`:
  - Add `uv run clutch host antigravity` to the Setup code block and add a `## Antigravity plugin` section describing global plugin setup, `--workspace` skills, and the MCP server / dashboard.
- New unit test file `tests/unit/test_antigravity_plugin.py` (uses only `tmp_path` and in-memory fakes; zero repo file reads or subprocesses): covers `default_plugin_dir`, `plugin_manifest`, `mcp_config`, `SKILLS` frontmatter / `<40`-line limit / `clutch_prompt` / Antigravity tool bindings / no `/loop`, `install_plugin` (atomic writes via `FileSystem`, pinned executable, no conduct-file or global Antigravity config writes), `install_workspace_skills`, `doctor_finding` (absent, valid, missing file, bad JSON, wrong schema/args, missing/non-executable `command`), `doctor.check` warning behavior with `env={"HOME": str(tmp_path)}` (absent/clean emit no row; drifted emits passing `WARN antigravity:` naming `clutch host antigravity`), CLI `host antigravity` dispatch (`--plugin-dir`, `--workspace`, default `HOME`, no-config-needed, refresh hint with `customization://clutchwork`, and both refusal paths), and keeps `clutch/antigravity.py` >= 90% branch coverage.
- New integration test file `tests/integration/test_antigravity_plugin.py` (reads repo files only via `Path(__file__)`; zero disk writes, zero subprocesses): verifies `clutch/assets/logo.svg` matches `vscode-clutchwork/media/icon.svg` and loads via `install_plugin` into a `FakeFileSystem`, verifies every skill's `clutch_prompt` `kind` is in `clutch.ask.KINDS` and every referenced `clutch_*` MCP tool is in `clutch.mcp.TOOLS`, and verifies `clutch/docs/host-running.md`, `clutch/docs/host-contract.md`, `docs/how-clutch-works.md`, and `README.md` document `host antigravity`.
- Engine-written `# clutch:meta` headers on newly created Python test files under `tests/` updated by Check.

Out:
- Modifying `clutch/hostfiles.py` (`CORE_TEMPLATE`, `routed_conduct_paths`, `stale_core`), `CLAUDE.md`, `AGENTS.md`, `clutch/mcp.py`, `clutch/ui/`, `clutch/specs/ask/*.md`, `clutch/help.py`, or `vscode-clutchwork/`.
- Editing `~/.gemini/config/config.json` or invoking Antigravity language-server RPCs.
- Adding tests to any of the seven hot test files (`tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`).

## Scope fence
- clutch/antigravity.py
- clutch/assets/logo.svg
- clutch/__main__.py
- clutch/doctor.py
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_antigravity_plugin.py
- tests/integration/test_antigravity_plugin.py

## Acceptance criteria
1. `tests/unit/test_antigravity_plugin.py` checks `install_plugin` writes `plugin.json` (with exact documented fields `name: "clutchwork"`, `displayName: "ClutchWork"`, `description`, `version`, `logo: "assets/logo.svg"`, and the 3 `suggestedPrompts`, ruling out unknown top-level fields or missing prompts), `mcp_config.json` (`mcpServers.clutchwork.command` pinned to the executable and `args == ["-m", "clutch", "mcp", "serve"]`, ruling out bare `"clutch"` PATH lookups or wrong args), `assets/logo.svg`, and all three skill files (`skills/clutch-drain-loop/SKILL.md`, `skills/clutch-plan-drain/SKILL.md`, `skills/clutch-plan-serve/SKILL.md`), without touching `CLAUDE.md`, `AGENTS.md`, or `config.json`. Verified by `./dev.py test tests/unit/test_antigravity_plugin.py`.
2. `tests/unit/test_antigravity_plugin.py` checks each generated `SKILL.md` starts with valid YAML frontmatter containing `name` (matching its directory) and `description`, has strictly fewer than 40 lines (ruling out bloated or duplicated process specs), instructs calling `clutch_prompt` with its exact canonical `kind` (`drain-loop`, `plan-ticket-drain`, `plan-ticket-serve`), references Antigravity's `clutch_wait_event` and `clutch_open_dashboard` (plus `invoke_subagent` in the two plan skills), and omits `/loop`; and checks `install_workspace_skills` writes only `.agents/skills/clutch-{drain-loop,plan-drain,plan-serve}/SKILL.md` under `repo`. Verified by `./dev.py test tests/unit/test_antigravity_plugin.py`.
3. `tests/unit/test_antigravity_plugin.py` checks `doctor_finding` and `doctor.check` return no `antigravity` row when `HOME` is unset, when `~/.gemini/config/plugins/clutchwork/` does not exist, or when `mcp_config.json` is valid with a resolvable executable (ruling out spurious `PASS` or `WARN` rows on clean or non-Antigravity machines), and emit a passing `Check("antigravity", True, ..., warn=True)` naming `clutch host antigravity` (ruling out `passed=False` failing `doctor` or silent pass on drift) when `mcp_config.json` is missing, invalid JSON, schema-drifted (`args` or server key mismatch), or points to a missing/non-executable `command`. Verified by `./dev.py test tests/unit/test_antigravity_plugin.py tests/unit/test_doctor_overdue.py tests/unit/test_main_host_group.py`.
4. `tests/unit/test_antigravity_plugin.py` checks `clutch host antigravity` runs without `config.yaml`, defaults to `<HOME>/.gemini/config/plugins/clutchwork/`, honors `--plugin-dir PATH` and `--workspace`, prints the `customization://clutchwork` refresh hint on plugin install, refuses `--plugin-dir` combined with `--workspace` with exit `2` (ruling out silent flag precedence), and refuses missing/blank `HOME` without `--plugin-dir` with exit `2`. Verified by `./dev.py test tests/unit/test_antigravity_plugin.py tests/unit/test_main_help.py tests/unit/test_main_host_group.py`.
5. `tests/integration/test_antigravity_plugin.py` checks `clutch/assets/logo.svg` exists, is non-empty SVG matching `vscode-clutchwork/media/icon.svg`, and loads through `install_plugin(..., logo_bytes=None)` into a `FakeFileSystem`; and checks every `clutch_prompt` `kind` in `clutch/antigravity.py` is in `clutch.ask.KINDS` and every `clutch_*` tool name in the three skills is registered in `clutch.mcp.TOOLS` (ruling out typos or unimplemented tool/prompt names). Verified by `./dev.py test tests/integration/test_antigravity_plugin.py`.
6. `clutch/docs/host-running.md`, `clutch/docs/host-contract.md`, `docs/how-clutch-works.md`, and `README.md` document `clutch host antigravity`, the Antigravity plugin and `--workspace` skills, and the `host doctor` drift warning while keeping `clutch/help.py`, the run-guide verb table, and host onboarding contracts green; `clutch/antigravity.py` meets the default 90% unit coverage floor in `test-gate.toml`. Verified by `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_antigravity_plugin.py tests/integration/test_help.py tests/integration/test_host_onboarding_doc.py tests/integration/test_antigravity_plugin.py`.

## Verification
```
./dev.py test tests/unit/test_antigravity_plugin.py tests/unit/test_main_help.py tests/unit/test_main_host_group.py tests/unit/test_host_running.py tests/unit/test_doctor_overdue.py tests/integration/test_antigravity_plugin.py tests/integration/test_help.py tests/integration/test_host_onboarding_doc.py
```

## Definition of rejected
- Any generated `SKILL.md` is 40 lines or longer, lacks YAML frontmatter (`name` and `description`), duplicates process rules from `clutch/specs/ask/*.md`, contains `/loop`, or references an unregistered `clutch_*` tool or `ask.KINDS` value.
- `mcp_config.json` relies on bare `PATH` lookup (such as `"clutch"` or `"uv"`) instead of the installing Python executable (`sys.executable -m clutch mcp serve`), or `plugin.json` includes unknown top-level keys.
- `clutch host antigravity` modifies `CLAUDE.md`, `AGENTS.md`, `routed_conduct_paths`, `CoreDriftGate`, or `~/.gemini/config/config.json`, or fails when no `config.yaml` is present.
- `clutch host doctor` fails (`passed=False`) on Antigravity drift, emits an `antigravity` row when no plugin is installed or when it is current, or reads the real user's `$HOME` when `HOME` is absent from `env`.
- Any file outside `## Scope fence` is modified, or `clutch/antigravity.py` drops below the 90% `test-gate.toml` unit coverage floor.

## Time budget
- expected: 25m
- stuck: 50m
