---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
none

## Context
- tests/integration/test_closed_sets_remaining.py
- tickets/drop-live-roadmap-content-test/ticket.md

## Goal / Why
Main is red, and the 0.3.0 release gate fails on `./dev.py test` (engine.log `roadmap_drive`, 2026-11-17 14:39Z: `gate 0.3.0: failed (exit 1): ./dev.py test -- dev: uv run pytest -q tests/integration failed`). The failing test is `tests/integration/test_closed_sets_remaining.py::test_follow_up_row`, merged with `closed-sets-remaining` (row 112). It asserts that the live roadmap holds exactly one row whose stem is `closed-sets-rest`. After a drafts recommendation rejected that ticket, the roadmap driver re-filed row 128 as `closed-sets-rest-r1`, as it is designed to, so the test now finds no such row.

This is the fourth standing test of live roadmap content to break on the driver's normal edits. The owner rules such tests gold plating, and `drop-live-roadmap-content-test` removed the previous one; box-000676 holds the cause. After this change the test is gone. The file's other two tests (`test_single_definitions`, `test_no_import_cycle`) check code, not the roadmap, and stay.

## Scope in / Scope out
In: delete the function `test_follow_up_row` from `tests/integration/test_closed_sets_remaining.py`, plus any import only it used.

Out: the file's other tests, `docs/roadmap.md`, and every other file.

## Scope fence
- tests/integration/test_closed_sets_remaining.py

## Acceptance criteria
1. `grep -c "def test_follow_up_row" tests/integration/test_closed_sets_remaining.py` prints 0, and the file still defines `test_single_definitions` and `test_no_import_cycle`.
2. `./dev.py test tests/integration` exits 0.

## Verification
```
./dev.py test tests/integration
```

## Definition of rejected
The branch is rejected if it changes any file other than `tests/integration/test_closed_sets_remaining.py`, removes or weakens `test_single_definitions` or `test_no_import_cycle`, or edits `docs/roadmap.md` to make the old test pass.

## Time budget
- expected: 5m
- stuck: 10m
