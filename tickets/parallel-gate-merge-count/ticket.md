---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- serve-dispatch-returns-on-slot

## Context
- clutch/roadmap.py::merged
- clutch/roadmap.py::gates
- clutch/status.py::latest_transitions
- clutch/runner.py::mark_running
- clutch/daemon.py::TicketWriter.consume_conflict_rerun
- clutch/caps.py::conflict_rerun_spent
- clutch/__main__.py::_parser
- tests/unit/test_roadmap_merged.py::FakeGit
- tests/unit/test_roadmap_merged.py::test_main_roadmap_merged
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks
- docs/parallel-tickets-plan.md#5. Merge queue: three conflict steps

## On-demand
- docs/roadmap.md

## Goal / Why
The 0.4.0 ship clause in `docs/roadmap.md` section 1 is "parallel serve has merged the next 10 tickets with no conflict-rerun cap hit". No merged verb records it, so the 0.4.0 `gate` block cannot check it and the section 8 note above that block lists it as unchecked. `clutch roadmap merged --since TAG --at-least N` already counts the tickets merged since a tag, with `--source` and `--unattended` filters, but it cannot tell a merge that ran beside another run from a serial one, and it cannot see a ticket that spent its conflict-rerun limit (`clutch/daemon.py::TicketWriter.consume_conflict_rerun` journals a terminal transition with `reason: merge_conflict_rerun_spent` when `clutch/caps.py::conflict_rerun_spent` holds).

The journal already holds the fact needed. `clutch/runner.py::mark_running` writes a `running` state transition when a run starts, and every run ends with one other transition for the same stem. A run that started while another stem's run had no terminal transition yet ran in parallel. The journal does not record the `scheduler.parallel.enabled` setting, so overlap is the checkable form of "dispatched while parallel was enabled": a run that overlapped another cannot have been dispatched with parallel off.

After this ticket, `uv run clutch roadmap merged --since TAG --at-least N --parallel` counts only the stems merged since TAG whose run overlapped another stem's run, and fails with one extra line per stem that ran in parallel and hit `merge_conflict_rerun_spent`. The 0.4.0 `gate` block gains `uv run clutch roadmap merged --since v0.4.0 --at-least 10 --parallel`, so the block fails until ten parallel merges exist and none of the parallel stems hit the cap. Today no serve run overlaps another (`Scheduler.dispatch_next` still awaits each run), so the count is 0 and the gate holds until the serve dispatch work makes runs overlap; that is the clause's intent. A new verb was rejected as the simpler path: `roadmap merged` already owns the tag lookup, the first-parent trailer log and the count filters, and a second verb would copy them. The row says "verb"; this adds a flag to the existing verb of the group `roadmap`, which the gate blocks already use.

## Boundary contract
### Roadmap merged query
- disposition: extend
- owner: clutch/roadmap.py::merged
- consumers: `clutch roadmap merged` in `clutch/__main__.py`, the `gate` blocks of `docs/roadmap.md` through `clutch/roadmap.py::run_gate`, and the driver's gate check
- observable change: `merged` takes a keyword `parallel` (default false). With it, the counted stems are those merged since the tag whose run overlapped another run, and a stem that overlapped and has a transition with `reason: merge_conflict_rerun_spent` adds the line `roadmap merged: <stem> hit merge_conflict_rerun_spent`. `parallel` without `at_least` raises `Refusal` with a road naming `--since` and `--at-least`. The CLI gains `--parallel` (`store_true`)
- compatibility: with `parallel` false every result, line and refusal is unchanged; the journal, tag lookup and git log call are the same
- acceptance: the unit tests in `tests/unit/test_roadmap_merged_parallel.py` and the updated `tests/unit/test_roadmap_merged.py::test_main_roadmap_merged`
- tests: `tests/unit/test_roadmap_merged_parallel.py` with fake git and journal; the existing integration test of the verb stays unchanged
- post-merge source of truth: `clutch/roadmap.py::merged`, which reads `state_transition` events only and writes nothing

