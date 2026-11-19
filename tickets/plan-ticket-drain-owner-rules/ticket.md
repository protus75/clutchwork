---
state: rejected
source: human
priority: P0
kind: chore
---

## Depends on
- plan-ticket-drain-small-window

## Context
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_ask_plan_drain.py::test_plan_ticket_drain_prompt_content

## Goal / Why
The plan-ticket-drain operator prompt carries the owner's process rules from 2026-11-19, so the next run follows them without the owner repeating them. During that session the owner set four rules that the shipped prompt does not state:
- An authored ticket is never left as an unconfirmed draft. Unconfirmed drafts do nothing and hold the driver's author window.
- A roadmap ticket authored prematurely is retired, and its row is re-authored at the last minute.
- A ticket the owner asks for is delivered confirmed, not as a draft.
- Status is reported from live reads, never from memory.

The supervising session broke each of these:
- Stopped author agents left `route-kinds-filter-judge`, `route-kinds-filter-admission`, `driver-pass-overlaps-dispatch`, `main-checkout-write-gate` and `serve-driver-overlaps-dispatch` as unconfirmed drafts.
- It reported "nothing waiting" from a prior drain summary while confirmed tickets waited.
- It delivered an owner-requested engine fix as drafts.

The repo rule (CLAUDE.md section B) says owner changes to how a plan-ticket-drain run works go into this shipped prompt.

## Boundary contract
### Plan-ticket-drain operator rules
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md
- consumers: `clutch prompt plan-ticket-drain` (clutch/ask.py renders it verbatim), operator sessions that run it, tests/integration/test_ask_plan_drain.py
- observable change: the Authoring section requires every authored ticket to end the same tick confirmed or rejected (never a standing draft), retires a premature roadmap ticket with `clutch ticket reject --yes --reason` so the driver re-files the row at the last minute, and delivers owner-requested tickets confirmed; the Supervising section requires status claims to come from a read made that tick (`clutch view status`, `clutch roadmap status`, the journal), never from an earlier summary
- compatibility: every phrase and ordering the existing test pins stays; window and parallel-authoring rules are unchanged
- acceptance: the extended phrase test passes
- tests: tests/integration/test_ask_plan_drain.py
- post-merge source of truth: clutch/specs/ask/plan-ticket-drain.md

## Scope in / Scope out
Scope in, all in `clutch/specs/ask/plan-ticket-drain.md`:
- Authoring: add one bullet saying an authored ticket never stays an unconfirmed draft. Every ticket the operator or its agents author ends the same tick confirmed after lint and review approve, or rejected; a stopped or abandoned author agent's draft is rejected at once. A ticket the owner asks for is delivered confirmed.
- Authoring: add one bullet saying a roadmap ticket authored too early is retired with `clutch ticket reject --yes --reason` naming it premature, and the driver re-files the row when it is about to run.
- Supervising: add one bullet saying every status claim to the owner comes from a read made that tick (`clutch view status`, `clutch roadmap status` or the journal), never from an earlier summary or memory.
- `tests/integration/test_ask_plan_drain.py::test_plan_ticket_drain_prompt_content`: add the phrases `unconfirmed draft`, `premature` and `read made that tick` to the pinned list. Change nothing else in that file.

Scope out: the window size and parallel-authoring wording (owned by the tickets this depends on), the drain-loop, author and review ask prompts, and every other section.

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- tests/integration/test_ask_plan_drain.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_ask_plan_drain.py` passes with the pinned list extended by `unconfirmed draft`, `premature` and `read made that tick`, so a prompt missing any of the three rules fails it.
2. Every phrase and ordering the test pinned before this change still passes; checked by `./dev.py test tests/integration/test_ask_plan_drain.py tests/unit/test_ask_plan_drain.py tests/integration/test_ask.py`.

## Verification
```
./dev.py test tests/integration/test_ask_plan_drain.py tests/unit/test_ask_plan_drain.py tests/integration/test_ask.py
```

## Definition of rejected
Any of the three rules is missing from the rendered prompt, a section other than Authoring and Supervising changes, or a test other than `test_plan_ticket_drain_prompt_content` changes.

## Time budget
- expected: 10m
- stuck: 20m
