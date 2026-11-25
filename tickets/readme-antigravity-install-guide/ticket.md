---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- antigravity-plugin-logo

## Context
- README.md
- plugin.json
- mcp_config.json
- clutch/antigravity.py
- tests/unit/test_readme.py
- tests/integration/test_antigravity_bundle.py
- tests/integration/test_antigravity_plugin.py

## Goal / Why
`README.md` serves as both the PyPI/GitHub overview and the plugin help shown in Antigravity's Plugins Manager. Currently `## Install` only shows adding `clutchwork` as a per-host dev dependency (`uv add --dev clutchwork`), leaving Antigravity plugin users unsure whether the plugin bundles all of ClutchWork or whether every host repo must add `clutchwork` to its own dependencies, and it lacks concrete end-to-end usage examples and a full description of what ClutchWork does. Expanding `README.md` with a clear overview of ClutchWork, explicit global/Antigravity vs per-host install paths, and worked usage examples makes the plugin help self-contained for new and multi-repo users.

## Boundary contract
none
- reason: documentation corrections without behavior change; only `README.md` is updated and no CLI, MCP, plugin manifest, or runtime behavior changes.

## Scope in / Scope out
Scope in:
- Expand the top overview of `README.md` with a clear, full description of what ClutchWork does:
  - Orchestrates CLI coding agents (`claude`, `codex`, `gemini`, `qwen`) through the ticket lifecycle (`author -> requisition -> implement -> check -> review -> merge` to local `main`) in isolated worktrees with scope fences, mechanical gates, and cross-model review.
  - Explains the engine plane (ClutchWork process/gates) vs host plane (target repository code, tests, `config.yaml`, and roadmap), unattended `engine drain` and continuous `engine serve`, the Suggestion Box escape valve for second problems and follow-ups, and the Antigravity MCP server + interactive dashboard + thin supervising skills.
- Update `## Install` and `## Antigravity plugin` in `README.md` to clearly distinguish installation modes:
  - **Antigravity plugin (no per-host project dependency required):** explain that the Antigravity plugin (`plugin.json`, `mcp_config.json`, `assets/logo.png`, and `skills/clutch-*/SKILL.md`) is a thin wrapper—all engine logic, MCP tools, and the bundled dashboard live in the `clutchwork` Python package. Installing via `agy plugin install https://github.com/protus75/clutchwork` launches `uvx --from clutchwork clutch mcp serve` automatically in an isolated tool environment, so you do **not** need `clutchwork` in each host repo's dependencies. For CLI verbs across multiple host repos without a per-repo dependency, install once globally (`uv tool install clutchwork`) or invoke via `uvx --from clutchwork clutch <verb>`.
  - **Local machine plugin install:** `uv run clutch host antigravity` (with `--plugin-dir PATH` and `--workspace` options, `customization://clutchwork` reload note, and `clutch host doctor` drift check).
  - **Per-host dev dependency (optional):** keep `uv add --dev clutchwork` and `uv sync` for teams that prefer pinning `clutchwork` in a host repository's `pyproject.toml`.
  - Keep `agy plugin validate --strict .` in `## Antigravity plugin`.
- Add a concrete `## Examples` section (or expand `## Author and run tickets` / `## Observe and decide`) with worked end-to-end examples:
  - Bootstrapping a new host repository without adding `clutchwork` to its dependencies (`uv tool install clutchwork` / `uvx`, `clutch config init --write`, `clutch provider install`, `clutch host doctor`, `clutch provider probe`, `clutch host core`).
  - Using the Antigravity plugin in any workspace: opening the live dashboard (*"Open the ClutchWork dashboard"*), supervising a queue (*"Supervise the Clutch queue (drain-loop)"*), and running a roadmap unattended (quoting the third suggested prompt from `plugin.json`).
  - Planning a feature into tickets, draining unattended, reviewing drafts/Reject-queue items, and triaging the Suggestion Box.
- Preserve all existing `README.md` test invariants:
  - Every Markdown link `](...)` is an absolute `https://` URL (including `https://github.com/protus75/clutchwork`).
  - `## Developing clutch` appears exactly once and `./dev.py` appears only after it.
  - Every `uv run clutch <verb>` command names a valid top-level subcommand in `clutch/__main__.py`.
  - Retain `uv add --dev clutchwork`, `clutch context suggest`, `uv run clutch view events`, `host antigravity`, `--workspace`, `host doctor`, and in `## Antigravity plugin`, `agy plugin install https://github.com/protus75/clutchwork` and `agy plugin validate --strict .`.

Scope out:
- Do not modify `plugin.json`, `mcp_config.json`, `skills/`, `clutch/antigravity.py`, other documentation or conduct files, or any test file.

## Scope fence
- README.md

## Acceptance criteria
1. `README.md` contains a full overview of what ClutchWork does, clearly explains that the Antigravity plugin is a thin wrapper running `uvx --from clutchwork clutch mcp serve` with no per-host `clutchwork` dependency required (alongside `uv tool install clutchwork` and optional `uv add --dev clutchwork`), and includes concrete end-to-end usage examples; verified by reading `README.md` in review.
2. All existing README checks pass with no broken links, invalid verbs, or missing Antigravity/CLI references (not failing `test_links_are_absolute`, `test_dev_commands_only_in_developer_section`, `test_clutch_verbs_exist`, or the Antigravity/CLI integration checks); verified by `./dev.py test tests/unit/test_readme.py tests/integration/test_antigravity_plugin.py tests/integration/test_antigravity_bundle.py tests/integration/test_context_suggest_cli.py tests/integration/test_ask_view_events.py`.

## Verification
```
./dev.py test tests/unit/test_readme.py tests/integration/test_antigravity_plugin.py tests/integration/test_antigravity_bundle.py tests/integration/test_context_suggest_cli.py tests/integration/test_ask_view_events.py
```

## Definition of rejected
`README.md` uses relative links, names `./dev.py` before `## Developing clutch`, omits the thin-plugin / no-per-host-dependency clarification, drops any required verb/install string checked by existing tests, or edits files outside `README.md`.

## Time budget
- expected: 6m
- stuck: 12m
