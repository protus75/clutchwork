---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- clutch/__main__.py::_parser
- clutch/__main__.py::_fail
- clutch/__main__.py::main
- clutch/ask.py::KINDS
- docs/how-clutch-works.md#2.1 Verbs
- clutch/docs/host-running.md
- tests/unit/test_host_running.py
- tests/unit/test_ask_drafts.py
- tests/integration/test_ask_plan_drain.py::test_prompts_name_only_existing_verbs
- tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner

## On-demand
- CLAUDE.md
- AGENTS.md

## Goal / Why
Roadmap row 129 (`cli-help-standard`), an owner request of 2026-11-17. At HEAD the CLI help is argparse's default: one line per verb, no examples, and nothing on what a command reads, writes or locks, or how it exits. Observed on 2026-11-17 at commit `aa923bc8`:
- `uv run clutch --help order` prints the top-level list, not the help of `order`: argparse's `-h` ignores the words after it.
- `uv run clutch help order` fails with `argument verb: invalid choice: 'help'` and exit 2.
- `uv run clutch --help` shows `roadmap` as one line (`maintain roadmap tickets`) and none of its five subcommands. It shows `prompt` as one line, with its eight kinds hidden in a `choices` list, so `clutch help prompt diagnose` has nothing to print.
- Every usage line says `python -m clutch`, while the installed command is `clutch`.

When this ticket is done:
- `clutch help <command...>`, `clutch --help <command...>` and `clutch -h <command...>` print the same text as `clutch <command...> --help`. With no command they print the top-level help. None of them needs a `config.yaml`.
- `clutch --help` lists every top-level command once with its one-line summary. Under each group (`roadmap`, `prompt`) it lists every subcommand by its full path with its one-line summary.
- The `roadmap` and `prompt` groups, every subcommand of each, and the new `help` command carry help to the standard. That help states what the command does, what it reads and writes, whether it takes the writer lock, and its exit codes, then gives an `Examples:` section of practical invocations.
- A structural test fails when a group, a subcommand of a group, or `help` has no description or no example. It never pins help wording.
- `CLAUDE.md` and `AGENTS.md` carry three repo-local rules, outside the managed block:
  1. Command help: every `clutch` command and subcommand carries help to the standard above, added through the `_command` helper in `clutch/__main__.py`, and every group carries a description, its subcommand list and examples. The verbs still ungrouped get theirs when roadmap rows 130-140 move them. A new or changed command updates its help and examples in the same change. CLI help lives only with the parser, and extension help stays in `clutch/help.py`; neither copies the other. `tests/unit/test_main_help.py` fails on a grouped command with no description or example; keeping the text true is this rule's job.
  2. Command groups: every command lives under a top-level group. A new command joins the group that fits or adds a new group, and the group's help lists it. `help` is the one ungrouped command by design; roadmap rows 130-140 move the verbs that are still ungrouped.
  3. Docs follow commands: a change to a `clutch` command, group or subcommand updates, in the same change, every document that describes it. These are `README.md`, the shipped host guides `clutch/docs/host-*.md`, `vscode-clutchwork/README.md` when it names the command, the verb tables in `docs/how-clutch-works.md` section 2 and `clutch/docs/host-running.md`, and the command's help.

Why: help is the reference a person and an agent reach first, and today it cannot answer how to run a command, what it touches, or how it exits. Roadmap rows 130-140 depend on this ticket. Each moves the ungrouped verbs into a group and writes their help through the same helper, which brings them under the structural test. This ticket moves no command and changes no argv: `clutch prompt <kind> ...` and `clutch roadmap <subcommand> ...` parse as they do today.

Help sources, per CLAUDE.md section A "Extension help has one source": CLI help text is written only with each command's parser in `clutch/__main__.py`. `clutch/help.py` stays the only source of extension help and is not changed: its `verb.*` topics keep reusing the run-guide verb row. So no help text gains a second home. The one-line verb summaries argparse already carries beside the run-guide rows are not new copies; rule 3 keeps them in step.

