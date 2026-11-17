---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
none

## Context
- docs/roadmap.md
- tests/integration/test_roadmap_start_gates.py

## Goal / Why
Roadmap decision 21 moves the journal window behind the training release, and the later releases take the versions they start at. After this ticket the roadmap and its owning plans use these names: parallel runs and the graphics kind are 0.4.0, training, panels and the index are 0.5.0, the journal window is 0.6.0, and the document agent stays 0.7.0. The journal window's table comes after the training release's table. Its "Gate to start" cell holds decision 21's absolute cost. This must merge before 0.3.0 ships. Otherwise the driver starts the journal window as 0.4.0.

## Scope in / Scope out
In `docs/roadmap.md`, rename the releases in these places:
- the section 1 table and its prose;
- the section 8 headings and their `gate` and `start` blocks, including every `--release` and `roadmap accept` argument;
- the phase names in sections 5 and 6;
- the release names in row Content.

Move the journal window's section 8 table after the training release's table. Set the journal window's "Gate to start" cell to decision 21's absolute cost, as the decision text states it.

In each owning plan, rename only the release names: `docs/journal-sql-refactor-plan.md`, `docs/parallel-tickets-plan.md`, `docs/gemini-graphics-refactor-plan.md`, `docs/evidence-trail-plan.md`, `docs/training-data-plan.md`, `docs/stage-panels-plan.md`, `docs/annotations-index-plan.md` and `docs/document-agent-plan.md`.

In `tests/integration/test_roadmap_start_gates.py`, only the pinned release key at the line asserting `roadmap.gates(text, "start")` may change, to the release that now holds that start block. The set asserted on the `gate` blocks may change only if the renamed headings change it.

Out of scope: code under `clutch/`, other tests, and any wording change beyond the release names, the table move and the gate cell. A mention of 0.3.0 stays as it is.

## Scope fence
- docs/roadmap.md
- docs/journal-sql-refactor-plan.md
- docs/parallel-tickets-plan.md
- docs/gemini-graphics-refactor-plan.md
- docs/evidence-trail-plan.md
- docs/training-data-plan.md
- docs/stage-panels-plan.md
- docs/annotations-index-plan.md
- docs/document-agent-plan.md
- tests/integration/test_roadmap_start_gates.py

## Acceptance criteria
1. In `docs/roadmap.md`, the journal window's heading and its `gate` block `--release` and `roadmap accept` arguments read `0.6.0`, and the heading for that release comes after the training release's heading. Check: `./dev.py test tests/integration/test_roadmap_table.py tests/integration/test_roadmap_start_gates.py`. A heading still named `0.4.0` or `0.5.0` for the journal window fails it.
2. `roadmap.parse` of `docs/roadmap.md` gives rows whose `release` is `0.4.0` for the parallel runs and graphics rows, `0.5.0` for the training, panels and index rows, `0.6.0` for the journal window rows, and `0.7.0` for the document agent rows. Check: `./dev.py test tests/unit/test_roadmap_table.py tests/integration/test_roadmap_table.py`. Any row still carrying its old release name fails it.
3. A `grep -n` of each owning plan for the old pairing finds none, for example the journal plan's release name `0.4.0` or `0.5.0`. Check: `grep -nE "journal.*0\.[45]\.0" docs/journal-sql-refactor-plan.md` prints nothing and exits 1.
4. The journal window's "Gate to start" cell in `docs/roadmap.md` states decision 21's absolute cost. Check: `grep -n "Gate to start" docs/roadmap.md` shows that cell, and it no longer names a relative or released-version condition.
5. The roadmap-reading tests all pass. Check: `./dev.py test tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_accept.py tests/unit/test_roadmap_author.py tests/integration/test_roadmap_merged.py tests/integration/test_roadmap_author.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_table.py tests/integration/test_roadmap_table.py tests/integration/test_roadmap_start_gates.py tests/unit/test_roadmap_start_gates.py tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_accept.py tests/unit/test_roadmap_author.py tests/integration/test_roadmap_merged.py tests/integration/test_roadmap_author.py
```

## Definition of rejected
A release name is changed in only some of the roadmap's sections or plans, so two names remain for one release. Or the branch edits `CLUTCH_PLAN.md`, code under `clutch/`, or any prose beyond the release names, the table move and the gate cell.

## Time budget
- expected: 30m
- stuck: 60m
