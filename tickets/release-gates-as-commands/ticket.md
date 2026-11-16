---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- roadmap-table-parser
- roadmap-author
- roadmap-merged-query

## Context
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/journal.py::SIGNAL_NAMES
- clutch/providers.py::child_env
- clutch/seams.py::ProcessExec
- clutch/seams.py::ExecutableNotFound
- clutch/config.py::Drain
- clutch/tickets.py::_fenced_commands
- clutch/runner.py::Refusal
- clutch/runner.py::Checkout
- tests/unit/test_release.py::test_main_release_locks_calls_and_prints
- tests/unit/test_retro_recurrence.py::MemoryJournal
- tests/integration/test_closed_sets.py::test_journal_closed_sets_and_constants
- tests/integration/test_cli.py::ENV
- tests/integration/test_cli.py::CONFIG
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1
- docs/roadmap-driver-plan.md#4.
- docs/roadmap.md#1. Release plan
- docs/roadmap.md#8. Master ticket table

## Goal / Why
`docs/roadmap-driver-plan.md` section 4 (roadmap row 91) turns each release's ship gate into commands, so the roadmap driver (`driver-loop`, row 93) can decide by itself when a release may ship. The owner decided on 2026-11-16 that no gate is a person's judgment (`docs/roadmap.md` section 6, the "No human in the loop" decision): every gate is one or more argv commands that exit 0 when the release may ship. Today the ship gates exist only as prose in the "Gate to ship" column of roadmap section 1. Nothing can run them, so the driver has nothing to check and no record says whether a gate passed.

This is the second part of the row's split. `roadmap-merged-query` adds `clutch roadmap merged`, the read-only query the blocks use; `roadmap-status` adds `clutch roadmap status`, which shows each gate's last result.

After this change:
1. Each release in `docs/roadmap.md` section 8 carries one fenced `gate` block: an opening line ```` ```gate ````, one argv command per line (split as `shlex.split(line, posix=True)`, no shell syntax, as `## Verification` commands are split in `clutch/tickets.py::_fenced_commands`), and a closing ```` ``` ````. A block belongs to the release named by `release_name` of the nearest `### ` heading above it.
2. `uv run clutch roadmap gate <release>` runs that release's commands in order from the checkout root, stops at the first that fails, prints one line per command run and a verdict line, journals one `roadmap_gate` signal with the result, and exits 0 when every command passed, 1 when one failed, and 2 on a refusal.
3. Release names follow the section 8 headings, so the blocks move with any rename of a release (`roadmap-plan-corrections` renames the phases; their names equal the versions `clutch release --minor` gives them at their start).

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py`:
  - `gates(text) -> dict[str, tuple[tuple[str, ...], ...]]`: maps each release name to its commands, in document order. A ```` ```gate ```` line (stripped) opens a block, and the next line that is exactly ```` ``` ```` (stripped) closes it. Blank lines inside are skipped. It raises `clutch/runner.py::Refusal`, each with a paved road that names the fix, for: a block with no `### ` heading above it; a second block for a release; a block never closed; a block with no command; and a line that `shlex.split` refuses or whose first element is empty.
  - `async def run_gate(checkout, release) -> tuple[bool, list[str]]`:
    1. Read `checkout.repo / ROADMAP`. A missing file raises `Refusal` naming `docs/roadmap.md`. Call `gates(text)`. A release with no block raises `Refusal` naming it, with the road "add a ```gate block under the release's heading in docs/roadmap.md section 8". Every refusal comes before any command runs and journals nothing.
    2. Run each command with `checkout.exec_.run(list(argv), cwd=checkout.repo, env=child_env(checkout.env, checkout.config), timeout=checkout.config.drain.max_ticket_minutes * 60.0)`. The ticket stuck ceiling bounds each command, so no new constant or config field is added. A command fails when it exits non-zero, raises `TimeoutError`, or raises `clutch/seams.py::ExecutableNotFound`. The first failure stops the run.
    3. The lines are `gate <release>: ok: <shlex.join(argv)>` for each passing command, and for the failing one `gate <release>: failed (<why>): <shlex.join(argv)>`. `<why>` is `exit <rc>`, `timeout`, or `not found`. For `exit <rc>` the line also ends ` -- <last non-blank line of stderr, else of stdout>` when either has one. The last line is `gate <release>: passed` or `gate <release>: failed`.
    4. Journal one event, `checkout.journal.append(EventType.SIGNAL, {"signal": "roadmap_gate", "release": release, "passed": <bool>, "failed": <shlex.join of the failing argv, or None>})`, written as one dict literal passed straight to `append` so `tests/integration/test_vocabularies.py::test_every_engine_signal_name_is_listed` finds the name. Return `(passed, lines)`.
