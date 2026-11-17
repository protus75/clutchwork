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
- clutch/drain.py::reexec_argv
- clutch/observe.py::extension_fields
- clutch/observe.py::drain_processes
- clutch/help.py::help_map
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_help.py
- tests/unit/test_host_running.py
- tests/integration/test_ask_plan_drain.py::prompts
- tests/integration/test_ask_plan_drain.py::test_prompts_name_only_existing_verbs

## On-demand
- clutch/specs/ask/author.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/running.md

## Goal / Why
Roadmap row 130 (`cli-group-engine-run`), group `engine` part 1. `cli-help-standard` (row 129, merged at `e09d9e05`) added `_command` in `clutch/__main__.py` and three repo-local rules in `CLAUDE.md` section A and `AGENTS.md`: every command and subcommand carries help to the standard through `_command`; every command lives under a top-level group; a command change updates every document that describes it in the same change. At HEAD (`60608fe6`) `drain`, `serve`, `run` and `stop` are still top-level verbs with one-line argparse help, and 22 lines of `README.md`, `clutch/` and `docs/how-clutch-works.md` spell them `clutch drain|serve|run|stop`.

When this ticket is done:
- `clutch engine drain`, `clutch engine serve`, `clutch engine run <stem>` and `clutch engine stop` take the same arguments, print the same output, take the same locks, write the same files, commits and journal events, and exit with the same codes as `clutch drain`, `clutch serve`, `clutch run <stem>` and `clutch stop` do at HEAD. The visible differences are the refusal prefix, the paved roads and prompts that name these commands, and the argv the engine and the extension build (Scope in).
- `clutch drain`, `clutch serve`, `clutch run` and `clutch stop` are argparse usage errors (exit 2). No alias, hidden parser or argv rewrite keeps them (CLAUDE.md "No dual-path code").
- The `engine` group and its four subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them.
- Every caller names the new form in the same change: engine argv (detach spawn, self-upgrade re-exec), engine roads, the extension's argv table and help topics, the ask prompts, `README.md`, the host guides, `docs/how-clutch-works.md`, and the tests.

Why: the owner's row 129 rules require every command under a group, and rows 131-140 move the rest. Row 131 (`cli-group-engine-control`) adds `pause`, `resume`, `kill` and `retro` to this group later.

Transition, once: a drain or serve started before this merges re-execs at its next self-upgrade with the argv it was started with (`drain` or `serve`), which the new parser refuses with exit 2 and a usage line in `<state_dir>/drain.out`. Restart it with `clutch engine drain --detach` or `clutch engine serve`. A supervising loop that still holds the old `clutch prompt drain-loop` text must use the new form too.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `stop`, `run`, `drain` and `serve` parsers. Add a group `engine` the way `roadmap` is built: a one-line summary, a `description` of what the group covers, an `Examples:` epilog, and `argparse.RawDescriptionHelpFormatter`. Its subparsers take `dest="engine_verb"` and `required=True`. Its four subcommands are built with `_command`:
  - `drain`, keeping `--detach`, `--parked`, `--deadline` and the suppressed `--stop-lifecycle` exactly as today. Facts: runs every eligible ticket to quiescence (section 7.1); `--detach` starts its own session and appends to `<state_dir>/drain.out`; the self-upgrade re-exec sets `--parked` and `--deadline`; writer lock (with `--detach`, the child takes it); exits 0 at quiescence, 1 when halted or killed, 2 on refusal. Examples include `clutch engine drain` and `clutch engine drain --detach`.
  - `serve`: runs the continuous daemon until `kill`, `engine stop` or a signal (section 7.2); writer lock; exits 0 after kill, stop or a signal, 1 when a component fails, 2 on refusal.
  - `run`, keeping positional `stem`: drives one ticket through intake and every stage; writer lock; exits 0 when it merges, 1 for a non-ok terminal, 2 on refusal.
  - `stop`: with a running drain or serve, publishes a stop request (finish the running ticket, admit nothing new, exit); refuses when nothing runs or a non-engine holder has the lock; takes the writer lock only to probe; exits 0 when submitted, 2 on refusal.
  Read each fact from its `docs/how-clutch-works.md` section 2.1 row and the code before writing it.
