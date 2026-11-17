---
state: confirmed
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Runs before
- closed-sets-remaining

## Context
- docs/roadmap.md#Status
- docs/roadmap.md#1. Release plan
- docs/roadmap.md#2. Analysis: duplication
- docs/roadmap.md#3. Analysis: gaps
- docs/roadmap.md#4. Analysis: drift
- docs/roadmap.md#0.4.0
- docs/roadmap.md#9. Keeping this document true
- clutch/roadmap.py::gates
- tests/integration/test_roadmap_table.py
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks

## Goal / Why
At the end of 0.3.0, `docs/roadmap.md` sections 2-4 describe the code as it was at commit `80b76d5d`, and section 9 says the audit is re-run before each minor release but names no actor. Once the driver ships unattended, nobody re-runs it. When this ticket is done:

- Sections 2-4 describe the code at this ticket's base commit. Items that merged work fixed are removed. Items that are still true are kept and marked "recurred in 0.3.0".
- The 0.4.0 `gate` block carries one command for each section 1 ship clause of 0.4.0 that merged code now records. A clause with no such code is named in the same block's lead-in prose as still unchecked.
- The last row of the 0.4.0 table is an audit row with its own stem, `release-audit-040`, so every release ends with one.
- Section 9 says merged rows stay struck in their release's table. It no longer says they move to a "Shipped" section, which no table has.

This follows decision 5's rule that the audit is re-run before each minor release, and row 105 of the master table.

## Scope in / Scope out
In, edits in `docs/roadmap.md`:
- Re-run the six read-only passes that produced sections 2-4, at the base commit, over the files the Status section lists. Remove fixed items from sections 2, 3 and 4. Mark each recurring item "recurred in 0.3.0". Update the Status section's commit hash, version and counts only where the audit measured them again.
- In the 0.4.0 `gate` block, add one command per section 1 ship clause that merged code now records. Use only existing `clutch` verbs, each starting `uv run clutch`. Insert them after the first command and before `./dev.py test`. Keep the first command `uv run clutch roadmap merged --release 0.4.0`, keep `./dev.py test` second-to-last and once, and keep the last `uv run clutch roadmap accept 0.4.0`.
- Append row 122, `release-audit-040`, kind `chore`, priority `P1`, as the last row of the 0.4.0 table. Row 121 is reserved for sibling ticket `closed-sets-remaining`, which appends `closed-sets-rest` to the 0.3.0 table; this ticket runs before it so the two numbers never collide. Its Content repeats row 105's instruction for the following release, so the audit repeats at each release. It carries no link until it is authored.
- In section 9, replace the clause "a shipped release's rows move to a \"Shipped\" section at the end" with the rule that rows stay struck in their release's table.
- Row 105 itself is linked and struck by the driver when this ticket merges. This ticket does not strike it.

In, edit in `tests/integration/test_roadmap_gate.py`, only `test_real_roadmap_gate_blocks`: the 0.4.0 expectation changes. The loop at lines 52-53 that asserts every non-first release's block equals (`roadmap merged --release R`, `./dev.py test`, `roadmap accept R`) is rewritten so each non-first release's block has `roadmap merged --release R` first, `./dev.py test` and `roadmap accept R` as the last two, and every command between them starting `uv run clutch`. The block for any release other than 0.4.0 must still equal the old three-command tuple. The first-release assertion and the lines 54-60 checks stay as they are.

Out:
- Fixing any drift the audit finds in other documents or in code. Each finding is filed with `clutch suggest`, not folded into this diff.
- Editing `CLUTCH_PLAN.md`, the plan documents under `docs/`, or any row other than the new one and row 105.
- Renumbering existing rows.

## Scope fence
- docs/roadmap.md
- tests/integration/test_roadmap_gate.py
- tests/integration/test_roadmap_release_audit.py

## Acceptance criteria
1. The last 0.4.0 row by line number, found with `clutch.roadmap.parse`, has number 122, stem `release-audit-040`, kind `chore`, priority `P1`, and is not struck; its line comes after every other parsed 0.4.0 row's line. Checked by `./dev.py test tests/integration/test_roadmap_release_audit.py`. The test rules out row 55 `visual-review-baseline`, the current last parsed 0.4.0 row, being last.
2. `clutch.roadmap.gates(text)["0.4.0"]` starts with `("uv", "run", "clutch", "roadmap", "merged", "--release", "0.4.0")` and ends with `("./dev.py", "test")` followed by `("uv", "run", "clutch", "roadmap", "accept", "0.4.0")`, with `("./dev.py", "test")` appearing once. Checked by `./dev.py test tests/integration/test_roadmap_release_audit.py`. The 0.3.0 gate stays unchanged: the test compares it to its pre-change tuple.
3. The section 9 text contains "stay struck" and does not contain `a "Shipped" section`. Checked by `./dev.py test tests/integration/test_roadmap_release_audit.py`. The test rules out the old sentence surviving.
4. With the added 0.4.0 gate commands in place, `./dev.py test tests/integration/test_roadmap_gate.py` passes; the test rules out a 0.4.0 block with a command in the middle that does not start `uv run clutch`, and a block whose `./dev.py test` is not second-to-last.
5. `docs/roadmap.md` still parses, with unique row numbers and stems, and the existing real-roadmap check passes. Checked by `./dev.py test tests/integration/test_roadmap_table.py`.
6. Every item still listed in sections 2-4 either has an unchanged description confirmed at the base commit or carries the exact text "recurred in 0.3.0". Checked by the reviewer reading `git diff` of `docs/roadmap.md` against each item's cited file. No test can decide this.

## Verification
```
./dev.py test tests/integration/test_roadmap_release_audit.py tests/integration/test_roadmap_gate.py tests/integration/test_roadmap_table.py tests/unit/test_roadmap_table.py
```

## Definition of rejected
The branch is thrown away if it edits any file outside the fence, strikes row 105, renumbers rows, edits another plan or `CLUTCH_PLAN.md`, adds a gate command that is not an existing `clutch` verb, changes `test_roadmap_gate.py` beyond the 0.4.0 expectation, or removes an audit item without a merged change that fixed it.

## Time budget
- expected: 45m
- stuck: 90m
- reason: the six audit passes are one read-only sweep that feeds one document, so splitting would repeat the sweep in each part.