## Scope in / Scope out
In, `clutch/__main__.py`:
- `prog="clutch"`, so every usage line reads `usage: clutch ...`.
- One helper, `_command(subparsers, name, *, summary, does, reads, writes, lock, exits, examples)`, adds a subcommand parser from the standard's fields, each a required keyword-only argument with no default: the one-line summary (its `help=`), what it does, what it reads, what it writes, its lock (none, the writer lock, or the commit lock only), its exit codes, and its examples (each a `clutch ...` invocation with a one-line explanation). It returns the new parser so the caller adds its arguments. The helper renders what it does, then `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines, as the parser's `description`, and an `Examples:` section as its `epilog`. It uses `argparse.RawDescriptionHelpFormatter` so those lines keep their layout. A missing field fails when the parser is built. Every subcommand of `roadmap` and `prompt`, and `help`, is added through it. A group parser (`roadmap`, `prompt`) gets a one-line summary, a `description` of what the group covers, and an `Examples:` epilog, with the same formatter so its examples keep their lines; its subcommands carry the reads, writes, lock and exit facts.
- `roadmap`: the group and its five subcommands (`author`, `status`, `accept`, `gate`, `merged`) get help to the standard. The facts come from their rows in `docs/how-clutch-works.md` section 2.1 and the `roadmap` row of the run guide. Arguments, defaults and `dest="roadmap_verb"` are unchanged.
- `prompt` becomes a group. Its `kind` positional becomes subparsers with `dest="kind"`, one subcommand per member of `ask.KINDS`. Each subcommand takes `stems` with `nargs="*"`, exactly as today. `handle_prompt` and every refusal it raises are unchanged: `clutch prompt review` still exits 2 with `clutch prompt: ticket prompt requires exactly one stem -- name one ticket stem`, not an argparse usage error. Each kind gets help to the standard from its rows in section 2.1.
- A new top-level `help` command takes `command` words (`nargs="*"`). With words, it prints the help of the parser at that path, exactly as `clutch <path> --help` prints it, and exits 0. With none, it prints the top-level help and exits 0. An unknown path refuses with exit 2, stderr `clutch help: unknown command <path> -- run clutch help to list commands`, and nothing on stdout. The refusal goes through `_fail` (or a `runner.Refusal` that `main` hands to `_fail`); no new `print(..., file=sys.stderr)` is added, because `tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner` allows stderr prints only in `_fail`, `handle_issue` and `handle_probe`. `main` dispatches `help` with the verbs that run before config loads (`docs`, `init-config`, ...), so it works where no `config.yaml` exists.
- `clutch --help <words...>` and `clutch -h <words...>` behave exactly as `clutch help <words...>`: same stdout, stderr and exit status. Bare `clutch --help` and `clutch -h` print the top-level help. `clutch <path> --help` keeps the subparser's own `-h`.
- The top-level help lists each top-level command once, in parser order, with its one-line summary. Under each group it lists each subcommand on its own line by full path (for example `roadmap merged`) with its one-line summary. It replaces argparse's flat `{watch,snapshot,...}` listing, so no command appears twice, and the usage line names `<command>` instead of every choice. It keeps `--config` and says how to get one command's help.

In, docs:
- `clutch/docs/host-running.md`: one verb-table row for `help`, with `Yes` in "Works while serve runs?", saying it prints a command's help and examples and that `clutch --help <command>` does the same. `tests/unit/test_host_running.py` compares the table with the parser's top-level choices, so the new verb forces this row.
- `docs/how-clutch-works.md` section 2.1: one row `help [command ...]`, lock `no`. It says what `help` prints, that `--help` and `-h` before a command do the same, that command help comes from each command's parser in `clutch/__main__.py`, and that it exits 0, or 2 for an unknown command. The `roadmap` and `prompt` rows stay as they are, since their argv is unchanged.

In, rules: the three rules listed in Goal / Why, as three new bullets in `CLAUDE.md` section `## A. Engine conduct` and three in the `## Engine conduct` section of `AGENTS.md` that follows `<!-- clutch:core end -->`, each placed after the "Extension help has one source" bullet with a `Why:` line citing the owner request of 2026-11-17 (roadmap row 129). Their home is this repo only: they govern clutch's own CLI, so they stay outside the managed blocks and out of the core template.

In, tests: a new `tests/unit/test_main_help.py`. It builds `_parser()` in memory and runs `main(..., cwd=tmp_path)` under `capsys`; it reads no repo file and starts no process.

Out:
- Moving or renaming any command, and help to the standard for the ungrouped verbs: roadmap rows 130-140 do both.
- `clutch/help.py`, `clutch/observe.py` and everything under `vscode-clutchwork/`: extension help and the extension's argv tables are unchanged.
- `clutch/ask.py`: `ask.KINDS` stays the owner of the prompt kinds.
- `README.md`: it describes neither `prompt` nor `roadmap`, its command block is a curated subset that sends readers to the run guide for every verb, and row 141 (`readme-host-first`, fence `README.md`) rewrites it.
- `clutch/hostfiles.py` (its core template) and both managed blocks.
- Any test that pins help wording.

## Scope fence
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- CLAUDE.md
- AGENTS.md
- tests/unit/test_main_help.py

