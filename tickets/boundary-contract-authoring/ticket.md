---
state: draft
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- boundary-contract-trial

## Context
- docs/boundary-contract-plan.md#Chosen grammar
- clutch/tickets.py::REQUIRED_SECTIONS
- clutch/tickets.py::SECTIONS
- clutch/docs/host-authoring.md

## Goal / Why
Roadmap row 151, boundary plan Phase 1. Tickets can carry a `## Boundary contract` section, using the grammar the trial recorded under `## Trial results` > `### Chosen grammar` in `docs/boundary-contract-plan.md`. After this ticket: (1) `clutch ticket new` writes the section in every kind's skeleton. (2) Intake and lint check the shape of a non-settled ticket's section whenever it is present, and check only presence and basic shape. The section is optional in this ticket; making it required is a separate follow-up ticket, because no ticket can carry the section until the parser accepts it. (3) `clutch/docs/host-authoring.md` is the one home of the fields, examples, `none` reasons, `create` earning reasons and repair roads. (4) The Author spec and the requisition review spec tell the model what to write and what to judge: meaning, reuse of the canonical owner, and whether a `none` or `create` reason is true. (5) `CORE_TEMPLATE` carries one short behavioral paragraph within the managed-block budget. Without this, authors skip boundary declarations and parallel owners keep appearing.

Basic shape means: the section body is either `none` followed by a `- reason:` bullet with non-empty text, or one or more `### <boundary>` entries. Each entry has labeled bullets `disposition`, `owner`, `consumers`, `observable change`, `compatibility`, `acceptance`, `tests`, `post-merge source of truth`, and `disposition` is one of `reuse`, `extend`, `replace`, `create`. A `create` entry also has `closest existing` and `earning reason` bullets. Path resolution, symbols, applicability and truth of reasons are not checked by code.

Rule homes (CLAUDE.md section A): the short paragraph belongs in `CORE_TEMPLATE` in `clutch/hostfiles.py`, because every host follows it; fields and examples belong only in `clutch/docs/host-authoring.md`; grammar belongs only in `clutch/tickets.py`.

## Scope in / Scope out
Scope in:
- `clutch/tickets.py`: add `Boundary contract` to `OPTIONAL_SECTIONS`, add its placeholder to each kind skeleton, and add the shape check described above, applied whenever the section is present. A missing section is never a finding. Settled and rejected tickets are exempt from the shape check, exactly like the existing bug-evidence exemption. Each finding names its fix. Add every import the change forces.
- `clutch/docs/host-authoring.md`: add a `Boundary contract` bullet under `What each section is for` with the fields, closed dispositions, `create` earning reasons, `none` reasons, restoration/preservation claims for bug fixes and refactors, breaking-change migration facts, and the form shown in the plan's chosen grammar. Say the section is optional until a later ticket requires it. Update only the sections the change makes false.
- `clutch/specs/author.md` and `clutch/specs/requisition_review.md`: add the Author instruction and the review judgment. Bump each `version` to the next minor above the version on main, never a literal target. Fence the pin test.
- `clutch/hostfiles.py`: one short paragraph in `CORE_TEMPLATE`: declare the boundary disposition, reuse the canonical owner, justify a new owner, and never invent an undeclared boundary. Then refresh the managed blocks in `CLAUDE.md` and `AGENTS.md` through `uv run clutch host core`; never hand-edit them.
- Tests: every existing test whose ticket fixture, skeleton expectation, spec version pin or `CORE_TEMPLATE` size assertion flips because of the new optional section or skeleton; grep `tests/` for `Definition of rejected` and the changed names, and update only those. New tests go in the new file `tests/unit/test_boundary_contract_shape.py` (shape check, run through fake or `tmp_path` tickets) and, if a repo file or process is needed, `tests/integration/test_boundary_contract_authoring.py`. `tests/unit/test_hostfiles.py` runs the `CORE_TEMPLATE` lines. Use the existing fixture helpers; do not edit the hot integration test files unless a flipped assertion forces it.