### Gate block for 0.4.0
- disposition: extend
- owner: docs/roadmap.md
- consumers: `clutch/roadmap.py::gates`, `clutch/roadmap.py::run_gate`, `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks`
- observable change: the 0.4.0 `gate` block gains one command, `uv run clutch roadmap merged --since v0.4.0 --at-least 10 --parallel`, after its first command and before `./dev.py test`
- compatibility: the first, second-to-last and last commands of the block, and every other release's block, are unchanged
- acceptance: `uv run python` structure check in `## Verification` and `tests/integration/test_roadmap_gate.py`, which parses every `uv run clutch` gate command with the real parser
- tests: `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks`, unchanged
- post-merge source of truth: the fenced `gate` block under `### 0.4.0` in `docs/roadmap.md`

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py`: add a pure function `parallel_stems(events) -> set[str]`. It walks the events in order, keeping the set of stems whose latest `state_transition` (with a `to` in its body) is `running`. A transition to `running` for a stem, while the set holds any other stem, adds both that stem and every stem then in the set to the result; then it adds the stem to the set. A transition to any other state removes the stem. In `merged`, add the keyword `parallel=False`. The existing refusal for `source` and `unattended` without `at_least` also covers `parallel`. When `parallel` is true, the counted stems are limited to `parallel_stems(events)`, and after the count line (when any) it appends one line per stem in `parallel_stems(events)` that has a `state_transition` event with `body["reason"] == "merge_conflict_rerun_spent"`, sorted by stem. The reason string is the literal `daemon.py` writes; it is not restated as a new constant (`clutch/daemon.py` stays unedited).
- `clutch/__main__.py`: `merged.add_argument("--parallel", action="store_true")`; the `roadmap merged` handler passes `parallel=args.parallel`; the `merged` `_command` gains the example `clutch roadmap merged --since v0.4.0 --at-least 10 --parallel` and its `does` text names the parallel filter and the cap check (it stays a one-line fact, with `reads`, `writes`, `lock` and `exits` unchanged because the verb still reads the same sources and writes nothing).
- `clutch/docs/host-running.md`: in the `roadmap` row, extend the `roadmap merged` sentence to say that `--parallel` counts only merges whose run overlapped another run and fails when any such ticket spent its conflict-rerun limit.
- `docs/how-clutch-works.md` section 2.1: in the `roadmap merged` row, add `[--parallel]` to the usage after `[--unattended]` and one sentence saying what `--parallel` does, as above. Nothing else in the file changes.
- `docs/roadmap.md`: add the command above to the 0.4.0 `gate` block, after the first command and before `./dev.py test`. Rewrite only the sentence under the 0.4.0 table that lists the unchecked ship clauses (it begins "The ship clauses for ten parallel merges"): drop the parallel-merges clause from the unchecked list and say the 0.4.0 gate block checks it with `roadmap merged --parallel`. Leave the rest of that sentence's clauses, every table row, and every other section as they are.
- `tests/unit/test_roadmap_merged.py`: the one forced edit is in `test_main_roadmap_merged`, whose exact `kwargs` dictionary gains `"parallel": False`. Nothing else in that file changes.
- New `tests/unit/test_roadmap_merged_parallel.py`, with its own small fake git (the tag lookup and the log), `tmp_path`-free, and the `tests.fakes.FakeJournal` the existing tests use. It runs every new line of `clutch/roadmap.py` (a floor-90 file under `[coverage.files]`) and the new `__main__` line.

Scope out:
- A new verb or a new command group: the filter joins the existing `roadmap merged`, so no group, `help` or verb-table row is added (one rejected alternative: a `roadmap parallel` verb, which would copy the tag, trailer and count code).
- Recording `scheduler.parallel.enabled` in the journal, or adding a field to `running` transitions: overlap is derivable from events that exist, and an engine write is a larger change than the row asks for. A ticket tag-time bound on the spent-cap check was rejected too: the clause is for 0.4.0, the only phase in which runs overlap, and a bound needs a second git call.
- The 10-ticket window "next 10": the verb checks at least N since the tag, as the existing count does.
- `clutch/daemon.py`, `clutch/scheduler.py`, `clutch/serve.py` and the dispatch work of `serve-parallel-fill-slots` and row 166; this ticket only reads the journal they produce.
- `clutch/help.py`, `clutch/observe.py` and `vscode-clutchwork/`: `roadmap merged` is not an extension surface.
- `tests/integration/test_roadmap_gate.py` and `tests/integration/test_roadmap_merged.py`: neither asserts against the changed flags or block length (the gate test allows extra 0.4.0 commands).
- Standing tests that pin roadmap text (the guide forbids them); the block edit is checked once in `## Verification`.

## Scope fence
- clutch/roadmap.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- docs/roadmap.md
- tests/unit/test_roadmap_merged.py
- tests/unit/test_roadmap_merged_parallel.py

