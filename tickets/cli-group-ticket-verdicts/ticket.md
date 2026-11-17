---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- cli-group-ticket-authoring

## Context
- clutch/__main__.py::_command
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/__main__.py::_verdict
- clutch/runner.py::verdict
- clutch/help.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_ticket_group.py
- tests/unit/test_verdict_extension.py

## On-demand
- README.md
- clutch/specs/ask/author.md
- clutch/specs/ask/drafts.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_control_cli.py
- tests/integration/test_reject_queue.py

## Goal / Why
Roadmap row 133 (`cli-group-ticket-verdicts`), group `ticket` part 2. Row 132 (`cli-group-ticket-authoring`, merged at `9de3d083`) created the `ticket` group in `clutch/__main__.py` with `new`, `lint`, `review` and `order`, each built through `_command` with help to the row 129 standard. At HEAD (`179b075d`) `confirm` and `reject` are still top-level verbs added by a bare `for verb in ("confirm", "reject")` loop with a one-line `help=`, so `clutch help confirm` prints no reads, writes, lock, exit codes or examples, and 32 lines of `README.md`, `clutch/`, `docs/how-clutch-works.md` and `tests/` spell them `clutch confirm` or `clutch reject`.

When this ticket is done:
- `clutch ticket confirm <stem>...` and `clutch ticket reject <stem>...` take the same arguments, print the same output (the `<stem>: <preview>` line, the `confirm <stem>? [y/N] ` or `reject <stem>? [y/N] ` prompt, `confirmed draft <stem>`, `kept <stem>`, `rejected <stem>`, `already rejected <stem>`, `verdict aborted`, `<verb> submitted: ...`), take the same writer lock under the same lock verb, write the same commits, journal events and control requests, and exit with the same codes as `clutch confirm` and `clutch reject` do at HEAD. The only visible differences are the help text, argparse's own usage and error lines, the refusal prefix, the roads, prompts and documents that name these commands, the extension's verdict argv, and the commit-lock label of a running verdict (all in Scope in).
- `clutch confirm` and `clutch reject` no longer parse: argparse exits 2 with an invalid-choice error. There is no alias (`CLAUDE.md` "No dual-path code").
- Both subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them, and `clutch help ticket` lists all six subcommands.
- Every caller names the new form in the same change: the terminal-check road, the Reject-queue and draft roads, the status Reject queue line, the ask prompts, the extension's verdict argv and help topics, `README.md`, the run guide, `docs/how-clutch-works.md`, and the tests.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140), so a person or agent finds the verdict commands beside the other per-ticket commands under `clutch help ticket`, each with what it reads, writes and locks and how it exits.

Transition, once: a supervising session that rendered `clutch prompt drafts`, `clutch prompt drain-loop` or `clutch prompt plan-ticket-drain` before this merges holds text naming `clutch confirm --yes` and `clutch reject --yes`. After the merge those commands exit 2 with an argparse invalid-choice error and apply no verdict. Re-render the prompt, or run `clutch ticket confirm --yes <stem>` or `clutch ticket reject --yes <stem>`. The VS Code extension runs `clutch snapshot` on each refresh and takes its verdict argv from it, so its Keep and Reject actions use the new form from the first refresh after the merge.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `for verb in ("confirm", "reject")` parsers. Add `confirm` and `reject` to the `ticket` group's subparsers, each through `_command` with every field, keeping their arguments exactly: `stems` (`nargs="+"`), `--yes` (`store_true`) and `--extension` (`store_true`). The `ticket` group's `description` names the verdicts too (for example "Author, validate, review, order, confirm and reject tickets."); its summary and epilog stay.
- Help facts, agreeing with the `docs/how-clutch-works.md` section 2.1 rows and with `_verdict` and `runner.verdict`:
  - `ticket confirm`: keeps each named stem, promoting a draft to confirmed or keeping a Reject-queue stem so its caps start over (section 6.6); a person answers `y` at a terminal unless `--yes` or `--extension` is given; refuses a running stem, a stem that is neither a draft nor in the Reject queue, and, without `--extension`, a repeat keep of unchanged content. Reads: tickets, journal, git state and config. Writes: the named ticket's pending edits through intake, then a `clutch(<stem>): confirmed` commit and a `draft_confirmed` signal, or a `reject_verdict` keep signal; with drain or serve running, a verdict request to that engine instead.
  - `ticket reject`: stamps each named stem `state: rejected`, commits it, journals the kill and files a `failure_report` for each confirmed ticket that depends on it; refuses running and settled stems; the same terminal rule. Reads as confirm. Writes: the named ticket's pending edits through intake, then a `clutch(<stem>): rejected` commit, `reject_verdict` kill and `rejected` events and the dependents' box messages; with drain or serve running, a verdict request to that engine instead.
  - Both: lock: the writer lock; with drain or serve holding it, publishes the request to that engine; refuses while any other holder has it. Exits 0 when applied or submitted, 1 when the prompt is not answered `y`, 2 on refusal. Examples are practical `clutch ticket ...` invocations, such as `clutch ticket confirm add-widget`, `clutch ticket confirm --yes add-widget`, `clutch ticket reject add-widget` and `clutch ticket reject --yes add-widget`.
