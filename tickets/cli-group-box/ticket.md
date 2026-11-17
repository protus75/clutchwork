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
- clutch/issue.py
- clutch/hostfiles.py::CORE_TEMPLATE
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_ticket_group.py
- tests/integration/test_ask_plan_drain.py::test_prompts_name_only_existing_verbs

## On-demand
- README.md
- clutch/specs/ask/author.md
- clutch/specs/ask/box.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_triage.py
- tests/integration/test_cli.py
- tests/unit/test_issue_link.py

## Goal / Why
Roadmap row 134 (`cli-group-box`), group `box`. `cli-help-standard` (row 129, merged at `e09d9e05`) added `_command` in `clutch/__main__.py` and the repo-local rules in `CLAUDE.md` section A: every command carries help to the standard through `_command`, every command lives under a top-level group, and a command change updates every document that describes it in the same change. Rows 130-133 (merged at `fcefb4f6`, `9de3d083`, `f2a246d7` and `084b9e48`) built the `engine` and `ticket` groups that way. At HEAD (`cda88370`) `suggest`, `triage`, `dismiss` and `issue` are still top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help triage` prints no reads, writes, lock, exit codes or examples, and 33 lines of `README.md`, the conduct files, `clutch/` and `docs/how-clutch-works.md` spell them `clutch suggest|triage|dismiss|issue`.

When this ticket is done:
- `clutch box suggest <summary>`, `clutch box triage [id ...]`, `clutch box dismiss <id> ...` and `clutch box issue [--class <class>] <title> --body FILE` take the same arguments, print the same stdout lines (`suggest: filed <id>`, `suggest: already in the box as <id>`, each triage and dismiss result line, `no pending suggestions`, the issue link), take the same locks under the same lock verbs (`triage` and `dismiss`; none for suggest and issue), write the same files, commits and journal events, and exit with the same codes as `clutch suggest`, `clutch triage`, `clutch dismiss` and `clutch issue` do at HEAD. The only visible differences are the help text, argparse's own usage and error lines, the refusal prefix, the issue body's last footer line, the one road, the docs, prompts, conduct block and extension argv that name these commands, and the commit-lock label of a running triage or dismiss (all in Scope in).
- `clutch suggest`, `clutch triage`, `clutch dismiss` and `clutch issue` no longer parse: argparse exits 2 with an invalid-choice error. There is no alias (`CLAUDE.md` "No dual-path code").
- The `box` group and its four subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them.
- Every caller names the new form in the same change: the engine's road, the issue footer, the prompt specs, the core template and the three managed blocks it renders, the host run guide, `README.md`, `docs/how-clutch-works.md`, the extension's argv table and help topics, the test harness, and the tests.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140), so a person or agent finds the Suggestion Box commands together under `clutch help box`, each with what it reads, writes and locks and how it exits. Rows 135-140 move the rest.

Transition, once: an agent or chat session that loaded a conduct block (`CLAUDE.md`, `AGENTS.md`) or rendered `clutch prompt author`, `clutch prompt box`, `clutch prompt drain-loop` or `clutch prompt plan-ticket-drain` before this merges holds text naming `clutch suggest`, `clutch triage`, `clutch dismiss` or `clutch issue`. After the merge those commands exit 2 with an argparse invalid-choice error and file or settle nothing. Re-read the conduct file or re-render the prompt, or run `clutch box suggest`, `clutch box triage`, `clutch box dismiss` or `clutch box issue`. No running engine needs a restart: drain and serve run triage in-process (never as a `clutch triage` child) and the lock verbs do not change. The VS Code extension runs `clutch snapshot` on each refresh and takes its Triage, Dismiss and Bulk triage argv from it, so those actions use the new form from the first refresh after the merge. Another host gets the new conduct block when it runs `clutch core` after upgrading, which `engine drain`, `engine serve` and `engine run` already require.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `suggest`, `issue`, `triage` and `dismiss` parsers. Add a group `box` the way `ticket` and `engine` are built: a one-line summary, a `description` of what the group covers (for example "File ideas into the Suggestion Box, settle its messages, and link critical clutch bugs upstream."), an `Examples:` epilog whose `clutch box ...` line parses, and `argparse.RawDescriptionHelpFormatter`. Its subparsers take `dest="box_verb"` and `required=True`. Its four subcommands are built with `_command`, with every field, and keep their arguments exactly:
  - `suggest`, positional `summary`. Facts: files the idea as a `suggestion` message in the Suggestion Box under `<state_dir>/box/`; a repeat of the same summary folds into the existing message; refuses a blank summary. Reads config and the box. Writes the message file, and a reopen signal to the journal when a tombstoned message is re-reported. Lock: none (it files while a writer holds the lock). Exits 0 when filed or already in the box, 2 on refusal. Example `clutch box suggest "<an idea>"` with a quoted idea.
  - `triage`, positional `ids` (`nargs="*"`). Facts: one sequential pass over named pending messages, or all pending messages, settling each as author, tombstone or declined with a model call (section 9.2); reaps interrupted runs first; refuses unknown ids before the pass. Reads config, the box, journal, tickets and git state. Writes decision records and authored tickets in commits, message resolutions and journal events. Lock: writer lock. Exits 0 after the pass, 2 on refusal. Examples `clutch box triage` and `clutch box triage <box id>`.
  - `dismiss`, positional `ids` (`nargs="+"`). Facts: declines named messages as operator decisions without a model call; unknown ids refuse before any message settles; an already-resolved message prints its resolution. Reads config, the box and journal. Writes `tickets/decisions/declined-<id>.md` records in commits and message resolutions. Lock: writer lock. Exits 0 when dismissed or already resolved, 2 on refusal.
  - `issue`: `--class` (`dest="issue_class"`, `default=None`, its help listing `issue.CLASSES`), positional `title`, and `--body` (`type=Path`, `required=True`). Facts: prints a prefilled GitHub new-issue link for a critical clutch bug and submits nothing; reads the `--body` file and, when it loads, config to scrub configured secrets; writes nothing; lock: none; exits 0 when printed, 2 on refusal (unknown or missing class, unreadable or empty body, link over 3,000 bytes). Example `clutch box issue --class engine-stuck "<title>" --body body.md`.
  Read each fact from its `docs/how-clutch-works.md` section 2.1 row and its handler before writing it.
- Dispatch: `handlers` drops the top-level `issue`, `suggest`, `dismiss` and `triage` entries and gains `"box"`, dispatching by `args.box_verb` to the unchanged `handle_suggest`, `handle_triage`, `handle_dismiss` and `handle_issue`. `box issue` still runs before config loads, where `issue` runs today: in the pre-config condition, `"issue"` leaves the set and `(args.verb == "box" and args.box_verb == "issue")` joins the `or`. `handle_triage` and `handle_dismiss` keep their `_locked` verbs `"triage"` and `"dismiss"`. `handle_issue` keeps its name and its `issue: config did not load, so no secrets were scrubbed: ...` stderr line, which `tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner` names.
- Refusals keep going through `_fail(args.verb, ...)`, the `UnknownBoxId` branch included, so a box refusal prints `clutch box: <message> -- <road>`, as `ticket` and `engine` refusals print `clutch ticket:` and `clutch engine:`. No `print(..., file=sys.stderr)` is added.
- Road: `handle_prompt`'s drafts refusal road `run triage, or author a ticket with clutch ticket new` becomes `run clutch box triage, or author a ticket with clutch ticket new`.
- Accepted visible change, as in row 132: `observe.lock_verb` names a commit-lock holder by the word after `clutch` in its `/proc/<pid>/cmdline`, so while `clutch box triage` or `clutch box dismiss` commits, the snapshot's `commitLock` field reads `box since ... (pid N)` instead of `triage since ...`. The writer-lock label still comes from the lockfile's `triage` or `dismiss` verb. `lock_verb` is not changed.

In, other code:
- `clutch/observe.py::extension_fields`: the `commands` entries `triage` and `dismiss` become `["box", "triage"]` and `["box", "dismiss"]`. The keys and every other entry stay. `vscode-clutchwork/` is unchanged: it runs these argv from the snapshot.
- `clutch/help.py`: topics `verb.triage` and `verb.dismiss` keep their keys, and their `verb` field (the run-guide row each reads) becomes `box triage` and `box dismiss`: the topic loop's `verb=` expression gains a `box` branch for them. `COMMANDS` is unchanged. `suggest` and `issue` have no topic and get none.
- `clutch/issue.py::link`: the body footer's last line becomes `Filed with clutch box issue`.
- `clutch/hostfiles.py` `CORE_TEMPLATE`: `clutch box suggest "<summary>"` in the "File an unrequested idea" bullet, `clutch box suggest` in the "With every fix or diagnosis" bullet, and both `clutch box issue` in the "Outside clutch's own repo" bullet. This adds 16 bytes (8,109 to 8,125, under the 8,192 cap). Refresh the managed blocks with `uv run clutch core` at the checkout root (`CLAUDE.md`, `AGENTS.md`) and in `hosts/fixture` (`hosts/fixture/CLAUDE.md`), never by hand, and regenerate `GOLDEN` in `tests/integration/test_hostfiles.py` with `uv run python -m tests.integration.test_hostfiles`. Nothing outside the managed blocks changes in the three conduct files. Rule home: existing host rules, edited in their home `CORE_TEMPLATE`.

In, prompts (these files carry no `version`):
- `clutch/specs/ask/author.md`: `clutch box triage` and `clutch box dismiss` in the "Never run" list, and "Second problems go to `clutch box suggest`".
- `clutch/specs/ask/box.md`: "give the exact `clutch box triage` or `clutch box dismiss` command".
- `clutch/specs/ask/drain-loop.md`: all ten references gain `box `: in step 4, `clutch box suggest` a replacement; the box bullet's "`clutch box triage` and `clutch box dismiss` take the writer lock", `clutch box triage <id> ...`, `clutch box dismiss <id> ...` and "as `clutch box triage <id>`"; the cause-fix bullet's `clutch box suggest "<summary>"`; and the hard limits' "comes only from `clutch box triage`" and the two "`clutch box suggest` it".
- `clutch/specs/ask/plan-ticket-drain.md`: "goes to `clutch box suggest`", "Pass `clutch box triage` only" and "with `clutch box suggest`".
- Prose naming the action or the pass stays: "never triaged or dismissed", "Triage or dismiss a Suggestion Box message only by executing", "Triage each message at most once per tick" and "Never triage a `roadmap_row`".

In, documents. Only references to the command change:
- `README.md`: the `# Authoring` lines become `uv run clutch box suggest` and `uv run clutch box issue`, with comments aligned like the other `# Authoring` lines, and step 6's "Retros and `clutch box suggest` from a chat session".
- `clutch/docs/host-running.md`: the first cells of the `suggest`, `issue`, `triage` and `dismiss` rows become `box suggest`, `box issue`, `box triage` and `box dismiss`, in place, text unchanged; "Stop serve before `roadmap author`, `box triage`, `box dismiss`, ..."; and under "Reporting a critical clutch bug", the channel table's "Suggestion Box (`clutch box suggest`)" and "Upstream issue (`clutch box issue`)" cells and "runs `clutch box issue --class <class> ...`".
- `docs/how-clutch-works.md`: the section 2.1 rows begin `` `box suggest <summary>` ``, `` `box issue --class <class> <title> --body FILE` ``, `` `box triage [id ...]` `` and `` `box dismiss <id> ...` ``, text unchanged; section 7.5 "files cause fixes with `clutch box suggest`"; section 8.1's Preflight list `box triage`; section 9.1 "with `box suggest` directly"; section 9.2 "`box triage` settles" and "`box dismiss <id> ...` records"; section 12 "a `clutch box issue` critical class".

