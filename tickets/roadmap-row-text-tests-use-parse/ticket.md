---
state: draft
source: box:suggestion
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- closed-sets-follow-up-row-struck

## Context
- clutch/docs/host-authoring.md#Keeping tickets apart
- tests/unit/test_specs.py

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
The roadmap driver rewrites the text of every `docs/roadmap.md` row a ticket touches: it links rows and strikes them after merge. A test that matches raw row text breaks main once the driver edits that row. This happened with the criterion 7 test of `closed-sets-single-owner`, whose strike commit df4ce0ae turned main red (box-000597, box-000598). The instance is fixed by `closed-sets-follow-up-row-struck`. This ticket fixes the cause. After it, the authoring guide and the requisition review spec both say that a test reading `docs/roadmap.md` reads rows through `clutch.roadmap.parse` and asserts on `Row` fields, never on raw row text. Requisition review snags a criterion that matches raw `docs/roadmap.md` row text, so the next ticket cannot repeat the defect.

## Scope in / Scope out
Scope in:
- `clutch/docs/host-authoring.md`: add one bullet under `## Keeping tickets apart` stating the rule above and the reason (the driver's link and strike edits). Change nothing else in that file.
- `clutch/specs/requisition_review.md`: add one `snag` bullet to the `## Task` list. It fires when a criterion or a test the ticket adds matches raw roadmap table row text (a regex or substring over row lines, or a row number or stem written into a pattern). Its paved road is to read rows through `clutch.roadmap.parse` and assert on `Row` fields. A test that uses `clutch.roadmap.parse` is not a hit. Bump the spec `version` to the next minor above the version on main.
- `tests/unit/test_specs.py`: update the pinned `requisition_review` version to the new value. This is the one expectation that may change there.
- New `tests/integration/test_roadmap_row_text_rule.py`: reads the guide and the spec from the repo and checks that both state the rule. It lives under `tests/integration/` because it reads repo files.
Scope out: the roadmap driver, `clutch/roadmap.py`, other spec bullets, the agent rule files, the roadmap table itself, and any lint gate.

## Scope fence
- clutch/docs/host-authoring.md
- clutch/specs/requisition_review.md
- tests/unit/test_specs.py
- tests/integration/test_roadmap_row_text_rule.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_roadmap_row_text_rule.py` passes. Its guide check asserts that `clutch/docs/host-authoring.md` contains both `clutch.roadmap.parse` and `docs/roadmap.md`, so it fails on the unchanged guide.
2. The same test asserts that `clutch/specs/requisition_review.md` contains `clutch.roadmap.parse`, `docs/roadmap.md` and `snag` within the new bullet. It fails on the unchanged spec, where `clutch.roadmap.parse` is absent.
3. `./dev.py test tests/unit/test_specs.py` passes with the `requisition_review` version pin equal to the new front-matter version and not the version on main before this change.
4. `./dev.py test tests/unit/test_host_authoring.py tests/integration/test_lint_guide_parity.py` passes, so the existing guide pins still hold.

## Verification
```
./dev.py test tests/integration/test_roadmap_row_text_rule.py tests/unit/test_specs.py tests/unit/test_host_authoring.py tests/integration/test_lint_guide_parity.py
```

## Definition of rejected
The branch changes any file outside the fence. Or the rule is added only to the guide or only to the spec. Or the rule bans reading `docs/roadmap.md` outright instead of requiring `clutch.roadmap.parse`. Or the spec `version` is not bumped.

## Time budget
- expected: 20m
- stuck: 45m
