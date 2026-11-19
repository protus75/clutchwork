---
state: confirmed
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- boundary-contract-authoring

## Context
- clutch/tickets.py::REQUIRED_SECTIONS
- clutch/tickets.py::OPTIONAL_SECTIONS
- clutch/tickets.py::_parse_ticket
- clutch/docs/host-authoring.md
- tests/unit/test_boundary_contract_shape.py

## Goal / Why
Roadmap row 154, boundary plan phase 2 follow-up. After this ticket a non-settled ticket without a `## Boundary contract` section fails intake and lint, with a finding that names the fix. A ticket journaled settled or rejected, or with state `merged` or `rejected`, is exempt, exactly like the existing shape check. Today the section is optional, so authors can skip the declaration and parallel owners keep appearing.

Precondition: the open tickets `box-issue-process-gap-class` and `release-audit-040-r1` must already carry a valid `## Boundary contract` section when this ticket runs. Implement cannot edit anything under `tickets/`, so a supervising session adds those two sections by path before dispatch; this ticket does not touch them. Every other ticket under `tickets/` is settled or rejected and stays exempt.

## Boundary contract
### Ticket parser required sections
- disposition: extend
- owner: clutch/tickets.py
- consumers: intake, `clutch ticket lint`, `clutch ticket new`, the Author and requisition review stages, and tests that build ticket text
- observable change: a non-settled ticket with no `## Boundary contract` yields a finding naming the fix; before, a missing section was never a finding. Shape rules for a present section are unchanged.
- compatibility: settled and rejected tickets stay valid; the skeleton already writes the section, so new tickets are unaffected
- acceptance: a draft ticket without the section returns a finding, and the same text journaled settled returns none
- tests: tests/unit/test_boundary_contract_required.py and the updated closed-set pin
- post-merge source of truth: clutch/tickets.py

## Scope in / Scope out
Scope in:
- `clutch/tickets.py`: move `Boundary contract` from `OPTIONAL_SECTIONS` to `REQUIRED_SECTIONS`, keeping the closed `SECTIONS` order consistent with the skeleton's section order. The missing-section finding applies only where the existing shape check applies (evidence on, state not `merged` or `rejected`). Settled and rejected tickets are never given a missing-section finding. Add every import the change forces.
- `clutch/docs/host-authoring.md`: in the `Boundary contract` bullet, drop the words `optional until a later ticket requires it` and say the section is required for every non-settled ticket. Edit nothing else.
- Existing tests whose ticket text lacks the section or whose set pin flips: `tests/integration/test_closed_sets.py` (the `OPTIONAL_SECTIONS`, `REQUIRED_SECTIONS` and `SECTIONS` pins), and every test, regress script, harness module or fixture script that builds a non-settled ticket without the section. Grep `tests/` and `hosts/fixture/` for `Definition of rejected` and add a minimal `## Boundary contract` with `none` and a `- reason:` bullet to each hit that is linted as non-settled.
- New tests go in the new file `tests/unit/test_boundary_contract_required.py`, run through `tmp_path` or fake tickets; they run the changed lines in `clutch/tickets.py`.

Scope out: do not edit any file under `tickets/`; no new shape rules, path or symbol checks; no spec, `CORE_TEMPLATE`, roadmap or plan edits; no new test in the hot test files unless a flipped assertion forces the edit.

## Scope fence
- clutch/tickets.py
- clutch/docs/host-authoring.md
- tests/unit/test_boundary_contract_required.py
- tests/unit
- tests/integration
- tests/harness
- tests/regress_lint_carries.py
- tests/regress_new_skeleton_draft.py
- tests/regress_requisition_prior_review.py
- tests/regress_review_intakes_own_stem.py
- tests/regress_requisition_events_owner_stem.py
- tests/regress_requisition_stage_events.py
- hosts/fixture/scripts.json

## Acceptance criteria
1. `./dev.py test tests/unit/test_boundary_contract_required.py` passes and asserts a draft ticket with no `## Boundary contract` returns a finding naming the fix, not an empty list.
2. The same file asserts the same ticket text journaled settled, and the same text with state `merged` or `rejected`, returns no boundary finding, not a finding.
3. The same file asserts a draft ticket with a valid `none` section plus `- reason:` returns no boundary finding, and a draft ticket with a malformed section still returns the shape finding.
4. `./dev.py test tests/integration/test_closed_sets.py` passes with `Boundary contract` in `tickets.REQUIRED_SECTIONS`, not in `OPTIONAL_SECTIONS`.
5. `uv run clutch ticket lint` exits 0 on the repo, so no open ticket gains a missing-section finding once the two open tickets carry the section.
6. `./dev.py test tests/unit/test_host_authoring.py tests/unit/test_lint_guide_parity.py` passes and `clutch/docs/host-authoring.md` no longer says the section is optional, checked by `./dev.py test` on those files.
7. `./dev.py test` passes in full.

## Verification
```
./dev.py test tests/unit/test_boundary_contract_required.py tests/integration/test_closed_sets.py tests/unit/test_host_authoring.py tests/unit/test_lint_guide_parity.py
uv run clutch ticket lint
./dev.py test
```

## Definition of rejected
The branch is rejected if any file under `tickets/` is edited, if a settled or rejected ticket starts failing lint, if the shape check gains path or symbol resolution, if the exemption is dropped, or if a standing test pins guide or plan text.

## Time budget
- expected: 20m
- stuck: 40m
