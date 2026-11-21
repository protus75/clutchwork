---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
none

## Context
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_drain_loop.py
- tests/unit/test_ask_plan_drain.py

## On-demand
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- clutch/specs/ask/drain-loop.md

## Goal / Why
An operator running `clutch prompt plan-ticket-drain`, `clutch prompt plan-ticket-serve` or `clutch prompt drain-loop` states the queue from memory and from the last command it happened to run. On 2026-11-21 an operator reported "the queue is empty" while five P0 tickets the owner had added from another chat were confirmed, one running and four waiting, and planned its own work around the stale picture. The owner asked for the prompts to read the queue with a command every time, not from memory.

`clutch view status` shows what is merged, in flight, blocked and in the Reject queue, but not the tickets that are waiting. The waiting tickets are the `status` field of each row of `clutch view snapshot` (`ready`, `after <stems>`, `running`, `draft`, `invalid`). After this ticket each of the three rendered prompts requires the operator to read the queue with `clutch view status` and `clutch view snapshot` at the start of every tick and again immediately before it confirms or rejects a ticket, authors a row, starts or stops an engine, or reports queue or engine state, and to take every ticket stem, state and order it states from that output, never from earlier in the conversation, a log it kept, or its own recollection. Tickets it did not author are expected to appear in the queue (the owner adds them from other chats); the operator treats them as work in flight, counts them toward the window of confirmed, unrun tickets, and does not comment on them.

## Boundary contract
### Operator prompt wording
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md, clutch/specs/ask/plan-ticket-serve.md and clutch/specs/ask/drain-loop.md
- consumers: `clutch prompt plan-ticket-drain`, `clutch prompt plan-ticket-serve`, `clutch prompt drain-loop` and the operator models that follow them
- observable change: each of the three specs carries one rule naming `clutch view status` and `clutch view snapshot`, when to run them, and that queue state is never taken from memory
- compatibility: every other line of the three specs stays as it is; the existing pinned phrases and the order `conduct files` before `clutch host doctor` before `clutch provider probe` before `clutch prompt drain-loop` hold; both verbs already exist, so `test_prompts_name_only_existing_verbs` holds
- acceptance: criteria 1 to 3
- tests: tests/integration/test_ask_plan_read_queue.py
- post-merge source of truth: the three spec files

## Scope in / Scope out
Scope in, in each of the three specs, one added rule in the section that already governs each tick (`Supervising` in the two plan prompts; step 1 `Observe` in `drain-loop.md`):
- At the start of every tick, and again immediately before confirming or rejecting a ticket, authoring a row, starting or stopping an engine, or reporting queue or engine state, run `clutch view status` and `clutch view snapshot`, and read the waiting tickets from the `status` of each snapshot row (`ready`, `after <stems>`, `running`, `draft`, `invalid`). Take every ticket stem, state and order you state from that output; never from earlier in the conversation, a note you kept, or memory. A statement about the queue or an engine carries the time of the command it came from.
- A ticket in the queue that you did not author (the owner adds tickets from other chats) is work in flight: count it toward the window of confirmed, unrun tickets and plan around it; do not remark on it.
- Nothing else in the three specs changes. In `drain-loop.md` step 1 the existing `clutch view status` mention stays and the rule is added to it.
- The new test file `tests/integration/test_ask_plan_read_queue.py` starts with a `clutch:meta` header created by `uv run clutch meta refresh tests/integration/test_ask_plan_read_queue.py` with only the `purpose` line edited by hand.

Scope out: the host's conduct files, `CORE_TEMPLATE`, any other prompt, any new verb or flag (`clutch view snapshot` and `clutch view status` exist), and any change to what the verbs print.

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- clutch/specs/ask/drain-loop.md
- tests/integration/test_ask_plan_read_queue.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_ask_plan_read_queue.py` renders each of `plan-ticket-drain`, `plan-ticket-serve` and `drain-loop` through `ask.render` and asserts each contains `clutch view snapshot`, `clutch view status` and the phrase `never from memory`, and that the rule precedes the first mention of authoring or confirming in the tick section it joins; a prompt without `clutch view snapshot` fails it.
2. The same test asserts each rendered prompt tells the operator that a ticket it did not author is work in flight to count toward the window, and that a statement about the queue carries the time of the command (`time of the command`).
3. `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_drain_loop.py tests/unit/test_ask_plan_drain.py` passes unedited, so every existing pinned phrase and the ordering test still hold.
4. `uv run clutch meta check tests/integration/test_ask_plan_read_queue.py` exits 0 (only the file this ticket creates).

## Verification
```
./dev.py test tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_drain_loop.py tests/unit/test_ask_plan_drain.py
```

## Definition of rejected
A prompt that still lets the operator state queue contents from memory; a change to any other line of the three specs; a new verb, flag or document; a change to an existing pinned phrase or to the order of the conduct-check, doctor, probe and drain-loop mentions; a test added to an existing test file.

## Time budget
- expected: 12m
- stuck: 24m