- Dispatch: the four subcommands run the same handlers as today, with the same lock verbs (`drain`, `serve`, `run`, `stop`), the same `--detach` short-circuit after config loads, and the same stale-core check before `engine drain`, `engine serve` and `engine run`. Refusals keep going through `_fail(args.verb, ...)`, so an engine refusal prints `clutch engine: <message> -- <road>`, as `roadmap` and `prompt` print their group name and as confirmed row 132 (`cli-group-ticket-authoring`) prints `clutch ticket:`. The stale-core road reads `run clutch core, then commit the conduct files and retry engine <subcommand>`. No `print(..., file=sys.stderr)` is added (`tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner`).
- Built argv: `handle_detach` spawns `[sys.executable, "-m", "clutch", *config, "engine", "drain"]`; the `argv` given to `drain.drain` is `[*config, "engine", "drain"]`; `build_serve`'s default `argv` becomes `("engine", "serve")`. `handle_serve` keeps passing `argv=invocation`, which now holds `engine serve`.
- `_new` prints ``fill these before `engine run {stem}`:``.

In, other engine code (lock verbs, `lockfile.ENGINE_VERBS`, engine.log `verb` fields and control request verbs stay `drain`, `serve`, `run`, `stop`):
- `clutch/drain.py`: `drain()`'s default `argv` becomes `("engine", "drain")`. `Report.render`'s kill and ceiling-halt heads end ``Continue with `clutch engine drain`.``. The halted re-offer road becomes `` `clutch engine drain` re-offers it ``. The dependency-cycle road ends ``then `engine drain` again``.
- `clutch/serve.py`: the default `argv` of `Serve.__init__` and `serve()` becomes `("engine", "serve")`.
- `clutch/observe.py`: in `extension_fields`, `commands` `run`, `serve` and `stop` become `["engine", "run"]`, `["engine", "serve"]` and `["engine", "stop"]`. In `snapshot`, `drainCommand` and the Drain, Serve and Stop `engineVerbs` argv gain `"engine"` before the verb; labels, details and order are unchanged. `drain_processes` matches `<python> -m clutch [--config <path>] engine drain`, and no longer the old `-m clutch drain`. `vscode-clutchwork/` is unchanged: it runs the argv the snapshot supplies.
- `clutch/help.py`: topics `verb.drain`, `verb.serve`, `verb.stop` and `verb.run` keep their keys, and their `verb` field (the run-guide row each reads) becomes `engine drain`, `engine serve`, `engine stop` and `engine run`. `COMMANDS` is unchanged.
- `clutch/status.py::run_admission`: the roads become ``fix the ticket, then `engine run {stem}` again``, ``author it with `clutch new {stem}`, fill it, then `clutch engine run {stem}` ``, and ``"`engine run {d}`" ... first, then `engine run {stem}` `` for unmerged dependencies.
- `clutch/merge.py` and `clutch/mergequeue.py`: their ``re-run `run {...}` `` roads become ``re-run `engine run {...}` ``.
- `clutch/providers.py`: the four `LOGIN_ROAD`s name `clutch engine drain`.

In, prompts (no spec `version` exists for these files): `clutch/specs/ask/author.md` (the "Never run" list), `drain-loop.md` (`clutch engine stop`, `clutch engine drain --detach`), `plan-ticket-drain.md` and `running.md` (`clutch engine stop`).

In, docs (each command spelled as its `engine` path):
- `README.md`: the "Set up a host" stale-block sentence, step 4 of "Author and run tickets", the four `# Running` lines of the command block, the "Stop `serve` before ..." sentence, and step 5's `clutch stop`.
- `clutch/docs/host-running.md`: the `uv run clutch serve` code line; the intro's `serve`, `stop` and `drain`; the first cells of the `stop`, `run`, `drain` and `serve` rows, in place, text unchanged; the `roadmap` row's "`drain` and `serve` run `roadmap author --ahead 2`"; and the "Stop serve before ..." list.
- `clutch/docs/host-contract.md`: onboarding step 8 and the `Instance custody` sentence "A git-checkout engine running `serve`".
- `clutch/docs/host-authoring.md`: Workflow step 4.
- `docs/how-clutch-works.md`: section 2.1 rows `engine run <stem>`, `engine drain [--detach] [--parked STEM] [--deadline ISO]` and `engine serve`, and the control row `` `pause` / `resume` / `kill` / `engine stop` ``; the section 3.2 sentence "`drain` and `serve` intake every pending ticket; `review`, `run`, ..."; the section 8.1 Preflight list; the section 10.1 `drain.out` row (`engine drain --detach`); and the section 12 stale-block bullet.