## Acceptance criteria
1. `tests/unit/test_roadmap_merged_parallel.py::test_overlapping_runs_count` journals `running` for `a-row`, then `running` for `b-row`, `merged` for both, then `running` and `merged` for `c-row` alone, with git's log naming all three. `run(c, since="v1", at_least=2, parallel=True)` returns `(True, ["roadmap merged: ok"])` and `at_least=3` returns `(False, ["roadmap merged: 2 of 3 tickets merged since v1 match"])`. Ruled out: counting `c-row` (3 of 3 would pass), and counting only the later-started `b-row` (1 would fail `at_least=2`).
2. `tests/unit/test_roadmap_merged_parallel.py::test_serial_runs_do_not_count` journals `a-row` `running` then `merged`, then `b-row` `running` then `merged`, and asserts `run(c, since="v1", at_least=1, parallel=True)` is `(False, ["roadmap merged: 0 of 1 tickets merged since v1 match"])` while the same call without `parallel` is `(True, ["roadmap merged: ok"])`. Ruled out: a count of every merged stem when the flag is set.
3. `tests/unit/test_roadmap_merged_parallel.py::test_spent_cap_on_a_parallel_stem_fails` journals `a-row` and `b-row` overlapping, `a-row` ending in `gate_failed` with `reason: merge_conflict_rerun_spent`, `b-row` `merged`, git's log naming `b-row`, and asserts `run(c, since="v1", at_least=1, parallel=True)` is `(False, ["roadmap merged: a-row hit merge_conflict_rerun_spent"])`. A `d-row` that ran alone and ended with the same reason adds no line. Ruled out: an ok result, and a line for `d-row` (a journal-wide scan of the reason).
4. `tests/unit/test_roadmap_merged_parallel.py::test_parallel_needs_a_count` asserts that `run(c, ["a-row"], parallel=True)` raises `Refusal` matching `count filter needs --at-least` before the journal is read (the fake journal's `read` fails the test), and that `run(c, since="v1", at_least=1, parallel=True)` does not. Ruled out: `parallel` left out of the count-filter refusal, which lets a stem query reach the journal read.
5. `tests/unit/test_roadmap_merged_parallel.py::test_main_passes_parallel` runs `cli.main(["roadmap", "merged", "--since", "v1", "--at-least", "10", "--parallel"], ...)` against a monkeypatched `roadmap.merged` and asserts the keyword `parallel` is `True`, and `False` without the flag.
6. `./dev.py test tests/unit/test_roadmap_merged.py tests/unit/test_main_help.py tests/integration/test_roadmap_merged.py tests/integration/test_roadmap_gate.py` exits 0, with `test_main_roadmap_merged`'s expected keywords gaining `"parallel": False` as Scope in says; `tests/unit/test_main_help.py` proves the changed `merged` help still has its fields and a parsing example.
7. The structure check in `## Verification` exits 0: the 0.4.0 block, read with `clutch.roadmap.gates`, holds `("uv", "run", "clutch", "roadmap", "merged", "--since", "v0.4.0", "--at-least", "10", "--parallel")` as its second command, starts with the `--release 0.4.0` command and still ends with `./dev.py test` and `roadmap accept 0.4.0`, and both guide documents contain `--parallel`. Ruled out: the command missing, in the wrong block or after `./dev.py test`.
8. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_merged_parallel.py
./dev.py test tests/unit/test_roadmap_merged.py tests/unit/test_main_help.py tests/integration/test_roadmap_merged.py tests/integration/test_roadmap_gate.py
uv run python -c "import pathlib; from clutch import roadmap; b = roadmap.gates(pathlib.Path('docs/roadmap.md').read_text())['0.4.0']; assert b[1] == ('uv', 'run', 'clutch', 'roadmap', 'merged', '--since', 'v0.4.0', '--at-least', '10', '--parallel'); assert b[0][-2:] == ('--release', '0.4.0'); assert b[-2:] == (('./dev.py', 'test'), ('uv', 'run', 'clutch', 'roadmap', 'accept', '0.4.0')); assert all('--parallel' in pathlib.Path(p).read_text() for p in ('clutch/docs/host-running.md', 'docs/how-clutch-works.md'))"
./dev.py test
```

## Definition of rejected
The branch is rejected if `roadmap merged` without `--parallel` changes any result, if the filter is a new verb or command group, if it reads `scheduler.parallel` from config or adds a journal field, event or signal, if it edits `clutch/daemon.py`, `clutch/scheduler.py` or `clutch/runner.py`, if the cap check scans stems that never overlapped another run, if a standing test pins roadmap text, or if the 0.4.0 block's other commands change.

## Time budget
- expected: 30m
- stuck: 60m
