---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- cli-group-engine-run

## Context
- clutch/__main__.py::_command
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/__main__.py::_retro
- clutch/__main__.py::_control
- clutch/help.py::help_map
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- docs/how-clutch-works.md#7.3 Control
- tests/unit/test_main_engine_group.py
- tests/unit/test_host_running.py
- tests/integration/test_ask_plan_drain.py::test_prompts_name_only_existing_verbs

## On-demand
- clutch/specs/ask/author.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/running.md

## Goal / Why
Roadmap row 131 (`cli-group-engine-control`), group `engine` part 2. Row 130 (`cli-group-engine-run`, merged at `fcefb4f6`) created the `engine` group with `drain`, `serve`, `run` and `stop`, each built through `_command`, with no alias for the old names. At HEAD (`731a68e7`) `pause`, `resume`, `kill` and `retro` are still top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help kill` prints no reads, writes, lock, exit codes or examples, and `CLAUDE.md` section A "Command groups" requires every command under a group.

When this ticket is done:
- `clutch engine pause`, `clutch engine resume`, `clutch engine kill` and `clutch engine retro` take the same arguments (none), print the same stdout lines, take the same lock verbs, write the same control requests, commits and journal events, and exit with the same codes as `clutch pause`, `clutch resume`, `clutch kill` and `clutch retro` do at HEAD. The visible differences are the refusal prefix (`clutch engine:`), the two retro roads named in Scope in, and the docs, prompts and extension argv that name these commands.
- `clutch pause`, `clutch resume`, `clutch kill` and `clutch retro` are argparse usage errors (exit 2). No alias, hidden parser or argv rewrite keeps them (CLAUDE.md "No dual-path code").
- The four subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them, and the `engine` group's summary and description cover controlling a running engine.
- Every caller names the new form in the same change: the extension's Kill and Retro argv, the help topics, the ask prompts, `README.md`, the host run guide, `docs/how-clutch-works.md`, and the tests.

Why: the owner's row 129 rules require every command under a group; rows 132-140 move the rest.

No running engine is restarted by this change. A drain or serve runs as `python -m clutch [--config <path>] engine drain|serve` (row 130), and its self-upgrade re-exec argv (`engine drain --parked ...`) still parses after this change. The control verbs run as their own short-lived processes that publish a `ControlRequest` to `<state_dir>/control/inbox/`; the request `verb` values (`control.Verb`: `pause`, `resume`, `kill`, `retro`, `stop`) and the lock verbs do not change, so a drain started before this merges accepts requests from `clutch engine kill` and the rest. Transition, once: a person or supervising loop that still types `clutch kill` (for example from a `clutch prompt drain-loop` or `clutch prompt running` text rendered before the merge) gets exit 2 and uses `clutch engine kill` instead.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `retro` parser, the `pause`/`resume` loop and the `kill` parser. Add `pause`, `resume`, `kill` and `retro` to `engine_sub`, after `stop`, each built with `_command` and taking no arguments. Read each fact from its `docs/how-clutch-works.md` section 2.1 and 7.3 rows and from `_control`, `_submit_engine` and `_retro` before writing it:
  - `pause`: asks a running drain or serve to admit no new ticket until `engine resume`; with no engine it prints `nothing running to pause`; refuses while a non-engine holder has the lock; writes one pause request to `<state_dir>/control/inbox/` when an engine runs; writer lock only to probe; exits 0 when submitted or nothing runs, 2 on refusal. Example `clutch engine pause`.
  - `resume`: asks a running drain or serve to release its current advertised hold (pause, storm trip or red streak); with no engine it prints `nothing running to resume`; refuses when the engine advertises no hold or a non-engine holder has the lock; exits as `pause`. Example `clutch engine resume`.
  - `kill`: asks a running drain or serve to stop at the next safe point, aborting its running ticket; refuses when nothing runs or a non-engine holder has the lock; writer lock only to probe; exits 0 when submitted, 2 on refusal. Example `clutch engine kill`.
  - `retro`: runs a retro report now under the writer lock, committing `tickets/retro/NNNNNN.md`, or, while a drain or serve holds the lock, queues one on it; refuses while a non-engine holder has the lock; exits 0 when committed, when nothing merged since the last report, or when queued, 1 when no report is committed, 2 on refusal. Example `clutch engine retro`.
- The `engine` group: `help` becomes `run and control the engine` and `description` becomes `Run tickets, control a running engine, and run retros.`; its `Examples:` epilog keeps `clutch engine drain`. The `serve` subcommand's `does` reads `Run the continuous daemon until engine kill, engine stop or a signal.`
- Dispatch: drop the `kill`, `pause`, `resume` and `retro` entries of `handlers`; the `engine` entry maps `pause`, `resume` and `kill` to `handle_control` and `retro` to `handle_retro`. `handle_control` passes `args.engine_verb`. `_control`, `_submit_engine` and `_retro` keep their lock verbs (`pause`, `resume`, `kill`, `retro`), request verbs and stdout lines. Refusals keep going through `_fail(args.verb, ...)`, so they print `clutch engine: <message> -- <road>`, as row 130's subcommands do. No `print(..., file=sys.stderr)` is added (`tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner`).
- Retro roads: the `ConfigError` road in `main`'s `except` names the command path, so `engine retro` prints `-- repair the selected config and retry engine retro` and `covmap` keeps `-- repair the selected config and retry covmap`; no other verb gains a road. `_retro`'s journal road becomes `restore journal readability from backup and retry engine retro`.

In, other code:
- `clutch/help.py`: topics `verb.kill` and `verb.retro` keep their keys; their `verb` field (the run-guide row each reads) becomes `engine kill` and `engine retro`. `COMMANDS` is unchanged.
- `clutch/observe.py` `snapshot`: the Kill and Retro `engineVerbs` argv become `["engine", "kill"]` and `["engine", "retro"]`; labels, details and order are unchanged. `vscode-clutchwork/` is unchanged: it runs the argv the snapshot supplies.

In, prompts (no spec `version` exists for these files): `clutch/specs/ask/author.md` (the "Never run" list), `drain-loop.md` (step 2) and `running.md` name `clutch engine kill`.

In, docs (each command spelled as its `engine` path; row text otherwise unchanged and rows stay in place):
- `README.md`: the three `# Running` lines `uv run clutch kill|pause|resume` of the command block, and step 5's `clutch kill`.
- `clutch/docs/host-running.md`: the intro's two `kill` mentions, and the first cells of the `retro`, `pause`, `resume` and `kill` rows.
- `docs/how-clutch-works.md`: section 2.1, the `engine serve` row's "until `kill`, `stop`, or a signal" (both become `engine` paths), the first cell of the `retro` row, and the first cell and the "With none" tail of the control row; section 7.1's "as `kill` does"; the `resume` of section 7.2.1's red-streak item and of section 7.4's storm breaker; section 8.1's Preflight "standalone `retro`"; section 9.5's "run one on demand with `retro`".

