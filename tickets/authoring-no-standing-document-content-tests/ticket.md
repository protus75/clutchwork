---
state: draft
source: box:suggestion
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/docs/host-authoring.md#Keeping tickets apart
- tests/unit/test_specs.py::test_requisition_review_spec_snags_non_protocol_regression

## Goal / Why
Authoring and requisition review both refuse a ticket criterion that adds a standing test of a document's current content. The target is a test that pins live roadmap rows, gate-block commands or section phrases. The driver's strike, link and re-file steps and `roadmap accept` rewrite those rows during normal work. Each rewrite turns main red, and a red main makes every run base_red until someone deletes the test. This has happened three times: `df4ce0ae` (row 19 raw text), `511967cd` (the release audit test pinning row 122), and the gate-block pin behind box-000593. A fourth instance is still open as `drop-closed-sets-owner-roadmap-test`. The owner ruled such tests gold plating on 2026-11-16. The paved road is that a ticket editing a document has its edit verified in review, not by a standing test. The one standing roadmap check stays: the roadmap parses and its gate commands are valid.

This is the cause fix. The instance fixes are separate tickets: `drop-closed-sets-owner-roadmap-test`, `drop-live-roadmap-content-test` and `drop-closed-sets-follow-up-test`. This ticket changes no test of roadmap content.

## Scope in / Scope out
Scope in:
- `clutch/docs/host-authoring.md`: add one bullet to the "Keeping tickets apart" section. It says a ticket that edits a document verifies the edit in its review and never adds a standing test or criterion that pins the document's current content (rows, exact commands, phrases) when a tool or the driver rewrites that content. It names the one allowed standing check: the roadmap parses and its gate commands are valid. It says what to write instead: a criterion checking structure, such as parsing, or a one-time review check.
- `clutch/specs/requisition_review.md`: add one snag. Snag a draft criterion that adds or keeps a standing test of live roadmap rows, exact gate-block text or other document content that tools rewrite. The snag names the paved road above. Bump the spec `version` to the next minor above the version on main.
- `tests/unit/test_specs.py`: update only the version pin for `requisition_review` (the `("requisition_review", "3.19")` tuple) to the bumped version.
- New `tests/integration/test_authoring_document_test_rule.py`: pins the new guide bullet and the new spec snag by reading the repo files. These phrase pins cover hand-edited files that no tool or driver rewrites, so they are allowed.

Scope out: deleting or editing any existing roadmap-content test, any other spec, and any lint or gate code.

## Scope fence
- clutch/docs/host-authoring.md
- clutch/specs/requisition_review.md
- tests/unit/test_specs.py
- tests/integration/test_authoring_document_test_rule.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_authoring_document_test_rule.py` passes. Its guide test asserts that `clutch/docs/host-authoring.md` contains the bullet's marker phrase ("standing test") and the allowed-check wording ("gate commands are valid"). It fails when the bullet is removed from the guide.
2. The same file asserts that `clutch/specs/requisition_review.md` contains the snag, which names "standing test" and "roadmap". It fails when the snag is removed.
3. `./dev.py test tests/unit/test_specs.py` passes with the `requisition_review` version pin equal to the new version. The spec `version` is the next minor above the version on main, not an unchanged 3.19 and not a major bump.
4. `./dev.py test tests/unit/test_host_authoring.py tests/integration/test_lint_guide_parity.py tests/unit/test_lint_guide_parity.py` passes, so the guide edit breaks no existing guide pin.

## Verification
```
./dev.py test tests/integration/test_authoring_document_test_rule.py tests/unit/test_specs.py tests/unit/test_host_authoring.py tests/unit/test_lint_guide_parity.py tests/integration/test_lint_guide_parity.py
```

## Definition of rejected
The branch adds a standing test that pins document content a tool or the driver rewrites (roadmap rows, gate-block commands), edits or deletes an existing roadmap test, changes a spec other than `requisition_review`, or states a literal version target instead of the next minor.

## Time budget
- expected: 15m
- stuck: 30m
