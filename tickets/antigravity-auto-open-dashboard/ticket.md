---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/antigravity.py
- clutch/docs/host-contract.md#Antigravity plugin
- tests/unit/test_antigravity_bundle.py
- tests/unit/test_antigravity_plugin.py
- tests/unit/test_release_audit_070_gates.py
- tests/integration/test_antigravity_bundle.py
- tests/integration/test_antigravity_plugin.py

## Goal / Why
Ship a plugin rule file (`rules/AGENTS.md`) in the ClutchWork Antigravity plugin bundle so that after an interactive Antigravity chat drafts and lints a new ticket, the agent automatically calls `clutch_open_dashboard` for that repository on the `tickets` tab. Because `clutch_open_dashboard` declares an `aux_pane` entrypoint, Antigravity opens or refreshes the ClutchWork dashboard in the side pane right when the user is ready to confirm the draft or monitor the queue.

Rule home: this rule belongs in the Antigravity plugin's `rules/AGENTS.md` (owned by `clutch/antigravity.py`), not in `CORE_TEMPLATE` (`clutch/hostfiles.py`) or repo-only `CLAUDE.md`/`AGENTS.md`, because `clutch_open_dashboard` is an Antigravity MCP App tool that only exists when the ClutchWork Antigravity plugin is enabled, and shipping it in the plugin reaches every host repository opened in Antigravity.

## Boundary contract
### Antigravity plugin bundle
- disposition: extend
- owner: clutch/antigravity.py
- consumers: `clutch host antigravity` (`--verify`), `clutch release bump`, Antigravity plugin loader, committed root plugin bundle
- observable change: define `PLUGIN_RULES` in `clutch/antigravity.py`, emit `rules/AGENTS.md` from `install_plugin` and `portable_bundle_files`, require non-empty `rules/AGENTS.md` in `verify_plugin`, and commit the matching root `rules/AGENTS.md`
- compatibility: additive plugin file; existing `plugin.json`, `mcp_config.json`, `hooks.json`, `assets/logo.png`, `skills/*/SKILL.md`, and `install_workspace_skills` are unchanged; existing local installs pick up `rules/AGENTS.md` on `clutch host antigravity`
- acceptance: `install_plugin` and `portable_bundle_files` both emit `rules/AGENTS.md` with plain markdown referencing `clutch_open_dashboard` and `tickets`, `verify_plugin` fails when `rules/AGENTS.md` is missing or empty, and root `rules/AGENTS.md` matches `portable_bundle_files`
- tests: `tests/unit/test_antigravity_bundle.py`, `tests/unit/test_antigravity_plugin.py`, `tests/unit/test_release_audit_070_gates.py`, `tests/integration/test_antigravity_bundle.py`, `tests/integration/test_antigravity_plugin.py`
- post-merge source of truth: clutch/antigravity.py

## Scope in / Scope out
Scope in:
- `clutch/antigravity.py`: add `PLUGIN_RULES` (plain markdown with no YAML frontmatter) instructing interactive Antigravity chats to call `clutch_open_dashboard` with the repository's absolute `repo` path and `tab: "tickets"` after finishing and linting a new draft ticket (`tickets/<stem>/ticket.md`), while skipping non-interactive or ticket-worktree runs. Write `rules/AGENTS.md` from `install_plugin` and `portable_bundle_files`, and include `plugin_dir / "rules/AGENTS.md"` in the non-empty required files checked by `verify_plugin`.
- `rules/AGENTS.md`: commit the exact bytes emitted by `portable_bundle_files(...)["rules/AGENTS.md"]` at the repository root.
- `clutch/docs/host-contract.md`: update `## Antigravity plugin` to mention that the plugin ships `rules/AGENTS.md` to open the ClutchWork dashboard after drafting a ticket.
- `tests/unit/test_antigravity_bundle.py`: add `"rules/AGENTS.md"` to the expected `portable_bundle_files` key set and assert `files["rules/AGENTS.md"] == ag.PLUGIN_RULES.encode()`.
- `tests/unit/test_antigravity_plugin.py`: update `test_bundle_and_skills` for `len(paths) == 8`, assert `rules/AGENTS.md` has no frontmatter (`not text.startswith("---")`) and mentions `clutch_open_dashboard` and `tickets`, and narrow the existing root-file exclusion check from `p.name` to `p.relative_to(target).as_posix()` so `rules/AGENTS.md` is allowed while root-level conduct and config files remain excluded.
- `tests/integration/test_antigravity_plugin.py`: assert that every `clutch_*` tool name mentioned in `antigravity.PLUGIN_RULES` is registered in `mcp.TOOLS`.

