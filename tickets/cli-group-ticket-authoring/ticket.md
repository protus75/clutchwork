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
- clutch/__main__.py::_lint
- clutch/__main__.py::_order
- clutch/__main__.py::_new
- clutch/status.py::run_admission
- clutch/status.py::review_admission
- clutch/status.py::order_admission
- clutch/status.py::lint_admission
- clutch/observe.py::extension_fields
- clutch/help.py
- clutch/hostfiles.py::CORE_TEMPLATE
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_help.py
- tests/unit/test_host_running.py
- tests/unit/test_observe_extension_fields.py
- tests/integration/test_help.py

## On-demand
- CLAUDE.md
- AGENTS.md
- README.md
- clutch/docs/host-authoring.md
- clutch/docs/host-contract.md
- clutch/specs/author.md
- clutch/specs/ask/author.md
- clutch/specs/ask/review.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_cli.py
- tests/integration/test_hostfiles.py

## Goal / Why
Roadmap row 132 (`cli-group-ticket-authoring`), group `ticket` part 1. `cli-help-standard` (row 129, merged at `e09d9e05`) added `_command` in `clutch/__main__.py` and three repo-local rules in `CLAUDE.md` section A and `AGENTS.md`: every command and subcommand carries help to the standard through `_command`; every command lives under a top-level group; a command change updates every document that describes it in the same change. At HEAD (`4dbff7d8`) `new`, `lint`, `review` and `order` are still ungrouped top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help lint` prints no reads, writes, lock, exit codes or examples, and `tests/unit/test_main_help.py` does not check them.

When this ticket is done:
- `clutch ticket new`, `clutch ticket lint`, `clutch ticket review` and `clutch ticket order` take the same arguments, print the same output, take the same locks, write the same files, commits and journal events, and exit with the same codes as `clutch new`, `clutch lint`, `clutch review` and `clutch order` do at HEAD. The only visible differences are the refusal prefix and the paved roads that name these commands (Scope in).
- `clutch new`, `clutch lint`, `clutch review` and `clutch order` no longer parse: argparse exits 2 with an invalid-choice error. There is no alias (`CLAUDE.md` "No dual-path code").
- The `ticket` group and its four subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them.
- Every caller names the new form in the same change: the engine's refusal text, the prompt specs, the core template and the three managed blocks it renders, the host guides, `README.md`, `docs/how-clutch-works.md`, the extension's argv table and help topics, and the tests.

Roadmap row 133 (`cli-group-ticket-verdicts`, which depends on this ticket) later adds `confirm` and `reject` to the same group. Rows 130-140 group the other verbs.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140), so a person or agent finds the authoring commands together under `clutch help ticket`, each with what it reads, writes and locks and how it exits.

## Scope in / Scope out
In:

Parser and dispatch, `clutch/__main__.py`:
- A `ticket` group parser like `roadmap`: a one-line summary, a `description` of what the group covers, and an `Examples:` epilog, with `argparse.RawDescriptionHelpFormatter`. Its subparsers use `dest="ticket_verb"` and `required=True`.
- `new`, `lint`, `review` and `order` move under it, each added through `_command` with every field, and their four top-level `sub.add_parser` calls are removed. Their arguments stay exactly as they are: `new` takes `stem`, `--kind` (choices `KINDS`, default `feature`) and `--evidence` (`nargs="+"`, metavar `PATH`); `lint` takes `stems` (`nargs="*"`); `review` takes `stems` (`nargs="+"`); `order` takes `stem`, `--priority` (choices `PRIORITIES`) and `--runs-before` (`nargs="*"`, metavar `STEM`).
- Help facts, agreeing with the rows of `docs/how-clutch-works.md` section 2.1:
  - `ticket new`: writes `tickets/<stem>/ticket.md` from the kind's skeleton and lints it; a bug needs `--evidence` and copies those files into `tickets/<stem>/evidence/`. Reads the evidence files and needs no `config.yaml`. Writes the ticket file and evidence only, no journal and no git. Lock: none. Exits 0 when authored, 2 on refusal.
  - `ticket lint`: reads tickets, the journal (the main checkout's in a linked worktree), git status and config; writes nothing; lock: none; exits 0 when all are valid, 1 for findings, 2 for a missing named ticket or an unreadable tickets directory.
  - `ticket review`: commits only the named ticket's pending edits through intake, reviews the committed ticket with a model call, and journals its verdict (a provisional review with an unmerged dependency is printed, not journaled); lock: commit lock only; exits 0 on approve, 1 on snag or rma, 2 on refusal.
  - `ticket order`: edits priority and the `## Runs before` section in the working tree for intake to commit; reads the ticket, the journal and the lock holder; lock: none; exits 0 when edited, 2 on refusal.
  - Examples are practical `clutch ticket ...` invocations, such as `clutch ticket new add-widget`, `clutch ticket new fix-crash --kind bug --evidence crash.txt`, `clutch ticket lint add-widget`, `clutch ticket review add-widget`, `clutch ticket order add-widget --priority P0` and `clutch ticket order add-widget --runs-before`.
