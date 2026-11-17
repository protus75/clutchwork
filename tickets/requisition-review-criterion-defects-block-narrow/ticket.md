---
state: rejected
source: box:suggestion
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/unit/test_specs.py::test_requisition_review_spec_raises_impossible_criteria_unchanged
- tests/integration/test_spec_unit_io_seam.py

## On-demand
- clutch/specs/requisition_review.md
- docs/how-clutch-works.md

## Goal / Why
The requisition review spec never approves while its own summary records a defect in an acceptance criterion or `## Verification` command, even when that text is unchanged since the prior review. Today the never-approve rule in `clutch/specs/requisition_review.md` covers only criteria that are impossible to satisfy. The Author-stage re-review of `closed-sets-single-owner-refile` noted that criterion 4's grep already passes on the base and still approved. The pre-run review then parked the ticket, which cost a review cycle and a park. The spec states the wider rule, and the Premise park bullet in `docs/how-clutch-works.md` describes it.

The rule must not list "already passes at base" as a blanket defect. That description fits every preservation criterion such as "existing test X still passes". The defect is a check written to prove the change that also passes on the base.

This narrows the rejected `requisition-review-criterion-defects-block`, which listed the base-pass case with no qualifier.

## Scope in / Scope out
Scope in:
- `clutch/specs/requisition_review.md`: keep the existing impossible-criteria sentence and its phrases unchanged. Add one sentence after it in the same paragraph. It says to never approve while the summary records a defect in an acceptance criterion or `## Verification` command, even in unchanged text, including a check written to prove the change that also passes on the base. It also says a preservation criterion (an existing test or behavior that must keep passing) is not a hit. Bump `version` to the next minor above the version on main.
- `docs/how-clutch-works.md`: update only the Premise park bullet, so it states the widened rule and the preservation qualifier in place of the impossible-only exception.
- `tests/unit/test_specs.py`: change only the pinned `requisition_review` version in `test_spec_lint_accepts_the_implement_and_requisition_specs` to the bumped version.
- New `tests/integration/test_requisition_review_criterion_defects.py` holds the spec-text test. It is an integration test because it reads a repo file.

Scope out: `docs/host-authoring.md`, including its sentence "a check that must print nothing quotes text the base contains", which stays as is. Also out: the review engine code, other specs, and the findings schema.

## Scope fence
- clutch/specs/requisition_review.md
- docs/how-clutch-works.md
- tests/unit/test_specs.py
- tests/integration/test_requisition_review_criterion_defects.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_requisition_review_criterion_defects.py` passes. The test asserts the normalized Task text of the spec contains a defect in an acceptance criterion or `## Verification` command, `even in unchanged text`, `a check written to prove the change that also passes on the base`, and the preservation-criterion qualifier. The test fails on the base spec, which contains none of them.
2. The same test asserts the Task text does not list a bare "already passes" or "passes on the base" rule: every occurrence of "passes on the base" sits in the phrase `written to prove the change that also passes on the base`. A blanket rule fails the test.
3. `./dev.py test tests/unit/test_specs.py` passes. The existing `test_requisition_review_spec_raises_impossible_criteria_unchanged` phrases are still present, and the version pin equals the bumped spec version, not `3.19`.
4. The same integration test asserts the Premise park bullet in `docs/how-clutch-works.md` contains the preservation qualifier and the widened rule. The old impossible-only wording alone fails the test.

## Verification
```
./dev.py test tests/unit/test_specs.py tests/integration/test_requisition_review_criterion_defects.py tests/integration/test_spec_sibling_tickets.py tests/integration/test_spec_unit_io_seam.py
```

## Definition of rejected
The branch is rejected if the spec lists "already passes at base" as a defect without the written-to-prove-the-change qualifier. It is also rejected if the impossible-criteria sentence or its test phrases are removed, if the spec version is not bumped, or if a file outside the fence is edited.

## Time budget
- expected: 20m
- stuck: 40m
