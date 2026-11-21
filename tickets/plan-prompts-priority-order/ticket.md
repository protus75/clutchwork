---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
none

## Context
- tests/integration/test_ask_plan_read_queue.py
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_drain_loop.py

## On-demand
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- clutch/specs/ask/drain-loop.md

## Goal / Why
An operator running `clutch prompt plan-ticket-drain`, `clutch prompt plan-ticket-serve` or `clutch prompt drain-loop` worked in the wrong order. On 2026-11-21 the owner's three P0 tickets (the requisition-review chain and the serve fixes) sat for about five hours, one held after `premise_failed` and one waiting on a stem that had been rejected and split, while the operator authored and confirmed P1 and lower roadmap tickets. Nothing in the three prompts says the queue is worked in priority order, and nothing says to repoint a ticket that depends on a stem that was rejected or replaced; the operator found the stale dependency only when the owner asked why the tickets were blocked.

After this ticket each of the three prompts requires the operator, at every tick and before it authors or confirms any ticket, to take the highest-priority ticket in the `clutch view snapshot` rows that is held, `invalid`, rejected, `retry pending` or waiting, and to repair or unblock it first; to author or confirm a lower-priority ticket only when no higher-priority ticket needs the operator. It also requires that when a ticket is rejected, split or replaced, the operator reads the snapshot in the same step for every ticket whose `## Depends on` names it and repoints each one to the replacement stems, because a ticket waiting on a stem that will never merge never runs.

## Boundary contract
### Operator prompt wording
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md, clutch/specs/ask/plan-ticket-serve.md and clutch/specs/ask/drain-loop.md
- consumers: `clutch prompt plan-ticket-drain`, `clutch prompt plan-ticket-serve`, `clutch prompt drain-loop` and the operator models that follow them
- observable change: each of the three specs carries two added rules, one on priority order and one on repointing a replaced dependency
- compatibility: every other line of the three specs stays as it is; the existing pinned phrases and the order `conduct files` before `clutch host doctor` before `clutch provider probe` before `clutch prompt drain-loop` hold; the new text names only existing verbs and snapshot fields, so `test_prompts_name_only_existing_verbs` holds
- acceptance: criteria 1 to 3
- tests: tests/integration/test_ask_plan_priority_order.py
- post-merge source of truth: the three spec files

## Scope in / Scope out
Scope in, in each of the three specs, two rules added in the section that already governs each tick (`Supervising` in the two plan prompts; step 1 `Observe` in `drain-loop.md`), next to the read-the-queue rule that `plan-prompts-read-queue-each-tick` added:
- Priority is the order. At every tick and immediately before authoring or confirming a ticket, take the highest-priority ticket (P0 before P1 before P2 before P3) among the snapshot rows whose `status` is `invalid`, `draft`, `retry pending`, `held`, `after <stems>` or a rejected stem in the Reject queue, and repair or unblock it first with the paved road (`clutch prompt drafts`, `clutch prompt diagnose`, a ticket edit a Recommendation names). Author or confirm a lower-priority ticket only when no higher-priority ticket needs the operator. A ticket the owner added from another chat counts at its own priority.
- Replaced stems. When a ticket is rejected, split or replaced, read `clutch view snapshot` in the same step and repoint the `## Depends on` of every ticket that names it to the replacement stems. A `## Depends on` stem that is rejected and will never merge blocks its dependents for good; repointing it is a ticket edit the operator makes without being asked.
- Nothing else in the three specs changes. In `drain-loop.md` the rules are added to step 1 beside the existing `clutch view status` mention.
- The new test file `tests/integration/test_ask_plan_priority_order.py` starts with a `clutch:meta` header created by `uv run clutch meta refresh tests/integration/test_ask_plan_priority_order.py` with only the `purpose` line edited by hand.

Scope out: the host's conduct files, `CORE_TEMPLATE`, any other prompt, any new verb or flag, and any change to what the verbs print.

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- clutch/specs/ask/drain-loop.md
- tests/integration/test_ask_plan_priority_order.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_ask_plan_priority_order.py` renders each of `plan-ticket-drain`, `plan-ticket-serve` and `drain-loop` through `ask.render` and asserts each contains the phrase `Priority is the order` and the phrase `Replaced stems`, and that each rule precedes the first mention of authoring or confirming in the tick section it joins; a prompt without both phrases fails it.
2. The same test asserts each rendered prompt names `clutch view snapshot` and `## Depends on` in the replaced-stems rule and names P0 before P3 in the priority rule.
3. `./dev.py test tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_drain_loop.py` passes unedited, so every existing pinned phrase and the ordering test still hold; `uv run clutch meta check tests/integration/test_ask_plan_priority_order.py` exits 0.

## Verification
```
./dev.py test tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_drain_loop.py
```

## Definition of rejected
A prompt that still lets the operator author or confirm lower-priority tickets while a higher-priority ticket is held or blocked; a change to any other line of the three specs; a new verb, flag or document; a change to an existing pinned phrase or to the order of the conduct-check, doctor, probe and drain-loop mentions; a test added to an existing test file.

## Time budget
- expected: 12m
- stuck: 24m
