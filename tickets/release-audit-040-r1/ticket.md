---
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
- cli-group-coverage

## Context
- docs/roadmap.md#Status
- docs/roadmap.md#1. Release plan
- docs/roadmap.md#2. Analysis: duplication
- docs/roadmap.md#3. Analysis: gaps
- docs/roadmap.md#4. Analysis: drift
- docs/roadmap.md#0.5.0
- docs/roadmap.md#9. Keeping this document true
- clutch/roadmap.py::gates
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks

## Goal / Why
At the end of 0.4.0, `docs/roadmap.md` sections 2-4 describe the code as it was at the 0.3.0 audit commit, and the 0.5.0 `gate` block checks no section 1 ship clause. When this ticket is done:

- Sections 2-4 describe the code at this ticket's base commit. Items that merged work fixed are removed. Items still true are kept and marked "recurred in 0.4.0".
- The 0.5.0 `gate` block carries one command for each 0.5.0 section 1 ship clause that merged code now records. A clause with no such code is named, as still unchecked, in the prose line directly above that block.
- The last row of the 0.5.0 table is an audit row with its own stem, `release-audit-050`, so every release ends with one.

This is row 122 of the master table and follows decision 5: the audit is re-run before each minor release. The roadmap driver holds row 122 until every stem in the row's Depends column has merged; this ticket lists only `cli-group-coverage` under `## Depends on` because that is the one row 122 dependency with a ticket directory today.

## Scope in / Scope out
In, edits in `docs/roadmap.md`:
- Re-run the six read-only passes that produced sections 2-4, at the base commit, over the files the Status section lists. Remove fixed items from sections 2, 3 and 4. Mark each recurring item "recurred in 0.4.0". Update the Status section's commit hash, version and counts only where the audit measured them again.
- In the 0.5.0 `gate` block, add one command per 0.5.0 ship clause that merged code now records. Use only existing `clutch` verbs, each starting `uv run clutch`. Insert them after the first command and before `./dev.py test`. Keep the first command `uv run clutch roadmap merged --release 0.5.0`, keep `./dev.py test` second-to-last and once, and keep the last `uv run clutch roadmap accept 0.5.0`. Add no command when no merged verb records a clause; the audit is then a prose-only change there, with the unchecked clauses named in the line directly above the block.
- Append a row to the 0.5.0 table as its last row: the next row number unused anywhere in the file at the base commit, stem `release-audit-050`, owner `roadmap`, kind `chore`, priority `P1`, no depends, no runs-before. Its Content repeats row 122's instruction for the following release (0.6.0): re-run the six passes, remove fixed items, mark recurring ones "recurred in 0.5.0", add gate commands for ship clauses that merged code records, and add the same audit row with its own stem as the last row of the next release's table. It carries no link until authored.
- Row 122 itself is linked and struck by the driver when this ticket merges. This ticket does not strike it.

In, edit in `tests/integration/test_roadmap_gate.py`, only `test_real_roadmap_gate_blocks`, and only if a command is added to the 0.5.0 block: the `if release != "0.4.0"` length check then also exempts `0.5.0`. Nothing else in that test changes. If no gate command is added, leave the file alone.

Out:
- Fixing any drift the audit finds in other documents or code. File each finding with `clutch box suggest`, not in this diff.
- Editing `CLUTCH_PLAN.md`, the plan documents under `docs/`, section 9, or any row other than the new one and row 122.
- Renumbering rows.
- Adding a standing test of roadmap row text or gate-block text; the edit is verified in review.

## Scope fence
- docs/roadmap.md
- tests/integration/test_roadmap_gate.py

## Acceptance criteria
1. The last row of the 0.5.0 table in `docs/roadmap.md` has stem `release-audit-050`, kind `chore`, priority `P1`, no strike, and a row number no other row uses. Checked by reading `git diff main -- docs/roadmap.md`, and `./dev.py test tests/integration/test_roadmap_table.py` passes with unique numbers and stems; a duplicated number or stem fails it.
2. `clutch.roadmap.gates(text)["0.5.0"]` starts with `("uv", "run", "clutch", "roadmap", "merged", "--release", "0.5.0")`, ends with `("./dev.py", "test")` then `("uv", "run", "clutch", "roadmap", "accept", "0.5.0")`, and holds `("./dev.py", "test")` once. Checked by `./dev.py test tests/integration/test_roadmap_gate.py`; a block whose `./dev.py test` is not second-to-last, or whose middle command is not an existing `uv run clutch` verb, fails it.
3. Every item still listed in sections 2-4 either has a description unchanged and confirmed true at the base commit, or carries the exact text "recurred in 0.4.0"; no item is removed unless merged work fixed it. Checked by the reviewer reading `git diff main -- docs/roadmap.md` against each item's cited file. No test can decide this.
4. Each 0.5.0 ship clause is either checked by a command in the 0.5.0 gate block or named as unchecked in the prose line above it. Checked by reading `git diff main -- docs/roadmap.md`. No test can decide this.
5. `docs/roadmap.md` parses and the real-roadmap checks pass. Checked by `./dev.py test tests/integration/test_roadmap_table.py tests/integration/test_roadmap_gate.py`.

## Verification
```
./dev.py test tests/integration/test_roadmap_gate.py tests/integration/test_roadmap_table.py tests/unit/test_roadmap_table.py
```

## Definition of rejected
The branch is thrown away if it edits a file outside the fence, strikes row 122, renumbers rows, edits another plan or `CLUTCH_PLAN.md`, adds a gate command that is not an existing `clutch` verb, adds a standing test of roadmap text, changes `test_roadmap_gate.py` beyond the 0.5.0 exemption, or removes an audit item without a merged change that fixed it.

## Time budget
- expected: 30m
- stuck: 60m
