---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: draft
---

## Depends on
- cli-help-standard
- cli-group-view

## Context
- clutch/__main__.py::_command
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/doctor.py
- clutch/hostfiles.py::CORE_TEMPLATE
- clutch/help.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_provider_group.py
- tests/unit/test_docs_verb.py

## On-demand
- README.md
- clutch/specs/ask/author.md
- clutch/specs/ask/review.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-contract.md
- clutch/docs/host-gemini.md
- clutch/providers.py
- tests/integration/test_cli.py
- tests/integration/test_doctor.py

## Goal / Why
Roadmap row 138 (`cli-group-host`), group `host`. `cli-help-standard` (row 129) added `_command` in `clutch/__main__.py` and the rules in `CLAUDE.md` section A: every command carries help to the standard through `_command`, lives under a top-level group, and a command change updates every document that describes it in the same change. Rows 130-137 built the `engine`, `ticket`, `box`, `config`, `provider` and `view` groups that way. Today `doctor`, `core` and `docs` are still top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help doctor` prints no reads, writes, lock, exit codes or examples.

When this ticket is done:
- `clutch host doctor`, `clutch host core` and `clutch host docs` take the same arguments and defaults, print the same stdout, read and write the same files, take the same lock (none for `doctor` and `docs`, as `docs/how-clutch-works.md` section 2.1 says) and exit with the same codes as `clutch doctor`, `clutch core` and `clutch docs` do today. The only visible differences are the help text, argparse's own usage and error lines, the refusal prefix (`clutch host:`), and the roads and documents that name the commands (Scope in).
- `clutch doctor`, `clutch core` and `clutch docs` no longer parse: argparse exits 2 with an invalid-choice error. There is no alias (`CLAUDE.md` 'No dual-path code').
- The `host` group and its three subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them.
- Every caller names the new form in the same change: the engine's roads, the core template and the three managed blocks it renders, the prompts, `README.md`, the host guides, `docs/how-clutch-works.md`, and the tests.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140), so a person or agent finds setup, conduct refresh and guide paths together under `clutch help host`.

Transition, once. The conduct block (`CLAUDE.md`, `AGENTS.md`, 'run clutch core to refresh it') and every prompt rendered before this merges name `clutch doctor`, `clutch docs` or `clutch core`; after the merge those exit 2 with an argparse invalid-choice error. Re-render the prompt or re-read the conduct file, or run the `clutch host ...` form. A road printed by a process started before the merge ('run `clutch core`') names the old form; run `clutch host core`. No running engine needs a restart: drain and serve never spawn these commands, and the self-upgrade re-exec runs `engine drain`, whose stale-conduct check passes because this change refreshes `CLAUDE.md` and `AGENTS.md` in the same commit. Another host gets the new conduct block when it runs `clutch host core` after upgrading, which `engine drain`, `engine serve` and `engine run` already require. The VS Code extension runs none of the three commands, so it needs no rebuild.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `doctor`, `core` and `docs` parsers. Add a group `host` built the way `ticket`, `engine`, `box`, `config`, `provider` and `view` are built: a one-line summary (for example 'check and refresh this host's setup'), a `description` of what the group covers, an `Examples:` epilog whose `clutch host ...` line parses, and `argparse.RawDescriptionHelpFormatter`. Its subparsers take `dest="host_verb"` and `required=True`. Its three subcommands are built with `_command`, with every field, keep their one-line summaries and take no arguments. Read each fact from its `docs/how-clutch-works.md` section 2.1 row, `clutch/docs/host-running.md` row and handler before writing it: `doctor` (checks venv, config load, git, lock probe, journal readability and the core row; changes nothing; no lock; exits 0 when every row passes, 2 on any failure), `core` (rewrites the managed `clutch:core` block in each routed agent's conduct file; reads config and the conduct files, writes those files; no lock; exits 0 on success, 2 on refusal), `docs` (prints the installed host guide paths and their purposes; reads nothing from the host; no lock; exits 0). Examples `clutch host doctor`, `clutch host core` and `clutch host docs`.
- The `_parser()` top-level description `Host guides: clutch docs` becomes `Host guides: clutch host docs`.
- Dispatch: `handlers` drops the `"docs"`, `"doctor"` and `"core"` entries and gains `"host"`, dispatching by `args.host_verb` to the unchanged `handle_docs`, `handle_doctor` and `handle_core`. Every membership test on `args.verb` for these three (the set holding `docs` and `doctor` that decides config loading, and the set holding `core`) keeps its meaning by testing the pair (`args.verb == "host"` and the `host_verb`), so each command behaves as before. `ruff format` may re-wrap those lines; no other line changes.
- Refusals: every refusal of the three already goes through `_fail(args.verb, ...)` and now prints `clutch host: ...`; no `print(..., file=sys.stderr)` is added. The road at the stale-conduct refusal (`run clutch core, then commit the conduct files and retry engine ...`) names `clutch host core`.

In, other code:
- `clutch/hostfiles.py`: `CORE_TEMPLATE`'s 'run clutch core to refresh it' becomes 'run clutch host core to refresh it', and the paved roads and messages ('run `clutch core` to insert the managed block', 'run `clutch core` to refresh the managed block', `clutch core is {state}`) name `clutch host core`. The core_drift finding message `cannot extract candidate clutch core template` becomes `cannot extract candidate clutch host core template` (no test pins it). This adds bytes to `CORE_TEMPLATE`, which must stay at or under 8192. Refresh the managed blocks with `uv run clutch host core` at the checkout root (`CLAUDE.md`, `AGENTS.md`) and in `hosts/fixture` (`hosts/fixture/CLAUDE.md`), never by hand, and regenerate `GOLDEN` in `tests/integration/test_hostfiles.py` with `uv run python -m tests.integration.test_hostfiles`, then `ruff format` it. Rule home: an existing host rule, edited in its home `CORE_TEMPLATE`.
- `clutch/doctor.py`: the venv row's `run `uv run clutch doctor`` becomes `uv run clutch host doctor`.
- `clutch/providers.py`: the generated config comment's 'then run clutch doctor and clutch provider probe' becomes 'then run clutch host doctor and clutch provider probe'.
- `clutch/help.py`: help topic keys and `COMMANDS` entries are unchanged; a topic whose `verb` field names a run-guide row for `doctor`, `core` or `docs` is changed to the new row text (`host doctor`, `host core`, `host docs`) so the topic still resolves.

In, prompts (no `version`): `clutch/specs/ask/author.md` (`clutch docs` becomes `clutch host docs`), `clutch/specs/ask/review.md` (`clutch docs` becomes `clutch host docs`) and `clutch/specs/ask/plan-ticket-drain.md` (`clutch doctor` becomes `clutch host doctor`, wherever it names the command).

In, documents. Only references to the three commands change:
- `README.md`: the `uv run clutch doctor` and `uv run clutch core` lines, their comments aligned, the `uv run clutch docs` sentence, and any `clutch doctor|core|docs` in the long step line.
- `clutch/docs/host-running.md`: the first line `uv run clutch doctor`; the first cells of the `doctor`, `core` and `docs` rows become `host doctor`, `host core` and `host docs`, text unchanged; the prose that names the verb (`doctor` also needs the lock; a setup `doctor` passes) becomes `host doctor`. The 'doctor output' noun stays.
- `clutch/docs/host-contract.md`: every `clutch doctor` and `clutch core` command reference (config init paragraph, Onboarding steps 5 and 6, Managed conduct paragraphs).
- `clutch/docs/host-gemini.md`: 'where `clutch core` writes' becomes `clutch host core`.
- `docs/how-clutch-works.md`: the section 2.1 rows for `doctor`, `core` and `docs` begin `host doctor`, `host core` and `host docs`, text unchanged; section 12's `clutch core` writes sentence and the `doctor` bullets name `host core` and `host doctor`.
- `CLAUDE.md` and `AGENTS.md`, outside the managed block: the 'A rule has one of two homes' rule's 'through `clutch core`' becomes 'through `clutch host core`'. Nothing else outside the managed block changes.

In, tests. Only the argv (`"host"` before the subcommand) and the pinned text named here change:
- New `tests/unit/test_main_host_group.py` (criteria 1-3). It builds `_parser()` in memory, calls `main(..., cwd=tmp_path, env={})` in an empty `tmp_path`, and for dispatch replaces the handlers' collaborators with fakes as `tests/unit/test_main_ticket_group.py` does. It reads no repo file and starts no process, and it runs the new parser and dispatch lines of `clutch/__main__.py` (coverage floor 13).
- Argv only: `tests/unit/test_docs_verb.py`; `tests/integration/test_cli.py` (its `cli(root, "doctor")`, `cli(..., "core")`, `main([... "core"])`, `main(["core"])` and `cli(root, "docs")` calls; a do-not-grow file, nothing is added to it); `tests/integration/test_doctor.py` (`main(["doctor"], ...)` calls); `tests/integration/test_provider_cooldown_failover.py` (the `core` entry's argv).
- Pinned text: `tests/unit/test_hostfiles.py`, `tests/integration/test_hostfiles.py` (including `GOLDEN`, regenerated), `tests/integration/test_gates.py`, `tests/integration/test_merge.py`, `tests/integration/test_host_contract.py` and `tests/integration/test_drain.py` (a do-not-grow file; only the pinned `clutch core is ...` and `clutch core` strings change) expect `clutch host core` where they expected `clutch core`; `tests/integration/test_doctor.py` expects `uv run clutch host doctor` and `clutch host core` in the core row detail; `tests/integration/test_host_onboarding_doc.py` (the verb tuple names `clutch host doctor` and `clutch host core`); `tests/integration/test_ask_plan_drain.py` (the phrase lists' `clutch doctor` and `clutch docs` become the `clutch host ...` form); `tests/unit/test_roadmap_accept.py` (the fixture gate line at line 108 becomes `clutch host doctor` and nothing else in it changes).

Out:
- An alias of any kind for the old names; every other command, including `view`, `prompt`, `covgate` and `roadmap` (rows 139-140 move the rest).
- Python and data names: `handle_docs`, `handle_doctor`, `handle_core`, the `clutch/doctor.py` and `clutch/hostfiles.py` module and function names, the `core` row name printed by doctor, the `clutch:core` marker text, the `core_drift` finding code, help topic keys, and every test file and function name.
- Output other than the refusal prefix and the roads and strings named above.
- `CHANGELOG.md`, `CLUTCH_PLAN.md` (frozen), `docs/roadmap.md`, the plans under `docs/`, `vscode-clutchwork/` and `tickets/`.
- `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_readme.py`, `tests/unit/test_help.py`, `tests/integration/test_help.py`, `tests/integration/test_main_verb_groups.py` and `tests/integration/test_menu_verb_parity.py` stay unedited and passing.

## Scope fence
- clutch/__main__.py
- clutch/doctor.py
- clutch/hostfiles.py
- clutch/help.py
- clutch/providers.py
- clutch/specs/ask/author.md
- clutch/specs/ask/review.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- clutch/docs/host-gemini.md
- docs/how-clutch-works.md
- README.md
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/unit/test_main_host_group.py
- tests/unit/test_docs_verb.py
- tests/unit/test_hostfiles.py
- tests/unit/test_roadmap_accept.py
- tests/integration/test_cli.py
- tests/integration/test_doctor.py
- tests/integration/test_drain.py
- tests/integration/test_gates.py
- tests/integration/test_merge.py
- tests/integration/test_host_contract.py
- tests/integration/test_hostfiles.py
- tests/integration/test_host_onboarding_doc.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_provider_cooldown_failover.py

## Acceptance criteria
1. `tests/unit/test_main_host_group.py::test_host_group_parses`: `_parser().parse_args(["host", "doctor"])`, `["host", "core"]` and `["host", "docs"]` give `verb == "host"` and `host_verb` equal to the subcommand; and `["host"]`, `["host", "doctor", "extra"]` and `["host", "core", "--x"]` raise `SystemExit(2)`. Ruled out: a changed arity or an added option.
2. `tests/unit/test_main_host_group.py::test_old_names_refuse`: none of `doctor`, `core` and `docs` is a choice of the top-level subparsers, each is a choice of the `host` group, and `_parser().parse_args([name])` raises `SystemExit(2)` for each. Ruled out: an alias, hidden parser or argv rewrite that keeps an old name working.
3. `tests/unit/test_main_host_group.py::test_dispatch_and_refusals`: with fakes for the handlers' collaborators, `main` returns 0 for `["host", "docs"]` printing the fake guide paths, and `["host", "core"]` and `["host", "doctor"]` reach their own handler exactly once and not each other's; in an empty `tmp_path` with no `config.yaml`, `["host", "doctor"]` returns 2 and `["host", "core"]` returns 2 with one stderr line starting `clutch host: `, while `["host", "docs"]` still returns 0 with no config. Ruled out: the old `clutch core:` or `clutch doctor:` prefix, `docs` demanding a config, and `core` dispatched to `handle_doctor`.
4. `./dev.py test tests/unit/test_main_help.py tests/unit/test_readme.py tests/unit/test_host_running.py tests/unit/test_help.py tests/integration/test_help.py` exits 0 with those files unchanged: the parser walk checks the `host` group and its subcommands for a description and parsing examples, the top-level help lists `host doctor`, `host core` and `host docs` once each, `uv run clutch help host core` prints `Reads:`, `Writes:`, `Lock:`, `Exit codes:` and `Examples:` parts, and `test_verb_table_matches_parser` fails while a run-guide row still names a removed top-level command. `grep -cE '^\| .host (doctor|core|docs). \|' clutch/docs/host-running.md` prints `3`.
5. ``sed -n '/^### 2.1 Verbs/,/^### 2.2/p' docs/how-clutch-works.md | grep -cE '^\| .host (doctor|core|docs). \|'`` prints `3`, and the same range with `'^\| .(doctor|core|docs). \|'` prints `0` (at HEAD `3`).
6. `CORE_TEMPLATE` in `clutch/hostfiles.py` contains `run clutch host core to refresh it`, and `len(CORE_TEMPLATE) <= 8192`. `./dev.py test tests/integration/test_hostfiles.py tests/unit/test_hostfiles.py tests/integration/test_gates.py tests/integration/test_host_contract.py` exits 0, so `GOLDEN` is regenerated and the managed blocks of `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` match the template byte for byte. `git diff main` of those three files changes only lines between the `clutch:core` markers, plus the one 'two homes' line in `CLAUDE.md` and `AGENTS.md`.
7. `./dev.py test tests/integration/test_cli.py tests/integration/test_doctor.py tests/unit/test_docs_verb.py tests/integration/test_provider_cooldown_failover.py tests/integration/test_merge.py tests/integration/test_drain.py tests/integration/test_host_onboarding_doc.py tests/integration/test_ask_plan_drain.py tests/unit/test_roadmap_accept.py` exits 0, with only the argv and pinned text named in Scope in changed, no assertion dropped or loosened, and nothing added to `tests/integration/test_cli.py` or `tests/integration/test_drain.py`.
8. `git grep -nE 'clutch (core|doctor|docs)([^a-z-]|$)' -- README.md CLAUDE.md AGENTS.md hosts/fixture/CLAUDE.md clutch docs/how-clutch-works.md tests` prints nothing (at HEAD it prints the lines listed in Scope in). Ruled out: a road, message, prompt, guide, document or test that still names a removed command, which an operator following it would see exit 2.
9. `./dev.py test` exits 0. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is a known base flake and is verified on the base commit, not chased.

## Verification
```
./dev.py test tests/unit/test_main_host_group.py tests/unit/test_main_help.py tests/unit/test_readme.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_docs_verb.py tests/unit/test_hostfiles.py tests/unit/test_roadmap_accept.py
./dev.py test tests/integration/test_help.py tests/integration/test_hostfiles.py tests/integration/test_gates.py tests/integration/test_host_contract.py tests/integration/test_host_onboarding_doc.py tests/integration/test_ask_plan_drain.py
./dev.py test tests/integration/test_cli.py tests/integration/test_doctor.py tests/integration/test_merge.py tests/integration/test_drain.py tests/integration/test_provider_cooldown_failover.py tests/integration/test_main_verb_groups.py tests/integration/test_menu_verb_parity.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `doctor`, `core` or `docs` still runs as a top-level command through an alias, a hidden or suppressed parser, or argv rewriting in `main`.
- An argument, default, stdout line, read, write, lock or exit code of the three commands changes, other than the help text, argparse's usage and error lines, the refusal prefix and the roads named in Scope in.
- A help topic key, `COMMANDS` entry or the doctor row names change.
- A managed block is edited by hand or differs from `CORE_TEMPLATE`, or `CLAUDE.md`, `AGENTS.md` or `hosts/fixture/CLAUDE.md` changes outside its managed block other than the one named line.
- A test is added to a do-not-grow file, or an existing assertion is dropped, loosened or changed beyond the argv and pinned text named in Scope in.
- Another command is moved or renamed, or a file outside the fence changes.

## Time budget
- expected: 30m
- stuck: 60m
- reason: not split, because a rename with no alias moves the parser and every caller in one change (`CLAUDE.md` 'No dual-path code'); the three commands share the parser block, the dispatch dict, the run-guide and section 2.1 tables and the core template line, and every edit outside `clutch/__main__.py` and the new test file is a one-line text or argv change; comparable group moves (rows 130-136) took 8 to 11 actual Implement minutes.