In, tests:
- New `tests/unit/test_main_engine_control.py`: builds `_parser()` in memory and calls `main(..., cwd=tmp_path, env={})` in an empty `tmp_path`; it reads no repo file and starts no process. It runs the new parser lines and the refusal dispatch lines of `clutch/__main__.py` (coverage floor 13).
- Argv only, `"engine"` inserted before the verb in each list passed to `main`, `entry.main`, `cli.main` or `cli(...)`, and in the helpers that build one: `tests/integration/test_cli.py` (the four `cli(root, "retro", ...)` and three `main(["retro"], ...)` calls); `tests/integration/test_control_cli.py` (its `invoke` helper builds `["engine", verb]` for every verb, in place of `["engine", verb] if verb == "stop" else [verb]`); `tests/integration/test_stale_running.py` (`("retro",)` becomes `("engine", "retro")`, and the `("kill", "stop", "pause", "resume")` loop invokes `"engine", verb` for each); `tests/integration/test_storm_hold.py` (`cli.main, ["resume"]`). `tests/integration/test_daemon_composition.py`, `test_kill_cli_activation.py`, `test_kill_signal_journal.py` and `test_kill_executor_abort.py` reach the CLI only through `test_control_cli.invoke` (directly or through `exercise_live_cli_kill`), so they pass with no argv edit. A scratch prototype of the code change without these test edits failed 62 integration tests across these nine files; all passed after the edits in the five fenced files.
- Pinned values: `tests/integration/test_kill_cli_activation.py` (the `clutch kill:` refusal line becomes `clutch engine: nothing running to kill -- start a drain before submitting kill`). No other test pins a moved command's argv or refusal text.