- `main` dispatches the group by `args.ticket_verb` to the existing handlers (`_new`, `_lint`, `_review`, `_order`), which are unchanged. `ticket new` still runs before config loads, where `new` runs today beside `docs` and `init-config`. `ticket lint` still builds its `Git` with `GIT_OPTIONAL_LOCKS=0`, as `lint`, `watch` and `snapshot` do today; the other three subcommands do not.
- Refusals keep going through `_fail(args.verb, ...)`, so a `ticket` refusal prints `clutch ticket: <message> -- <road>`, the group name, as `roadmap` and `prompt` refusals print `clutch roadmap:` and `clutch prompt:` today. No `print(..., file=sys.stderr)` is added (`tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner`).
- Output lines stay byte for byte: `authored <path>`, `lint: <valid>/<total> tickets valid`, `review <stem>: <verdict> -- <summary>`, `ordered <stem>: ...`.

Command references. A reference names one of the four commands as something a person or agent runs: `clutch <verb>`, `uv run clutch <verb>`, a backticked verb or invocation such as `` `review <stem>` `` or `` `new` ``, an argv list, or a plain word used as the command ("If new refuses", "rerun new", "retry order", "The review verb"). Each gains `ticket ` before the verb. A word that names a check, stage, surface, config block or file stays: the lint check in "Lint requires", the `review` stage, prompt and config block, `review.md`, `llm/review-<stem>/`, and the list "intake, lint, confirm, drain, serve, run, and Author". `clutch prompt review` is another command and stays. The references at HEAD `4dbff7d8`:
- `clutch/__main__.py`: the `handle_prompt` roads `author a ticket with clutch new` and `author it with clutch new {stem}`; the `_lint` road `retry clutch lint`; the two `_order` roads ending `then retry order`; the `_new` road `then rerun new {stem} --kind bug --evidence <file>`.
- `clutch/status.py`: `run_admission` (`` `clutch new {stem}` `` and "with `new`"), `review_admission` (`` retry `review {stem}` `` and `` before `review {stem}` ``), `order_admission` (`clutch new {stem}`) and `lint_admission` (`clutch new <stem>`).
- `clutch/observe.py::extension_fields`: the `commands` entries `review`, `lint` and `order` become `["ticket", "review"]`, `["ticket", "lint"]` and `["ticket", "order"]`. The keys, `orderFlags` and every other entry stay. The extension reads these argv from the snapshot.
- `clutch/help.py`: the topics `verb.review`, `verb.lint` and `verb.order` keep their keys, and their `verb` field (the run-guide row each reads) becomes `ticket review`, `ticket lint` and `ticket order`. `COMMANDS` is unchanged. `tests/integration/test_help.py::test_links_resolve` and `::test_verb_what_from_run_guide` find each topic's row by `TOPICS[key]["verb"]` instead of the key's text after `verb.`; nothing else in that file changes.
- `clutch/hostfiles.py` `CORE_TEMPLATE`, the "Never write a ticket from memory" bullet: `clutch ticket new <stem> --kind feature|bug|chore`, `clutch ticket lint <stem>` and `clutch ticket review <stem>`. This adds 21 bytes (8,088 to 8,109, under the 8,192 cap). Refresh the managed blocks with `uv run clutch core` at the checkout root (`CLAUDE.md`, `AGENTS.md`) and in `hosts/fixture` (`hosts/fixture/CLAUDE.md`), never by hand, and regenerate `GOLDEN` in `tests/integration/test_hostfiles.py` with `uv run python -m tests.integration.test_hostfiles`. Nothing outside the managed blocks changes in the three conduct files. Rule home: an existing host rule, edited in its home `CORE_TEMPLATE`.
- Prompt specs: `clutch/specs/author.md` ("the guide's `new`, `lint`, and `review` steps"); `clutch/specs/ask/author.md` (steps 2, 4 and 6, the "If new refuses" sentence, and "The review verb" limit); `clutch/specs/ask/review.md` (`clutch lint` and `clutch review` in its second paragraph); `clutch/specs/ask/drain-loop.md` (the two `clutch lint <stem>` and one `clutch review <stem>`); `clutch/specs/ask/plan-ticket-drain.md` (the "Author while a ticket runs" bullet). No spec's `version` changes.
- Docs: `README.md` (the "Set up a host" paragraph, step 3 of "Author and run tickets", and the four authoring lines of the command block); `clutch/docs/host-authoring.md` (Workflow steps 1-3, `clutch order` in the `Runs before` bullet, and "`new` copies" under `### Evidence`); `clutch/docs/host-contract.md` (onboarding step 7); `clutch/docs/host-running.md` (the first cells of the four rows become `ticket new`, `ticket lint`, `ticket review` and `ticket order`, in place, text unchanged); `docs/how-clutch-works.md` (the four section 2.1 rows begin `ticket new`, `ticket lint`, `ticket order` and `ticket review`, text unchanged; in section 3.2 the opening sentence's `review` and "Intake, `lint`, `new`, and requisition review"; in section 6.7 "`order` treats it as open"; in section 8.1 the Preflight list's `review`).
- `tests/unit/test_host_running.py::test_verb_table_matches_parser`: a row may name a top-level command or a `<group> <subcommand>` path of the parser. Every top-level command begins at least one row, a group with any subcommand row has a row for every one of its subcommands, and no row repeats. It still reads only `clutch/docs/host-running.md`, as today. `roadmap` and `prompt` keep their single rows.