Scope out: do not add `Boundary contract` to `REQUIRED_SECTIONS` and do not edit any file under `tickets/` (Implement cannot edit tickets, and open tickets may be queued or running). Adding the section to open tickets and making it required, with the settled/rejected exemption, are follow-up work filed after this merges. No Python symbol resolution, path-resolution lint, Context-owner checks or unfenced-consumer checks (those are `boundary-contract-lint`); no Implement or Review changes; no discovery catalog; no standing test pinning the exact text of any plan or guide; no edit to the frozen bootstrap plan or the boundary plan document.

## Scope fence
- clutch/tickets.py
- clutch/docs/host-authoring.md
- clutch/specs/author.md
- clutch/specs/requisition_review.md
- clutch/hostfiles.py
- CLAUDE.md
- AGENTS.md
- docs/how-clutch-works.md
- tests/unit/test_boundary_contract_shape.py
- tests/unit/test_hostfiles.py
- tests/unit
- tests/integration
- tests/regress_new_skeleton_draft.py
- tests/regress_requisition_prior_review.py
- tests/regress_review_intakes_own_stem.py
- tests/regress_requisition_events_owner_stem.py
- tests/regress_requisition_stage_events.py
- tests/harness
- hosts/fixture/scripts.json

## Acceptance criteria
1. `./dev.py test tests/unit/test_boundary_contract_shape.py` passes. It asserts a draft ticket with no `## Boundary contract` yields no boundary finding, not a finding, and a draft ticket with a malformed section yields a finding that names a fix.
2. The same test file asserts `none` with `- reason: <text>` passes, while `none` with no reason bullet or an empty reason returns a finding, not a pass.
3. The same test file asserts a full entry with every common field and disposition `extend` passes, an entry missing `owner` returns a finding naming `owner`, and disposition `maybe` returns a finding, not a pass.
4. The same test file asserts a `create` entry lacking `closest existing` or `earning reason` returns a finding, and a `reuse` entry lacking them passes.
5. `./dev.py test tests/unit/test_boundary_contract_shape.py` also asserts a ticket journaled settled or rejected that contains a malformed `## Boundary contract` section produces no boundary finding, and the same malformed section in a draft ticket produces one.
6. `clutch ticket new <stem> --kind feature`, `--kind bug` and `--kind chore` each write a skeleton containing `## Boundary contract`; asserted by an updated skeleton test run through `./dev.py test tests/unit tests/integration/test_tickets.py`, which returns the section for all three kinds, not only feature.
7. `uv run clutch ticket lint` with no stems exits 0 on the repo, so no existing ticket gains a boundary finding.
8. `clutch/docs/host-authoring.md` names `## Boundary contract` and the four dispositions, and `./dev.py test tests/unit/test_host_authoring.py tests/unit/test_lint_guide_parity.py` passes.
9. `./dev.py test tests/unit/test_specs.py tests/integration/test_requisition.py` passes with both spec `version` fields raised one minor above main, and `tests/unit/test_hostfiles.py` plus `tests/integration/test_hostfiles.py` pass, showing `CORE_TEMPLATE` plus the new paragraph still fits the managed-block budget (its budget test, not a raised limit).
10. `uv run clutch host core` run on this repo leaves `CLAUDE.md` and `AGENTS.md` with the same managed block text as `CORE_TEMPLATE`, checked by the existing core drift test in `tests/integration/test_hostfiles.py`.
11. `./dev.py test` passes in full.

## Verification
```
./dev.py test tests/unit/test_boundary_contract_shape.py tests/unit/test_host_authoring.py tests/unit/test_lint_guide_parity.py tests/unit/test_specs.py tests/unit/test_hostfiles.py tests/integration/test_hostfiles.py tests/integration/test_tickets.py tests/integration/test_requisition.py
uv run clutch ticket lint
./dev.py test
```

## Definition of rejected
The branch is rejected if the paragraph in `CORE_TEMPLATE` restates the fields, if the budget limit is raised instead of the paragraph shortened, if any lint check resolves paths or Python symbols, if `Boundary contract` is added to `REQUIRED_SECTIONS`, if any file under `tickets/` is edited, if a settled ticket starts failing lint, if the managed blocks are hand-edited rather than rendered, or if a standing test pins the plan text.

## Time budget
- expected: 30m
- stuck: 60m
