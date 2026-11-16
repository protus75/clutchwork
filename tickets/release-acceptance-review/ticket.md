---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- roadmap-accept

## Runs before
- evidence-envelope

## Context
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks
- clutch/roadmap.py::gates
- clutch/roadmap.py::run_gate
- clutch/roadmap.py::ship
- docs/how-clutch-works.md#7.5 Roadmap driver

## On-demand
- docs/roadmap.md

## Goal / Why
The owner asked on 2026-11-16 that a release ship only when its tickets, taken together, satisfy the plan of the release: "it is one thing for each ticket to pass its acceptance criteria, however the sum of the tickets need to have satisfied the plan of the feature/phase of roadmap". `roadmap-accept` builds the check as `clutch roadmap accept <release>`. That verb runs a read-only model review of the release's merged rows against the release's theme and ship gate in section 1 of `docs/roadmap.md` and its owning plans' Target design. It appends a P1 row for each partial or unmet promise and exits 0 only when there is none. Nothing runs it yet.

The driver's `clutch/roadmap.py::ship` runs the current release's fenced `gate` block (`run_gate`) and tags the release when every command exits 0. Today every block checks only merged rows and the suite. For 0.3.0, the last required row is `evidence-envelope`; once it merges and the suite passes, the driver tags 0.3.0 without anyone checking that the release delivered its theme.

This ticket makes `uv run clutch roadmap accept <release>` the last command of every release's gate block, after the cheap `roadmap merged` checks and the suite, so the review runs only when those pass. It also says so in the section 8 intro and in how-clutch-works section 7.5. With it, `ship` tags a release only after the acceptance review finds no partial or unmet promise. The rows the review appends hold the gate until they merge, and the driver authors them like any other row.

## Scope in / Scope out
In:
- `docs/roadmap.md`, section 8 only:
  - In each of the five fenced `gate` blocks (under `### 0.3.0`, `### 0.4.0 (conditional)`, `### 0.5.0`, `### 0.6.0`, `### 0.7.0`), add one line after `./dev.py test`, the block's current last line: `uv run clutch roadmap accept <release>`, with `<release>` the block's own release name (`0.3.0` to `0.7.0`). Every other line of each block stays as it is, in order.
  - In the intro paragraph that begins "Each release's ship gate (section 1) is also a fenced `gate` block":
    - After the sentence "`clutch roadmap merged` is the query the blocks use.", insert: "Every block ends with `uv run clutch roadmap accept <release>`, after the `roadmap merged` checks and the suite: a model reviews the release's merged rows, taken together, against its theme and ship gate in section 1 and its owning plans' Target design, and appends a P1 row for each partial or unmet promise to the release's table (or, for a gap that should wait, to the next release's table) in a `clutch(roadmap): accept <release>` commit, so the gate fails until those rows merge."
    - Change "A later release's block checks only the suite and that release's rows:" to "A later release's block checks only the suite, that release's rows, and the acceptance review:".
  - Nothing else in the file changes: no row, decision, heading, or other section.
- `docs/how-clutch-works.md` section 7.5 only. After the sentence "A passing gate releases, and publishes only with `release.publish: true`.", insert: "Every gate block ends with `roadmap accept <release>` (section 2.1), so a release ships only when the acceptance review finds no partial or unmet promise; the driver authors the rows it appends like any other row."
- `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks`:
  - The first release's expected tuple gains `("uv", "run", "clutch", "roadmap", "accept", first)` as its last entry.
  - Each later release's expected tuple becomes `(("uv", "run", "clutch", "roadmap", "merged", "--release", release), ("./dev.py", "test"), ("uv", "run", "clutch", "roadmap", "accept", release))`.
  - The closing loop asserts, for every block, that `commands[-1] == ("uv", "run", "clutch", "roadmap", "accept", <that block's release>)` and `commands[-2] == ("./dev.py", "test")`, replacing `commands[-1] == ("./dev.py", "test")`. It keeps the `("./dev.py", "test")` count of 1 and the `cli._parser().parse_args` check of every `uv run clutch` command.
  - `test_roadmap_gate_runs_real_commands` does not change.

Out:
- Any code change. `roadmap accept`, its spec, and its docs rows in how-clutch-works section 2.1 and `clutch/docs/host-running.md` are `roadmap-accept`'s.
- Section 1's Gate to ship column, rows, decisions, `docs/roadmap-driver-plan.md`, and the gate commands already in each block.

## Scope fence
- docs/roadmap.md
- docs/how-clutch-works.md
- tests/integration/test_roadmap_gate.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_roadmap_gate.py` exits 0 with `test_real_roadmap_gate_blocks` changed as Scope in says. Its exact tuples rule out four wrong results: a block with no `roadmap accept` line, the line placed before `./dev.py test` (the suite and the cheap checks must pass before a model call is spent), a later block whose `accept` names another release or a hard-coded version, and an edited or reordered existing command.
2. The `uv run python -c` check in `## Verification` exits 0. It requires:
   - `docs/roadmap.md` holds the inserted section 8 sentence exactly;
   - it holds `A later release's block checks only the suite, that release's rows, and the acceptance review:`;
   - it no longer holds `A later release's block checks only the suite and that release's rows:`;
   - `docs/how-clutch-works.md` holds the inserted section 7.5 sentence exactly.
3. `./dev.py test tests/integration/test_roadmap_table.py` exits 0 unchanged: `parse` and `choose` still accept the edited checked-in roadmap.
4. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_roadmap_gate.py
uv run python -c "import pathlib; b = chr(96); r = pathlib.Path('docs/roadmap.md').read_text(); h = pathlib.Path('docs/how-clutch-works.md').read_text(); s = 'Every block ends with ' + b + 'uv run clutch roadmap accept <release>' + b + ', after the ' + b + 'roadmap merged' + b + ' checks and the suite: a model reviews the release' + chr(39) + 's merged rows, taken together, against its theme and ship gate in section 1 and its owning plans' + chr(39) + ' Target design, and appends a P1 row for each partial or unmet promise to the release' + chr(39) + 's table (or, for a gap that should wait, to the next release' + chr(39) + 's table) in a ' + b + 'clutch(roadmap): accept <release>' + b + ' commit, so the gate fails until those rows merge.'; assert s in r; assert 'A later release' + chr(39) + 's block checks only the suite, that release' + chr(39) + 's rows, and the acceptance review:' in r; assert 'A later release' + chr(39) + 's block checks only the suite and that release' + chr(39) + 's rows:' not in r; t = 'Every gate block ends with ' + b + 'roadmap accept <release>' + b + ' (section 2.1), so a release ships only when the acceptance review finds no partial or unmet promise; the driver authors the rows it appends like any other row.'; assert t in h"
./dev.py test tests/integration/test_roadmap_table.py
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- any file outside the fence changes;
- any roadmap row, decision, heading, or section other than the five gate blocks and the section 8 intro paragraph changes;
- an existing gate command is removed, reordered, or edited;
- `roadmap accept` runs before `./dev.py test` in any block;
- any test other than `test_real_roadmap_gate_blocks` changes.

## Time budget
- expected: 25m
- stuck: 60m
