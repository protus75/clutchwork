---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- cli-help-standard

## Context
- clutch/__main__.py::_command
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/observe.py::extension_fields
- clutch/help.py
- clutch/hostfiles.py::CORE_TEMPLATE
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_provider_group.py
- tests/unit/test_main_ticket_group.py
- tests/integration/test_extension_argv.py
- tests/integration/test_ask_plan_drain.py::test_prompts_name_only_existing_verbs

## On-demand
- README.md
- clutch/specs/ask/author.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/review.md
- clutch/docs/host-contract.md
- vscode-clutchwork/extension.js
- tests/vscode_task_identity.js
- tests/integration/test_watch.py
- tests/integration/test_cli.py
- tests/integration/test_status.py

## Goal / Why
Roadmap row 137 (`cli-group-view`), group `view`. `cli-help-standard` (row 129, merged at `e09d9e05`) added `_command` in `clutch/__main__.py` and the repo-local rules in `CLAUDE.md` section A: every command carries help to the standard through `_command`, every command lives under a top-level group, and a command change updates every document that describes it in the same change. Rows 130-136 (merged at `fcefb4f6`, `9de3d083`, `f2a246d7`, `084b9e48`, `8362970e`, `3415221a` and `81f93f59`) built the `engine`, `ticket`, `box`, `config` and `provider` groups that way. At HEAD (`dca6ea04`) the read-only projections `watch`, `snapshot`, `status` and `stats` are still top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help status` prints no reads, writes, lock, exit codes or examples. 33 lines of `README.md`, the three conduct files, `clutch/` (engine roads, the core template, four ask prompts, the host guides) and `tests/` spell them `clutch status|stats|snapshot|watch`, and the VS Code extension's one bootstrap argv is `['snapshot']`.

When this ticket is done:
- `clutch view watch [--once]`, `clutch view snapshot`, `clutch view status` and `clutch view stats [--window W] [--json] [--tree]` take the same arguments and defaults, print the same stdout, read the same files, write nothing, take no lock, and exit with the same codes as `clutch watch`, `clutch snapshot`, `clutch status` and `clutch stats` do at HEAD. `view watch` and `view snapshot` still run git with `GIT_OPTIONAL_LOCKS=0`, and `view status` and `view stats` still do not. The only visible differences are the help text, argparse's own usage and error lines, the refusal prefix (`clutch view:`), the `view watch` header line, the four roads that name `clutch status`, and the documents, prompts, conduct block, extension argv and tests that name these commands (all in Scope in).
- `clutch watch`, `clutch snapshot`, `clutch status` and `clutch stats` no longer parse: argparse exits 2 with an invalid-choice error. There is no alias (`CLAUDE.md` "No dual-path code").
- The `view` group and its four subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them.
- Every caller names the new form in the same change: the engine's roads, the core template and the three managed blocks it renders, the author, drain-loop, plan-ticket-drain and review prompts, `README.md`, the host guides, `docs/how-clutch-works.md`, the snapshot's argv tables and help topic, the extension's bootstrap argv and its test harness, and the tests.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140), so a person or agent finds the read-only views together under `clutch help view`, each with what it reads and that it takes no lock. Rows 138-140 move the rest.

Transition, once. Supervisors and agents: the conduct block (`CLAUDE.md`, `AGENTS.md`, "Read `clutch status`") and every prompt rendered before this merges (`clutch prompt drain-loop` and `clutch prompt plan-ticket-drain`, which read `clutch status` every tick, and `clutch prompt author` and `clutch prompt review`, which run it before each ticket write) hold `clutch status`. After the merge that command exits 2 with an argparse invalid-choice error and prints no projection, so a supervising loop that reads it each tick sees an error instead of the queue. Re-render the prompt or re-read the conduct file, or run `clutch view status`. A road printed by a process started before the merge (a verdict's "`clutch status` shows the outcome", an unknown box id's "name ids that clutch status lists") names the old form; run `clutch view status`. No running engine needs a restart: drain and serve never spawn these commands, no lock verb changes, and the self-upgrade re-exec runs `engine drain`, whose stale-conduct check passes because this change refreshes `CLAUDE.md` and `AGENTS.md` in the same commit. Another host gets the new conduct block when it runs `clutch core` after upgrading, which `engine drain`, `engine serve` and `engine run` already require. VS Code extension: an installed extension built before this merge (the owner's is 0.3.0, from `dist/vscode-clutchwork-0.3.0.vsix`) runs `clutch snapshot` on every refresh. After the merge that exits 2, so until the new extension is installed the views keep the last snapshot they loaded and show the argparse error on each refresh (after a window reload, only the error), and the Stats view and the Engine picker's Status action, whose argv come from that older snapshot, run the removed `stats` and `status`. `vscode-clutchwork/package.json` gets the next minor version, so `./dev.py vscode-package` builds a new `dist/vscode-clutchwork-<version>.vsix` instead of printing `kept` for the old file. Install it from the VS Code Extensions view (`...` menu, Install from VSIX..., choose that file), then run Developer: Reload Window. `./dev.py vscode` builds and installs in one step instead, and bumps the patch in `package.json`. The new extension run against a clutch from before this merge (another host on an older release) gets exit 2 from `clutch view snapshot`; upgrade clutch there first. Publishing the new VSIX to the Marketplace is a separate step outside this ticket.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `watch`, `snapshot`, `status` and `stats` parsers. Add a group `view` where the `watch` parser was, the way `ticket`, `engine`, `box`, `config` and `provider` are built: a one-line summary (for example "show read-only engine views"), a `description` of what the group covers, an `Examples:` epilog whose `clutch view ...` line parses, and `argparse.RawDescriptionHelpFormatter`. Its subparsers take `dest="view_verb"` and `required=True`. Its four subcommands are built with `_command`, with every field, keep their one-line summaries, and keep their arguments exactly. Read each fact from its `docs/how-clutch-works.md` section 2.1 row and its handler before writing it:
  - `watch`, with `--once` (`store_true`). Facts: prints a live text view of the configured host state, refreshing every three seconds until Ctrl-C; `--once` prints one view. Reads config, the journal, the engine log, tickets, git state and the process list. Writes nothing. Lock: none; it works while an engine holds the writer lock. Exits 0 when stopped or printed, 2 on refusal. Examples `clutch view watch` and `clutch view watch --once`.
  - `snapshot`, no arguments. Facts: prints the extension snapshot as JSON, including the absolute state directory and the resolved config path. Reads config, the journal, the engine log, lockfiles, the box, tickets and git state. Writes nothing. Lock: none. Exits 0 when printed, 2 on refusal. Example `clutch view snapshot`.
  - `status`, no arguments. Facts: prints the journal projection of section 10.3. Reads config, the journal, the box, the retro spec, `HEAD` and committed checks records. Writes nothing. Lock: none. Exits 0 when printed, 2 on refusal. Example `clutch view status`.
  - `stats`, with `--window` (default `7d`), `--json` and `--tree` (`store_true`). Facts: prints a health and efficiency projection over a time or ticket window; `--json` prints it as JSON and `--tree` as the extension's tree. Reads config, the journal, tickets and committed checks records. Writes nothing. Lock: none. Exits 0 when printed, 2 on refusal (a bad window). Examples `clutch view stats` and `clutch view stats --window 3d --json`.
- Dispatch: `handlers` drops the `"snapshot"`, `"watch"`, `"stats"` and `"status"` entries and gains `"view"`, dispatching by `args.view_verb` to the unchanged `handle_watch` (for `watch` and `snapshot`), `handle_status` and `handle_stats`. All four still run after the config load and checkout build, as today. `handle_watch` tests `args.view_verb == "snapshot"` where it tested `args.verb`. The checkout's git env keeps `GIT_OPTIONAL_LOCKS=0` for exactly `view watch`, `view snapshot` and `ticket lint`: `args.verb in {"watch", "snapshot"}` becomes `(args.verb == "view" and args.view_verb in {"watch", "snapshot"})`. `ruff format` then splits that `env=` dict over lines; no other line changes.
- Refusals: `handle_stats`'s bad-window refusal `_fail("stats", ...)` becomes `_fail(args.verb, ...)`, so it prints `clutch view: bad window 0d -- use <N>h, <N>d, or <N>t`. Every other refusal already goes through `_fail(args.verb, ...)` and now prints `clutch view: ...`. No `print(..., file=sys.stderr)` is added.
- Roads: the `UnknownBoxId` branch's `name ids that clutch status lists` becomes `name ids that clutch view status lists`, and `_verdict`'s `` -- `clutch status` shows the outcome `` becomes `` -- `clutch view status` shows the outcome ``.

In, other code:
- `clutch/status.py::_box_admission`: the road `` name ids that `clutch view status` lists ``.
- `clutch/box.py` (`Box.resolve`): `` ...; its resolution stands and `clutch view status` shows it ``.
- `clutch/observe.py`: `extension_fields`'s `commands` entry `stats` becomes `["view", "stats", "--tree"]` (the key and every other entry stay); the snapshot's `engineVerbs` Status entry's `argv` becomes `["view", "status"]` (label and detail stay); and `text_snapshot`'s first line becomes `f"clutch view watch  {...}"`, so the `view watch` header names the command that prints it.
- `clutch/help.py`: topic `verb.status` keeps its key, and its `verb` field (the run-guide row it reads) becomes `view status`: the topic loop's last `else _verb` becomes `else f"view {_verb}"` (only `status` reaches it). `COMMANDS` and every topic key are unchanged.
- `clutch/hostfiles.py` `CORE_TEMPLATE`: the Diagnosis bullet's "Read `clutch status`," becomes "Read `clutch view status`,". This adds 5 bytes (8,125 to 8,130, under the 8,192 cap). Refresh the managed blocks with `uv run clutch core` at the checkout root (`CLAUDE.md`, `AGENTS.md`) and in `hosts/fixture` (`hosts/fixture/CLAUDE.md`), never by hand, and regenerate `GOLDEN` in `tests/integration/test_hostfiles.py` with `uv run python -m tests.integration.test_hostfiles`, then `ruff format` it. Nothing outside the managed blocks changes in the three conduct files. Rule home: an existing host rule, edited in its home `CORE_TEMPLATE`.
- `vscode-clutchwork/extension.js`: `Snapshot.refresh`'s `runData(root, ['snapshot'], ...)` becomes `runData(root, ['view', 'snapshot'], ...)`. This is the one argv the extension holds itself, because it is how the extension gets the snapshot that supplies every other argv (`CLAUDE.md` "The extension is a thin wrapper"). Nothing else in the file changes.
- `vscode-clutchwork/package.json`: only `version` changes, to the next minor above the version on main (`0.3.0` at `dca6ea04`, so `0.4.0`), so the new VSIX is distinct from the installed one.

In, prompts (these files carry no `version`): every `` `clutch status` `` becomes `` `clutch view status` ``, and `` `clutch roadmap status` `` stays: `clutch/specs/ask/author.md` (the write check), `clutch/specs/ask/drain-loop.md` (step 1's observe list, the box bullet's "listed by", and step 5's `merged:` count), `clutch/specs/ask/plan-ticket-drain.md` (the doctor bullet and the "Match this checkout's engine" bullet) and `clutch/specs/ask/review.md` (its first paragraph).

In, documents. Only references to the four commands change:
- `README.md`: step 5's "watch `clutch view status` and `clutch view watch`", and the `# Observing` lines `uv run clutch view status`, `uv run clutch view watch` and `uv run clutch view stats`, their comments aligned with each other.
- `clutch/docs/host-running.md`: the first cells of the `watch`, `snapshot`, `status` and `stats` rows become `view watch`, `view snapshot`, `view status` and `view stats`, in place, text unchanged.
- `clutch/docs/host-contract.md`: the VS Code extension paragraph's "The extension calls `view snapshot`" and "`clutch view watch [--once]` provides", and Onboarding step 9's "with `clutch view status`".
- `docs/how-clutch-works.md`: the section 2.1 rows begin `` `view watch [--once]` ``, `` `view snapshot` ``, `` `view status` `` and `` `view stats [--window W] [--json] [--tree]` ``, in place, text unchanged; the extension paragraph's "`clutch view snapshot` builds its data"; "`view status` lists them" (Reject queue paragraph); "With no engine running, `view status` shows such a stem as interrupted"; section 7.1's "`view watch` displays it"; section 8.5's "`view status` prints the total"; and section 10.3's heading `` ### 10.3 `view status` `` and first sentence "`view status` is a write-free projection of the journal:". Nothing links to the old heading's anchor.

