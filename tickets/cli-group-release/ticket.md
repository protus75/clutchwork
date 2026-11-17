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
- clutch/__main__.py::_command
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/release.py
- clutch/roadmap.py::merged
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_provider_group.py
- tests/integration/test_ask_plan_drain.py::test_prompts_name_only_existing_verbs

## On-demand
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-contract.md
- tests/unit/test_release.py
- tests/unit/test_release_publish.py
- tests/integration/test_release.py
- tests/integration/test_release_publish.py

## Goal / Why
Roadmap row 139 (`cli-group-release`), group `release`. `cli-help-standard` (row 129, merged at `e09d9e05`) added `_command` in `clutch/__main__.py` and the repo-local rules in `CLAUDE.md` section A: every command carries help to the standard through `_command`, every command lives under a top-level group, and a command change updates every document that describes it in the same change. Rows 130-138 built the `engine`, `ticket`, `box`, `config`, `provider`, `view` and `host` groups that way (row 138 merged at `8a832338`). At HEAD (`8a832338`) `release` and `publish` are still top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help publish` prints no reads, writes, lock, exit codes or examples. 15 lines of `clutch/` (the publish roads in `clutch/release.py`, the missing-tag road in `clutch/roadmap.py::merged`, the plan-ticket-drain prompt, the host contract), `docs/how-clutch-works.md` and `tests/` spell them `clutch publish` or `clutch release --minor|--patch`, three roads in `clutch/release.py::release` name a bare `release` (`then retry release`), and both verb tables have top-level `release` and `publish` rows.

When this ticket is done:
- `clutch release bump --minor|--patch` and `clutch release publish` take the same arguments, print the same stdout, read and write the same files, take the writer lock under the same `Lockfile` verbs (`release` and `publish`), and exit with the same codes as `clutch release --minor|--patch` and `clutch publish` do at HEAD. The only visible differences are the help text, argparse's own usage and error lines, the refusal prefix (`clutch release:` for both; a `publish` refusal printed `clutch publish:`), the roads named in Scope in, and the documents, prompt and tests that name these commands (all in Scope in).
- `clutch publish` no longer parses (argparse exits 2 with an invalid-choice error), and `clutch release --minor` exits 2 because the `release` group requires a subcommand. There is no alias (`CLAUDE.md` "No dual-path code").
- The `release` group and its two subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them.
- Every road that tells an operator to bump or publish names the new form, including `release publish`'s refusal for an untagged HEAD: ``tag v<version> is missing or not on HEAD -- run clutch release bump --minor or clutch release bump --patch to tag the version at HEAD, then retry clutch release publish``.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140), so a person or agent finds the release commands together under `clutch help release`, each with what it reads, writes and locks and how it exits. `CLAUDE.md` "Guides name verbs, not command lines" also needs every guide and road to name the verb the CLI accepts. Row 140 moves the rest.

Transition, once. `clutch prompt plan-ticket-drain` rendered before this merges names `clutch release --minor` for the hand bump before the first phase. After the merge that command exits 2 with argparse's `the following arguments are required: release_verb`, and `clutch publish` exits 2 with an invalid-choice error that lists `release`. Re-render the prompt, or run `clutch release bump --minor` and `clutch release publish`. A road printed by a process started before the merge (a publish refusal's "retry clutch publish" or "run clutch release --minor", `roadmap merged`'s "made at its start by `clutch release --minor`", a bump refusal's "retry release", or the same roads in a roadmap digest line) names the old form; run the `release bump` or `release publish` form. No running engine needs a restart: the driver's `clutch/roadmap.py::ship` calls `clutch/release.py` in process and never spawns these commands, the lock verbs stay `release` and `publish`, and the self-upgrade re-exec runs `engine drain` or `engine serve`. The managed conduct block, the snapshot, the help topics and the VS Code extension name neither command, so no `clutch host core` run and no extension rebuild is needed. `docs/roadmap.md` (section 1's "named for the version `clutch release --minor` gives it") and the plans under `docs/` keep the old form; box-000710-8e20cb52 tracks that sweep.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `publish` and `release` parsers: the `sub.add_parser("publish", ...)` line, and the `sub.add_parser("release", ...)` line with its `--minor`/`--patch` group. Add a group `release` where the `publish` parser was (after the `roadmap merged` arguments), the way `view`, `host` and `provider` are built: a one-line summary (for example "bump, tag and publish releases"), a `description` of what the group covers, an `Examples:` epilog whose `clutch release ...` line parses, and `argparse.RawDescriptionHelpFormatter`. Its subparsers take `dest="release_verb"` and `required=True`. Its two subcommands are built with `_command`, with every field, and keep today's one-line summaries. Read each fact from its `docs/how-clutch-works.md` section 2.1 row, its handler and its `clutch/release.py` function before writing it:
  - `bump`, with today's required mutually exclusive `--minor` and `--patch` (`dest="part"`, `action="store_const"`), unchanged. Facts: bumps the version with uv, writes a new changelog section, commits `pyproject.toml`, `uv.lock` and the changelog as `release: <version>`, tags `v<version>` and journals a `release` signal; publishes nothing. Reads config, the git status of those three files, uv's next-version preview, existing tags and the subjects merged since the previous release tag. Writes those three files in one commit, an annotated tag and one journal signal. Lock: the writer lock; refuses while another process holds it. Exits 0 when tagged, 2 on refusal (dirty version files, an existing tag, a uv failure or a held lock). Examples `clutch release bump --minor` and `clutch release bump --patch`.
  - `publish`, no arguments. Facts: builds the version whose `v<version>` tag is on HEAD into `<state_dir>/dist` and lists the artifacts; uploads them to PyPI only with `release.publish: true`; never bumps. Reads config, the tracked tree's git status, uv's version, HEAD and its tag, and the variable `release.pypi_token` names. Writes the wheel and sdist under `<state_dir>/dist` (emptied on each run) and, with `release.publish: true`, an upload; no commit, tag or journal event. Lock: the writer lock; refuses while another process holds it. Exits 0 when built (and uploaded with `release.publish: true`), 2 on refusal (missing token, dirty tracked tree, tag missing or not on HEAD, a uv failure or a held lock). Example `clutch release publish`.
- Dispatch: `handlers` drops the `"release"` and `"publish"` entries and gains `"release"`, dispatching by `args.release_verb` to the unchanged `handle_release` (for `bump`) and `handle_publish`. Both still run after the config load and checkout build; no pre-config or post-config clause changes.
- Locks: `handle_release` keeps `_locked(config.state_dir, "release", ...)` and `handle_publish` keeps `_locked(config.state_dir, "publish", ...)`.
- Output: the stdout lines `release: tagged v<version> at <sha>`, `publish: built <path>`, `publish: uploaded <version> to PyPI` and `publish: release.publish is false; ...` stay; `clutch/roadmap.py::ship` prints the same `release:` and `publish:` lines in the driver's digest. Refusals keep going through `_fail(args.verb, ...)`, so both subcommands print `clutch release: <message>`. No `print(..., file=sys.stderr)` is added.

In, other code, string literals only:
- `clutch/release.py`: the five `then retry clutch publish` roads (dirty tracked tree, uv version, uv build, no artifacts, uv publish) become `then retry clutch release publish`; the missing-tag road becomes `run clutch release bump --minor or clutch release bump --patch to tag the version at HEAD, then retry clutch release publish`; and `release`'s three bare roads end `before release bump` (dirty version files), `then retry release bump` (uv dry run) and `before retrying release bump` (uv bump) instead of `before release`, `then retry release` and `before retrying release`. No other line changes.
- `clutch/roadmap.py::merged`: the missing-tag road ``a phase's tag is made at its start by `clutch release bump --minor` ``. `ship` calls `clutch/release.py` directly and is not edited.

In, prompt (this file carries no `version`): `clutch/specs/ask/plan-ticket-drain.md`'s bullet begins "`clutch release bump --minor` bumps and tags a release."; the rest of that bullet and the "publishing happens only through the driver" bullet stay.

In, documents. Only references to the two commands change:
- `clutch/docs/host-running.md`: the first cells of the `publish` and `release` rows become `release publish` and `release bump`, in place, text unchanged; and the writer-lock sentence reads "`box dismiss`, `release bump`, `release publish`, `engine run`".
- `clutch/docs/host-contract.md`: "only the `clutch release publish` upload receives its value".
- `docs/how-clutch-works.md`: the section 2.1 rows begin `` `release bump --minor\|--patch` `` and `` `release publish` ``, in place, text unchanged; section 8.1's "except the `clutch release publish` upload receives it as `UV_PUBLISH_TOKEN`"; and section 10.1's `dist/` row "Wheel and sdist last built by `clutch release publish`".

In, tests. Only the argv (`"bump"` or `"publish"` after `"release"`) and the pinned text named here change:
- New `tests/unit/test_main_release_group.py` (criteria 1-3). It builds `_parser()` in memory and calls `main(..., cwd=tmp_path, env={})` in an empty `tmp_path`, as `tests/unit/test_main_provider_group.py` does. It reads no repo file, starts no process, and runs the new parser and dispatch lines of `clutch/__main__.py` (coverage floor 13).
- Argv only: `tests/unit/test_release.py` (`test_parser_requires_one_part`'s two `parse_args(["release", "bump", ...])` and `test_main_release_locks_calls_and_prints`'s `cli.main(["release", "bump", "--minor"], ...)`); `tests/unit/test_release_publish.py` (`cli.main(["release", "publish"], ...)` and `cli.main(["release", "bump", "--minor"], ...)`); `tests/integration/test_release.py` (two `main(["release", "bump", "--minor"], ...)`); `tests/integration/test_release_publish.py` (three `main(["release", "publish"], ...)` and one `main(["release", "bump", "--minor"], ...)`).
- Pinned text: `tests/unit/test_release_publish.py` (`test_publish_refuses_a_tag_not_on_head`'s `match="v0.4.0.*clutch release bump --minor"` and `test_main_publish_locks_calls_and_prints`'s `startswith("clutch release:")`); `tests/integration/test_release_publish.py` (`test_publish_refusals_change_nothing`'s `startswith("clutch release:")` and `"clutch release bump --minor" in err`); `tests/unit/test_roadmap_merged.py` (`test_missing_tag_refuses`'s `match="v9.9.9.*clutch release bump --minor"`); `tests/integration/test_ask_plan_drain.py` (the plan-ticket-drain phrase `"clutch release bump --minor"`). The two tag-road patterns tighten from `clutch release`, which the old road also matched.
- Test file and function names stay. `tests/integration/test_release_publish.py::test_dev_publish_is_removed` checks `dev.py publish`, not clutch, and is not edited.
- A scratch prototype of exactly this change on `8a832338` touched the 14 fenced files: 946 unit tests passed with the unit coverage gate, 3,410 integration tests passed, and `ruff check` and `ruff format --check` passed. Without the test edits the code change failed 19 tests in `tests/unit/test_release.py`, `tests/unit/test_release_publish.py`, `tests/integration/test_release.py`, `tests/integration/test_release_publish.py` and `tests/integration/test_ask_plan_drain.py`; `tests/unit/test_roadmap_merged.py` passes either way and is fenced only to tighten its pattern. Without the prompt edit `test_prompts_name_only_existing_verbs` fails, and without the run-guide edit `test_verb_table_matches_parser` fails.

Merge order. Row 138 (`cli-group-host`) merged at `8a832338`, and this ticket starts from it: its `host` group sits above the `prompt` parser, its `handlers` entry is the first, and the run guide's writer-lock sentence already reads "`host doctor` also needs the lock". No other confirmed, unmerged ticket fences a file in this fence (`clutch view status` showed nothing in flight at this writing). Before row 138 merged, the same change on `e05f8055` touched the same 14 files and passed 941 unit tests with the coverage gate, 3,410 integration tests and both ruff checks; row 138's prototype applied after it conflicted with this ticket only on the run guide's writer-lock sentence, where each edits its own words, so either order held. Row 140 (`cli-group-coverage`, a draft committed at `d2e4ec5b`) also fences `clutch/__main__.py`, `clutch/docs/host-running.md`, `clutch/docs/host-contract.md` and `docs/how-clutch-works.md`. Its `covmap` and `covgate` parsers sit directly below this ticket's `publish` and `release` parsers, so those two hunks touch; its other edits (the `covgate` and `covmap` `handlers` entries, the pre-config clause, the config-error road, the `covmap` and `covgate` rows of both verb tables, host-contract's unit check argv and section 10.1's `coverage-map.json` row) are on other lines, at least one line from this ticket's. Each ticket names only its own commands and neither's criteria count the other's, so whichever runs second edits the first's merged text and every criterion of both holds.

Out:
- An alias of any kind for the old names; every other command, including `roadmap gate|accept <release>` and `roadmap merged --release` (there `release` is an argument), `covmap` and `covgate` (row 140).
- Python and data names: `handle_release`, `handle_publish`, the functions of `clutch/release.py`, the `release` config block and its keys (`release.publish`, `release.pypi_token`, `release.packages`), the `release` journal signal, the `Lockfile` verbs `release` and `publish`, the stdout prefixes `release:` and `publish:`, and every test file and function name.
- Behaviour of `clutch/release.py` and `clutch/roadmap.py` beyond the road strings named above.
- Prose naming the step, not the command: `docs/how-clutch-works.md` section 7's "A passing gate releases, publishes only with `release.publish: true`", the run guide's `roadmap` row ("releasing and, with `release.publish: true`, publishing"), and the prompts' "publishing happens only through the driver" and "release when the gate passes".
- `clutch/hostfiles.py` `CORE_TEMPLATE` and the managed blocks of `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md`, `clutch/help.py`, `clutch/observe.py`, `vscode-clutchwork/`, `README.md` and `dev.py`: none names either command (`git grep -nE 'clutch (release|publish)|\["(release|publish)"' -- clutch/hostfiles.py clutch/help.py clutch/observe.py vscode-clutchwork README.md CLAUDE.md AGENTS.md hosts/fixture/CLAUDE.md dev.py` prints nothing at `8a832338`), so no `clutch host core` run applies.
- `CHANGELOG.md` (release history), `CLUTCH_PLAN.md` (frozen), `docs/roadmap.md` (never edited by a ticket), the plans under `docs/` (`docs/roadmap-driver-plan.md`, `docs/journal-sql-refactor-plan.md`; box-000710-8e20cb52 tracks their sweep), and `tickets/`.
- `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_readme.py`, `tests/unit/test_help.py`, `tests/unit/test_main_verb_groups.py`, `tests/unit/test_roadmap_ship.py`, `tests/integration/test_help.py` and `tests/integration/test_main_verb_groups.py` stay unedited and passing; they already walk the parser and groups, match run-guide rows to parser paths, list the stderr print owners, and call `clutch/release.py` without the CLI.

## Scope fence
- clutch/__main__.py
- clutch/release.py
- clutch/roadmap.py
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_main_release_group.py
- tests/unit/test_release.py
- tests/unit/test_release_publish.py
- tests/unit/test_roadmap_merged.py
- tests/integration/test_release.py
- tests/integration/test_release_publish.py
- tests/integration/test_ask_plan_drain.py

## Acceptance criteria
1. `tests/unit/test_main_release_group.py::test_release_group_parses`: `_parser().parse_args(["release", "bump", "--minor"])` gives `verb == "release"`, `release_verb == "bump"` and `part == "minor"`, and `--patch` gives `part == "patch"`; `["release", "publish"]` gives `release_verb == "publish"`; and `["release"]`, `["release", "bump"]`, `["release", "bump", "--minor", "--patch"]`, `["release", "bump", "--major"]` and `["release", "publish", "--minor"]` raise `SystemExit(2)`. Ruled out: a `bump` that accepts no part or both parts, and a `publish` that gains an option.
2. `tests/unit/test_main_release_group.py::test_old_names_refuse`: `publish` is not a choice of the top-level subparsers, the `release` group's choices are exactly `bump` and `publish`, and `_parser().parse_args(argv)` raises `SystemExit(2)` for `["publish"]`, `["release", "--minor"]` and `["release", "--patch"]`. Ruled out: an alias, hidden parser, group-level `--minor` or argv rewrite that keeps an old form working.
3. `tests/unit/test_main_release_group.py::test_refusals_name_group`: in an empty `tmp_path` (no `config.yaml`), `main` with `["release", "bump", "--minor"]` and with `["release", "publish"]` each returns 2, prints nothing on stdout, and prints exactly one stderr line that starts with `clutch release: ` and contains `config file not found`; `tmp_path` is still empty afterwards. Ruled out: the old `clutch publish:` prefix, a `clutch release bump:` or `clutch release publish:` prefix, and an uncaught exception.
4. `./dev.py test tests/unit/test_release.py tests/unit/test_release_publish.py tests/integration/test_release.py tests/integration/test_release_publish.py` exits 0 with only the argv and pinned text named in Scope in changed and no assertion dropped or loosened: `release bump --minor` takes the `release` lock, bumps, commits, tags, prints `release: tagged v0.2.0 at <sha>` and journals the `release` signal; `release publish` takes the `publish` lock, prints the same `publish: built ...` and `publish: uploaded ...` lines and passes the token to the upload only; a refusal of either prints `clutch release:`; and a tag missing from HEAD refuses with a road containing `clutch release bump --minor`. Ruled out: a changed lock verb, stdout line, journal event or token path, and a missing-tag road that names `clutch release --minor`.
5. `./dev.py test tests/unit/test_main_help.py tests/unit/test_readme.py` exits 0 with both files unchanged. The parser walk checks the `release` group and its two subcommands for a description and examples that parse, and the top-level help lists `release bump` and `release publish` once each with their summaries. `uv run clutch help release bump` prints `usage: clutch release bump [-h] (--minor | --patch)`, what it does, then `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with Scope in (the writer lock; exits 0 when tagged, 2 on refusal), then `Examples:` with `clutch release bump --minor` and `clutch release bump --patch` lines. `uv run clutch help release publish` prints the same parts with the facts in Scope in, and `uv run clutch help release` lists `bump` and `publish` and its examples.
6. `./dev.py test tests/unit/test_host_running.py` exits 0 with that file unchanged; its `test_verb_table_matches_parser` fails while a row still names the removed top-level `publish` or the `release` group lacks a row for one of its subcommands. `grep -cE '^\| .release (bump|publish). \|' clutch/docs/host-running.md` prints `2`, `grep -cE '^\| .(release|publish). \|' clutch/docs/host-running.md` prints `0` (at HEAD, `2`), and ``grep -c '`box dismiss`, `release bump`, `release publish`, `engine run`' clutch/docs/host-running.md`` prints `1`. ``sed -n '/^### 2.1 Verbs/,/^### 2.2/p' docs/how-clutch-works.md | grep -cE '^\| .release (bump|publish)[ `]'`` prints `2`, and the same range piped to ``grep -cE '^\| .(release --|publish`)'`` prints `0` (at HEAD, `2`).
7. `./dev.py test tests/integration/test_ask_plan_drain.py` exits 0: the rendered plan-ticket-drain prompt contains `clutch release bump --minor`, and `test_prompts_name_only_existing_verbs` passes unedited. That test fails while a rendered prompt names `` `clutch release --minor``, because its pattern reads `--minor` as a subcommand the `release` group lacks.
8. `git grep -nE 'clutch (publish|release --)|release --(minor|patch)' -- README.md CLAUDE.md AGENTS.md hosts/fixture/CLAUDE.md clutch docs/how-clutch-works.md tests vscode-clutchwork` prints nothing; at HEAD `8a832338` it prints 15 lines. `git grep -nE '(retry|retrying|before) (release|clutch publish)"' -- clutch` prints nothing (at HEAD, 9 lines). `git grep -c 'clutch release publish' -- clutch/release.py clutch/docs/host-contract.md docs/how-clutch-works.md` prints `clutch/docs/host-contract.md:1`, `clutch/release.py:6` and `docs/how-clutch-works.md:2`. Ruled out: a road, prompt, host guide, document or test left naming a removed form.
9. `./dev.py test tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_ship.py tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py` exits 0 with only `test_missing_tag_refuses`'s pattern changed among them; `test_roadmap_ship.py` passes unedited, and `test_stderr_prints_have_one_prefixed_owner` still finds the owners `_fail`, `handle_issue` and `handle_probe`.
10. `./dev.py test` exits 0; Check's `unit` and `integration` mechanical checks in `config.yaml` run both full suites. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is the known base flake (box-000706-10233120) and is verified on the base commit, not chased.

## Verification
```
./dev.py test tests/unit/test_main_release_group.py tests/unit/test_release.py tests/unit/test_release_publish.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_ship.py tests/unit/test_main_help.py tests/unit/test_readme.py tests/unit/test_host_running.py tests/unit/test_help.py
./dev.py test tests/integration/test_release.py tests/integration/test_release_publish.py tests/integration/test_ask_plan_drain.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `publish` still runs as a top-level command, or `release --minor|--patch` still parses without `bump`, through an alias, a hidden or suppressed parser, a group-level option or argv rewriting in `main`.
- An argument, stdout line, read, write, lock verb, journal event or exit code of the two commands changes, other than the help text, argparse's usage and error lines, the refusal prefix and the roads named in Scope in.
- `clutch/release.py` or `clutch/roadmap.py` changes beyond the road strings named in Scope in, or `handle_release`, `handle_publish`, the `release` config block, its keys or the `release` journal signal is renamed.
- A file outside the fence changes, including `clutch/hostfiles.py`, a managed block, `clutch/help.py`, `clutch/observe.py`, `vscode-clutchwork/`, `README.md`, `dev.py`, `docs/roadmap.md` or a plan under `docs/`.
- An existing assertion is dropped, loosened or changed beyond the argv and pinned text named in Scope in.
- Another command is moved or renamed.

## Time budget
- expected: 25m
- stuck: 50m
