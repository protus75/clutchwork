---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/requisition.py::review_ticket
- clutch/requisition.py::test_sources
- clutch/policy.py::_path_overlap
- clutch/rework.py::settled_dependencies
- tests/unit/test_requisition_dependents.py
- tests/unit/test_requisition_stage_events.py

## On-demand
- clutch/specs/requisition_review.md
- tests/integration/test_requisition.py

## Goal / Why
Requisition review today judges a ticket only against merged code. It never sees other confirmed tickets that have not merged yet. On 2026-11-16 `upstream-issue-verb` and `gemini-provider` each passed review with new tests built on `SimpleNamespace` fake configs that lack the `release` attribute. The confirmed, unmerged `release-publish` makes `Redactor.from_config` and `child_env` read that attribute. Whichever ticket merged first would have broken the other's Verification in a file outside its fence. A separate manual audit caught it. If such a conflict reaches a run, Implement hits red tests outside its fence, returns `premise_failed`, and the ticket lands in the Reject queue or a requisition park.

After this change the requisition review prompt carries a `sibling_tickets` data block. It lists each other confirmed, unmerged ticket whose `## Scope fence` overlaps this ticket's fence. Each entry shows that ticket's stem, the shared fence paths, and its `## Scope in / Scope out` text. The spec tells the reviewer to snag a criterion or new test that a listed sibling's stated change would break, in either merge order.

The block is bounded because nearly every ticket fences `clutch/__main__.py` and `docs/how-clutch-works.md`. It carries Scope in and the shared paths only, never whole ticket bodies. It lists at most 5 siblings, those sharing the most fence paths first and ties by stem. Each Scope in is cut to 1500 characters. The spec limits the snag to what a sibling's stated change would actually break, never to a shared file alone.

This is the cause fix for the sibling-ticket blindness gap. The instance fixes were applied by hand in the two tickets' audit edits.

## Scope in / Scope out
Scope in:
- `clutch/requisition.py`: add a pure function `sibling_tickets_block(own, others, settled)`. `own` is the reviewed `Ticket`, `others` are parsed `Ticket`s, and `settled` is a set of stems. It returns the block text, or `none` when nothing qualifies. A sibling qualifies when its `frontmatter.state` is `confirmed`, its stem is not `own.stem`, its stem is not in `settled`, its stem is not in `own`'s parsed `## Depends on` stems, `own.stem` is not in the sibling's parsed `## Depends on` stems, and at least one of its fence paths overlaps one of `own.scope_fence` under the `clutch/policy.py::_path_overlap` rule. Import `_path_overlap` rather than copying it.
- `review_ticket` loads the other tickets by parsing each `tickets/*/ticket.md` under `repo`, skipping any that does not parse. It takes `settled` from `settled_dependencies(driver.journal.read())` and passes the block as the new `sibling_tickets` input to `render`. No caller of `review_ticket` changes signature.
- `clutch/specs/requisition_review.md`: add the `sibling_tickets` data block under Inputs, placed after `coverage_dependents` and before `prior_review`, and one Task bullet. The bullet says: when a listed sibling's Scope in changes an interface, fixture shape, attribute, or behavior that a criterion, `## Verification` line, or test this ticket adds depends on, raise a `snag` naming the sibling stem, the changed interface, and the criterion or test it would break, whichever ticket merges first. A shared file alone, or a sibling change the ticket's tests do not touch, is not a hit. Bump `version` to the next minor above the version on main.
- `tests/unit/test_specs.py`: update the existing requisition_review version pin to the bumped version. That is the one expectation that may change there.
- `tests/integration/test_requisition.py`: the exact-equality assertion on the spec inputs (the tuple near line 116) gains `sibling_tickets` after `coverage_dependents` and before `prior_review`. That is the only expectation that changes there.
- `tests/unit/test_requisition_dependents.py` and `tests/unit/test_requisition_stage_events.py`: fake updates only. Give each fake driver `journal=SimpleNamespace(read=lambda: [])`, and give each in-memory repo (`MemoryPath`) a `glob` that returns no tickets. Every existing assertion stays unchanged.
- Documentation: if `docs/how-clutch-works.md` has a section describing requisition review inputs, add the `sibling_tickets` block there and edit nothing else.