Tests whose argv or pinned text the rename forces; only those lines change:
- `tests/unit/test_main_help.py`: the `("order",)` case of `test_help_forms_agree` becomes `("ticket", "order")`.
- `tests/unit/test_help.py`: `test_verb_what_follows_run_guide` replaces `Description of ticket review.` and `test_unresolved_link_raises` replaces the row `` | `ticket review` | ``, the text its `documents()` helper now builds from the topic's `verb`; both still read topic `verb.review`.
- `tests/unit/test_observe_extension_fields.py`: the three argv values, plus the new `test_extension_commands_parse` of criterion 8.
- `tests/unit/test_verdict_extension.py::test_verdict_and_review_loop_over_stems`: the `review` case runs `["ticket", "review", "a", "b"]`.
- `tests/unit/test_paved_roads.py`, `tests/unit/test_ask_drafts.py` and `tests/integration/test_ask.py`: the expected roads.
- `tests/integration/test_ask_plan_drain.py` and `tests/integration/test_ask_drain_loop_agent.py`: the phrase lists.
- `tests/integration/test_host_onboarding_doc.py`: the three authoring phrases.
- `tests/integration/test_review_command.py`: the argv and the refusal prefix `clutch ticket: probe refused`.
- `tests/integration/test_lint_verb.py`, `tests/integration/test_menu_verb_parity.py`, `tests/integration/test_intake_scope.py`, `tests/integration/test_tickets.py`, `tests/integration/test_stale_running.py` and `tests/integration/test_cli.py`: the argv. `tests/integration/test_cli.py` is a do-not-grow file, fenced only because its `new` and `order` tests call `cli(root, "new", ...)` and `cli(root, "order", ...)`; nothing is added to it.
- `tests/regress_lint_worktree_journal.py`, `tests/regress_requisition_prior_review.py` and `tests/regress_review_intakes_own_stem.py`: the argv, so each still prints `{"regression_result": "pass"}`.