Merge order. The drain runs one ticket at a time from main's tip, so whichever of two overlapping tickets runs second starts from the other's merged code.
- `cli-group-ticket-verdicts` (row 133, being authored now) moves `confirm` and `reject` into group `ticket` and edits many of the same files, sometimes the same line: `clutch/__main__.py` (`_parser`, `handlers`), the `help.py` topic loop line (`verb=`), `clutch/specs/ask/author.md`'s "Never run" list, `docs/how-clutch-works.md` section 2.1 and 7.3, `clutch/docs/host-running.md`'s table, `README.md`, and `tests/integration/test_stale_running.py`'s `("retro",)` / `("reject", "--yes", "stale")` tuple and `tests/integration/test_control_cli.py`. In a line both touch, this ticket changes only the words for `pause`, `resume`, `kill` and `retro`; every other word keeps the form main has when it runs. Where a criterion compares a whole dict, table, prompt or list, the other entries match main, not HEAD `731a68e7`. Either order passes.
- `step-names-every-surface` (confirmed) edits `clutch/observe.py::STEP_NAMES` and the `step` topic's name tuple in `clutch/help.py`; this ticket edits the `engineVerbs` lines of `snapshot` and the `verb.*` topic loop. Either order keeps both.
- `plan-status-lines-030` (running) fences only plans under `docs/`; no overlap.

Out:
- An alias of any kind for the old names.
- Lock and request vocabulary: `Lockfile` verbs, `lockfile.ENGINE_VERBS`, `control.Verb` and the inbox request format, engine.log `verb` fields, `observe.lock_verb`, `hostfiles._IMPERATIVES`.
- Stdout lines (`kill submitted: ...`, `nothing running to pause`, `retro: committed ...`) and the `start a drain before submitting kill` road.
- Prose that names the control request or the mode rather than the command: section 7.3's list "`pause`, `resume`, `kill`, `retro`, and `stop` write a request file", section 3.1's reserved stem `retro`, section 11's `retro` config row, `retro:` config keys, stage and event names, module docstrings.
- `clutch/hostfiles.py` CORE_TEMPLATE, the managed blocks, `CLAUDE.md` and `AGENTS.md`: none names these commands (`grep -nE 'clutch (pause|resume|kill|retro)' clutch/hostfiles.py CLAUDE.md AGENTS.md` prints nothing at HEAD), so `clutch core` is not run.
- `dev.py`, `vscode-clutchwork/` (its README and `package.json` name none of the four as a command), `clutch/docs/host-contract.md`, `host-authoring.md`, `host-qwen.md` and `host-gemini.md` (none names them), `CLUTCH_PLAN.md`, `docs/roadmap.md` and the plans under `docs/`.
- `tests/unit/test_main_help.py`, `tests/unit/test_main_engine_group.py`, `tests/integration/test_help.py`, `tests/integration/test_watch.py` and `tests/unit/test_help.py`: unedited; their parser walk, inclusion checks, `TOPICS[key]["verb"]` row lookup and `engineVerbs` detail lookup (the word after `engine`) cover the moved commands as they stand.
- Control-request-only tests that publish `"kill"`, `"pause"` or `"resume"` requests without the CLI (for example `tests/integration/test_serve_kill.py`, `test_kill_signal_journal.py`, `test_closed_sets.py`).

## Scope fence
- clutch/__main__.py
- clutch/help.py
- clutch/observe.py
- clutch/specs/ask/author.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/running.md
- README.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_main_engine_control.py
- tests/integration/test_cli.py
- tests/integration/test_control_cli.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_stale_running.py
- tests/integration/test_storm_hold.py