- Dispatch: the `ticket` handler table gains `"confirm": handle_verdict` and `"reject": handle_verdict`, and the top-level `"confirm"` and `"reject"` handler entries are removed. `handle_verdict` passes `args.ticket_verb` to `_verdict`, never `args.verb` (now `ticket`), so the prompt, `kill=verb == "reject"`, the control request verb and the `<verb> submitted:` line keep `confirm` and `reject`. The interactive-terminal check runs for `args.verb == "ticket" and args.ticket_verb in {"confirm", "reject"}`, before config loads as today, and its road becomes ``a human runs this in a terminal: `clutch ticket confirm|reject <stem>` ``. `_verdict`, `_submit_engine` and `runner.verdict` are unchanged.
- Refusals keep going through `_fail(args.verb, ...)`, so a verdict refusal prints `clutch ticket: <message> -- <road>`, as `ticket review` refusals do. No `print(..., file=sys.stderr)` is added (`tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner`).

In, other engine code. Lock verbs (`runner.verdict`'s `Lockfile` verb), `lockfile.ENGINE_VERBS`, control request and decision `verb` values, engine.log `verb` fields and journal bodies stay `confirm` and `reject`:
- `clutch/drain.py` (`_Drain._settle`): the three roads become ``... or retire it with `clutch ticket reject {stem}` ``, ``... then keep (`clutch ticket confirm {stem}`) or kill (`clutch ticket reject {stem}`)`` and ``edit ..., then `clutch ticket confirm {stem}`; or retire it with `clutch ticket reject {stem}` ``.
- `clutch/stages.py::ticket_change_findings`: the road becomes ``review the change to {rel}, then keep (`clutch ticket confirm {stem}`) or kill (`clutch ticket reject {stem}`)``.
- `clutch/rework.py::supervise_findings`: the escalation road names `clutch ticket confirm {stem}` and `clutch ticket reject {stem}`.
- `clutch/roadmap.py::choose`: the draft wait road becomes ``confirm the draft with `clutch ticket confirm` ``.
- `clutch/status.py::render`: the Reject queue line becomes `<stem>: <to> at <stage> -- ticket confirm <stem> after editing, or ticket reject <stem>`. The `interrupted (the engine stopped mid-run; reject it, or start the engine to rerun it)` heading and the roads of `verdict_refusal` stay.
- `clutch/observe.py::snapshot`: `verdictCommands` becomes `{"confirm": ["ticket", "confirm", "--extension"], "reject": ["ticket", "reject", "--extension"]}`, and the comment ``Only a committed draft awaits `clutch confirm` `` names `clutch ticket confirm`. `MENU`, `lock_verb` and `vscode-clutchwork/` are unchanged: the extension runs `verdictCommands` from the snapshot.
- `clutch/help.py`: topics `verb.confirm` and `verb.reject` keep their keys, and their `verb` field (the run-guide row each reads) becomes `ticket confirm` and `ticket reject`: the condition that maps `review`, `lint` and `order` to `ticket ...` gains them. The `verdict` topic's after-text becomes "Fix the reason and run ticket confirm or ticket reject again for the stem.". `COMMANDS` is unchanged.
- Accepted visible change, as in row 132: `observe.lock_verb` names a commit-lock holder by the word after `clutch` in its `/proc/<pid>/cmdline`, so while a verdict commits, the snapshot's `commitLock` field reads `ticket since ... (pid N)` instead of `confirm since ...`. The writer-lock label still comes from the lockfile's `confirm` or `reject` verb. `lock_verb` is not changed.

In, prompts (these files carry no `version`):
- `clutch/specs/ask/drafts.md`: ``give the exact `clutch ticket confirm --yes STEM ...` or `clutch ticket reject --yes STEM ...` command``.
- `clutch/specs/ask/drain-loop.md`: the seven `clutch confirm --yes` and `clutch reject --yes` references in steps 3 and 4 and the closing rules gain `ticket `, and "confirm refuses any other" becomes "`ticket confirm` refuses any other".
- `clutch/specs/ask/plan-ticket-drain.md`: the two references in the "Supervise through" bullet.
- `clutch/specs/ask/author.md`: `clutch ticket confirm` and `clutch ticket reject` in the "Never run" list.
- Prose naming the verdict as an action stays: "Confirm or reject only by executing a Recommendation" in `drain-loop.md`, "then confirm the ticket" in `plan-ticket-drain.md`, and "recommend confirm or reject" in `drafts.md`. The diagnose, box, running and review ask prompts name no verdict command and are not edited.

In, documents. Only references to the command change; a Diagnose verdict named `reject` (`docs/how-clutch-works.md` sections 6.3 and 6.4), the `reject_verdict` signal, the Reject queue, and the words keep, kill and confirm used as actions stay:
- `README.md`: step 6's ``waits for `ticket confirm` or `ticket reject` ``, step 7's `clutch ticket confirm` and `clutch ticket reject`, and the two `# Decisions` lines `uv run clutch ticket confirm` and `uv run clutch ticket reject`, with comments aligned like the `# Authoring` lines.
- `clutch/docs/host-running.md`: the intro's ``Drafts written by Author wait for `ticket confirm`. ``, and the first cells of the `confirm` and `reject` rows become `ticket confirm` and `ticket reject`, in place, text unchanged.
- `docs/how-clutch-works.md`: the section 2.1 rows begin `` `ticket confirm <stem> [--yes|--extension]` `` and `` `ticket reject <stem> [--yes|--extension]` ``, text unchanged; section 3.1 "awaiting `ticket confirm`"; section 3.2 "`ticket review`, `engine run`, `ticket confirm`, and `ticket reject` intake only the named stem"; section 6.4 "only an operator `ticket confirm`"; section 6.6 "`ticket reject` refuses settled stems", `` **`ticket confirm <stem>` (keep)** ``, `` **`ticket reject <stem>` (kill)** `` and "`ticket confirm` on a `draft` ticket"; section 6.7 `clutch ticket confirm <stem>`, `clutch ticket reject <stem>`, "no `ticket confirm` is needed", "operator `ticket confirm`" and "`ticket reject` reaps and rejects it"; section 7.3 "`ticket confirm` and `ticket reject` publish verdict requests" and "run `ticket confirm` or `ticket reject` again"; section 7.5 `clutch ticket confirm --yes` and `clutch ticket reject --yes`; section 9.3 "needs `ticket confirm`".

In, tests. Only the argv (`"ticket"` before the verb) and the pinned text named here change:
- New `tests/unit/test_main_ticket_verdicts.py` (criteria 1-4). It builds `_parser()` in memory and calls `main(..., cwd=tmp_path, env={})`, with the stubs `tests/unit/test_main_ticket_group.py` uses for `load_config`, `Journal`, `Git`, `CommitLock` and `SubprocessExec`. It reads no repo file and starts no process, and it runs the new parser and dispatch lines of `clutch/__main__.py` (coverage floor 13).
- `tests/unit/test_verdict_extension.py`: `test_request_actor_and_parser` parses `["ticket", "confirm", "sample", "--extension"]`; `test_verdict_and_review_loop_over_stems` parses `["ticket", "confirm", "a", "b"]` and runs `["ticket", verb, "a", "b", *args]` for both cases.
- `tests/unit/test_rework_supervise_gate.py::test_split_is_refused`: the two road fragments.
- `tests/integration/test_watch.py::test_snapshot_display_fields`: the `verdictCommands` pin. `tests/integration/test_status.py::test_status_preserves_sections_and_is_write_free`: the Reject queue line. `tests/integration/test_paved_roads.py::test_reject_queue_road_names_confirm_and_reject` and the `ticket_changed` road pinned in `tests/integration/test_drain.py::_mid_run_hold`: the roads.
- `tests/integration/test_ask_drafts.py`, `tests/integration/test_ask_drain_loop_agent.py` and `tests/integration/test_ask_plan_drain.py`: the phrases `clutch ticket confirm --yes` and `clutch ticket reject --yes`, in the phrase lists and the `text.index(...)` order checks.
- `tests/integration/test_reject_queue.py`: the argv and the terminal road in `test_verdict_refused_without_terminal`.
- Argv only: `tests/integration/test_control_cli.py`, `tests/integration/test_drain.py`, `tests/integration/test_drain_admissions.py`, `tests/integration/test_intake_scope.py` (the parametrized argv builder puts `"ticket"` before `confirm` and `reject` as it does before `review`), `tests/integration/test_ladder.py`, `tests/integration/test_stale_running.py` and `tests/regress_stale_running.py`. `tests/integration/test_drain.py` and `tests/integration/test_watch.py` are do-not-grow files, fenced only for these forced lines; nothing is added to either.

Merge order. The drain runs one ticket at a time from main's tip, so whichever of two overlapping tickets runs second starts from the other's merged code.
- `cli-group-engine-control` (row 131, confirmed) moves `pause`, `resume`, `kill` and `retro` into group `engine` and edits some of the same files and lines: the parser and `handlers` of `clutch/__main__.py` (its entries sit beside the `confirm` and `reject` entries), the `verb=` condition of the `help.py` topic loop, the `engineVerbs` lines of `observe.py::snapshot` (not `verdictCommands`), the "Never run" line of `clutch/specs/ask/author.md`, step 2 of `drain-loop.md` (this ticket edits steps 3 and 4 and the closing rules), the `# Running` lines of the `README.md` command block (this ticket edits the `# Decisions` lines), rows of the run-guide table and of `docs/how-clutch-works.md` section 2.1, section 7.3, `tests/integration/test_control_cli.py` (its `invoke` helper; this ticket edits only direct `entry.main` calls) and `tests/integration/test_stale_running.py` (the `test_every_locked_verb_reaps` loop holds `("retro",)` and `("reject", "--yes", "stale")` on one line). In a line both touch, this ticket changes only the words for `confirm` and `reject`; every other word keeps the form main has when it runs. Where a criterion or pin compares a whole dict, list or line, its other entries match main, not HEAD `179b075d`. Row 131 leaves `tests/integration/test_watch.py` unedited and greps only `pause`, `resume`, `kill` and `retro`, so either order keeps both tickets' criteria true.
- `step-names-every-surface` (confirmed, running) edits `clutch/observe.py::STEP_NAMES`, the `step` topic of `clutch/help.py` and `vscode-clutchwork/extension.js`. These are different lines from `snapshot`'s `verdictCommands` and comment and from the `help.py` topic loop and `verdict` topic, so either order passes.

Out:
- An alias of any kind for `confirm` or `reject`; and every other command, including `pause`, `resume`, `kill` and `retro` (row 131), `status`, `triage` and `dismiss`.
- `clutch/hostfiles.py` `CORE_TEMPLATE`, the managed blocks, `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md`: `grep -nE 'clutch (confirm|reject)|(confirm|reject) --yes' clutch/hostfiles.py CLAUDE.md AGENTS.md hosts/fixture/CLAUDE.md` prints nothing at HEAD. Their "It may confirm or reject" names the verdict, not the command, and `_IMPERATIVES` classifies prose, so `clutch core` is not run.
- `vscode-clutchwork/` (it runs the snapshot's argv), `clutch/control.py`, `clutch/serve.py`, `clutch/runner.py`, `clutch/lockfile.py`, `tests/harness/host_loop.py` and every journaled or published `confirm` and `reject` value.
- Output headings: `drafts awaiting confirm` in `clutch/drain.py`, the `interrupted (...; reject it, ...)` heading in `clutch/status.py`, and `verdict_refusal`'s roads.
- `CLUTCH_PLAN.md` (frozen), `docs/roadmap.md` and the plans under `docs/`: design records.
- `clutch/docs/host-authoring.md`'s "Every ticket read (intake, lint, confirm, drain, serve, run, and Author)": it names checks.
- `tests/unit/test_main_help.py`, `tests/unit/test_main_ticket_group.py`, `tests/unit/test_host_running.py`, `tests/unit/test_help.py`, `tests/integration/test_help.py` and `tests/unit/test_readme.py` stay unedited and passing; they already walk the parser, the `ticket` group and the run-guide rows by `TOPICS[key]["verb"]`.

## Scope fence
- clutch/__main__.py
- clutch/observe.py
- clutch/help.py
- clutch/status.py
- clutch/drain.py
- clutch/stages.py
- clutch/rework.py
- clutch/roadmap.py
- clutch/specs/ask/author.md
- clutch/specs/ask/drafts.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_main_ticket_verdicts.py
- tests/unit/test_verdict_extension.py
- tests/unit/test_rework_supervise_gate.py
- tests/integration/test_ask_drafts.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_control_cli.py
- tests/integration/test_drain.py
- tests/integration/test_drain_admissions.py
- tests/integration/test_intake_scope.py
- tests/integration/test_ladder.py
- tests/integration/test_paved_roads.py
- tests/integration/test_reject_queue.py
- tests/integration/test_stale_running.py
- tests/integration/test_status.py
- tests/integration/test_watch.py
- tests/regress_stale_running.py

## Acceptance criteria
1. `tests/unit/test_main_ticket_verdicts.py::test_verdicts_join_ticket_group`: neither `confirm` nor `reject` is a choice of the top-level subparsers, both are choices of the `ticket` group, and `_parser().parse_args([name, "x"])` raises `SystemExit(2)` for each. Ruled out: an alias, hidden parser or argv rewrite that keeps an old name working.
2. `tests/unit/test_main_ticket_verdicts.py::test_verdict_arguments_unchanged`: `_parser().parse_args(["ticket", "confirm", "a", "b"])` gives `ticket_verb == "confirm"`, `stems == ["a", "b"]`, `yes is False` and `extension is False`; `["ticket", "reject", "--yes", "x"]` gives `ticket_verb == "reject"`, `yes is True` and `stems == ["x"]`; `["ticket", "confirm", "--extension", "x"]` gives `extension is True`; and `["ticket", "reject"]` raises `SystemExit(2)`, not `stems == []`. Ruled out: a changed arity or a dropped flag.
3. `tests/unit/test_main_ticket_verdicts.py::test_dispatch_passes_subcommand`: with `load_config`, `Journal`, `Git`, `CommitLock` and `SubprocessExec` stubbed and `_verdict` replaced by an `AsyncMock(return_value=0)`, `main(["ticket", verb, "a", "--yes"], cwd=tmp_path, env={})` returns 0 for each of `confirm` and `reject`, and the awaited call's stem and verb arguments are `("a", verb)` with `yes` true and `extension` false. Ruled out: passing `args.verb` (`"ticket"`), under which every `ticket reject` would become a keep (`kill=verb == "reject"` is false) and a live verdict would publish a control request with verb `ticket`.
4. `tests/unit/test_main_ticket_verdicts.py::test_terminal_refusal_names_group`: in an empty `tmp_path`, `main(["ticket", "confirm", "x"], cwd=tmp_path, env={}, terminal=(lambda: False, reader))`, where `reader` fails the test when called, returns 2 with empty stdout, and stderr is exactly ``clutch ticket: verdict requires an interactive terminal -- a human runs this in a terminal: `clutch ticket confirm|reject <stem>`\n``. Ruled out: the old `clutch confirm:` prefix or road, and a terminal check skipped for the group, which would reach the config load and refuse with `config file not found`.
5. `./dev.py test tests/unit/test_main_ticket_verdicts.py tests/unit/test_main_help.py tests/unit/test_main_ticket_group.py tests/unit/test_verdict_extension.py tests/unit/test_rework_supervise_gate.py` exits 0, with `tests/unit/test_main_help.py` and `tests/unit/test_main_ticket_group.py` unchanged; the parser walk checks `ticket confirm` and `ticket reject` for a description and examples that parse, and the top-level help lists each once with its summary.
6. `uv run clutch help ticket reject` prints `usage: clutch ticket reject`, what it does, then `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines agreeing with Scope in (writer lock; exits 0 when applied or submitted, 1 when the prompt is not answered `y`, 2 on refusal), its options `--yes` and `--extension`, then `Examples:` with a `clutch ticket reject <stem>` line. `uv run clutch help ticket confirm` prints the same parts for confirm, and `uv run clutch help ticket` lists `new`, `lint`, `review`, `order`, `confirm` and `reject`.
7. `./dev.py test tests/unit/test_host_running.py tests/unit/test_help.py tests/integration/test_help.py` exits 0 with those files unchanged, and `grep -cE '^\| .ticket (confirm|reject). \|' clutch/docs/host-running.md` prints `2`. `help.TOPICS["verb.confirm"]["verb"] == "ticket confirm"`, `help.TOPICS["verb.reject"]["verb"] == "ticket reject"`, and `help.COMMANDS` is unchanged. Ruled out: a `verb.*` topic whose run-guide row is gone, which raises `LookupError` when the snapshot builds its help, and a renamed topic key.
8. `./dev.py test tests/integration/test_watch.py tests/integration/test_status.py tests/integration/test_paved_roads.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_drain.py` exits 0. The snapshot's `verdictCommands` is `{"confirm": ["ticket", "confirm", "--extension"], "reject": ["ticket", "reject", "--extension"]}`; the status Reject queue line reads `-- ticket confirm held after editing, or ticket reject held`; and `test_prompts_name_only_existing_verbs` passes unedited, which fails if a rendered author, drain-loop or plan-ticket-drain prompt still names `` `clutch confirm `` or `` `clutch reject ``. Ruled out: an extension Keep or Reject action that runs a removed command.
9. `git grep -nE 'clutch (confirm|reject)([^a-z-]|$)' -- README.md clutch docs/how-clutch-works.md tests` prints nothing; at HEAD `179b075d` it prints 32 lines. Ruled out: a road, prompt, document, comment, test or reproducer still naming a removed command.
10. ``grep -nE '`(confirm|reject)( <stem>[^`]*)?`' docs/how-clutch-works.md README.md clutch/docs/host-running.md`` prints exactly the two Diagnose verdict lines of `docs/how-clutch-works.md` (section 6.3 `` - `reject`, `abandon-human`: `` and section 6.4 `` a `reject` / `abandon-human` verdict ``); at HEAD it prints 21 lines. `grep -cE '^\| .ticket (confirm|reject) <stem> \[--yes\|--extension\]. \|' docs/how-clutch-works.md` prints `2`.
11. `./dev.py test tests/integration/test_control_cli.py tests/integration/test_reject_queue.py tests/integration/test_drain.py tests/integration/test_drain_admissions.py tests/integration/test_intake_scope.py tests/integration/test_ladder.py tests/integration/test_stale_running.py tests/integration/test_main_verb_groups.py` exits 0. In those files only the argv lists (with `"ticket"` before the verb) and the pinned roads named in Scope in change; no assertion is dropped or loosened, and `tests/integration/test_drain.py` gains no test.
12. `uv run python tests/regress_stale_running.py` and `uv run python tests/regress_reject_invalid_ticket.py` each print `{"regression_result": "pass"}` and exit 0. Ruled out: a reproducer still calling a removed command, which raises an uncaught `SystemExit(2)` and prints no result.
13. `./dev.py test` exits 0. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is the known base flake (box-000706-10233120) and is verified on the base commit, not chased.

## Verification
```
./dev.py test tests/unit/test_main_ticket_verdicts.py tests/unit/test_main_help.py tests/unit/test_main_ticket_group.py tests/unit/test_verdict_extension.py tests/unit/test_rework_supervise_gate.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_readme.py
./dev.py test tests/integration/test_help.py tests/integration/test_watch.py tests/integration/test_status.py tests/integration/test_paved_roads.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_drain.py tests/integration/test_main_verb_groups.py
./dev.py test tests/integration/test_control_cli.py tests/integration/test_reject_queue.py tests/integration/test_drain.py tests/integration/test_drain_admissions.py tests/integration/test_intake_scope.py tests/integration/test_ladder.py tests/integration/test_stale_running.py
uv run python tests/regress_stale_running.py
uv run python tests/regress_reject_invalid_ticket.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `confirm` or `reject` still runs as a top-level command through an alias, a hidden or suppressed parser, or argv rewriting in `main`.
- An argument, default, arity, output line, prompt, exit code, lock or lock verb, commit, journal event or control request verb of the two commands changes, other than the help text, argparse's usage and error lines, the refusal prefix, the roads named in Scope in and the accepted commit-lock label.
- `_verdict` receives `ticket` as its verb, or `clutch/control.py`, `clutch/runner.py`, `clutch/lockfile.py` or a journaled `confirm` or `reject` value changes.
- Anything under `vscode-clutchwork/` changes, a help topic key or `COMMANDS` entry changes, or `clutch/hostfiles.py`, `CLAUDE.md`, `AGENTS.md` or `hosts/fixture/CLAUDE.md` changes.
- A Diagnose verdict name `reject`, the `reject_verdict` signal or an output heading is renamed.
- A test is added to a do-not-grow file, or an existing assertion is dropped, loosened or changed beyond the argv and pinned text named in Scope in.
- Another command is moved or renamed.

## Time budget
- expected: 40m
- stuck: 80m
- reason: a rename with no alias moves the parser and every caller in one change (`CLAUDE.md` "No dual-path code"), so splitting `confirm` from `reject` would edit the same tests, roads and doc lines twice, since most name both; a scratch prototype touched 32 files, and every edit outside `clutch/__main__.py` and the new test file is a one-line text or argv change.
