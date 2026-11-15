---
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
source: box:retro_finding
state: rejected
---

## Depends on
none

## Context
- tests/unit/test_specs.py::test_requisition_review_spec_snags_non_protocol_regression

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Retro finding retro/27 asked for a set-membership closure in requisition review and Author. That rule already exists on main: `clutch/specs/requisition_review.md` line 24 and `clutch/docs/host-authoring.md` line 55. `tests/integration/test_author.py` pins the rule's trigger on the Author side. `tests/unit/test_specs.py` pins the trigger and the "asserts against the changed set or hardcodes the moved path" clause on the review side. Nothing pins the limit sentence ("A mere textual mention, a path built under `tmp_path`, or a historical form the ticket keeps valid is not a hit"). That sentence is the finding's own overcorrection guard. If it is dropped, reviewers fence loose grep hits and approvals stall. After this change a test fails if the limit sentence leaves the requisition review spec.

## Scope in / Scope out
Scope in: add one assertion to `tests/unit/test_specs.py::test_requisition_review_spec_snags_non_protocol_regression` that the rendered Task contains the limit sentence. Scope out: the spec text, `clutch/docs/host-authoring.md`, `clutch/specs/author.md`, and every other test. The retro finding's rule is already merged and is not re-implemented. The spec file is fenced only so the lint rule is met; it is read, not edited.

## Scope fence
- tests/unit/test_specs.py
- clutch/specs/requisition_review.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_specs.py::test_requisition_review_spec_snags_non_protocol_regression` passes, and the test asserts by exact substring match that the rendered Task contains "A mere textual mention, a path built under `tmp_path`, or a historical form the ticket keeps valid is not a hit.". A spec with that sentence removed makes the substring check fail, so the assertion is not satisfied by a paraphrase or a partial match.
2. `./dev.py test tests/unit/test_specs.py` exits 0, so every other existing assertion in the file still passes.

## Verification
```
./dev.py test tests/unit/test_specs.py
```

## Definition of rejected
Any change outside `tests/unit/test_specs.py`, or any edit to the spec wording, rejects the branch.

## Time budget
- expected: 10m
- stuck: 30m
