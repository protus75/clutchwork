---
state: rejected
source: box:retro_finding
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/unit/test_host_running.py::test_verb_table_matches_parser
- clutch/docs/host-running.md

## Goal / Why
Retro finding retro/61. `test_verb_table_matches_parser` reads only the first backticked cell of each verb-table row in `clutch/docs/host-running.md`, so a row with the wrong number of cells passes Check. `meta-schema-and-refresh-r2` attempt 4 added a two-cell `meta` row to the three-column table (Verb | Works while serve runs? | What it does). Review caught it, which cost a Diagnose call and a retry, and `evidence-verbs` attempt 1 needed a lesson on the same row shape. When this ticket is done, a malformed row fails the unit test at Check, not at Review. The test pins only the column count and the closed values of the serve column, never description text, so wording edits do not break it.

## Boundary contract
### Verb table row shape check
- disposition: extend
- owner: tests/unit/test_host_running.py
- consumers: Check (unit gate) and any ticket that edits the verb table in clutch/docs/host-running.md
- observable change: the unit suite fails when a verb row does not have exactly three cells or its 'Works while serve runs?' cell is not `Yes` or `No`; the doc and the engine are untouched
- compatibility: the current table in clutch/docs/host-running.md passes unchanged; the existing parser-match assertions stay as they are
- acceptance: a two-cell row and a row whose serve cell is outside the closed set each make the shape check report a problem; every current row passes
- tests: tests/unit/test_host_running.py
- post-merge source of truth: tests/unit/test_host_running.py for the row-shape rule, clutch/docs/host-running.md for the table content

## Scope in / Scope out
Scope in: in `tests/unit/test_host_running.py`, add a small module-level function that takes one table row line and returns the list of shape problems. It splits cells on unescaped `|` and checks that there are exactly 3 cells and that cell 2 is in the closed set `{Yes, No}`. Add a test that applies it to every verb row found in the doc (rows matched by the same `^\| `...` \|` pattern the existing test uses). Add a second test that applies the same function to two hand-built strings, a two-cell row and a row with serve cell `Maybe`, and asserts each yields a non-empty problem list while a valid three-cell string yields an empty list. The function has two callers, which is why it is a function. The simpler alternative, asserting inline in the existing test, was rejected because the failure cases could then not be shown to fail.
Scope out: no assertion on cell text or description wording; no edit to the verb-table document or any production file; no change to the meta block header of the test file, which Check refreshes.

## Scope fence
- tests/unit/test_host_running.py

## Acceptance criteria
1. The shape function returns a non-empty list for the string `| `meta` | Yes |` (two cells), checked by `./dev.py test tests/unit/test_host_running.py`; an empty list would fail the test.
2. The shape function returns a non-empty list for a three-cell row whose serve cell is `Maybe`, and an empty list for `| `view watch` | Yes | text |`, checked by `./dev.py test tests/unit/test_host_running.py`.
3. Every verb row in clutch/docs/host-running.md passes the shape function, checked by `./dev.py test tests/unit/test_host_running.py`.
4. `git diff --name-only` against the merge base lists only `tests/unit/test_host_running.py`, checked by `git diff --name-only HEAD~1 HEAD`.

## Verification
```
./dev.py test tests/unit/test_host_running.py
```

## Definition of rejected
The branch changes any file other than tests/unit/test_host_running.py, or asserts on description text or exact cell wording, or the new tests pass when a row has two cells.

## Time budget
- expected: 8m
- stuck: 16m
