---
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
source: box:retro_finding
state: rejected
---

## Depends on
none

## Context
- tests/integration/test_specs_delimiter_note.py

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Retro finding retro/61: requisition review approved `evidence-verbs` (ticket 2f40778a, spec 3.25) although a criterion limited `docs/how-clutch-works.md` to gaining 'exactly four rows and no other text'. The verbs that ticket adds made two sentences in that same document false: line 821 said no command exposes json_schema, and line 825 said no call record has a normalized/ directory. Implement attempt 0 replied premise_failed with an empty diff. That cost a premise_bounce cap, a reject diagnosis, a rework call and a Reject-queue hold until a supervisor keep. The rework only fixed the ticket by allowing the two sentences to be rewritten.

After this ticket, `clutch/specs/requisition_review.md` tells the reviewer to check this impossibility. When a criterion or Definition-of-rejected clause limits a fenced document to an exact edit ('exactly N rows', 'no other text changes'), the reviewer greps that document for statements the Scope-in behavior makes false (existence claims such as 'no command', 'not yet', 'no ... has'). Each hit is a finding that cites file:line. Its paved road names each sentence to rewrite in Scope in and widens the criterion to allow only those sentences. Wording that is merely speculative, or a statement the change leaves true, is not a hit.

The nearest merged work is `requisition-review-impossible-criteria-unchanged`, which fixed the changed-text exemption but did not add this detection, and `requisition-review-impossible-scope-guard`, which this ticket does not re-solve. Class prevention is this spec rule itself: it moves detection from a failed Implement run to review.

Rule placement: this is a requisition-review process rule, so it lives only in the spec `clutch/specs/requisition_review.md`, not in CLAUDE.md, AGENTS.md or CORE_TEMPLATE.

## Boundary contract
### Requisition review spec
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage, which embeds the spec in its prompt
- observable change: the reviewer gains one rule that snags an exact-edit limit on a fenced document when the Scope-in behavior falsifies a statement in that document. The finding cites file:line and the paved road names each sentence to rewrite and the widened criterion. The spec version moves to the next minor above the version on main.
- compatibility: existing rules, the reply format and the changed-text limit stay as they are. The rule fires only on an exact-edit limit together with a falsified statement, so other tickets are not newly snagged.
- acceptance: a phrase test shows the new rule text in the spec, and the version pins are updated.
- tests: a new integration test file reads the spec; the two existing version pins are updated.
- post-merge source of truth: clutch/specs/requisition_review.md

## Scope in / Scope out
Scope in:
- Add one rule to the Task section of `clutch/specs/requisition_review.md`, next to the changed-text paragraph that begins 'The changed-text limit never applies'. It covers: the trigger (a criterion or Definition-of-rejected clause limiting a fenced document to an exact edit); the check (grep that document for statements the Scope-in change makes false); the finding (each hit cited by file:line); the paved road (name each sentence to rewrite in Scope in and widen the criterion to allow only those sentences); and the limit (speculative wording or still-true statements are not hits).
- Bump the spec `version` to the next minor above the version on main (never a literal target).
- Update the version pin in `tests/unit/test_specs.py` (the `requisition_review` entry) and in `tests/integration/test_specs_delimiter_note.py`. The one expectation that may change in each is the `requisition_review` version string.
- Add `tests/integration/test_requisition_review_exact_edit_rule.py`. It reads the spec through a `Path(__file__)` anchor and asserts the rule's key phrases are present.

Scope out:
- No engine code, gate, lint or other spec changes.
- No re-solving of `requisition-review-impossible-criteria-unchanged` or `requisition-review-impossible-scope-guard`.
- No docs change; no docs describe this spec's rule list.

## Scope fence
- clutch/specs/requisition_review.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_requisition_review_exact_edit_rule.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_requisition_review_exact_edit_rule.py` passes. The spec text contains the exact-edit trigger, the grep-for-falsified-statements check, the file:line citation requirement and the widen-the-criterion paved road. The test fails on the base spec, which has none of these phrases.
2. `./dev.py test tests/integration/test_requisition_review_exact_edit_rule.py` also asserts the spec says speculative wording and statements the change leaves true are not hits, so the rule cannot be read as 'snag every exact-edit limit'.
3. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py` passes with the `requisition_review` version pinned to the new next-minor value, not the old value.
4. The spec `version` is the next minor above the version on main, checked by `./dev.py test tests/unit/test_specs.py`.

## Verification
```
./dev.py test tests/integration/test_requisition_review_exact_edit_rule.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py
```

## Definition of rejected
The branch edits any file outside the fence. The rule snags every exact-edit document limit without a falsified statement. The paved road widens the limit to 'any document text'. The rule is added without a version bump or without updated pins.

## Time budget
- expected: 10m
- stuck: 20m
