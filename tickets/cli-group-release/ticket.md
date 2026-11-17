---
state: draft
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- cli-help-standard

## Context
- clutch/release.py

## On-demand
- clutch/__main__.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md

## Goal / Why
Roadmap row 139. `release` and `publish` are top-level verbs added with a bare `sub.add_parser` and a one-line `help=`. When this ticket is done, `clutch release bump --minor|--patch` bumps, commits and tags a local release, and `clutch release publish` builds and uploads the tagged release. The old top-level `clutch release --minor` and `clutch publish` no longer parse. Both commands carry help to the row 129 standard (reads, writes, lock, exit codes, examples) through `_command`. Every caller and document spells the new names, so no road tells an operator to run a verb that no longer exists.

## Scope in / Scope out
Scope in:
- In `clutch/__main__.py`, add a top-level `release` group with subcommands `bump` and `publish`, built through `_command` like the existing groups. `bump` keeps the required `--minor`/`--patch` choice and the `handle_release` behaviour. `publish` keeps the `handle_publish` behaviour. The group description lists both subcommands and gives examples. Dispatch uses the group's subcommand names. Lock identities passed to `_locked` stay `"release"` and `"publish"`. Printed `release:` and `publish:` output prefixes stay unchanged unless a test pins otherwise.
- Remove the old top-level `publish` and `release` parsers in place, with no alias or shim.
- Change every Refusal road and message that names `clutch release --minor|--patch` or `clutch publish` to the new spelling: the `retry clutch publish` roads in `clutch/release.py` and the missing-tag road in `clutch/roadmap.py`.
- Update the shipped prompt `clutch/specs/ask/plan-ticket-drain.md` line naming `clutch release --minor` to `clutch release bump --minor`. The prompt has no `version` field, so no version bump applies. Update its phrase pin in `tests/integration/test_ask_plan_drain.py`.
- Update documents that describe the commands: the verb rows in `docs/how-clutch-works.md` section 2 and `clutch/docs/host-running.md` (including the writer-lock sentence naming `release`, `publish`), the `clutch publish` mention in `clutch/docs/host-contract.md`, the `clutch publish` mention in `docs/how-clutch-works.md` about `release.pypi_token`, and `README.md` and `CLAUDE.md`/`AGENTS.md` only if they name the old spelling (grep first).
- Update tests that call or assert the old spelling: `tests/unit/test_release.py`, `tests/unit/test_release_publish.py`, `tests/integration/test_release.py`, `tests/integration/test_release_publish.py`, `tests/unit/test_roadmap_merged.py`. Update the verb-group expectations in `tests/unit/test_main_verb_groups.py` and `tests/integration/test_main_verb_groups.py` only where they list `release` or `publish` as ungrouped top-level verbs.
- Grep `clutch/hostfiles.py` CORE_TEMPLATE, `clutch/observe.py`, and `clutch/help.py` for the old spellings. If any hit, update it and the matching test. If none, change nothing there, and no `clutch core` run is needed.
Scope out: the release behaviour in `clutch/release.py`, the `release.publish` config key and the `release` journal signal name, `docs/*-plan.md` text, and every other command group.

## Scope fence
- clutch/__main__.py
- clutch/release.py
- clutch/roadmap.py
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- README.md
- CLAUDE.md
- AGENTS.md
- clutch/hostfiles.py
- clutch/observe.py
- clutch/help.py
- tests/unit/test_release.py
- tests/unit/test_release_publish.py
- tests/unit/test_roadmap_merged.py
- tests/unit/test_main_verb_groups.py
- tests/unit/test_main_release_group.py
- tests/integration/test_release.py
- tests/integration/test_release_publish.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_main_verb_groups.py

## Acceptance criteria
1. `cli.main(["release", "bump", "--minor"], ...)` runs the bump and returns 0, and `cli.main(["release", "publish"], ...)` runs the publish. Both are checked in `tests/unit/test_release.py` and `tests/unit/test_release_publish.py`.
2. `cli._parser().parse_args(["publish"])` and `cli._parser().parse_args(["release", "--minor"])` each raise `SystemExit`, not a parsed namespace. This is checked in the new `tests/unit/test_main_release_group.py`.
3. `clutch release bump` with neither `--minor` nor `--patch`, or with both, exits 2 from argparse. This is checked in `tests/unit/test_release.py`.
4. The help text of `release`, `release bump` and `release publish` contains reads, writes, lock, exit codes and an `Examples:` section, checked in `tests/unit/test_main_release_group.py` the way `tests/unit/test_main_help.py` checks other groups.
5. A Refusal raised by `release.publish` for a missing tag carries a road containing `clutch release bump`, and no source string under `clutch/` contains `clutch release --` or `clutch publish`. Both are checked by `tests/unit/test_release_publish.py` and `rg -n "clutch (release --|publish)" clutch` printing nothing.
6. The `plan-ticket-drain.md` prompt names `clutch release bump --minor` and not `clutch release --minor`, and `tests/integration/test_ask_plan_drain.py` pins the new phrase in its phrase list.
7. `docs/how-clutch-works.md` and `clutch/docs/host-running.md` list `release bump` and `release publish` rows and no row for a top-level `publish`. The `release` group is listed in the verb tables, checked by `tests/unit/test_host_running.py` and `tests/integration/test_help.py`.

## Verification
```
./dev.py test tests/unit/test_release.py tests/unit/test_release_publish.py tests/unit/test_main_release_group.py tests/unit/test_main_verb_groups.py tests/unit/test_main_help.py tests/unit/test_roadmap_merged.py tests/unit/test_host_running.py tests/integration/test_release.py tests/integration/test_release_publish.py tests/integration/test_ask_plan_drain.py tests/integration/test_main_verb_groups.py tests/integration/test_help.py tests/integration/test_hostfiles.py
```

## Definition of rejected
A top-level `release --minor` or `publish` still parses, or an alias or shim for the old names is added. Any caller or document still spells the old verbs. A moved command lacks reads, writes, lock, exit codes or examples in its help. Release or publish behaviour changes.

## Time budget
- expected: 25m
- stuck: 50m
