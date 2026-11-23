---
state: rejected
source: box:retro_finding
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs
- tests/integration/test_specs_delimiter_note.py

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Requisition review approved `review-panel` (ticket f5b37106) although its Scope in added a `/m<k>` member part to the effect key. The fence left out consumers that take that key apart by position: `clutch/providers.py` unpacks exactly six parts, `clutch/rework.py` parses the last part as an int, and `clutch/stats.py`, `clutch/scorecard.py` and `clutch/training.py` accept only 6-part keys. Implement returned premise_failed, Diagnose rejected the ticket, and the operator killed it and split it as `review-panel-r2`. Retro finding retro/60 names this gap.

The merged closure rules in the spec trace references to changed symbols, recorded constant values, set members, whole-value comparisons and stand-ins. None reaches code that splits or parses a structured string (a key, id or path) by part count, separator, or the position or type of a part, because that code never names the symbol that builds the string.

When this ticket is done, the requisition review spec carries one Task bullet that raises a `snag` for that case. It keeps the retro's limit on overcorrection: only a consumer whose decomposition the new shape actually breaks is a hit. A consumer that passes the string through or compares it whole is not.

The review judges only the supplied ticket and Context and never searches the repo, so the bullet works from what the ticket text and Context show. It does not ask the reviewer to grep. Related rules, not re-solved here: `requisition-review-whole-value-closure`, `requisition-review-stand-in-closure`, `set-membership-fence-closure`, `fence-closure-registries`. The open `requisition-review-diff-budget-volume` covers diff volume, a different class.

## Boundary contract
### Requisition review Task rules
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage, which renders this spec, and the spec lint and version pins in tests
- observable change: one added Task bullet. A ticket whose Scope in changes the shape of a structured string (part count, separator, or position or type of a part) that code outside the fence splits, unpacks or parses, as shown by the ticket text or Context, now gets a `snag` naming that consumer. Spec `version` goes to the next minor above the version on main.
- compatibility: existing Task bullets are unchanged. Tickets that do not change a decomposed string's shape are judged as before. The reply format is unchanged.
- acceptance: the rendered Task section contains the new bullet's key phrases, and the spec lints clean within the line limit.
- tests: a new integration phrase test, plus the two existing version pins updated.
- post-merge source of truth: clutch/specs/requisition_review.md

## Scope in / Scope out
Scope in:
- Add one bullet to the `## Task` list of `clutch/specs/requisition_review.md`, after the existing closure-style bullets. It says: when Scope in changes the shape of a structured string (key, id or path) by part count, separator, or the position or type of a part, and the ticket text or Context shows code outside `## Scope fence` that splits, unpacks, indexes or parses that string by position, raise a `snag` naming that consumer. Paved road: fence the consumer and say in Scope in how its parse changes, or raise the mismatch as a snag. It also says only a consumer whose parse the new shape actually breaks is a hit, and a consumer that passes the string through or compares it whole is not.
- Bump the spec `version` to the next minor above the version on main.
- Update the version pins: `tests/unit/test_specs.py` (the tuple in `test_spec_lint_accepts_the_implement_and_requisition_specs`) and `tests/integration/test_specs_delimiter_note.py`. No other expectation in these files changes.
- Add `tests/integration/test_requisition_review_decomposed_string.py`, which reads the spec through a `Path(__file__)` anchor, renders the Task section as the existing phrase tests do, and asserts the bullet's phrases.

Scope out:
- No code change in `clutch/` and no change to the other spec bullets.
- Making the keys themselves single-owner, per `declined-box-000734`, is a code refactor and stays out.
- No gate or lint for this rule. The spec prose is the only enforcement.

## Scope fence
- clutch/specs/requisition_review.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_requisition_review_decomposed_string.py

## Acceptance criteria
1. The rendered Task section of the requisition review spec contains the phrases "splits, unpacks", "part count", and "actually breaks", checked by `./dev.py test tests/integration/test_requisition_review_decomposed_string.py`. The test also asserts that the bullet says a consumer that only passes the string through or compares it whole is not a hit. A spec without that limit fails the test.
2. The spec `version` is the next minor above the main value. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py` passes with both pins updated. A stale pin of the old version fails.
3. The spec still lints with no findings and stays within `SPEC_MAX_LINES`, checked by `test_spec_lint_accepts_the_implement_and_requisition_specs` in `./dev.py test tests/unit/test_specs.py`.
4. The existing phrase tests in `tests/unit/test_specs.py` for the changed-text, impossible-criteria, reproduction-exit and regression-protocol rules still pass, checked by `./dev.py test tests/unit/test_specs.py`.

## Verification
```
./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_requisition_review_decomposed_string.py
```

## Definition of rejected
The branch is rejected if it edits any file outside the fence, adds an instruction for the reviewer to search the repo, makes every string-format change force a wide fence (a pass-through or whole-value consumer counted as a hit), or leaves a stale version pin.

## Time budget
- expected: 12m
- stuck: 24m