In, tests. Only the argv (`"box"` before the verb) and the pinned text named here change:
- New `tests/unit/test_main_box_group.py` (criteria 1-4). It builds `_parser()` in memory and calls `main(..., cwd=tmp_path, env={})` in a `tmp_path` holding at most a body file, replacing `clutch.issue.link` with a fake where a link is printed. It reads no repo file and starts no process. It runs the new parser and dispatch lines of `clutch/__main__.py` (coverage floor 13).
- Pinned text: `tests/unit/test_ask_drafts.py` (the drafts road); `tests/unit/test_issue_link.py` and `tests/integration/test_issue_verb.py` (the footer line and the `clutch box:` refusal prefix); `tests/unit/test_observe_extension_fields.py` (the two argv); `tests/integration/test_ask_drain_loop_agent.py` (phrases `clutch box suggest`, `clutch box triage` and `clutch box dismiss`) and `tests/integration/test_ask_plan_drain.py` (the two `clutch box suggest` phrases); `tests/integration/test_cli.py` (`clutch box: blank summary -- ...`); `tests/integration/test_main_verb_groups.py` (`clutch box: {LockHeld(...)}`); `tests/integration/test_triage.py` (`clutch box: probe refused`); `tests/integration/test_hostfiles.py` (`GOLDEN`, regenerated).
- Argv only: `tests/unit/test_issue_link.py`, `tests/unit/test_suggest_box.py`, `tests/unit/test_stale_running.py` (`(["box", "dismiss", "id"], ["box", "triage"])`), `tests/integration/test_author.py` (its `_run` helper), `tests/integration/test_cli.py` (the four `cli(root, "suggest", ...)` calls), `tests/integration/test_inbox.py`, `tests/integration/test_issue_verb.py`, `tests/integration/test_main_verb_groups.py`, `tests/integration/test_menu_verb_parity.py` (the `dismiss` call and the `("triage", "dismiss")` loop, which runs `["box", verb, "missing"]`), `tests/integration/test_roadmap_row_author.py`, `tests/integration/test_stale_running.py` (the `("dismiss", "id")` and `("triage",)` entries of the `test_every_locked_verb_reaps` loop), `tests/integration/test_triage.py` (its `run` helper and direct `main` calls), `tests/harness/host_loop.py` (its spawned `[sys.executable, "-m", "clutch", "box", "triage"]`), and `tests/regress_suggest_lands_in_box.py`, so it still prints `{"regression_result": "pass"}`. `tests/integration/test_cli.py` is a do-not-grow file, fenced only for its suggest calls and pin; nothing is added to it.
- `tests/integration/test_box.py` and `tests/integration/test_open_tickets_closed.py` reach the CLI only through `tests/integration/test_triage.py::run`, and `tests/integration/test_host_loop.py` through `tests/harness/host_loop.py` (its `argv[-1] == "triage"` count still holds), so they pass with no edit. A scratch prototype of the code change without the test edits failed 9 unit and 114 integration tests in the fenced files and these three; with them, 910 unit and 3,408 integration tests passed at `cda88370`, the one failure being the base flake named in criterion 16.

