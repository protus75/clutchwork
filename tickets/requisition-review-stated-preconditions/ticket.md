---
state: draft
source: box:retro_finding
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/docs/host-authoring.md#What each section is for
- tests/integration/test_spec_sibling_tickets.py

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Today, requisition review approved ticket `boundary-contract-required` although its Goal stated a precondition that was false on HEAD: two open tickets "must already carry a valid ## Boundary contract section when this ticket runs". Neither did. No `## Depends on` stem delivered it, and the ticket said a supervising session would add the sections by hand before dispatch. Implement then failed `clutch ticket lint` on two out-of-fence files and returned premise_failed. That cost a premise_bounce cap, a diagnosis call, a rework call, and a Reject-queue park that needed a human.

After this ticket, two rules exist. (1) The requisition review spec checks every precondition a ticket states about current repo state (a file's content, an open ticket's section, a lint result) against HEAD, and raises a `snag` when it does not hold and no `## Depends on` stem delivers it. The snag's paved road is a `## Depends on` edge to a ticket that delivers it, or fencing the file and putting the edit in Scope in. (2) The authoring guide forbids a precondition that a person must perform outside the pipeline. Under the one-authoring-process rule, the guide `clutch/docs/host-authoring.md` is the only home for this rule, so `clutch/specs/author.md` is not edited.

Two exemptions bound the rule. A precondition delivered by a declared `## Depends on` is not a snag. A precondition about a `tickets/` path is expressed with `## Depends on`, never by fencing a file that Implement may not edit.

## Boundary contract
### Requisition review spec
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage (`clutch/requisition.py`) and the `clutch ticket review` verb
- observable change: a ticket that states a repo-state precondition that is false on HEAD, with no delivering `## Depends on` stem, gets a `snag` finding naming the precondition and the paved road; a precondition delivered by a `## Depends on` stem is approved as before
- compatibility: the reply schema and verdict vocabulary are unchanged; tickets without stated preconditions review as before; the spec `version` moves to the next minor above the version on main
- acceptance: the spec Task section carries the HEAD-check rule, both exemptions, and the paved road
- tests: a new integration test reads the spec and checks the rule text; the existing version pins are updated
- post-merge source of truth: clutch/specs/requisition_review.md

### Authoring guide
- disposition: extend
- owner: clutch/docs/host-authoring.md
- consumers: the Author stage prompt, which embeds the guide, and the ticket authoring chat sessions
- observable change: the guide forbids stating a precondition that a person must perform outside the pipeline and names the two replacements
- compatibility: no ticket format change; existing tickets remain valid
- acceptance: the guide's `Depends on` section states the rule
- tests: a new integration test checks the guide text
- post-merge source of truth: clutch/docs/host-authoring.md

## Scope in / Scope out
Scope in:
- `clutch/specs/requisition_review.md`: add one bullet to the Task section's `snag` list stating the HEAD-precondition rule, both exemptions, and the paved road. Bump `version` to the next minor above the version on main.
- `clutch/docs/host-authoring.md`: add the no-manual-precondition rule to the `Depends on` section only, naming the two replacements (a `## Depends on` edge, or a fenced file with the edit in Scope in) and the `tickets/` path exemption.
- `tests/unit/test_specs.py` and `tests/integration/test_specs_delimiter_note.py`: change the `requisition_review` version pin to the bumped version. Nothing else changes in these files.
- A new `tests/integration/test_precondition_rules.py` with the criteria's checks.

Scope out: the author prompt spec (it embeds the guide, so it is not edited), any gate or lint code, and any change to the reply schema.

## Scope fence
- clutch/specs/requisition_review.md
- clutch/docs/host-authoring.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_precondition_rules.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_precondition_rules.py` passes. It asserts that the Task section of `clutch/specs/requisition_review.md` names checking a stated repo-state precondition against HEAD, a `snag` when it does not hold and no `## Depends on` stem delivers it, and the two paved roads (a `## Depends on` edge, or fencing the file with the edit in Scope in). It also asserts the exemption for a precondition delivered by `## Depends on`. A spec lacking the exemption fails the test.
2. In `./dev.py test tests/integration/test_precondition_rules.py`, a test renders the Task section and asserts that it still contains the existing sibling-ticket and missing-fence-path bullets. It fails if the new bullet replaced either.
3. In the same file, a test asserts that the `Depends on` section of `clutch/docs/host-authoring.md` forbids a precondition a person must perform outside the pipeline and names both replacements and the `tickets/` path exemption. It fails if the rule appears only outside that section.
4. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py` passes with the `requisition_review` pin set to the bumped version, not `3.21`.
5. `./dev.py test tests/integration/test_lint_guide_parity.py tests/unit/test_host_authoring.py` passes, so the guide edit breaks no parity check.
6. `git diff --stat main -- clutch/specs/author.md` prints nothing, which shows author.md is untouched.

## Verification
```
./dev.py test tests/integration/test_precondition_rules.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_lint_guide_parity.py tests/unit/test_host_authoring.py tests/integration/test_spec_sibling_tickets.py
```

## Definition of rejected
The branch edits `clutch/specs/author.md`, restates the guide rule outside `clutch/docs/host-authoring.md`, adds a gate or lint code, drops or rewrites an existing requisition review bullet, or leaves the version pins at `3.21`.

## Time budget
- expected: 15m
- stuck: 30m
