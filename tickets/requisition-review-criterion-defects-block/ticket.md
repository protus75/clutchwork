---
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Context
- clutch/docs/host-authoring.md#What each section is for
- tests/unit/test_specs.py::test_requisition_review_spec_raises_impossible_criteria_unchanged
- tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Requisition review can no longer approve while its own summary records a defect in a criterion or `## Verification` command, whether or not that text changed. Today the spec exempts from its changed-text limit only a defect that makes a criterion or Verification command impossible to satisfy against merged code. A vacuous criterion in unchanged text (one that already passes at base, or whose check must print nothing but quotes text that never appears) falls under the limit, so the reviewer notes it and approves. On `closed-sets-single-owner-refile` (2026-11-16) the Author-stage re-review recorded that criterion 4 grep "already passes on the base" as a non-blocking note and approved. The pre-run review then parked the stem on that defect plus two more. If a later review also misses it, a criterion that proves nothing merges as verification.

This is the fourth exception on one surface (see `requisition-review-impossible-criteria-unchanged`, `requisition-review-changed-text-vs-unchanged`, `requisition-review-invalid-prior-full-rereview`). The root model: the changed-text limit narrows what a re-review must search again, never what it may report. The spec replaces the impossible-only exception with one rule covering every criterion or Verification defect. The authoring guide also gains the rule that stops authors from writing the vacuous form. This ticket belongs to the engine's own gate spec and guide; no host file is touched.

## Scope in / Scope out
Scope in:
- `clutch/specs/requisition_review.md`: replace the sentence beginning "The changed-text limit never applies to a defect that makes a criterion or `## Verification` command impossible to satisfy against merged code" with one sentence saying the limit never applies to a defect in a criterion or `## Verification` command. The sentence names three kinds: it cannot be satisfied against merged code, it already passes at base, and it names output its command never prints. It keeps "raise it as a finding whether or not the text changed", "never approve while the summary records such a defect" and "do not treat style or arguable wording as hits". Bump the spec `version` to the next minor above the version on main (never a literal target). Change nothing else in the spec.
- `clutch/docs/host-authoring.md`: in the `Acceptance criteria` bullet of "What each section is for", add one sentence: a check that must print nothing quotes text the base contains. Edit only that bullet.
- `tests/unit/test_specs.py`: raise the `requisition_review` version pin in `test_spec_lint_accepts_the_implement_and_requisition_specs` to the bumped version, and change the first phrase in `test_requisition_review_spec_raises_impossible_criteria_unchanged` to the new sentence's opening, "The changed-text limit never applies to a defect in a criterion or `## Verification` command". The other three phrases there stay.
- New `tests/integration/test_requisition_review_criterion_defects.py` (reads two repo files, so it lives under `tests/integration/`) pins the new sentence's three kinds and the guide sentence.

Scope out: the other `requisition-review-*` bullets, the dependents-accounting rule, engine code, and any other spec. A sibling that bumps the same spec version merges first or after; this ticket takes the next minor above whatever main holds when it runs.

## Scope fence
- clutch/specs/requisition_review.md
- clutch/docs/host-authoring.md
- tests/unit/test_specs.py
- tests/integration/test_requisition_review_criterion_defects.py

## Acceptance criteria
1. The rendered Task section of `clutch/specs/requisition_review.md` contains "The changed-text limit never applies to a defect in a criterion or `## Verification` command", "already passes at base", "names output its command never prints", "cannot be satisfied against merged code" and "never approve while the summary records such a defect"; `./dev.py test tests/integration/test_requisition_review_criterion_defects.py` fails if any is missing, and the old impossible-only wording "makes a criterion or `## Verification` command impossible to satisfy" is absent from the rendered Task, not merely present alongside.
2. `clutch/specs/requisition_review.md` still lints clean and its `version` is the next minor above main's, not the unchanged "3.18"; `./dev.py test tests/unit/test_specs.py` passes with the updated pin and fails if the version stays "3.18".
3. The `Acceptance criteria` bullet in `clutch/docs/host-authoring.md` contains "a check that must print nothing quotes text the base contains"; `./dev.py test tests/integration/test_requisition_review_criterion_defects.py` fails if the sentence is absent.
4. `test_requisition_review_spec_raises_impossible_criteria_unchanged` in `tests/unit/test_specs.py` still asserts "raise it as a finding whether or not the text changed", "never approve while the summary records such a defect" and "do not treat style or arguable wording as hits"; `./dev.py test tests/unit/test_specs.py` fails if any of the three is dropped from the spec.
5. No other statement in the spec changes: `./dev.py test tests/unit/test_specs.py tests/integration/test_requisition.py tests/integration/test_spec_unit_io_seam.py tests/integration/test_fence_closure_registries.py tests/unit/test_host_authoring.py tests/unit/test_lint_guide_parity.py` exits 0.

## Verification
```
./dev.py test tests/integration/test_requisition_review_criterion_defects.py tests/unit/test_specs.py tests/integration/test_requisition.py tests/integration/test_spec_unit_io_seam.py tests/integration/test_fence_closure_registries.py tests/unit/test_host_authoring.py tests/unit/test_lint_guide_parity.py
```

## Definition of rejected
The branch keeps the impossible-only exception beside a new one instead of replacing it with one rule. Or it adds a second spec sentence for "already passes at base" rather than extending the single exception. Or it edits any spec bullet other than the changed-text sentence and the version. Or the new test accepts a spec that lacks any of the three defect kinds. Or the version is a literal copied from a sibling rather than the next minor above main's.

## Time budget
- expected: 25m
- stuck: 50m