New `tests/unit/test_main_ticket_group.py`: it builds `_parser()` in memory and calls `main(..., cwd=tmp_path)`, with stubs for `load_config`, `Journal`, `Git`, `CommitLock` and `SubprocessExec` where a config is needed, as `tests/unit/test_verdict_extension.py::test_verdict_and_review_loop_over_stems` does. It reads no repo file and starts no process. It runs the new parser and dispatch lines of `clutch/__main__.py` (coverage floor 13).

Merge order. The drain runs one ticket at a time from main's tip, so whichever of these runs second starts from the other's merged code.
- `cli-group-engine-run` (row 130, being authored now) moves `drain`, `serve`, `run` and `stop` into group `engine` and edits many of these files: `clutch/__main__.py`, `clutch/help.py`, `clutch/observe.py`, `clutch/status.py::run_admission`, `clutch/docs/host-running.md`, `clutch/docs/host-authoring.md`, `docs/how-clutch-works.md` (including the section 3.2 and 8.1 sentences above), `README.md`, the ask specs, and the tests `test_main_help.py`, `test_host_running.py`, both `test_help.py` files, `test_observe_extension_fields.py`, `test_paved_roads.py`, `test_intake_scope.py`, `test_menu_verb_parity.py`, `test_ask_plan_drain.py`, `test_ask_drain_loop_agent.py` and `test_cli.py`. In a line both touch, this ticket changes only the words for `new`, `lint`, `review` and `order`; every other word keeps the base commit's form. For example the `run_admission` road and its pin in `tests/unit/test_paved_roads.py` read ``author it with `clutch ticket new item`, fill it, then `` followed by whatever run command the base commit has. The criteria name only this ticket's commands; where a criterion compares a whole dict or table, the other entries match the base commit, not HEAD `4dbff7d8`. If row 130 has already changed `test_verb_table_matches_parser` so that it meets criterion 9, or already makes `tests/integration/test_help.py` find rows by `TOPICS[key]["verb"]`, keep its version. Row 130's draft takes the same two approaches for `engine drain`, `engine serve`, `engine run` and `engine stop`.
- `rule-restatements-single-home` (running) edits `clutch/docs/host-contract.md` section `## Managed conduct and ticket ownership` and `docs/how-clutch-works.md` sections 3.2 (the "Every ticket read" bullet), 4.2 and 5.2. This ticket leaves the "Every ticket read (intake, lint, ...)" sentences as they are, because they name checks, and edits other lines: onboarding step 7 of the contract, and the opening sentence and Regression paragraph of section 3.2. Either order leaves both tickets' criteria true.
- `projection-helpers-single-owner` (confirmed) edits other functions of `clutch/__main__.py` (the journal fold in `handle_prompt`, `build_control`, `provider_holds`, `handle_suggest`, `build_daemon_core`), of `clutch/status.py` (`latest_transitions`, `last_states`) and of `clutch/observe.py` (`as_events`, `last_bodies`, `snapshot`), and `tests/unit/test_verdict_extension.py::test_drain_logs_refusal`. These are different lines, and its source scan flags no string this ticket writes, so either order passes.