Scope out:
- Do not edit `clutch/hostfiles.py` (`CORE_TEMPLATE`), repository conduct files, `clutch/mcp.py`, `clutch/ui/`, or `install_workspace_skills` (workspace installs remain skills-only).
- Do not change side-pane width or Antigravity layout settings (Antigravity's desktop host owns side-pane sizing).

## Scope fence
- clutch/antigravity.py
- rules/AGENTS.md
- clutch/docs/host-contract.md
- tests/unit/test_antigravity_bundle.py
- tests/unit/test_antigravity_plugin.py
- tests/integration/test_antigravity_plugin.py

## Acceptance criteria
1. `clutch/antigravity.py::PLUGIN_RULES` is plain markdown without YAML frontmatter (`not text.startswith("---")`), instructs interactive chats to call `clutch_open_dashboard` with the repository path and `tickets` tab after drafting a ticket, and references only registered `mcp.TOOLS` names; verified by `./dev.py test tests/unit/test_antigravity_plugin.py tests/integration/test_antigravity_plugin.py` (rules out frontmatter in `rules/AGENTS.md`, missing tool guidance, or an unregistered tool name).
2. `install_plugin` writes `rules/AGENTS.md` (8 files total, not 7) without writing root-level `CLAUDE.md`, `AGENTS.md`, or `config.json`, and `portable_bundle_files` emits identical bytes under `"rules/AGENTS.md"`; verified by `./dev.py test tests/unit/test_antigravity_plugin.py tests/unit/test_antigravity_bundle.py` (rules out omitted `rules/AGENTS.md` or local/portable bundle drift).
3. `verify_plugin` returns a non-empty findings list when `rules/AGENTS.md` is missing or empty and `[]` on a complete install; verified by `./dev.py test tests/unit/test_release_audit_070_gates.py` (rules out `verify_plugin` passing with a missing or blank `rules/AGENTS.md`).
4. Committed repo-root `rules/AGENTS.md` matches `portable_bundle_files(...)["rules/AGENTS.md"]` byte-for-byte, and `clutch/docs/host-contract.md` documents `rules/AGENTS.md` under `## Antigravity plugin`; verified by `./dev.py test tests/integration/test_antigravity_bundle.py tests/integration/test_antigravity_plugin.py` and reading `clutch/docs/host-contract.md`.

## Verification
```
./dev.py test tests/unit/test_antigravity_bundle.py tests/unit/test_antigravity_plugin.py tests/unit/test_release_audit_070_gates.py tests/unit/test_release_plugin_bundle.py tests/unit/test_mcp_auto_project.py tests/integration/test_antigravity_bundle.py tests/integration/test_antigravity_plugin.py
```

## Definition of rejected
- `rules/AGENTS.md` contains YAML frontmatter or names a `clutch_*` tool not in `mcp.TOOLS`.
- `install_plugin`, `portable_bundle_files`, `verify_plugin`, or committed root `rules/AGENTS.md` disagree on the presence or bytes of `rules/AGENTS.md`.
- Any edit to `clutch/hostfiles.py`, `CLAUDE.md`, `AGENTS.md`, or `install_workspace_skills`.

## Time budget
- expected: 6m
- stuck: 12m
