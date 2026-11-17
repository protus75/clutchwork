---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
none

## Context
- tests/integration/test_closed_sets_single_owner.py
- tickets/drop-closed-sets-follow-up-test/ticket.md

## Goal / Why
`tests/integration/test_closed_sets_single_owner.py::test_follow_up_row` reads the live `docs/roadmap.md` and asserts the current text of three rows: row 112 (`closed-sets-remaining`: release 0.3.0, owner, kind, priority P3, depends `closed-sets-single-owner`, no runs-before), row 19's stem, and row 49's stem and depends. The roadmap driver rewrites rows as part of normal work (link, strike, re-file under a new stem), and the release acceptance review adds and replaces rows, so this test breaks main whenever one of those rows changes. Two earlier tests of the same kind did exactly that on 2026-11-17 and were deleted: `drop-live-roadmap-content-test` and `drop-closed-sets-follow-up-test`. The owner ruled tests of live roadmap content gold plating; box-000676 carries the cause.

After this change the test is gone. The file's other two tests, `test_single_definitions` and `test_closed_set_literals_have_one_home`, check code, not the roadmap, and stay unchanged.

## Scope in / Scope out
In: delete the function `test_follow_up_row` from `tests/integration/test_closed_sets_single_owner.py`, and the `from clutch import roadmap` import, which only that function uses.

Out: the file's other tests and helpers, `docs/roadmap.md`, and every other file.

## Scope fence
- tests/integration/test_closed_sets_single_owner.py

## Acceptance criteria
1. `grep -c "def test_follow_up_row\|from clutch import roadmap" tests/integration/test_closed_sets_single_owner.py` prints 0, and the file still defines `test_single_definitions` and `test_closed_set_literals_have_one_home` with their bodies unchanged.
2. `./dev.py test tests/integration/test_closed_sets_single_owner.py` exits 0.
3. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_closed_sets_single_owner.py
./dev.py test
```

## Definition of rejected
The branch is rejected if it changes any file other than `tests/integration/test_closed_sets_single_owner.py`, removes or weakens `test_single_definitions` or `test_closed_set_literals_have_one_home`, or edits `docs/roadmap.md`.

## Time budget
- expected: 5m
- stuck: 10m