In, tests:
- New `tests/unit/test_main_engine_group.py`: builds `_parser()` in memory and calls `main(..., cwd=tmp_path, env={})` in an empty `tmp_path`; it reads no repo file and starts no process. It runs the new parser lines and the refusal dispatch lines of `clutch/__main__.py` (coverage floor 13).
- Argv only, the subcommand gaining `"engine"` before it in each list passed to `main`, `cli.main`, `entry.main`, `cli(...)` or `parse_args`, and in the helpers that build one (`[verb, STEM] if verb == "run" else [verb]`, `["run", "work"] if verb == "run" else ["drain"]`, `invoke(root, verb)` with `"stop"`, the `("kill", "stop", "pause", "resume")` and `("review", "run", "order")` loops, the `["review", "run", "confirm", "reject"]` parametrize): `tests/integration/test_caps.py`, `test_checkpoint.py`, `test_cli.py`, `test_control.py`, `test_control_cli.py`, `test_daemon_admission.py`, `test_daemon_composition.py`, `test_daemon_config.py`, `test_daemon_pause.py`, `test_daemon_tasks.py`, `test_diagnose.py`, `test_drain.py`, `test_drain_reentry.py`, `test_drain_signals.py`, `test_harvest.py`, `test_harvest_orphans.py`, `test_heartbeat.py`, `test_hostfiles.py`, `test_intake_scope.py`, `test_kill_cli_activation.py`, `test_kill_failure_suppression.py`, `test_kill_worker_stop.py`, `test_ladder.py`, `test_menu_verb_parity.py`, `test_merge.py`, `test_providers.py`, `test_reconcile.py`, `test_reject_queue.py`, `test_requisition_gate.py`, `test_roadmap_driver.py`, `test_second_problems.py`, `test_serve_lifecycle.py`, `test_stale_running.py`, `test_storm_hold.py`, `test_storm_notification_activation.py`, `test_storm_producer.py`, `test_terminal.py` (all under `tests/integration/`); `tests/unit/test_drain_deadline.py`; `tests/harness/host_loop.py` (its spawned `serve`); and `tests/regress_drain_detach.py`, `tests/regress_drain_park_findings.py` and `tests/regress_drain_signals.py`, so each still runs.
- Pinned values: `tests/integration/test_drain_upgrade.py` (re-exec argv, and its `argv[:8]`/`[8:]` slices become `[:9]`/`[9:]`); `tests/integration/test_drain_detach.py` and `tests/unit/test_drain_detach_cli.py` (spawn argv); `tests/integration/test_restart_timers.py::test_restart_construction_is_idle` (finds `serve` under the `engine` group); `tests/unit/test_observe_extension_fields.py` (the three commands); `tests/integration/test_watch.py` (the `test_drain_processes_only_this_repo` rows, the `engineVerbs` detail lookup, which takes the word after `engine`, the pinned first entry and `drainCommand`); `tests/integration/test_help.py::test_links_resolve` and `::test_verb_what_from_run_guide` (find each topic's row by `TOPICS[key]["verb"]`); `tests/unit/test_host_running.py` (rule in criterion 6); `tests/integration/test_host_onboarding_doc.py` (its `clutch (?:drain|serve)` search becomes `clutch engine (?:drain|serve)`); `tests/integration/test_ask_plan_drain.py` and `tests/integration/test_ask_drain_loop_agent.py` (phrases, criterion 9); `tests/unit/test_paved_roads.py`, `tests/integration/test_paved_roads.py`, the `Continue with` asserts in `tests/integration/test_drain.py` and `tests/integration/test_kill_cli_activation.py`, and the copied login road in `tests/harness/shakeout/providers.py`.

Merge order. The drain runs one ticket at a time from main's tip, so whichever of two overlapping tickets runs second starts from the other's merged code.
- `cli-group-ticket-authoring` (row 132, confirmed) moves `new`, `lint`, `review` and `order` into group `ticket` and edits many of the same files, sometimes the same line (`status.py::run_admission`'s missing-file road, the `observe.py` commands dict, the `help.py` topic loop, `test_menu_verb_parity.py`'s verb loop, `test_intake_scope.py`'s parametrize, `test_paved_roads.py`, `test_stale_running.py`, host-contract onboarding, how-clutch-works sections 3.2 and 8.1). In a line both touch, this ticket changes only the words for `drain`, `serve`, `run` and `stop`; every other word keeps the form main has when it runs. Where a criterion compares a whole dict, table, road or list, the other entries match main, not HEAD `60608fe6`. Both tickets take the same approach to `test_verb_table_matches_parser` and to finding run-guide rows by `TOPICS[key]["verb"]`: if row 132 already merged either change, keep it.
- `rule-restatements-single-home` (running) edits `clutch/docs/host-contract.md` section `## Managed conduct and ticket ownership` and `docs/how-clutch-works.md` sections 3.2 (the bug-evidence bullet), 4.2 and 5.2. This ticket edits other lines of both files, so either order keeps both.
- `projection-helpers-single-owner` (confirmed) edits other functions of `clutch/__main__.py` (`handle_prompt`, `build_control`, `provider_holds`, `handle_suggest`, `build_daemon_core`), `clutch/status.py` (`last_states`), `clutch/observe.py` (`as_events`, `last_bodies`, `queue`, `snapshot`'s box and path lines) and the `EngineLog` sites of `clutch/drain.py` and `clutch/serve.py`. Its rejection of edits to `tests/integration/test_daemon_composition.py` and `tests/integration/test_watch.py` binds its branch only; this ticket's edits there are argv and pins. Either order passes.

Out:
- An alias of any kind for the old names, and `pause`, `resume`, `kill` and `retro` (row 131).
- Lock and journal vocabulary: `Lockfile` verbs, `lockfile.ENGINE_VERBS`, engine.log `verb`, control request `verb`, `observe.lock_verb`.
- Mode names in prose and headings: `### 7.1 \`drain\`` and `### 7.2 \`serve\`` (`clutch/help.py` links them by heading), "rerun drain", "restart serve", "start a drain or serve before submitting stop", "Every ticket read (intake, lint, confirm, drain, serve, run, and Author)", and the rest of `docs/how-clutch-works.md`. Module docstrings.
- `clutch/hostfiles.py` CORE_TEMPLATE, the managed blocks, `CLAUDE.md` and `AGENTS.md`: none names these commands (`grep -nE 'clutch (drain|serve|run|stop)' clutch/hostfiles.py CLAUDE.md AGENTS.md` prints nothing at HEAD), so `clutch core` is not run.
- `dev.py` (no engine verb), `vscode-clutchwork/`, `CLUTCH_PLAN.md`, `docs/roadmap.md` and the plans under `docs/`.
- Textual mentions a test does not parse or compare with code: `tests/unit/test_issue_link.py`'s issue body, the `"clutch drain"` process rows of `tests/unit/test_live_call.py` and `tests/unit/test_live_call_gemini.py`, the lock-holder process strings of `tests/integration/test_watch.py::test_engine_flag_follows_lock_holder` (its holder verb comes from the lockfile), and `tests/integration/serve_rig.py`'s opaque `("--config", "config.yaml", "serve")` re-exec argv with its pass-through check in `tests/integration/test_serve_upgrade.py`.
- `tests/unit/test_main_help.py`: unedited; its parser walk picks up the group.

## Scope fence
- clutch/__main__.py
- clutch/drain.py
- clutch/serve.py
- clutch/observe.py
- clutch/help.py
- clutch/status.py
- clutch/merge.py
- clutch/mergequeue.py
- clutch/providers.py
- clutch/specs/ask/author.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/running.md
- README.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- clutch/docs/host-authoring.md
- docs/how-clutch-works.md
- tests/unit/test_main_engine_group.py
- tests/unit/test_drain_deadline.py
- tests/unit/test_drain_detach_cli.py
- tests/unit/test_host_running.py
- tests/unit/test_observe_extension_fields.py
- tests/unit/test_paved_roads.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_caps.py
- tests/integration/test_checkpoint.py
- tests/integration/test_cli.py
- tests/integration/test_control.py
- tests/integration/test_control_cli.py
- tests/integration/test_daemon_admission.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_config.py
- tests/integration/test_daemon_pause.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_diagnose.py
- tests/integration/test_drain.py
- tests/integration/test_drain_detach.py
- tests/integration/test_drain_reentry.py
- tests/integration/test_drain_signals.py
- tests/integration/test_drain_upgrade.py
- tests/integration/test_harvest.py
- tests/integration/test_harvest_orphans.py
- tests/integration/test_heartbeat.py
- tests/integration/test_help.py
- tests/integration/test_host_onboarding_doc.py
- tests/integration/test_hostfiles.py
- tests/integration/test_intake_scope.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_ladder.py
- tests/integration/test_menu_verb_parity.py
- tests/integration/test_merge.py
- tests/integration/test_paved_roads.py
- tests/integration/test_providers.py
- tests/integration/test_reconcile.py
- tests/integration/test_reject_queue.py
- tests/integration/test_requisition_gate.py
- tests/integration/test_restart_timers.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_second_problems.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_stale_running.py
- tests/integration/test_storm_hold.py
- tests/integration/test_storm_notification_activation.py
- tests/integration/test_storm_producer.py
- tests/integration/test_terminal.py
- tests/integration/test_watch.py
- tests/harness/host_loop.py
- tests/harness/shakeout/providers.py
- tests/regress_drain_detach.py
- tests/regress_drain_park_findings.py
- tests/regress_drain_signals.py

## Acceptance criteria
1. `tests/unit/test_main_engine_group.py::test_engine_group_owns_the_four`: the `engine` group's subcommands include `drain`, `serve`, `run` and `stop`, and none of the four is a top-level command. It checks inclusion, not equality, so row 131 adds subcommands without editing it. Ruled out: a top-level parser kept beside the group.
2. `tests/unit/test_main_engine_group.py::test_old_names_are_refused`: in an empty `tmp_path`, `main(argv, cwd=tmp_path, env={})` for each of `["drain"]`, `["serve"]`, `["run", "x"]` and `["stop"]` raises `SystemExit(2)`, and stderr contains `invalid choice`. Ruled out: an argv rewrite in `main`, which would reach the config load and return 2 with a `clutch engine:` line instead.
3. `tests/unit/test_main_engine_group.py::test_subcommands_keep_their_arguments`: `_parser().parse_args(["engine", "drain", "--detach", "--parked", "a", "--parked", "b", "--deadline", "2026-01-01T02:00:00+00:00"])` gives `detach is True`, `parked == ["a", "b"]` and a non-`None` `deadline`; `["engine", "run", "x"]` gives `stem == "x"`; `["engine", "serve"]` and `["engine", "stop"]` parse; `["engine", "run"]` raises `SystemExit(2)`. Ruled out: a dropped option or a lost `stem`.
4. `tests/unit/test_main_engine_group.py::test_refusal_names_the_group`: in an empty `tmp_path` (no `config.yaml`), `main` with each of `["engine", "drain"]`, `["engine", "serve"]`, `["engine", "run", "x"]` and `["engine", "stop"]` returns 2, prints nothing on stdout, and prints one stderr line that starts with `clutch engine: ` and contains `config file not found`. Ruled out: `clutch drain:` (a dispatch that rewrites the verb), `clutch engine drain:`, and an uncaught exception.
5. `./dev.py test tests/unit/test_main_help.py` exits 0 with that file unchanged. Its parser walk now checks the `engine` group and its four subcommands for a description and examples that parse, and its top-level listing shows `engine drain`, `engine serve`, `engine run` and `engine stop` once each with their summaries. `uv run clutch help engine drain` prints `usage: clutch engine drain`, then what it does with `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with the facts in Scope in, then its options, then `Examples:`.
6. `./dev.py test tests/unit/test_host_running.py` exits 0, and `grep -cE '^\| .engine (drain|serve|run|stop). \|' clutch/docs/host-running.md` prints `4`. `test_verb_table_matches_parser` accepts a row naming a top-level command or a `<group> <subcommand>` path; it fails on a row naming a removed top-level command such as `drain`, on an `engine` group with a row for some but not all of its subcommands, and on a repeated row, and it passes with the single `roadmap` and `prompt` rows.
7. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py` exits 0 with `tests/unit/test_help.py` unchanged. `help.TOPICS["verb.drain"]["verb"] == "engine drain"`, `help.COMMANDS` is unchanged, and `test_verb_what_from_run_guide` checks that the `what` of `verb.drain` is the text of the `engine drain` run-guide row. Ruled out: a `verb.*` topic whose row is gone, which raises `LookupError` when the snapshot builds its help, and a renamed topic key.
8. `./dev.py test tests/unit/test_observe_extension_fields.py tests/integration/test_watch.py tests/unit/test_drain_detach_cli.py tests/integration/test_drain_detach.py tests/integration/test_drain_upgrade.py` exits 0. The snapshot's `commands` hold `["engine", "run"]`, `["engine", "serve"]` and `["engine", "stop"]`; `drainCommand` and the first `engineVerbs` argv are `["engine", "drain", "--detach"]`; `drain_processes` counts `-m clutch engine drain` rows of this checkout only; `engine drain --detach` spawns `[sys.executable, "-m", "clutch", "engine", "drain"]` (with `--config <path>` before `engine` when given); and the self-upgrade re-exec argv is `["uv", "run", "--project", <engine>, "python", "-m", "clutch", "engine", "drain", "--parked", ...]`. Ruled out: a child or re-exec argv naming bare `drain`, which the new parser refuses with exit 2.
9. `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py` exits 0. The `prompts` fixture also renders `drain-loop` and `running`. `test_prompts_name_only_existing_verbs` checks the second word of every `` `clutch <group> <word>`` against that group's subcommands, for any group found by walking the parser, in place of its `prompt`- and `roadmap`-only checks. The phrase `clutch stop` becomes `clutch engine stop` and `clutch drain --detach` becomes `clutch engine drain --detach`. Ruled out: a prompt naming `` `clutch stop` `` (first word not a command) or `` `clutch engine drian` `` (not a subcommand).
10. `git grep -nE 'clutch (drain|serve|run|stop)([^a-z-]|$)' -- README.md clutch docs/how-clutch-works.md` prints nothing; at HEAD `60608fe6` it prints 22 lines. ``git grep -nE '`(drain|serve|run|stop)( [^`]*)?`' -- README.md 'clutch/docs/host-*.md'`` prints nothing; at HEAD it prints 11 lines. ``git grep -nE '`(run \{|drain` again)' -- clutch`` prints nothing; at HEAD it prints 6 lines. ``git grep -nE '\("(serve|drain)",\)' -- clutch`` prints nothing (at HEAD, the four default `argv`s). `grep -c 'conduct files and retry engine ' clutch/__main__.py` prints `1`. Ruled out: a reference left in a doc, prompt, default argv or engine road.
11. In `docs/how-clutch-works.md` section 2.1, `grep -nE '^\| .(run|drain|serve|stop)( [^|]*)?. \|' docs/how-clutch-works.md` prints nothing (at HEAD it prints the `run <stem>`, `drain [...]` and `serve` rows), `grep -cE '^\| .engine (run|drain|serve)( [^|]*)?. \|' docs/how-clutch-works.md` prints `3`, and `grep -cE '^\| .pause. / .resume. / .kill. / .engine stop. \|' docs/how-clutch-works.md` prints `1`.
12. `./dev.py test tests/unit/test_paved_roads.py tests/integration/test_paved_roads.py` exits 0, asserting `` Continue with `clutch engine drain`. ``, `` `clutch engine drain` re-offers it ``, the `run_admission` missing-file road ending `` then `clutch engine run item` `` and the two login roads ending `` then `clutch engine drain` ``.
13. `./dev.py test` exits 0. In the test files of Scope in only the argv lists, the slices, phrases, roads, process rows, help-row lookups and the table rule named there change; no assertion is dropped. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is the known base flake (box-000706-10233120) and is verified on the base commit, not chased.

## Verification
```
./dev.py test tests/unit/test_main_engine_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_observe_extension_fields.py tests/unit/test_paved_roads.py tests/unit/test_drain_detach_cli.py tests/unit/test_drain_deadline.py
./dev.py test tests/integration/test_help.py tests/integration/test_watch.py tests/integration/test_drain_detach.py tests/integration/test_drain_upgrade.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_paved_roads.py tests/integration/test_host_onboarding_doc.py tests/integration/test_main_verb_groups.py
./dev.py test
```

## Definition of rejected
The branch is rejected, even if it passes, when any old name still parses (a top-level parser, a hidden or suppressed subparser, or an argv rewrite in `main`); an argument, default, output line other than the named roads, exit code, lock, commit or journal event of the four commands changes; a lock verb, `ENGINE_VERBS`, an engine.log `verb` or a control request verb changes; `pause`, `resume`, `kill` or `retro` moves; a help field gets a default, or command help is copied into `clutch/help.py`; `clutch/hostfiles.py`, `CLAUDE.md`, `AGENTS.md`, `vscode-clutchwork/`, `tests/integration/serve_rig.py`, `tests/integration/test_mergequeue.py` or `tests/integration/test_stages.py` changes; or a test is added to a do-not-grow file, or an existing assertion is dropped or loosened beyond the argv, pin, phrase, road and table updates named in Scope in.

## Time budget
- expected: 40m
- stuck: 80m
- reason: not split, because the old names get no alias, so the parser move and every caller must land in one change for the suite to pass; a scratch prototype of this change touched 75 files, and splitting by command would edit the same run/drain-parametrized tests in both parts.
