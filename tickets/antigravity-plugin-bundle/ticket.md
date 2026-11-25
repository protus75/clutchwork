---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- host-antigravity-plugin

## Context
- docs/antigravity-plan.md#6. Host and machine onboarding
- docs/antigravity-plan.md#Open decisions
- pyproject.toml
- tests/unit/test_readme.py

## On-demand
- README.md

## Goal / Why
Roadmap row 226 (`antigravity-plugin-bundle`, `docs/antigravity-plan.md` §6, Ticket breakdown row 9, Open decision 4). After `host-antigravity-plugin` merges, `clutch host antigravity` installs a machine-local Antigravity plugin pointing at `sys.executable`, but this repository has no committed publishable Antigravity plugin root for direct GitHub installation (`agy plugin install https://github.com/protus75/clutchwork`) or Antigravity Marketplace submission (`agy plugin validate --strict .`), `plugin_manifest()` omits Marketplace metadata (`author`, `homepage`, `repository`), and no drift test keeps a committed bundle synchronized with `clutch/antigravity.py`, `clutch/assets/logo.svg`, and `pyproject.toml`.

After this ticket:
- `clutch/antigravity.py` is the single source for both the machine-local installer and the committed portable plugin bundle: `plugin_manifest()` includes full documented Marketplace metadata (`name`, `displayName`, `version`, `description`, `author`, `homepage`, `repository`, `logo`, `suggestedPrompts`), `portable_mcp_config()` renders the portable `uvx --from clutchwork clutch mcp serve` server entry, and `portable_bundle_files()` renders the exact byte contents of all six committed bundle files.
- The repository root commits the publishable Antigravity plugin bundle (`plugin.json` synced to `pyproject.toml`'s `[project].version`, portable `mcp_config.json`, `assets/logo.svg` matching `clutch/assets/logo.svg`, and `skills/clutch-{drain-loop,plan-drain,plan-serve}/SKILL.md` matching `clutch.antigravity.SKILLS`).
- `tests/unit/test_antigravity_bundle.py` verifies the pure generator helpers and maintains >= 90% unit branch coverage on `clutch/antigravity.py`, and `tests/integration/test_antigravity_bundle.py` fails on any byte drift between the committed bundle files, `pyproject.toml`, `clutch/assets/logo.svg`, and `clutch/antigravity.py`.
- `README.md` documents direct GitHub install (`agy plugin install https://github.com/protus75/clutchwork`) and Marketplace validation (`agy plugin validate --strict .`).

Rejected simpler approach: hand-maintaining `plugin.json`, `mcp_config.json`, `assets/logo.svg`, and `skills/clutch-*/SKILL.md` at the repository root without a shared renderer or drift test. Hand-maintained copies drift from `clutch/antigravity.py`, `clutch/assets/logo.svg`, and `pyproject.toml` on the next skill or version update.

## Boundary contract

### Single-source portable Antigravity plugin bundle renderer
- disposition: extend
- owner: clutch/antigravity.py
- consumers: `clutch/__main__.py` (`host antigravity` via `install_plugin`/`plugin_manifest`), `tests/unit/test_antigravity_plugin.py`, `tests/unit/test_antigravity_bundle.py`, `tests/integration/test_antigravity_bundle.py`
- observable change: adds `AUTHOR = "ClutchWork"`, `HOMEPAGE_URL = "https://github.com/protus75/clutchwork"`, `REPOSITORY_URL = "https://github.com/protus75/clutchwork"`, `PORTABLE_MCP_COMMAND = "uvx"`, `PORTABLE_MCP_ARGS = ("--from", "clutchwork", "clutch", "mcp", "serve")`; extends `plugin_manifest(version_str=None)` to include documented Marketplace fields `author`, `homepage`, and `repository` alongside `name`, `displayName`, `version`, `description`, `logo`, and `suggestedPrompts` (no unknown top-level keys); adds pure functions `portable_mcp_config() -> dict[str, object]` and `portable_bundle_files(*, version_str: str | None = None, logo_bytes: bytes) -> dict[str, bytes]` returning the exact repo-relative file map for `plugin.json`, `mcp_config.json`, `assets/logo.svg`, and the three `skills/clutch-*/SKILL.md` files.
- compatibility: additive functions and documented optional Marketplace fields on `plugin_manifest()`; `install_plugin`, `install_workspace_skills`, `mcp_config`, `default_plugin_dir`, and `doctor_finding` keep their signatures and local-executable behavior unchanged. `tests/unit/test_antigravity_plugin.py` is fenced solely to include `author`, `homepage`, and `repository` in its `plugin.json` expected-keys assertion if it checks exact keys.
- acceptance: criteria 1 and 2
- tests: tests/unit/test_antigravity_bundle.py, tests/unit/test_antigravity_plugin.py, tests/integration/test_antigravity_bundle.py
- post-merge source of truth: clutch/antigravity.py

### Committed publishable Antigravity plugin root
- disposition: create
- owner: plugin.json, mcp_config.json, assets/logo.svg, skills/clutch-drain-loop/SKILL.md, skills/clutch-plan-drain/SKILL.md, skills/clutch-plan-serve/SKILL.md
- closest existing: `clutch/antigravity.py` (writes the same bundle locally to `~/.gemini/config/plugins/clutchwork/` with a machine-local `sys.executable` MCP config) and `clutch/assets/logo.svg` (packaged wheel logo asset)
- earning reason: independently deployed external-host package boundary required at the Git repository root so `agy plugin install https://github.com/protus75/clutchwork` and Antigravity Marketplace ingestion (`agy plugin validate --strict .`) discover the plugin manifest, portable MCP config, logo, and skills directly from the repository without running a local Python installer first.
- consumers: Antigravity CLI/Marketplace (`agy plugin install`, `agy plugin validate --strict .`), `tests/integration/test_antigravity_bundle.py`
- observable change: commits the six generated bundle files at the repository root, matching `portable_bundle_files(version_str=<pyproject.toml version>, logo_bytes=<clutch/assets/logo.svg>)` byte-for-byte.
- compatibility: additive root files; `pyproject.toml` wheel packaging (`module-name = "clutch"`), `config.yaml` `meta.paths`, and existing CLI/extension behavior are unaffected.
- acceptance: criteria 3 and 4
- tests: tests/integration/test_antigravity_bundle.py
- post-merge source of truth: clutch/antigravity.py (generator), plugin.json, mcp_config.json, assets/logo.svg, skills/clutch-drain-loop/SKILL.md, skills/clutch-plan-drain/SKILL.md, skills/clutch-plan-serve/SKILL.md

### README GitHub install and Marketplace validation docs
- disposition: extend
- owner: README.md
- consumers: operators, Antigravity plugin users, `tests/unit/test_readme.py`, `tests/integration/test_antigravity_bundle.py`
- observable change: extends `## Antigravity plugin` in `README.md` with direct GitHub installation (`agy plugin install https://github.com/protus75/clutchwork`) and Marketplace validation/submission (`agy plugin validate --strict .`).
- compatibility: preserves all existing README sections, absolute `https://` links (`tests/unit/test_readme.py::test_links_are_absolute`), `./dev.py` placement under `## Developing clutch`, and valid `uv run clutch <verb>` references.
- acceptance: criterion 5
- tests: tests/unit/test_readme.py, tests/integration/test_antigravity_bundle.py
- post-merge source of truth: README.md

## Scope in / Scope out
In:
- `clutch/antigravity.py`:
  - Add constants `AUTHOR = "ClutchWork"`, `HOMEPAGE_URL = "https://github.com/protus75/clutchwork"`, `REPOSITORY_URL = "https://github.com/protus75/clutchwork"`, `PORTABLE_MCP_COMMAND = "uvx"`, and `PORTABLE_MCP_ARGS = ("--from", "clutchwork", "clutch", "mcp", "serve")`.
  - Extend `plugin_manifest(version_str: str | None = None) -> dict[str, object]` to include `"author": AUTHOR`, `"homepage": HOMEPAGE_URL`, and `"repository": REPOSITORY_URL` alongside the existing documented fields (`name`, `displayName`, `version`, `description`, `logo`, `suggestedPrompts`).
  - Add `portable_mcp_config() -> dict[str, object]` returning `{"mcpServers": {MCP_SERVER_NAME: {"command": PORTABLE_MCP_COMMAND, "args": list(PORTABLE_MCP_ARGS)}}}`.
  - Add `portable_bundle_files(*, version_str: str | None = None, logo_bytes: bytes) -> dict[str, bytes]` returning the exact mapping of repo-relative paths (`plugin.json`, `mcp_config.json`, `assets/logo.svg`, `skills/clutch-drain-loop/SKILL.md`, `skills/clutch-plan-drain/SKILL.md`, `skills/clutch-plan-serve/SKILL.md`) to their serialized bytes, reusing `plugin_manifest(version_str=version_str)`, `portable_mcp_config()`, `logo_bytes`, and `SKILLS` with consistent `json.dumps(..., indent=2) + "\n"` formatting.
- Commit the six generated bundle files at the repository root, matching `portable_bundle_files(version_str=<pyproject.toml version>, logo_bytes=<clutch/assets/logo.svg>)` byte-for-byte:
  - `plugin.json`
  - `mcp_config.json`
  - `assets/logo.svg`
  - `skills/clutch-drain-loop/SKILL.md`
  - `skills/clutch-plan-drain/SKILL.md`
  - `skills/clutch-plan-serve/SKILL.md`
- `README.md`:
  - Update `## Antigravity plugin` to document direct GitHub install (`agy plugin install https://github.com/protus75/clutchwork`, backed by the committed portable `uvx --from clutchwork clutch mcp serve` bundle) and Marketplace validation (`agy plugin validate --strict .`) for publishing after a PyPI release. Keep all markdown links `https://`-prefixed (never `[...](customization://...)` or relative links) and keep `./dev.py` exclusively under `## Developing clutch`.
- `tests/unit/test_antigravity_plugin.py`:
  - Only update the `plugin.json` expected top-level keys assertion (if it checks exact keys) to include `"author"`, `"homepage"`, and `"repository"`. Leave all other assertions in `tests/unit/test_antigravity_plugin.py` unchanged.
- New unit test file `tests/unit/test_antigravity_bundle.py` (pure/hermetic: zero repo file reads, zero subprocesses, zero network):
  - Covers `plugin_manifest(version_str=...)` Marketplace metadata (`author`, `homepage`, `repository`, `name`, `displayName`, `version`, `description`, `logo`, 3 `suggestedPrompts`, no unknown top-level keys), `portable_mcp_config()` (`uvx --from clutchwork clutch mcp serve`, no machine-local path), `portable_bundle_files(version_str=..., logo_bytes=...)` exact key set and byte rendering, and keeps `clutch/antigravity.py` >= 90% branch coverage.
- New integration test file `tests/integration/test_antigravity_bundle.py` (reads repo files only via `Path(__file__).resolve().parents[2]`; zero disk writes, zero subprocesses, zero network):
  - Reads `pyproject.toml` `[project].version` and `clutch/assets/logo.svg` bytes, computes `portable_bundle_files(version_str=version, logo_bytes=logo_bytes)`, and asserts every committed repo-root bundle file exists and matches byte-for-byte.
  - Asserts `skills/` contains exactly the three expected skill directories (`clutch-drain-loop`, `clutch-plan-drain`, `clutch-plan-serve`) and no extra directories.
  - Asserts `README.md` documents `agy plugin install https://github.com/protus75/clutchwork` and `agy plugin validate --strict .`.
- Engine-written `# clutch:meta` headers on newly created Python test files under `tests/` updated by Check.

Out:
- Modifying `clutch/__main__.py`, `clutch/doctor.py`, `clutch/release.py`, `clutch/hostfiles.py`, `clutch/mcp.py`, `clutch/docs/host-running.md`, `clutch/docs/host-contract.md`, `docs/how-clutch-works.md`, `pyproject.toml`, `CLAUDE.md`, `AGENTS.md`, or `vscode-clutchwork/`.
- Running `agy plugin validate`, publishing to PyPI, or submitting to the Antigravity Marketplace (manual post-`0.7.0` release step).
- Adding tests to any of the seven hot test files (`tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`).

## Scope fence
- clutch/antigravity.py
- plugin.json
- mcp_config.json
- assets/logo.svg
- skills/clutch-drain-loop/SKILL.md
- skills/clutch-plan-drain/SKILL.md
- skills/clutch-plan-serve/SKILL.md
- README.md
- tests/unit/test_antigravity_plugin.py
- tests/unit/test_antigravity_bundle.py
- tests/integration/test_antigravity_bundle.py

## Acceptance criteria
1. `tests/unit/test_antigravity_bundle.py` checks `plugin_manifest(version_str="0.7.0")` returns the exact nine documented Antigravity top-level keys (`name: "clutchwork"`, `displayName: "ClutchWork"`, `version: "0.7.0"`, `description`, `author: "ClutchWork"`, `homepage: "https://github.com/protus75/clutchwork"`, `repository: "https://github.com/protus75/clutchwork"`, `logo: "assets/logo.svg"`, and 3 non-empty `suggestedPrompts`), ruling out missing Marketplace fields or unknown top-level keys. Verified by `./dev.py test tests/unit/test_antigravity_bundle.py tests/unit/test_antigravity_plugin.py`.
2. `tests/unit/test_antigravity_bundle.py` checks `portable_mcp_config()` returns `{"mcpServers": {"clutchwork": {"command": "uvx", "args": ["--from", "clutchwork", "clutch", "mcp", "serve"]}}}` (ruling out `sys.executable` or machine-local paths) and checks `portable_bundle_files(version_str="0.7.0", logo_bytes=b"<svg/>")` returns the exact six repo-relative paths (`plugin.json`, `mcp_config.json`, `assets/logo.svg`, `skills/clutch-drain-loop/SKILL.md`, `skills/clutch-plan-drain/SKILL.md`, `skills/clutch-plan-serve/SKILL.md`) with valid UTF-8 JSON ending in `\n`, exact logo bytes, and exact `SKILLS` contents, keeping `clutch/antigravity.py` >= 90% unit branch coverage. Verified by `./dev.py test tests/unit/test_antigravity_bundle.py tests/unit/test_antigravity_plugin.py`.
3. `tests/integration/test_antigravity_bundle.py` checks all six committed repo-root bundle files (`plugin.json`, `mcp_config.json`, `assets/logo.svg`, `skills/clutch-drain-loop/SKILL.md`, `skills/clutch-plan-drain/SKILL.md`, `skills/clutch-plan-serve/SKILL.md`) exist and match `portable_bundle_files(version_str=<pyproject.toml version>, logo_bytes=<clutch/assets/logo.svg>)` byte-for-byte, ruling out `plugin.json` version drift from `pyproject.toml`, stale skills, or local-path leaks in `mcp_config.json`. Verified by `./dev.py test tests/integration/test_antigravity_bundle.py`.
4. `tests/integration/test_antigravity_bundle.py` checks `skills/` at the repository root contains exactly the three expected skill directories (`clutch-drain-loop`, `clutch-plan-drain`, `clutch-plan-serve`), ruling out extra or misnamed skill directories. Verified by `./dev.py test tests/integration/test_antigravity_bundle.py`.
5. `README.md` documents `agy plugin install https://github.com/protus75/clutchwork` and `agy plugin validate --strict .` under `## Antigravity plugin` while keeping all `README.md` link, developer-section, and CLI-verb invariants green. Verified by `./dev.py test tests/unit/test_readme.py tests/integration/test_antigravity_bundle.py`.

## Verification
```
./dev.py test tests/unit/test_antigravity_bundle.py tests/unit/test_antigravity_plugin.py tests/unit/test_readme.py tests/integration/test_antigravity_bundle.py tests/integration/test_antigravity_plugin.py
```

## Definition of rejected
- Any committed root bundle file (`plugin.json`, `mcp_config.json`, `assets/logo.svg`, or `skills/clutch-*/SKILL.md`) differs from `clutch.antigravity.portable_bundle_files(...)` for the repo's `pyproject.toml` version and `clutch/assets/logo.svg`, or `mcp_config.json` contains a machine-local executable path instead of `uvx --from clutchwork clutch mcp serve`.
- `plugin.json` omits `author`, `homepage`, or `repository`, or introduces any undocumented top-level key.
- `tests/unit/test_antigravity_bundle.py` reads repository files from disk or spawns subprocesses, or `tests/integration/test_antigravity_bundle.py` writes to disk or spawns subprocesses.
- `README.md` introduces a non-`https://` markdown link (breaking `tests/unit/test_readme.py`) or places `./dev.py` outside `## Developing clutch`.
- Any file outside `## Scope fence` is modified, or `clutch/antigravity.py` drops below the 90% `test-gate.toml` unit coverage floor.

## Time budget
- expected: 15m
- stuck: 30m