Merge order. No confirmed, unmerged ticket fences a file this ticket fences: `plan-status-rusage-packages` (running) fences only two plans under `docs/`. Row 133 (`cli-group-ticket-verdicts`) merged at `084b9e48` and already rewrote `confirm` and `reject` in lines this ticket also edits: the `verb=` expression of the `help.py` topic loop, the "Never run" line of `clutch/specs/ask/author.md`, the step 4 Reject-queue and box bullets of `drain-loop.md`, `README.md` step 6, the section 7.5 sentence of `docs/how-clutch-works.md`, and the `test_every_locked_verb_reaps` loop line of `tests/integration/test_stale_running.py`. In those lines this ticket changes only the words for `suggest`, `triage`, `dismiss` and `issue`, and every other word keeps the form main has when it runs. Where a criterion compares a whole dict, list or line, its other entries match main. A later row (135-140) that moves another command starts from this ticket's merged code.

Out:
- An alias of any kind for the old names; every other command, including `status` (row 137) and `prompt box` (a `prompt` subcommand).
- Lock, journal and stage vocabulary: the `_locked` verbs `triage` and `dismiss`, `lockfile.ENGINE_VERBS`, the `triage` LLM surface and `clutch/specs/triage.md`, the `triage_pass` signal, `observe.STEP_NAMES`, `observe.lock_verb` and `hostfiles._IMPERATIVES`.
- Output text other than the footer line, the refusal prefix and the one road: `suggest: filed <id>`, `suggest: already in the box as <id>`, `no pending suggestions`, the triage and dismiss result lines, and `handle_issue`'s `issue: config did not load ...` warning.
- Roads that name the triage pass rather than the command: `clutch/triage.py`'s `repair repository/evidence access and retry triage` (also printed by the drain and serve passes) and `clutch/inbox.py`'s `repair this arrival and retry triage` (engine log, from the serve, drain and triage passes).
- Prose naming the pass, stage or action: section 9.2's heading, section 9.4's "serve, drain, and triage ingest", the extension paragraph's "manual triage or dismissal", `clutch/docs/host-contract.md`'s "sequential triage", and `clutch/docs/host-running.md`'s "Ticket agents, triage, retro, Author, and harvest".
- `vscode-clutchwork/` (its command ids `clutch.box.triage`, `clutch.box.dismiss` and `clutch.bulkTriage` stay; it runs the snapshot's argv), `dev.py` and `tests/integration/test_dev.py` (its `suggest` case checks that `dev.py` rejects engine verbs), `CLUTCH_PLAN.md` (frozen), `docs/roadmap.md`, and the plans under `docs/` (`docs/upstream-issue-plan.md`, `docs/roadmap-driver-plan.md`).
- Textual strings no test parses as a command: the `python -m clutch triage` process rows of `tests/integration/test_watch.py::test_engine_flag_follows_lock_holder` and `tests/regress_engine_flag_only_drain_serve.py` (holder verbs come from the lockfile), `tests/unit/test_main_verb_groups.py`'s direct `_fail("dismiss", ...)` formatting check, and the lock verb `triage` in `tests/unit/test_lock_holder.py` and `tests/integration/test_lockfile.py`.
- `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_help.py`, `tests/integration/test_help.py` and `tests/unit/test_readme.py` stay unedited and passing; they already walk the parser and groups, find run-guide rows by `TOPICS[key]["verb"]`, and check the first word of each `uv run clutch` line.

## Scope fence
- clutch/__main__.py
- clutch/observe.py
- clutch/help.py
- clutch/issue.py
- clutch/hostfiles.py
- clutch/specs/ask/author.md
- clutch/specs/ask/box.md
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/unit/test_main_box_group.py
- tests/unit/test_ask_drafts.py
- tests/unit/test_issue_link.py
- tests/unit/test_observe_extension_fields.py
- tests/unit/test_stale_running.py
- tests/unit/test_suggest_box.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_author.py
- tests/integration/test_cli.py
- tests/integration/test_hostfiles.py
- tests/integration/test_inbox.py
- tests/integration/test_issue_verb.py
- tests/integration/test_main_verb_groups.py
- tests/integration/test_menu_verb_parity.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_stale_running.py
- tests/integration/test_triage.py
- tests/harness/host_loop.py
- tests/regress_suggest_lands_in_box.py

## Acceptance criteria
1. `tests/unit/test_main_box_group.py::test_box_group_parses`: `_parser().parse_args(["box", "suggest", "an idea"])` gives `box_verb == "suggest"` and `summary == "an idea"`; `["box", "triage"]` gives `ids == []` and `["box", "triage", "a", "b"]` gives `ids == ["a", "b"]`; `["box", "dismiss", "a"]` gives `ids == ["a"]`; `["box", "issue", "--class", "state-loss", "t", "--body", "b.md"]` gives `issue_class == "state-loss"`, `title == "t"` and `body == Path("b.md")`, and without `--class` gives `issue_class is None`; `["box", "dismiss"]`, `["box", "suggest"]` and `["box", "issue", "--class", "state-loss", "t"]` raise `SystemExit(2)`. Ruled out: a changed arity, default, type or option name.
2. `tests/unit/test_main_box_group.py::test_old_names_refuse`: none of `suggest`, `triage`, `dismiss` and `issue` is a choice of the top-level subparsers, each is a choice of the `box` group, and `_parser().parse_args([name, "x"])` raises `SystemExit(2)` for each. Ruled out: an alias, hidden parser or argv rewrite that keeps an old name working.
3. `tests/unit/test_main_box_group.py::test_issue_needs_no_config`: in a `tmp_path` holding only `body.md`, with `clutch.issue.link` replaced by a fake that returns a string built from its class, title and body, `main(["box", "issue", "--class", "state-loss", "t", "--body", "body.md"], cwd=tmp_path, env={})` returns 0, stdout is that string and a newline, stderr contains `no secrets were scrubbed`, and `tmp_path / ".clutch"` does not exist. Ruled out: `box issue` dispatched after the config load, which returns 2 with a `clutch box:` line containing `config file not found`.
4. `tests/unit/test_main_box_group.py::test_refusals_name_group`: in an empty `tmp_path` (no `config.yaml`), `main` with each of `["box", "suggest", "an idea"]`, `["box", "triage"]` and `["box", "dismiss", "x"]` returns 2, prints nothing on stdout, and prints one stderr line that starts with `clutch box: ` and contains `config file not found`. Ruled out: the old `clutch suggest:`, `clutch triage:` or `clutch dismiss:` prefix, a `clutch box triage:` prefix, and an uncaught exception.
5. `./dev.py test tests/unit/test_main_help.py` exits 0 with that file unchanged. Its parser walk now checks the `box` group and its four subcommands for a description and examples that parse, and the top-level help lists `box suggest`, `box triage`, `box dismiss` and `box issue` once each with their summaries. `uv run clutch help box triage` prints `usage: clutch box triage`, what it does, then `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with Scope in (writer lock; exits 0 after the pass, 2 on refusal), its arguments, then `Examples:` with a `clutch box triage` line. `uv run clutch help box suggest`, `uv run clutch help box dismiss` and `uv run clutch help box issue` print the same parts with the facts in Scope in, and `uv run clutch help box` lists the four subcommands and its examples.
6. `./dev.py test tests/unit/test_host_running.py` exits 0 with that file unchanged, and `grep -cE '^\| .box (suggest|issue|triage|dismiss). \|' clutch/docs/host-running.md` prints `4`. Its `test_verb_table_matches_parser` fails while a row still names a removed top-level command or the `box` group lacks a row for one of its subcommands.
7. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py` exits 0 with both files unchanged. `help.TOPICS["verb.triage"]["verb"] == "box triage"`, `help.TOPICS["verb.dismiss"]["verb"] == "box dismiss"`, and `help.COMMANDS` is unchanged. Ruled out: a `verb.*` topic whose run-guide row is gone, which raises `LookupError` when the snapshot builds its help, and a renamed topic key.
8. `./dev.py test tests/unit/test_observe_extension_fields.py` exits 0. `test_extension_fields` expects `["box", "triage"]` and `["box", "dismiss"]` for those keys and main's value for every other key, and `test_extension_commands_parse` passes unedited; it fails while an entry still reads `["triage"]` or `["dismiss"]`. Ruled out: an extension Triage, Dismiss or Bulk triage action that runs a removed command.
9. `CORE_TEMPLATE` in `clutch/hostfiles.py` contains `` `clutch box suggest "<summary>"` `` and `` `clutch box issue` ``, `git grep -nE 'clutch (suggest|issue)([^a-z-]|$)' -- clutch/hostfiles.py` prints nothing, and `len(CORE_TEMPLATE) <= 8192`. `./dev.py test tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/integration/test_contention_rules.py` exits 0, so `GOLDEN` is regenerated and the managed blocks of `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` match the template byte for byte. `git diff` of those three files changes only lines between the `clutch:core` markers.
10. `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask.py tests/unit/test_ask_drafts.py tests/unit/test_readme.py` exits 0. The phrase lists require `clutch box suggest` in the plan-ticket-drain, author and drain-loop prompts and `clutch box triage` and `clutch box dismiss` in the drain-loop prompt; the drafts refusal road is `run clutch box triage, or author a ticket with clutch ticket new`. `test_prompts_name_only_existing_verbs` passes unedited; it fails while a rendered author, drain-loop or plan-ticket-drain prompt still names `` `clutch suggest`` or `` `clutch triage``.
11. `git grep -nE 'clutch (suggest|triage|dismiss|issue)([^a-z-]|$)' -- README.md CLAUDE.md AGENTS.md hosts/fixture/CLAUDE.md clutch docs/how-clutch-works.md` prints nothing; at HEAD `cda88370` it prints 33 lines. ``git grep -nE '`(suggest|triage|dismiss|issue)( [^`]*)?`' -- README.md 'clutch/docs/host-*.md' docs/how-clutch-works.md`` prints nothing; at HEAD it prints 13 lines. Ruled out: a reference left in a doc, prompt spec (including `clutch/specs/ask/box.md`), conduct file, footer or engine road.
12. `grep -cE '^\| .box (suggest|issue|triage|dismiss)( [^|]*)?. \|' docs/how-clutch-works.md` prints `4` and `grep -cE '^\| .(suggest|issue|triage|dismiss)( [^|]*)?. \|' docs/how-clutch-works.md` prints `0` (at HEAD, `4`).
13. `./dev.py test tests/unit/test_issue_link.py tests/integration/test_issue_verb.py` exits 0: the link's body ends with `Filed with clutch box issue`, each refusal's stderr has a line starting `clutch box:`, `_parser().parse_args(["box", "issue", "--help"])` exits 0 and lists every class, and a secret configured in `config.yaml` is still scrubbed.
14. `./dev.py test tests/integration/test_cli.py tests/integration/test_triage.py tests/integration/test_author.py tests/integration/test_inbox.py tests/integration/test_main_verb_groups.py tests/integration/test_menu_verb_parity.py tests/integration/test_roadmap_row_author.py tests/integration/test_stale_running.py tests/integration/test_box.py tests/integration/test_open_tickets_closed.py tests/integration/test_host_loop.py tests/unit/test_suggest_box.py tests/unit/test_stale_running.py` exits 0, with only the argv and the pinned text named in Scope in changed in those files, no assertion dropped or loosened, and nothing added to `tests/integration/test_cli.py`. `grep -cE '_locked\(config.state_dir, "(triage|dismiss)"' clutch/__main__.py` prints `2`. Ruled out: a `_locked` verb renamed to `box`, which those tests would still pass but which changes the snapshot's writer-lock label and the lock verb a holder reports.
15. `uv run python tests/regress_suggest_lands_in_box.py` prints `{"regression_result": "pass"}` and exits 0. Ruled out: a reproducer still calling a removed command, which prints `{"regression_result": "error"}`.
16. `./dev.py test` exits 0; Check's `unit` and `integration` mechanical checks in `config.yaml` run both full suites. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is the known base flake (box-000706-10233120) and is verified on the base commit, not chased.

## Verification
```
./dev.py test tests/unit/test_main_box_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_observe_extension_fields.py tests/unit/test_ask_drafts.py tests/unit/test_issue_link.py tests/unit/test_suggest_box.py tests/unit/test_stale_running.py tests/unit/test_readme.py tests/unit/test_hostfiles_supervisor_verdicts.py
./dev.py test tests/integration/test_help.py tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py tests/integration/test_contention_rules.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask.py tests/integration/test_issue_verb.py tests/integration/test_main_verb_groups.py
./dev.py test tests/integration/test_cli.py tests/integration/test_triage.py tests/integration/test_author.py tests/integration/test_inbox.py tests/integration/test_menu_verb_parity.py tests/integration/test_roadmap_row_author.py tests/integration/test_stale_running.py tests/integration/test_box.py tests/integration/test_open_tickets_closed.py tests/integration/test_host_loop.py
uv run python tests/regress_suggest_lands_in_box.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `suggest`, `triage`, `dismiss` or `issue` still runs as a top-level command through an alias, a hidden or suppressed parser, or argv rewriting in `main`.
- An argument, default, arity, stdout line, exit code, lock, lock verb, commit or journal event of the four commands changes, other than the help text, argparse's usage and error lines, the refusal prefix, the footer line, the road named in Scope in and the accepted commit-lock label.
- `box issue` needs a loadable config, `handle_issue` is renamed, or its config warning changes.
- Anything under `vscode-clutchwork/` changes, or a help topic key or `COMMANDS` entry changes.
- A managed block is edited by hand or differs from `CORE_TEMPLATE`, or `CLAUDE.md`, `AGENTS.md` or `hosts/fixture/CLAUDE.md` changes outside its managed block.
- A test is added to a do-not-grow file, or an existing assertion is dropped, loosened or changed beyond the argv and pinned text named in Scope in.
- Another command is moved or renamed.

## Time budget
- expected: 30m
- stuck: 60m
- reason: not split, because a rename with no alias moves the parser and every caller in one change (`CLAUDE.md` "No dual-path code"), and the box verbs share the same tests, prompt lines and doc rows; a scratch prototype touched 35 files, every edit outside `clutch/__main__.py` and the new test file a one-line text or argv change, and rows 130 and 132 of the same shape ran in 14 and 11 minutes.
