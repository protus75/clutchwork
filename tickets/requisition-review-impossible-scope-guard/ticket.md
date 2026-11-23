---
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
source: box:retro_finding
state: rejected
---

## Depends on

- `requisition-review-impossible-criteria-unchanged`

## Context

- tests/unit/test_specs.py::test_requisition_review_spec_raises_impossible_criteria_unchanged

## Goal / Why

Retro finding retro/43 (commit-lock-commands attempt 1) reported a requisition review that recorded an unbuildable criterion in its summary and still approved, because the changed-text limit had no exception. The merged ticket `requisition-review-impossible-criteria-unchanged` already repaired this. The Task text of the requisition review spec now says the changed-text limit never applies to a defect that makes a criterion or `## Verification` command impossible to satisfy against merged code. It says such a defect is raised whether or not the text changed, never approved while the summary records one, and that style and arguable wording are not hits. That ticket added a phrase test in `tests/unit/test_specs.py`. This ticket does not re-solve the repair.

The retro also names an overcorrection risk: reviewers reopening settled text every round. The merged phrase test checks that the sentences exist but not that the original limit is still the governing rule next to the exception. This ticket adds one bounded guard for that: a test that the changed-text limit and the exception stay in the same prior-review paragraph and that the exception is the only carve-out from that limit beyond the existing dependents and invalid-prior wording. No spec or code changes. The retro reopens only if a requisition review run after the merge again approves while its summary records an unsatisfiable criterion, and no such run is evidenced here.

## Boundary contract

none
- reason: tests encoding an existing contract; the spec text, its version, and every consumer are unchanged.

## Scope in / Scope out

Scope in:

- Add `tests/integration/test_requisition_review_impossible_scope.py`. It reads the shipped requisition review spec through a `Path(__file__)` anchor, takes the paragraph that contains `Raise a NEW finding only against text the diff shows changed`, and asserts that paragraph also contains the exception sentence and the words `style or arguable wording`.

Scope out:

- Any edit to the spec, its version, `tests/unit/test_specs.py`, docs, or code.
- Any new standing check on roadmap rows or document wording beyond the one paragraph above.

## Scope fence

- tests/integration/test_requisition_review_impossible_scope.py

## Acceptance criteria

1. `./dev.py test tests/integration/test_requisition_review_impossible_scope.py` passes on main. The test fails if the exception sentence sits outside the paragraph holding the changed-text limit, which rules out an exception that detaches from the limit it qualifies.
2. The same test fails if `style or arguable wording` is missing from that paragraph, which rules out an unbounded exception.
3. `./dev.py test tests/unit/test_specs.py` still passes, which rules out a spec or version change by this ticket.

## Verification

```
./dev.py test tests/integration/test_requisition_review_impossible_scope.py tests/unit/test_specs.py
```

## Definition of rejected

- Any file outside the fence is edited, including the spec.
- The new test only repeats the phrase assertions already in `tests/unit/test_specs.py`.

## Time budget

- expected: 10m
- stuck: 20m