## Acceptance criteria
1. `tests/unit/test_main_help.py::test_commands_have_description_and_examples` walks `_parser()` and finds every group by its subparsers action, never from a literal list, so a group a later row adds is checked too; today that is `roadmap` and `prompt`. Each group, each subcommand of a group, and `help` has a non-blank `description`, and its `epilog` has an `Examples:` line followed by at least one line that, stripped, starts with `clutch <its command path>`. Every stripped epilog line after `Examples:` that starts with `clutch ` parses with `_parser().parse_args(shlex.split(line)[1:])`; a `SystemExit(0)` from a help form counts as parsed, and exit 2 fails. Every other top-level command has a non-blank one-line summary. On the base commit the test fails, because no `roadmap` subcommand has a description; it does not pass.
2. `tests/unit/test_main_help.py::test_prompt_group_matches_kinds`: the `prompt` group's subcommand names equal `set(ask.KINDS)`, not a subset. `_parser().parse_args(["prompt", "box", "a", "b"])` gives `kind == "box"` and `stems == ["a", "b"]`, and `["prompt", "review"]` gives `stems == []` rather than an argparse exit.
3. `tests/unit/test_main_help.py::test_help_forms_agree` runs in an empty `tmp_path` with no `config.yaml`. For each of the paths `roadmap merged`, `prompt diagnose`, `roadmap` and `order`, `main(["help", *path])`, `main(["--help", *path])`, `main(["-h", *path])` and `main([*path, "--help"])` each exit 0 (returned, or raised as `SystemExit(0)`). All four print identical stdout that starts with `usage: clutch <path>`. Ruled out: `--help order` printing the top-level list as it does today, a `usage: python -m clutch` line, and a missing-config refusal.
4. `tests/unit/test_main_help.py::test_top_level_lists_groups`: `main(["help"])`, `main(["--help"])` and `main(["-h"])` print identical stdout. With all whitespace collapsed to single spaces, that stdout contains `<name> <summary>` exactly once for every top-level command, and `<group> <subcommand> <summary>` exactly once for every subcommand of every group, groups found by walking the parser as in criterion 1. Each summary is read from the parser, never written as a literal in the test. Ruled out: today's listing, which names no `roadmap` or `prompt` subcommand, and a listing that keeps argparse's flat list beside the grouped one.
5. `tests/unit/test_main_help.py::test_unknown_command_refuses`: `main(["help", "nosuch"])` and `main(["--help", "roadmap", "nosuch"])` each exit 2 (returned, or raised as `SystemExit(2)`) with empty stdout and a stderr line that starts with `clutch help: ` and contains ` -- `. Ruled out: exit 0 with the top-level help, and an uncaught traceback.
6. `tests/unit/test_main_help.py::test_command_helper_requires_every_field`: on a throwaway `argparse` subparsers action, calling `_command` with any one of `summary`, `does`, `reads`, `writes`, `lock`, `exits` or `examples` omitted raises `TypeError`, not builds a parser with a blank section.
7. `uv run clutch help roadmap author` prints its usage line, then what the subcommand does with `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with its row in `docs/how-clutch-works.md` section 2.1 (it takes the writer lock), then its options, then `Examples:`. Every other `roadmap` and `prompt` subcommand, and `help`, prints the same parts.
8. `grep -cE '^\| .help' clutch/docs/host-running.md docs/how-clutch-works.md` prints 1 for each file (one row each begins with the `help` verb), and `./dev.py test tests/unit/test_host_running.py` exits 0 with that test file unchanged.
9. `CLAUDE.md` section `## A. Engine conduct` and the `## Engine conduct` section of `AGENTS.md` after `<!-- clutch:core end -->` each hold the three rules of Goal / Why as new bullets with `Why:` lines. Nothing above `<!-- clutch:core end -->` changes in either file, so `./dev.py test tests/integration/test_hostfiles.py tests/integration/test_contention_rules.py tests/integration/test_core_supervisor_verdicts.py` exits 0. `plan-drain-author-in-parallel` (confirmed, unmerged) adds one rule to `CLAUDE.md` section B and one to `AGENTS.md`. In either merge order both tickets' rules end up present, because this ticket inserts its bullets only after the "Extension help has one source" bullet and changes no other line.
10. `./dev.py test tests/unit` and `./dev.py test tests/integration/test_ask.py tests/integration/test_ask_plan_drain.py tests/integration/test_main_verb_groups.py tests/integration/test_roadmap_gate.py tests/integration/test_restart_timers.py tests/integration/test_help.py` exit 0 with every existing test file unchanged. The existing prompt refusals, `roadmap` parsing and parser walks keep passing as they are. `plan-drain-author-in-parallel` edits only the phrase lists of `tests/integration/test_ask_plan_drain.py`; in either merge order `test_prompts_name_only_existing_verbs` passes, because every `clutch prompt <kind>` its new prompt text names is still a `prompt` subcommand.

## Verification
```
./dev.py test tests/unit/test_main_help.py
./dev.py test tests/unit
./dev.py test tests/integration/test_ask.py tests/integration/test_ask_plan_drain.py tests/integration/test_main_verb_groups.py tests/integration/test_roadmap_gate.py tests/integration/test_restart_timers.py tests/integration/test_help.py
./dev.py test tests/integration/test_hostfiles.py tests/integration/test_contention_rules.py tests/integration/test_core_supervisor_verdicts.py
```

## Definition of rejected
The branch is rejected, even if it passes, when any command's argv changes (a command moved or renamed, an option renamed, or a prompt kind's `stems` arity tightened so an existing refusal becomes an argparse usage error); a test pins help wording beyond the structure in criteria 1-6; `clutch/help.py`, `clutch/observe.py`, `clutch/ask.py`, `clutch/hostfiles.py`, `README.md` or anything under `vscode-clutchwork/` changes; a rule lands inside a managed block or the core template; a help field gets a default so a command can skip it; or `help` needs a config to run.

## Time budget
- expected: 15m
- stuck: 30m
