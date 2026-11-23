---
state: confirmed
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/unit/test_specs.py

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Requisition review approves a ticket whose `## Context` selects a Python definition (`path.py::Name`) or Markdown heading that the ticket's `## Scope in / Scope out` deletes or renames. After a correct implementation the selector cannot resolve, so `clutch ticket lint <stem>` fails and any criterion of the form "`clutch ticket lint <stem>` exits 0" cannot pass. Incident: `serve-no-roadmap` attempt 3 (harvest.json) was a full passing implementation thrown away. Eight Context selectors (ship, ship_when_queue_low, drive, Serve.driver_pending, Serve.run_driver, Serve.wait_driver, build_driver, _Drain._run_driver) named symbols the ticket required to disappear. Lint passed on the base tree and failed after the change.

After this ticket the requisition review spec tells the reviewer to raise a snag when such a selector exists, so the ticket is repaired before Implement. The paved road for the repair is to drop the selector from Context (or select the surviving file or an unaffected symbol) and list the file under `## On-demand` if the agent still needs it.

This does not duplicate open ticket `implement-context-unresolved-selector-notice`: that ticket only turns the Implement-time ValueError from `render_context` into a notice. It does not stop review from approving a ticket that cannot pass its own lint criterion.

## Boundary contract
### Requisition review spec
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage, which embeds the spec
- observable change: the Task text adds one rule: raise a snag when a Context selector names a definition or heading that Scope in deletes, renames or moves, because the selector stops resolving once the change lands and lint then fails
- compatibility: existing rules and the JSON reply shape are unchanged; only a new finding case is added
- acceptance: a phrase test in tests/unit/test_specs.py pins the new rule text and the next minor version
- tests: tests/unit/test_specs.py
- post-merge source of truth: clutch/specs/requisition_review.md

## Scope in / Scope out
Scope in: add the rule to the Task section of `clutch/specs/requisition_review.md`. State that it applies whether or not the ticket text changed, that it applies to selectors in Context only, and that a selector on a symbol the ticket merely edits is not a hit. Bump the spec `version` to the next minor above the version on main (never a literal target). In `tests/unit/test_specs.py`, update the existing requisition review version pin to the new minor and add one phrase test for the new rule. Scope out: any change to `clutch/tickets.py` or lint code, other specs, and docs.

## Scope fence
- clutch/specs/requisition_review.md
- tests/unit/test_specs.py

## Acceptance criteria
1. The requisition review spec Task text contains the new rule naming a Context selector deleted by Scope in; `./dev.py test tests/unit/test_specs.py` asserts the phrase and fails if the rule is removed.
2. The spec `version` is the next minor above main's, and the `tests/unit/test_specs.py` pin matches it; `./dev.py test tests/unit/test_specs.py` fails when the pin and the spec disagree.
3. The new rule states that a selector on a symbol the ticket only edits is not a hit; the phrase test in `./dev.py test tests/unit/test_specs.py` asserts that sentence, so an over-broad rule fails.

## Verification
```
./dev.py test tests/unit/test_specs.py
```

## Definition of rejected
The branch edits any file outside the fence, adds a lint or code change, or states the rule so that it flags selectors on symbols the ticket keeps.

## Time budget
- expected: 10m
- stuck: 20m