Out:
- `vscode-clutchwork/`: it runs the argv the snapshot supplies. `tests/vscode_task_identity.js` and `tests/regress_vscode_task_identity.py` fake a snapshot with arbitrary argv and stay.
- `CLUTCH_PLAN.md` (frozen), `docs/roadmap.md`, and the plans under `docs/` (`docs/document-agent-plan.md`, `docs/gemini-graphics-refactor-plan.md`, `docs/roadmap-driver-plan.md`, `docs/upstream-issue-plan.md`): design records, not on the "Docs follow commands" list; a later sweep is filed to the Suggestion Box.
- Any spec `version`; every other command, including `confirm` and `reject` (row 133); and output wording beyond the roads named above.
- The `clutch <verb>:` refusal line of `docs/how-clutch-works.md` section 2.1: the group is still the first word.
- `tests/unit/test_readme.py` and `tests/integration/test_ask_plan_drain.py::test_prompts_name_only_existing_verbs` stay unedited and passing; they fail on any `uv run clutch new` line or rendered `` `clutch lint `` reference left behind.

## Scope fence
- clutch/__main__.py
- clutch/status.py
- clutch/observe.py
- clutch/help.py
- clutch/hostfiles.py
- clutch/specs/author.md
- clutch/specs/ask/author.md
- clutch/specs/ask/review.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-authoring.md
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/unit/test_main_ticket_group.py
- tests/unit/test_main_help.py
- tests/unit/test_host_running.py
- tests/unit/test_help.py
- tests/integration/test_help.py
- tests/unit/test_observe_extension_fields.py
- tests/unit/test_verdict_extension.py
- tests/unit/test_paved_roads.py
- tests/unit/test_ask_drafts.py
- tests/integration/test_ask.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_host_onboarding_doc.py
- tests/integration/test_review_command.py
- tests/integration/test_lint_verb.py
- tests/integration/test_menu_verb_parity.py
- tests/integration/test_intake_scope.py
- tests/integration/test_tickets.py
- tests/integration/test_stale_running.py
- tests/integration/test_cli.py
- tests/integration/test_hostfiles.py
- tests/regress_lint_worktree_journal.py
- tests/regress_requisition_prior_review.py
- tests/regress_review_intakes_own_stem.py

## Acceptance criteria
1. `tests/unit/test_main_ticket_group.py::test_ticket_group_parses`: `_parser().parse_args(["ticket", "new", "some-stem"])` gives `ticket_verb == "new"`, `stem == "some-stem"`, `kind == "feature"` and `evidence is None`; `["ticket", "new", "some-stem", "--kind", "bug", "--evidence", "a.txt", "b.txt"]` gives `kind == "bug"` and `evidence == ["a.txt", "b.txt"]`; `["ticket", "lint"]` gives `stems == []`; `["ticket", "review", "a", "b"]` gives `stems == ["a", "b"]`, and `["ticket", "review"]` raises `SystemExit(2)`, not `stems == []`; `["ticket", "order", "some-stem", "--runs-before"]` gives `runs_before == []` and `priority is None`. Ruled out: a changed arity, default or option name.
2. `tests/unit/test_main_ticket_group.py::test_old_names_refuse`: none of `new`, `lint`, `review` and `order` is a choice of the top-level subparsers, each is a choice of the `ticket` group, and `_parser().parse_args([name, "some-stem"])` raises `SystemExit(2)` for each. Ruled out: an alias, hidden parser or argv rewrite that keeps an old name working.
3. `tests/unit/test_main_ticket_group.py::test_ticket_new_needs_no_config`: in an empty `tmp_path` with no `config.yaml`, `main(["ticket", "new", "some-stem"], cwd=tmp_path)` returns 0, `tmp_path / "tickets/some-stem/ticket.md"` exists, and `tmp_path / ".clutch"` does not. Ruled out: exit 2 with a missing-config refusal because `ticket new` is dispatched after config load.
4. `tests/unit/test_main_ticket_group.py::test_lint_git_skips_optional_locks`: with `load_config` returning a stub config, `Journal`, `CommitLock` and `SubprocessExec` stubbed, `Git` replaced by a recorder of its `env` keyword, and `_lint` and `_order` replaced by fakes returning 0, `main(["ticket", "lint"], cwd=tmp_path, env={})` builds `Git` with `env["GIT_OPTIONAL_LOCKS"] == "0"`, and `main(["ticket", "order", "some-stem", "--priority", "P1"], cwd=tmp_path, env={})` builds it without that key. Ruled out: `ticket lint` losing the read-only git environment once `args.verb` is `ticket`.
5. `tests/unit/test_main_ticket_group.py::test_refusal_names_group`: with the stubs of criterion 4 and the real `_order`, `main(["ticket", "order", "some-stem"], cwd=tmp_path, env={})` returns 2 and stderr is exactly `clutch ticket: no ordering option supplied -- supply --priority or --runs-before\n`. Ruled out: the old `clutch order:` prefix, a `clutch ticket order:` prefix, and an uncaught `Refusal`.
6. `./dev.py test tests/unit/test_main_help.py` exits 0 with only the `("order",)` case changed to `("ticket", "order")`. Its parser walk now checks the `ticket` group and its four subcommands for a description and examples that parse, and the top-level help lists `ticket new`, `ticket lint`, `ticket review` and `ticket order` once each with their summaries. On the base commit the `("ticket", "order")` case fails with `clutch help: unknown command`.
7. `uv run clutch help ticket review` prints `usage: clutch ticket review`, what it does, then `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with the `ticket review` row of `docs/how-clutch-works.md` section 2.1 (commit lock only; exits 0 on approve, 1 on snag or rma, 2 on refusal), its options, then `Examples:` with a `clutch ticket review <stem>` line. `uv run clutch help ticket new`, `uv run clutch help ticket lint` and `uv run clutch help ticket order` print the same parts with the facts in Scope in, and `uv run clutch help ticket` lists the four subcommands and its examples.
8. `./dev.py test tests/unit/test_observe_extension_fields.py` exits 0. `test_extension_fields` expects `["ticket", "review"]`, `["ticket", "lint"]` and `["ticket", "order"]` for those keys and the base commit's value for every other key. The new `test_extension_commands_parse` calls `_parser().parse_known_args([*argv, "some-stem"])` for every argv in `extension_fields(tmp_path)["commands"].values()` and fails on `SystemExit`, so it fails if an entry still reads `["review"]`, `["lint"]` or `["order"]`. Ruled out: an extension menu action that runs a removed command.
9. `./dev.py test tests/unit/test_host_running.py` exits 0, and `grep -cE '^\| .ticket (new|lint|review|order). \|' clutch/docs/host-running.md` prints `4`. `test_verb_table_matches_parser` fails on a row naming a removed top-level command such as `lint`, on a `ticket` group with a row for some but not all of its subcommands, and on a repeated row; it passes with the single `roadmap` and `prompt` rows.
10. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py` exits 0. `help.TOPICS["verb.lint"]["verb"] == "ticket lint"`, `help.COMMANDS` is unchanged, and `test_verb_what_from_run_guide` checks that the `what` of topic `verb.review` is the text of the `ticket review` run-guide row. Ruled out: a `verb.*` topic whose run-guide row is gone, which raises `LookupError` when the snapshot builds its help, and a renamed topic key.
11. `CORE_TEMPLATE` in `clutch/hostfiles.py` contains `clutch ticket new <stem> --kind feature|bug|chore`, `clutch ticket lint <stem>` and `clutch ticket review <stem>`, and `len(CORE_TEMPLATE) <= 8192`. `./dev.py test tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/integration/test_contention_rules.py` exits 0, so the managed blocks of `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` match the template byte for byte and `GOLDEN` is regenerated. `git diff` of those three files changes only lines between the `clutch:core` markers.
12. `git grep -nE 'clutch (new|lint|review|order)([^a-z-]|$)' -- README.md CLAUDE.md AGENTS.md hosts/fixture/CLAUDE.md clutch docs/how-clutch-works.md tests` prints nothing; on the base commit it prints 39 lines. Ruled out: a reference left in a doc, spec, conduct file, engine road or test.
13. `grep -cE '^\| .ticket (new|lint|review|order) ' docs/how-clutch-works.md` prints `4` and `grep -cE '^\| .(new|lint|review|order) ' docs/how-clutch-works.md` prints `0`. A reader finds `ticket review`, `ticket lint`, `ticket new` and `ticket order` at the section 3.2, 6.7 and 8.1 sites named in Scope in, and `` `ticket new` copies `` under `### Evidence` in `clutch/docs/host-authoring.md`.
14. `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask.py tests/unit/test_ask_drafts.py tests/unit/test_paved_roads.py tests/unit/test_readme.py` exits 0. The phrase lists require `clutch ticket new unique-stem --kind`, `clutch ticket lint unique-stem` and `clutch ticket review unique-stem`, in that order, in the author prompt, and `clutch ticket lint` and `clutch ticket review` in the drain-loop prompt. `test_prompts_name_only_existing_verbs` passes unedited; it fails if a rendered prompt still names `` `clutch new ``, `` `clutch lint `` or `` `clutch review ``.
15. `./dev.py test tests/integration/test_cli.py tests/integration/test_review_command.py tests/integration/test_lint_verb.py tests/integration/test_menu_verb_parity.py tests/integration/test_intake_scope.py tests/integration/test_tickets.py tests/integration/test_stale_running.py tests/integration/test_host_onboarding_doc.py tests/integration/test_main_verb_groups.py tests/unit/test_verdict_extension.py` exits 0. In those files only the argv lists (with `"ticket"` before the verb), the refusal prefix in `tests/integration/test_review_command.py` and the onboarding phrases change; no other assertion changes, and `tests/integration/test_cli.py` gains no test.
16. `uv run python tests/regress_lint_worktree_journal.py`, `uv run python tests/regress_requisition_prior_review.py` and `uv run python tests/regress_review_intakes_own_stem.py` each print `{"regression_result": "pass"}` and exit 0. Ruled out: a reproducer still calling a removed command.

## Verification
```
./dev.py test tests/unit/test_main_ticket_group.py tests/unit/test_main_help.py tests/unit/test_observe_extension_fields.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_verdict_extension.py tests/unit/test_paved_roads.py tests/unit/test_ask_drafts.py tests/unit/test_readme.py tests/unit/test_hostfiles_supervisor_verdicts.py
./dev.py test tests/integration/test_help.py tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py tests/integration/test_contention_rules.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask.py tests/integration/test_host_onboarding_doc.py
./dev.py test tests/integration/test_cli.py tests/integration/test_review_command.py tests/integration/test_lint_verb.py tests/integration/test_menu_verb_parity.py tests/integration/test_intake_scope.py tests/integration/test_tickets.py tests/integration/test_stale_running.py tests/integration/test_main_verb_groups.py
uv run python tests/regress_lint_worktree_journal.py
uv run python tests/regress_requisition_prior_review.py
uv run python tests/regress_review_intakes_own_stem.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `new`, `lint`, `review` or `order` still runs as a top-level command through an alias, a hidden parser or argv rewriting in `main`.
- An argument, default, arity, output line, exit code, lock, commit or journal event of the four commands changes, other than the refusal prefix and the roads named in Scope in.
- A spec `version` changes; a managed block is edited by hand or differs from `CORE_TEMPLATE`; or `CLAUDE.md`, `AGENTS.md` or `hosts/fixture/CLAUDE.md` changes outside its managed block.
- Anything under `vscode-clutchwork/` changes, or a help topic key or `COMMANDS` entry changes.
- A test is added to a do-not-grow file, or an existing assertion changes beyond the argv, prefix, road, phrase, table-check and help-topic updates named in Scope in.
- Another command is moved or renamed.

## Time budget
- expected: 50m
- stuck: 100m
- reason: a rename with no alias moves the parser and every caller in one change (CLAUDE.md "No dual-path code"); splitting by command would repeat the same file edits in up to four tickets, and every edit outside the parser is a one-line text or argv change.