Scope out: no change to the other callers of `review_ticket`, to `clutch lint`, to the Author spec or the authoring guide, or to how tickets are parked or rejected. The block is advisory input to the reviewer, not a mechanical gate. A sibling that is merged or in a `Depends on` relationship with this ticket in either direction is never listed. New unit tests read no repo files; the phrase test and the real-spec render live in a new integration file.

## Scope fence
- clutch/requisition.py
- clutch/specs/requisition_review.md
- tests/unit/test_specs.py
- tests/unit/test_requisition_sibling_tickets.py
- tests/unit/test_requisition_dependents.py
- tests/unit/test_requisition_stage_events.py
- tests/integration/test_requisition.py
- tests/integration/test_spec_sibling_tickets.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `sibling_tickets_block` for a confirmed sibling that shares one fence path and is not settled returns text containing the sibling's stem, the shared path, and its Scope in text, tested in `tests/unit/test_requisition_sibling_tickets.py`. The test fails if the block returns `none` for this case.
2. In `tests/unit/test_requisition_sibling_tickets.py`, each of these siblings produces `none`: one whose state is `draft`, one whose stem is in `settled`, one with no overlapping fence path, one whose stem is in `own`'s `## Depends on`, and one that lists `own.stem` in its own `## Depends on`. The test checks all five, and a wrong implementation that lists any of them fails it.
3. With 7 qualifying siblings, `sibling_tickets_block` lists exactly 5 stems, those sharing the most paths first with ties by stem. A Scope in of 4000 characters appears cut to 1500 characters. The test in `tests/unit/test_requisition_sibling_tickets.py` rules out listing all 7 and an untruncated Scope in.
4. The block never contains a sibling's `## Acceptance criteria` or `## Verification` text. The test in `tests/unit/test_requisition_sibling_tickets.py` asserts those strings from the sibling are absent, not just that Scope in is present.
5. `tests/unit/test_requisition_sibling_tickets.py` drives `review_ticket` through fakes, as `tests/unit/test_requisition_dependents.py` does: it monkeypatches `load_spec`, `render` (capturing the values), `review_target` and `_base_render`, uses an in-memory repo whose `glob` yields `tickets/*/ticket.md` fixtures, and uses a driver whose `journal.read()` returns `[]`. With two confirmed tickets that overlap, `values['sibling_tickets']` contains the other ticket's stem. With a lone ticket, `values['sibling_tickets']` is `none`, not an empty string.
6. `tests/integration/test_spec_sibling_tickets.py` reads `clutch/specs/requisition_review.md` and asserts it has the `sibling_tickets` placeholder, a Task bullet naming sibling stem, changed interface, and the broken criterion or test, and the statement that a shared file alone is not a hit. It also renders the real spec for a fixture repo with two overlapping confirmed tickets and asserts the other stem is in the prompt. The spec `version` is the next minor above the version on main, and `tests/unit/test_specs.py` pins it.
7. In `tests/unit/test_requisition_sibling_tickets.py`, `review_ticket` for an in-memory repo whose `tickets/` holds an unparseable `ticket.md` text still reviews without raising, and the other fixture tickets still appear. The test rules out an exception.
8. `tests/integration/test_requisition.py` asserts the spec inputs equal `("ticket", "context", "render", "coverage_dependents", "sibling_tickets", "prior_review", "retry_findings")`, and `tests/unit/test_requisition_dependents.py` and `tests/unit/test_requisition_stage_events.py` pass with every existing assertion unchanged.

## Verification
```
./dev.py test tests/unit/test_requisition_sibling_tickets.py tests/unit/test_specs.py tests/unit/test_requisition_dependents.py tests/unit/test_requisition_stage_events.py tests/integration/test_requisition.py tests/integration/test_spec_sibling_tickets.py
```

## Definition of rejected
The branch lists whole sibling ticket bodies, or lists siblings on a shared file with no cap. It adds a mechanical gate that parks or snags a ticket without the reviewer. It changes a `review_ticket` caller signature. It copies `_path_overlap` instead of importing it. It edits any assertion in the three existing test files beyond the ones Scope in names.

## Time budget
- expected: 45m
- stuck: 90m