## Acceptance criteria
1. `tests/unit/test_main_engine_control.py::test_engine_group_owns_the_control_verbs`: the `engine` group's subcommands include `pause`, `resume`, `kill` and `retro` as well as `drain`, `serve`, `run` and `stop`, and none of the eight is a top-level command. Ruled out: a top-level parser kept beside the group.
2. `tests/unit/test_main_engine_control.py::test_old_control_names_are_refused`: in an empty `tmp_path`, `main([verb], cwd=tmp_path, env={})` for each of `pause`, `resume`, `kill` and `retro` raises `SystemExit(2)`, and stderr contains `invalid choice`. Ruled out: an argv rewrite in `main`, which would reach the config load and return 2 with a `clutch engine:` line instead.
3. `tests/unit/test_main_engine_control.py::test_control_subcommands_take_no_arguments`: `_parser().parse_args(["engine", verb])` gives `engine_verb == verb` for each of the four, and `["engine", "kill", "x"]` raises `SystemExit(2)`. Ruled out: a positional or option added to a moved command.
4. `tests/unit/test_main_engine_control.py::test_control_refusal_names_the_group`: in an empty `tmp_path` (no `config.yaml`), `main(["engine", verb], cwd=tmp_path, env={})` returns 2 for each of the four, prints nothing on stdout, and prints one stderr line that starts with `clutch engine: ` and contains `config file not found`. For `retro` the line ends with `-- repair the selected config and retry engine retro`; for `pause`, `resume` and `kill` it contains no `retry`. Ruled out: `clutch kill:`, `clutch engine kill:`, `retry retro`, `retry engine` with no subcommand, and the retro road leaking onto the control verbs.
5. `./dev.py test tests/unit/test_main_help.py tests/unit/test_main_engine_group.py` exits 0 with both files unchanged. The parser walk now checks `engine pause`, `engine resume`, `engine kill` and `engine retro` for a description and examples that parse, and the top-level listing shows each once with its summary. `uv run clutch help engine kill` prints `usage: clutch engine kill`, then what it does with `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with the facts in Scope in, then `Examples:`.
6. `./dev.py test tests/unit/test_host_running.py` exits 0 unchanged, and `grep -cE '^\| .engine (pause|resume|kill|retro). \|' clutch/docs/host-running.md` prints `4`. Its `test_verb_table_matches_parser` fails while a row still names a removed top-level command or the `engine` group lacks a row for one of its eight subcommands.
7. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_watch.py` exits 0 with these files unchanged. `help.TOPICS["verb.kill"]["verb"] == "engine kill"`, `help.TOPICS["verb.retro"]["verb"] == "engine retro"`, and `help.COMMANDS` is unchanged. Ruled out: a `verb.*` topic whose run-guide row is gone, which raises `LookupError` when the snapshot builds its help.
8. `grep -cE '"argv": \["engine", "(kill|retro)"\]' clutch/observe.py` prints `2` and `grep -cE '"argv": \["(kill|retro)"\]' clutch/observe.py` prints `0`. Ruled out: an extension Kill or Retro button that runs a removed command.
9. `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py` exits 0. `test_prompts_name_only_existing_verbs` renders `author`, `drain-loop` and `running` and fails on a prompt that names `` `clutch kill` `` (first word not a command).
10. `git grep -nE 'clutch (pause|resume|kill|retro)([^a-z-]|$)' -- README.md clutch docs/how-clutch-works.md` prints nothing; at HEAD `731a68e7` it prints 7 lines. ``git grep -nE '`(pause|resume|kill|retro)( [^`]*)?`' -- README.md 'clutch/docs/host-*.md'`` prints nothing; at HEAD it prints 5 lines. ``git grep -nE '`(pause|resume|kill|retro)`' -- docs/how-clutch-works.md`` prints exactly 3 lines, the section 3.1 reserved-stem sentence, the section 7.3 request list and the section 11 `retro` config row; at HEAD it prints 11. `grep -c 'retry retro' clutch/__main__.py` prints `0` and `grep -c 'from backup and retry engine retro' clutch/__main__.py` prints `1`. Ruled out: a reference left in a doc, prompt or engine road.
11. `./dev.py test tests/integration/test_drain_upgrade.py tests/integration/test_closed_sets.py tests/integration/test_control_cli.py` exits 0 with the first two files unchanged: the self-upgrade re-exec argv stays `... -m clutch engine drain --parked ...`, `control.Verb` stays `{"kill", "pause", "resume", "retro", "stop"}`, and the published retro request keeps `verb == "retro"`. Ruled out: a renamed request or lock verb, which a drain or serve started before the merge would reject, forcing a restart this change must not need.
12. `./dev.py test` exits 0; Check's `unit` and `integration` mechanical checks in `config.yaml` run both full suites. In the test files of Scope in only the edits named there change, and no assertion is dropped. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is the known base flake (box-000706-10233120) and is verified on the base commit, not chased.

## Verification
```
./dev.py test tests/unit/test_main_engine_control.py tests/unit/test_main_engine_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_help.py
./dev.py test tests/integration/test_help.py tests/integration/test_watch.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_main_verb_groups.py tests/integration/test_cli.py tests/integration/test_control_cli.py tests/integration/test_kill_cli_activation.py tests/integration/test_stale_running.py tests/integration/test_storm_hold.py tests/integration/test_daemon_composition.py tests/integration/test_kill_signal_journal.py tests/integration/test_kill_executor_abort.py tests/integration/test_drain_upgrade.py tests/integration/test_closed_sets.py
```

## Definition of rejected
The branch is rejected, even if it passes, when any old name still parses (a top-level parser, a hidden or suppressed subparser, or an argv rewrite in `main`); an argument, stdout line, exit code, lock verb, control request, commit or journal event of the four commands changes; `control.Verb`, `lockfile.ENGINE_VERBS` or an engine.log `verb` changes; `drain`, `serve`, `run` or `stop` changes beyond the `serve` help sentence named in Scope in; a help field gets a default, or command help is copied into `clutch/help.py`; `clutch/hostfiles.py`, `CLAUDE.md`, `AGENTS.md` or `vscode-clutchwork/` changes; or a test is added to a do-not-grow file, or an existing assertion is dropped or loosened beyond the edits named in Scope in.

## Time budget
- expected: 20m
- stuck: 40m