- `clutch/journal.py`: add `"roadmap_gate"` to `SIGNAL_NAMES`.
- `clutch/__main__.py`:
  - `_parser`: the `roadmap` subcommand's sub-subcommands gain `gate` with one positional `release`.
  - `main`: a `roadmap gate` invocation calls `clutch.roadmap.run_gate` (looked up on the module at call time) without taking the writer lock, prints the lines, and returns 0 when it passed and 1 when it failed. `Refusal` already maps to exit 2.
- `docs/roadmap.md` (as `roadmap-plan-corrections` and `roadmap-no-human-gates` leave it), section 8 only:
  - The section's intro gains one paragraph after its first: each release's ship gate (section 1) is also a fenced `gate` block under that release's first heading below. It has one argv command per line, no shell syntax, and runs from the checkout root. The gate passes when every command exits 0. `clutch roadmap gate <release>` runs it and journals the result. `clutch roadmap merged` is the query the blocks use.
  - One block per release, placed after the table under the release's first `### ` heading. In what follows `<R>` is that release's name (`release_name` of the heading).
    - The first release in document order (the current phase, 0.3.0 at HEAD after the renames) gets exactly these four lines, in this order. Its section 1 ship gate is "every P0 and P1 row merged; evidence capture live; `docs-truth-sweep` merged ...; the driver has authored and run at least three roadmap rows on this repo with no operator verdict":
      1. `./dev.py test`
      2. `uv run clutch roadmap merged --release <R> --priority P0 P1`
      3. `uv run clutch roadmap merged docs-truth-sweep evidence-envelope`. Evidence capture is live when `evidence-envelope` (row 29, the writer for every call's record) has merged.
      4. `uv run clutch roadmap merged --since v<R> --at-least 3 --source box:roadmap_row --unattended`
    - Every later release gets exactly two lines: `./dev.py test` and `uv run clutch roadmap merged --release <R>`.
  - Nothing else in the file changes: not section 1's prose gates, the rows, or any other section.
- `docs/how-clutch-works.md` section 2.1: add a row `roadmap gate <release>` (Lock: no) describing points 1 and 2 of the Goal and the `roadmap_gate` signal. Nothing else in the file changes.
- `clutch/docs/host-running.md`: the `roadmap` verb-table row gains one sentence: `roadmap gate <release>` runs the release's gate block from `docs/roadmap.md`, journals the result, exits 0 when every command passes and 1 otherwise, and works while serve runs.
- `tests/integration/test_closed_sets.py::test_journal_closed_sets_and_constants`: its expected `SIGNAL_NAMES` set gains `roadmap_gate`. Nothing else in that file changes.
- New tests in two new files: `tests/unit/test_roadmap_gate.py` (fakes only: `MemoryJournal` from `tests/unit/test_retro_recurrence.py`, a recording fake exec, roadmap text under `tmp_path`; it runs every new line of `clutch/roadmap.py` and the new `main` branch, which have unit floors of 90 and 13) and `tests/integration/test_roadmap_gate.py` (real processes and a real `Journal`, plus the check of the real `docs/roadmap.md`).

Scope out:
- `clutch roadmap status` and its display of the last gate result (`roadmap-status`); `clutch roadmap merged` (`roadmap-merged-query`), which this ticket only names in the blocks.
- Calling `run_gate` from serve or drain, and releasing when a gate passes (`driver-loop`).
- Ship-gate clauses whose facts no merged code records yet. The later blocks check them through the release's own rows, because the rows that build those facilities are the release's rows. Each later block's `--release <R>` line fails until every one of those rows has merged. The clauses are:
  - for 0.4.0, "no feature ticket runs during the window" (the journal plan enforces that freeze through the roadmap's schedule);
  - for 0.5.0, parallel serve's next 10 merges without a conflict-rerun cap hit, the `generate` graphics merge through the select commit, and the recorded `visual_baseline` GO;
  - for 0.6.0, the `training export` and `training eval` results on this repo, the two-member panel's next 10 reviews, the filled meta blocks, and `context suggest` on a real ticket;
  - for 0.7.0, the doc-set review of the 2026-11-13 plans.

  Their verbs, signals, and caps do not exist at HEAD, so a direct command now would guess an interface no plan fixes. The follow-up that replaces those lines with direct checks as each facility lands is filed to the Suggestion Box. The simpler alternative, a `gate: operator` placeholder, is what the owner forbade.
- Section 1's table, the master-table rows, `docs/roadmap-driver-plan.md`, and every other plan document.
- `clutch/help.py`, `clutch/observe.py`, `vscode-clutchwork/`, `README.md`, `CLAUDE.md`, and `AGENTS.md`.

## Scope fence
- clutch/roadmap.py
- clutch/journal.py
- clutch/__main__.py
- docs/roadmap.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/integration/test_closed_sets.py
- tests/unit/test_roadmap_gate.py
- tests/integration/test_roadmap_gate.py

## Acceptance criteria
1. `tests/unit/test_roadmap_gate.py::test_gates_parse` parses a text with a `### 1.0.0` heading, a table, then a block holding `./dev.py test`, a blank line, and `uv run clutch roadmap merged --release 1.0.0 --priority P0 P1`; a `### 1.0.0, last group` heading with no block; and a `### 2.0.0 (conditional)` heading whose block holds `tool "a b" c`. `gates` returns exactly `{"1.0.0": (("./dev.py", "test"), ("uv", "run", "clutch", "roadmap", "merged", "--release", "1.0.0", "--priority", "P0", "P1")), "2.0.0": (("tool", "a b", "c"),)}`. Ruled out: a release keyed by the full heading text, a blank line read as a command, and a quoted argument split apart.
2. `tests/unit/test_roadmap_gate.py::test_gates_refuse` asserts `gates` raises `Refusal` for each of: a block before any `### ` heading; a second block under `### 1.0.0, last group` after one under `### 1.0.0`; a block with no closing fence; a block with only blank lines; a line `tool "unclosed`; and a line `''`. Ruled out: a later block silently replacing an earlier one, and a malformed block read as an empty gate that passes.
3. `tests/unit/test_roadmap_gate.py::test_run_gate_passes` writes a roadmap whose `1.0.0` block holds `first one` and `second`, with a fake exec answering `(0, "", "")` for both. `run_gate(checkout, "1.0.0")` returns `(True, ["gate 1.0.0: ok: first one", "gate 1.0.0: ok: second", "gate 1.0.0: passed"])`. Both calls ran with `cwd` equal to the repo, `env` equal to `{"SAFE": "yes"}` (the test replaces `child_env` in `clutch.roadmap` with a fake returning it), and `timeout == 420.0` for a config fake whose `drain.max_ticket_minutes` is 7. The journal holds exactly one event, a `signal` whose body is `{"signal": "roadmap_gate", "release": "1.0.0", "passed": True, "failed": None}`. Ruled out: a run in another directory, an unbounded command, the provider-key env passed through, and no record.
4. `tests/unit/test_roadmap_gate.py::test_run_gate_stops_at_first_failure`. The block holds `first`, `second`, and `third`, and `second` returns `(3, "out line\n", "warn\n\nlast err\n\n")`. `run_gate` returns `False`, `third` is never run, and the lines are `gate 1.0.0: ok: first`, `gate 1.0.0: failed (exit 3): second -- last err`, and `gate 1.0.0: failed`. The one journaled body is `{"signal": "roadmap_gate", "release": "1.0.0", "passed": False, "failed": "second"}`. Two more cases make `second` raise `TimeoutError` and then `ExecutableNotFound("second")`. Each gives `failed (timeout): second` or `failed (not found): second`, returns `False`, never runs `third`, and journals `passed: False`. Ruled out: running past a failure, a timeout or missing executable escaping as a crash, and a failed gate journaled as passed.
5. `tests/unit/test_roadmap_gate.py::test_run_gate_refusals`: `run_gate(checkout, "9.9.9")` on a roadmap with only a `1.0.0` block, and `run_gate` with no `docs/roadmap.md`, each raise `Refusal`, naming `9.9.9` and `docs/roadmap.md` respectively. In both cases the fake exec records no call and the journal is empty. Ruled out: a release with no gate treated as passing.
6. `tests/unit/test_roadmap_gate.py::test_main_roadmap_gate` fakes `load_config` and `child_env` as `tests/unit/test_release.py::test_main_release_locks_calls_and_prints` does, replaces `cli.Lockfile` with a class whose constructor fails the test, and replaces `clutch.roadmap.run_gate` with a fake. A fake returning `(True, ["a", "b"])` makes `main(["roadmap", "gate", "1.0.0"], ...)` print `a` and `b` and return 0. One returning `(False, ["c"])` makes it print `c` and return 1. One raising `Refusal("no gate", "add one")` makes it return 2 and print `clutch roadmap: no gate -- add one` to stderr. Ruled out: taking the writer lock, and an exit code that ignores the gate result.
7. `tests/integration/test_roadmap_gate.py::test_roadmap_gate_runs_real_commands` builds a checkout under `tmp_path` with `config.yaml` (`tests/integration/test_cli.py::CONFIG`) and a `docs/roadmap.md` whose `### 1.0.0` block runs `<sys.executable> -c "print('hi')"` and then `<sys.executable> -c "import sys; print('boom', file=sys.stderr); sys.exit(4)"` (the interpreter's absolute path, because `ENV`'s `PATH` is `/usr/bin:/bin`). `main(["roadmap", "gate", "1.0.0"], cwd=..., env=...)` returns 1 and prints `gate 1.0.0: failed (exit 4): ... -- boom`. The state dir's `Journal` then holds one `roadmap_gate` signal with `passed: false`. A second roadmap whose block has only the first command returns 0 and journals `passed: true`. Ruled out: a gate result that never reaches the journal through the real seams.
8. `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks` reads the repo's `docs/roadmap.md`:
   - The set of `gates(text)` keys equals `{release_name(row.release) for row in parse(text)}`, so there is one block per release and no block for anything else.
   - With `first` the first release in document order (the release of `parse(text)[0]`), its block is exactly the four commands of `## Scope in / Scope out`, with `<R>` replaced by `first`.
   - Every other release `r` has exactly `(("./dev.py", "test"), ("uv", "run", "clutch", "roadmap", "merged", "--release", r))`.
   - Every command that starts `uv run clutch` parses with `clutch.__main__._parser().parse_args(command[3:])` without `SystemExit`.

   Ruled out: a release with no gate, a `gate: operator` line or other prose in a block, a flag `roadmap merged` does not accept, and a block keyed to a hard-coded version.
9. `./dev.py test tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py tests/unit/test_host_running.py` exits 0. `journal.SIGNAL_NAMES` contains `roadmap_gate`, the only expected-set change in `test_closed_sets.py`, and the signal scan finds `roadmap_gate` emitted in `clutch/roadmap.py`.
10. The docs command in `## Verification` exits 0: `docs/how-clutch-works.md` section 2.1 has a row starting `` | `roadmap gate ``, the `roadmap` row of `clutch/docs/host-running.md` names `roadmap gate`, and `docs/roadmap.md` section 8 names `clutch roadmap gate`.
11. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes, with `clutch/roadmap.py` at or above `test-gate.toml`'s `default = 90`, and `clutch/__main__.py` and `clutch/journal.py` at or above their floors.
12. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_gate.py tests/unit/test_host_running.py
./dev.py test tests/integration/test_roadmap_gate.py tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py
uv run python -c "import pathlib; q = chr(96); t = pathlib.Path('docs/how-clutch-works.md').read_text(); verbs = t.split('### 2.1 Verbs')[1].split('### 2.2')[0]; assert '| ' + q + 'roadmap gate' in verbs; h = pathlib.Path('clutch/docs/host-running.md').read_text(); row = next(line for line in h.splitlines() if line.startswith('| ' + q + 'roadmap' + q + ' |')); assert 'roadmap gate' in row; r = pathlib.Path('docs/roadmap.md').read_text(); s8 = r.split('## 8. ', 1)[1].split('## 9. ', 1)[0]; assert 'clutch roadmap gate' in s8"
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- a gate block holds `operator`, prose, or a shell construct, or any release lacks a block;
- `run_gate` runs a command through a shell, outside the exec seam, without a timeout, or with provider keys in its env;
- it keeps running after a failed command, or journals a failed gate as passed;
- `roadmap gate` takes the writer lock;
- it adds a config field, a timeout constant, a `clutch/help.py` entry, or an extension menu item;
- it edits section 1, a master-table row, or another plan document;
- a block names a release by anything but its own heading;
- it calls `run_gate` from serve or drain.

## Time budget
- expected: 80m
- stuck: 170m