In, tests. Only the argv (`"view"` before the subcommand) and the pinned text named here change:
- New `tests/unit/test_main_view_group.py` (criteria 1-4). It builds `_parser()` in memory, calls `main(..., cwd=tmp_path, env={})` in an empty `tmp_path`, and for dispatch replaces `clutch.__main__`'s `load_config`, `Journal`, `CommitLock`, `SubprocessExec`, `Git`, `_status`, `render` and `_stats` and `clutch.observe`'s `snapshot` and `text_snapshot` with fakes, as `tests/unit/test_main_ticket_group.py` does. It reads no repo file and starts no process, and it runs the new parser and dispatch lines of `clutch/__main__.py` (coverage floor 13).
- Argv only: `tests/unit/test_commit_lock.py` (`test_cli_handles_timeout`'s `main(["view", "status"], ...)`); `tests/integration/test_cli.py` (its five `cli(root, "view", "status")` calls, `main(["view", "status"], ...)` and `[sys.executable, "-m", "clutch", "view", "status"]`; a do-not-grow file, fenced only for these, and nothing is added to it); `tests/integration/test_reject_queue.py` (one `main` call); `tests/integration/test_stale_running.py` (two `invoke(stopped, "view", "status")`); `tests/integration/test_stats.py` (three `main(["view", "stats", ...])`); `tests/integration/test_status.py` (five `main(["view", "status"], ...)`); `tests/integration/test_watch.py` (three `main(["--config", str(config), "view", "snapshot"])` and one `"view", "watch", "--once"`; a do-not-grow file, and nothing is added to it).
- Pinned text: `tests/unit/test_observe_extension_fields.py` (`"stats": ["view", "stats", "--tree"]`); `tests/unit/test_paved_roads.py` (`` name ids that `clutch view status` lists ``); `tests/unit/test_verdict_submitted_message.py` and `tests/regress_verdict_submitted_message.py` (`` -- `clutch view status` shows the outcome ``, so the reproducer still prints `{"regression_result": "pass"}`); `tests/integration/test_ask.py` and `tests/integration/test_triage.py` (`-- name ids that clutch view status lists`); `tests/integration/test_status.py` (`test_corrupt_box_does_not_receive_unknown_id_advice`'s negative assertion names `name ids that clutch view status lists`, so it still checks the road main now prints); `tests/integration/test_paved_roads.py` (`` its resolution stands and `clutch view status` shows it ``); `tests/integration/test_stats.py` (`clutch view: bad window 0d -- use <N>h, <N>d, or <N>t`); `tests/integration/test_ask_plan_drain.py` (the author and review phrase lists' `"clutch view status"`); `tests/integration/test_extension_argv.py` (`source.count("['view', 'snapshot']") == 1`); `tests/integration/test_watch.py` (`test_snapshot_display_fields`'s `engineVerbs` detail check reads `snap["help"]["verb." + verb["argv"][1]]` for every entry, because every picker argv is now a group path); `tests/integration/test_hostfiles.py` (`GOLDEN`, regenerated); and `tests/vscode_task_identity.js` (its fake `execFile` answers when `args.join(' ') === 'view snapshot'`, so `tests/regress_vscode_task_identity.py` still prints `{"regression_result": "pass"}`).
- A scratch prototype of exactly this change on `977f561b` touched the 38 fenced files. With it, 921 unit tests passed with the unit coverage gate, 3,409 integration tests passed, `ruff check` and `ruff format --check` passed, and both reproducers printed pass. Without the test edits the code change failed 4 unit and 26 integration tests in the fenced files, and the reproducer `tests/regress_vscode_task_identity.py` printed `error`. `tests/integration/test_gates.py::test_core_activation_committed_conduct` reads the committed conduct files, so it passes once the refreshed `CLAUDE.md` and `AGENTS.md` are committed. Inside the fence, `dca6ea04` differs from `977f561b` only by `evidence-record-doc-section`'s new section 10.4 and 10.1 row in `docs/how-clutch-works.md`, which the merge test below covers.

Merge order. `estimate-calibration` (row 142 part 1, P1, confirmed and running at this writing, so expected to merge first) fences `clutch/__main__.py`, `clutch/docs/host-running.md`, `clutch/docs/host-contract.md` and `docs/how-clutch-works.md`. It changes the `engine` group's description, adds `engine calibrate` after `retro` in `_parser` and in the `engine` dispatch dict, adds a run-guide row and a section 2.1 row after `engine retro`, a section 11 row, and the host-contract `config-fields` block. This ticket edits the four parsers at the top of `_parser`, the four `handlers` entries above `roadmap`, the git env line, `handle_watch`, `handle_stats` and two roads, the first four rows of each verb table, and host-contract's VS Code extension paragraph and Onboarding step 9. No line is shared or adjacent. Its added text names none of the four commands (`clutch/calibration.py` imports `clutch.stats._summary`, a module name this ticket keeps), so every criterion here and there holds in either order; only the top-level help gains `engine calibrate`. Parts 2 and 3 (`estimate-calibration-idle` and `estimate-calibration-author`, each depending on part 1) also fence `docs/how-clutch-works.md`. They edit section 7.1's loop item 2, a new paragraph in section 7.2, section 9.3, the section 2.1 row and the section 11 row; this ticket's nearest edit is section 7.1's "`view watch` displays it", nine lines below item 2, so either order merges. `evidence-record-doc-section` merged at `7fb2ebfc`: it inserted `### 10.4 Evidence records` after section 10.3's list and changed the 10.1 `evidence/` row, and this ticket renames the 10.3 heading and its first sentence, above that list. Its section names no command, and this ticket's criteria check named sentences and the section 2.1 table, never every backticked `status` in the document, so a later section naming an `exit.status` field cannot break them. `evidence-scoped-call-key` merged at `efca4c45` and shares no file. In a scratch three-way merge of this ticket's prototype with `estimate-calibration`'s prototype patch and `evidence-record-doc-section`'s diff, git merged every shared file with no conflict, and 927 unit tests, 3,410 integration tests and every grep in the criteria here passed. Rows 138-140 start from this ticket's merged code.

Out:
- An alias of any kind for the old names; every other command, including `roadmap status` (a `roadmap` subcommand whose name stays), `prompt`, and `doctor`, `core` and `docs` (row 138).
- Python and data names: `handle_watch`, `handle_stats`, `handle_status`, `_status`, `_stats`, the `clutch/status.py`, `clutch/stats.py` and `clutch/observe.py` modules and their functions, the snapshot's field names (`watch`, `engineVerbs`, the `commands` key `stats`), help topic keys (`verb.status`, `view.clutch.stats`, `stat.*`), extension view, command and setting ids (`clutch.stats`, `clutch.statsWindow`), and every test file and function name.
- Output other than the refusal prefix, the `view watch` header and the four roads: the projection, the stats text and JSON, and the snapshot JSON.
- Prose naming the projection, the Stats view or the picker action, not the command: "The picker also runs serve, stop, kill, status, or retro", "The collapsed Stats view", and host-contract's "Both verbs work while the engine holds its lock".
- `vscode-clutchwork/` beyond the bootstrap argv and the version (its other argv come from the snapshot, its README names no command), `dev.py` and `tests/integration/test_dev.py` (its `status` case checks that `dev.py` rejects engine verbs), `CLAUDE.md`'s repo-local "`stats --tree` was unreachable" incident note outside the managed block, `CHANGELOG.md` (release history), `CLUTCH_PLAN.md` (frozen), `docs/roadmap.md`, the plans under `docs/` (`docs/parallel-tickets-plan.md`, `docs/journal-sql-refactor-plan.md`), and `tickets/`.
- `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_readme.py`, `tests/unit/test_help.py`, `tests/integration/test_help.py`, `tests/integration/test_main_verb_groups.py`, `tests/integration/test_ask_drain_loop_agent.py` and `tests/integration/test_menu_verb_parity.py` stay unedited and passing; they already walk the parser and groups, find run-guide rows by `TOPICS[key]["verb"]`, check the first word of each `uv run clutch` line, list the stderr print owners, and check prompt phrases.

## Scope fence
- clutch/__main__.py
- clutch/observe.py
- clutch/help.py
- clutch/box.py
- clutch/status.py
- clutch/hostfiles.py
- clutch/specs/ask/author.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/review.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- README.md
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- vscode-clutchwork/extension.js
- vscode-clutchwork/package.json
- tests/unit/test_main_view_group.py
- tests/unit/test_observe_extension_fields.py
- tests/unit/test_paved_roads.py
- tests/unit/test_verdict_submitted_message.py
- tests/unit/test_commit_lock.py
- tests/integration/test_ask.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_cli.py
- tests/integration/test_extension_argv.py
- tests/integration/test_hostfiles.py
- tests/integration/test_paved_roads.py
- tests/integration/test_reject_queue.py
- tests/integration/test_stale_running.py
- tests/integration/test_stats.py
- tests/integration/test_status.py
- tests/integration/test_triage.py
- tests/integration/test_watch.py
- tests/regress_verdict_submitted_message.py
- tests/vscode_task_identity.js

## Acceptance criteria
1. `tests/unit/test_main_view_group.py::test_view_group_parses`: `_parser().parse_args(["view", "watch"])` gives `verb == "view"`, `view_verb == "watch"` and `once is False`, and `["view", "watch", "--once"]` gives `once is True`; `["view", "snapshot"]` and `["view", "status"]` give those `view_verb` values; `["view", "stats"]` gives `window == "7d"`, `json is False` and `tree is False`, and `["view", "stats", "--window", "3t", "--json", "--tree"]` gives `"3t"`, `True` and `True`; and `["view"]`, `["view", "snapshot", "--once"]`, `["view", "status", "extra"]` and `["view", "stats", "--once"]` raise `SystemExit(2)`. Ruled out: a changed arity, default or option.
2. `tests/unit/test_main_view_group.py::test_old_names_refuse`: none of `watch`, `snapshot`, `status` and `stats` is a choice of the top-level subparsers, each is a choice of the `view` group, and `_parser().parse_args([name])` raises `SystemExit(2)` for each. Ruled out: an alias, hidden parser or argv rewrite that keeps an old name working.
3. `tests/unit/test_main_view_group.py::test_refusals_name_group`: in an empty `tmp_path` (no `config.yaml`), `main` with each of `["view", "watch", "--once"]`, `["view", "snapshot"]`, `["view", "status"]` and `["view", "stats"]` returns 2, prints nothing on stdout, and prints exactly one stderr line that starts with `clutch view: ` and contains `config file not found`; `tmp_path` is still empty afterwards. Ruled out: the old `clutch status:` or `clutch stats:` prefix, a `clutch view status:` prefix, and an uncaught exception.
4. `tests/unit/test_main_view_group.py::test_dispatch_and_optional_locks`: with the fakes named in Scope in (the fake `Git` records each `env` it is built with), `main` returns 0 for `["view", "snapshot"]`, `["view", "watch", "--once"]`, `["view", "status"]` and `["view", "stats", "--json"]`, printing exactly the fake snapshot as JSON, the fake text view, the rendered fake projection and the fake stats as JSON; the recorded `GIT_OPTIONAL_LOCKS` values are `["0", "0", None, None]` in that order; and `["view", "stats", "--window", "0d"]` returns 2 with stderr exactly `clutch view: bad window 0d -- use <N>h, <N>d, or <N>t\n`. Ruled out: `snapshot` dispatched to the text view or the reverse, `view status` or `view stats` gaining `GIT_OPTIONAL_LOCKS` or `view watch` or `view snapshot` losing it, and the bad-window refusal printing `clutch stats:`.
5. `./dev.py test tests/unit/test_main_help.py tests/unit/test_readme.py` exits 0 with both files unchanged. The parser walk checks the `view` group and its four subcommands for a description and examples that parse, the top-level help lists `view watch`, `view snapshot`, `view status` and `view stats` once each with their summaries, and every `uv run clutch` line of `README.md` names a top-level command. `uv run clutch help view stats` prints `usage: clutch view stats`, what it does, then `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with Scope in (writes nothing; no lock; exits 0 when printed, 2 on a bad window), its three options, then `Examples:` with a `clutch view stats` line. `uv run clutch help view watch`, `uv run clutch help view snapshot` and `uv run clutch help view status` print the same parts with the facts in Scope in, and `uv run clutch help view` lists the four subcommands and its examples.
6. `./dev.py test tests/unit/test_host_running.py` exits 0 with that file unchanged, and `grep -cE '^\| .view (watch|snapshot|status|stats). \|' clutch/docs/host-running.md` prints `4`. Its `test_verb_table_matches_parser` fails while a row still names a removed top-level command or the `view` group lacks a row for one of its subcommands. ``sed -n '/^### 2.1 Verbs/,/^### 2.2/p' docs/how-clutch-works.md | grep -cE '^\| .view (watch|snapshot|status|stats)( [^|]*)?. \|'`` prints `4`, and `grep -cE '^\| .(watch|snapshot|status|stats)( [^|]*)?. \|'` prints `0` for `clutch/docs/host-running.md` and for that section 2.1 range (at HEAD, `4` each).
7. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py` exits 0 with both files unchanged. `help.TOPICS["verb.status"]["verb"] == "view status"`, and `help.COMMANDS` and the set of `TOPICS` keys equal main's. Ruled out: a `verb.status` topic whose run-guide row is gone, which raises `LookupError` when the snapshot builds its help.
8. `./dev.py test tests/unit/test_observe_extension_fields.py tests/integration/test_watch.py tests/integration/test_extension_argv.py` exits 0. `test_extension_fields` expects `["view", "stats", "--tree"]` for `stats` and main's value for every other key, and `test_extension_commands_parse` passes unedited. `test_snapshot_display_fields` reads every `engineVerbs` detail by `argv[1]`, so a Status entry left as `["status"]` raises `IndexError`; `grep -c '"argv": \["view", "status"\]' clutch/observe.py` prints `1`. `test_extension_argv_from_snapshot` finds `['view', 'snapshot']` exactly once in `vscode-clutchwork/extension.js`, and `git grep -n "\['snapshot'\]" -- vscode-clutchwork` prints nothing. `uv run python tests/regress_vscode_task_identity.py` prints `{"regression_result": "pass"}`. Ruled out: an extension refresh, Stats view or Engine picker Status action that runs a removed command.
9. `vscode-clutchwork/package.json`'s `version` is the next minor above the version on main (`0.4.0` while main has `0.3.0`), and `git diff main -- vscode-clutchwork/package.json` changes only that line. `git diff main -- vscode-clutchwork/extension.js` changes only the `runData(root, ['view', 'snapshot'], ...)` line.
10. `CORE_TEMPLATE` in `clutch/hostfiles.py` contains ``Read `clutch view status`,``, and `len(CORE_TEMPLATE) <= 8192`. `./dev.py test tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/integration/test_contention_rules.py` exits 0, so `GOLDEN` is regenerated and the managed blocks of `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` match the template byte for byte. `git diff main` of those three files changes only lines between the `clutch:core` markers.
11. `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask.py` exits 0. The author and review prompts' phrase lists require `clutch view status`. `test_prompts_name_only_existing_verbs` passes unedited; it fails while a rendered author, review, drain-loop or plan-ticket-drain prompt still names `` `clutch status``. `grep -c 'clutch view status' clutch/specs/ask/drain-loop.md` prints `3` and `grep -c 'clutch roadmap status' clutch/specs/ask/drain-loop.md` prints main's count.
12. `./dev.py test tests/unit/test_paved_roads.py tests/unit/test_verdict_submitted_message.py tests/integration/test_paved_roads.py tests/integration/test_triage.py tests/integration/test_status.py` exits 0 with the roads named in Scope in, and `uv run python tests/regress_verdict_submitted_message.py` prints `{"regression_result": "pass"}`. Ruled out: a road that names the removed `clutch status`, which an operator following it would see exit 2.
13. `git grep -nE 'clutch (status|stats|snapshot|watch)([^a-z-]|$)' -- README.md CLAUDE.md AGENTS.md hosts/fixture/CLAUDE.md clutch docs/how-clutch-works.md tests vscode-clutchwork` prints nothing; at HEAD `dca6ea04` it prints 33 lines. `grep -c '^### 10.3 .view status.$' docs/how-clutch-works.md` prints `1`, and ``grep -cE '`view status` (lists them|shows such a stem|prints the total|is a write-free)|`view watch` displays it|`clutch view snapshot` builds' docs/how-clutch-works.md`` prints `6`. ``grep -oE 'calls `view snapshot`|`clutch view watch \[--once\]`|with `clutch view status`' clutch/docs/host-contract.md | wc -l`` prints `3`. Ruled out: a reference left in a road, the watch header, the core template, a managed block, a prompt, a host guide, the README, a document or a test.
14. `./dev.py test tests/integration/test_cli.py tests/integration/test_stats.py tests/integration/test_status.py tests/integration/test_stale_running.py tests/integration/test_reject_queue.py tests/unit/test_commit_lock.py` exits 0, with only the argv and pinned text named in Scope in changed in those files and in `tests/integration/test_watch.py`, no assertion dropped or loosened, and nothing added to `tests/integration/test_cli.py` or `tests/integration/test_watch.py`.
15. `./dev.py test` exits 0; Check's `unit` and `integration` mechanical checks in `config.yaml` run both full suites. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is the known base flake (box-000706-10233120) and is verified on the base commit, not chased.

## Verification
```
./dev.py test tests/unit/test_main_view_group.py tests/unit/test_main_help.py tests/unit/test_readme.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_observe_extension_fields.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/unit/test_paved_roads.py tests/unit/test_verdict_submitted_message.py tests/unit/test_commit_lock.py
./dev.py test tests/integration/test_help.py tests/integration/test_watch.py tests/integration/test_extension_argv.py tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py tests/integration/test_contention_rules.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask.py
./dev.py test tests/integration/test_paved_roads.py tests/integration/test_triage.py tests/integration/test_status.py tests/integration/test_cli.py tests/integration/test_stats.py tests/integration/test_stale_running.py tests/integration/test_reject_queue.py tests/integration/test_main_verb_groups.py tests/integration/test_menu_verb_parity.py
uv run python tests/regress_vscode_task_identity.py
uv run python tests/regress_verdict_submitted_message.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `watch`, `snapshot`, `status` or `stats` still runs as a top-level command through an alias, a hidden or suppressed parser, or argv rewriting in `main`.
- An argument, default, stdout line, read, write, lock or exit code of the four commands changes, other than the help text, argparse's usage and error lines, the refusal prefix, the `view watch` header and the roads named in Scope in.
- The set of commands whose git runs with `GIT_OPTIONAL_LOCKS=0` changes, or a view command takes a lock.
- `vscode-clutchwork/` changes beyond the bootstrap argv in `extension.js` and the `version` in `package.json`, or the extension builds, filters or derives any other argv.
- A help topic key, `COMMANDS` entry, snapshot field name or extension command, view or setting id changes.
- A managed block is edited by hand or differs from `CORE_TEMPLATE`, or `CLAUDE.md`, `AGENTS.md` or `hosts/fixture/CLAUDE.md` changes outside its managed block.
- A test is added to a do-not-grow file, or an existing assertion is dropped, loosened or changed beyond the argv and pinned text named in Scope in.
- Another command is moved or renamed, or a file outside the fence changes.

## Time budget
- expected: 30m
- stuck: 60m
- reason: not split, because a rename with no alias moves the parser and every caller in one change (`CLAUDE.md` "No dual-path code"), and the four views share the parser block, the dispatch dict, the run-guide and section 2.1 tables, the core template line and the extension's snapshot argv; a scratch prototype touched 38 files, every edit outside `clutch/__main__.py` and the new test file a one-line text or argv change, and row 130 (75 files, 40m budget) took 10.6 actual Implement minutes and rows 131-136 took 8 to 9.4.
