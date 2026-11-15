---
state: confirmed
source: box:suggestion
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/unit/test_specs.py::test_requisition_review_spec_snags_missing_reproduction_exit
- tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs

## On-demand
- clutch/specs/requisition_review.md
- tests/integration/test_requisition.py

## Goal / Why
Requisition review has no rule for a ticket that adds a unit test which must read a named repo file. On 2026-11-13, `drain-loop-prompt` (`tests/unit/test_ask_drain_loop.py` renders the real `clutch/specs/ask` templates) and `vscode-help` (`tests/unit/test_help.py` reads `vscode-clutchwork/package.json` and real docs) both passed requisition review. Implement then returned `premise_failed`, citing the unit-disk rule in `clutch/specs/review.md`. Each failure cost a Diagnose pass and ended in the Reject queue. The earlier preflight in `author.md` was declined because human-path tickets skip it. Requisition review is the one stage every authoring path passes through. After this change the reviewer snags such a ticket before Implement runs, with a paved road to `tests/integration/`.

The rule fires only when the ticket adds a unit test, or newly requires an existing one, to read a named repo file. Updating a pinned value in an existing unit test that already reads the file is not a hit, so routine spec version bumps are not snagged.

Measure the effect by watching for fewer Implement `premise_failed` findings that cite the unit-disk rule in later retros.

## Scope in / Scope out
Scope in:
- Add one bullet to the `## Task` list of `clutch/specs/requisition_review.md`, placed after the unit-floor bullet. When a criterion or `## Verification` line names a `tests/unit/` file whose test the ticket adds, or newly requires, to read a named repo file (a spec, doc, `package.json`, or `importlib.metadata` data), the reviewer raises a `snag` finding. The finding's paved road is to place that test under `tests/integration/` and fence that file.
- The bullet states three guard clauses. A unit test that reads only `tmp_path` is not a hit. A unit test that reaches a repo file only through an injected seam or fake is not a hit. Updating a pinned value in an existing unit test that already reads the file is not a hit.
- Bump the spec `version` to the next minor above the version on main.
- In `tests/integration/test_requisition.py`, add one test named `test_requisition_review_spec_snags_unit_test_disk_read`. It reads `SPECS / "requisition_review.md"` the way the existing test near line 112 does, and pins the bullet's trigger, its paved road and all three guard clauses.
- In `tests/unit/test_specs.py`, update only the version pin in `test_spec_lint_accepts_the_implement_and_requisition_specs` to the bumped version. Add no new disk-reading unit test.

Scope out:
- `author.md`, `clutch/docs/host-authoring.md`, any lint check in `clutch/tickets.py`, and `clutch/specs/review.md` stay unchanged.
- No existing ticket is edited.

## Scope fence
- clutch/specs/requisition_review.md
- tests/integration/test_requisition.py
- tests/unit/test_specs.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_requisition.py tests/unit/test_specs.py -k requisition_review` passes. The new `test_requisition_review_spec_snags_unit_test_disk_read` asserts that the spec text contains the `tests/unit/` trigger, the `tests/integration/` paved road, the `tmp_path` guard, the injected seam or fake guard, and the pinned-value-update guard. The test fails if any of these five is removed from the spec.
2. The spec's `version` is the next minor above the version on main (`3.14` on main today). `test_spec_lint_accepts_the_implement_and_requisition_specs` pins that version and passes. A stale `3.14` pin fails it.
3. `./dev.py test tests/unit/test_specs.py` passes. This confirms the spec still lints and renders within its size budget, and that no new unit test reads a repo file.

## Verification
```
./dev.py test tests/integration/test_requisition.py tests/unit/test_specs.py
```

## Definition of rejected
The branch edits any file outside the fence. Or the new bullet flags a unit test that reads only `tmp_path`, reaches a repo file only through an injected seam, or merely updates a pinned value. Or the new test still passes after any of the three guard clauses is removed from the spec. Or a new unit test in `tests/unit/` reads a repo file from disk.

## Time budget
- expected: 15m
- stuck: 40m
