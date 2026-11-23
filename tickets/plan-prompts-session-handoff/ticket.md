---
state: draft
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Context
- tests/integration/test_ask_plan_read_queue.py

## On-demand
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- docs/how-clutch-works.md

## Goal / Why
`clutch prompt plan-ticket-drain` and `clutch prompt plan-ticket-serve` run one supervising session for as long as the plan takes. Measured from local transcripts since the 2026-11-18 reset, five such sessions lasted 8 to 28 hours each, and 44% to 80% of their requests started from a monitor line. Each wake re-reads the whole accumulated context, so these sessions are most of the VS Code usage: 794M of 2,230M cache-read tokens came from monitor-started turns.

After this ticket both prompts make the operator end its own session at a fixed count and hand off through the log it already keeps, and stop it building its own polling loops:

- After 20 merged tickets since the session began (counted from `clutch view status`, never wall-clock time), finish the current tick, write a HANDOFF section at the end of its log, report, and stop. The report ends with the one line the owner pastes into a new session: the same `clutch prompt` verb and "Read the HANDOFF section at the end of the log first".
- The HANDOFF section holds only what the next session cannot re-derive: decisions made and why, open threads, verdicts about to be executed, and instructions the owner gave in chat that no ticket holds. It never copies ticket stems, statuses, order or engine state; the next session reads those from `clutch view snapshot` and `clutch view status`, as the existing tick rule requires.
- A starting session that finds a HANDOFF section reads it before the before-start checks finish, then reads the live queue.
- Arm `clutch view events` under the monitor facility once, with the longest timeout the facility allows, and re-arm only when it expires. Never write a loop that polls `clutch view status`, `clutch prompt drafts` or a process list on a timer: it wakes the operator on every change of its own digest, which measured 16 hand-built loops across five sessions.

This is the cause fix for session-length cost. The repeated gate lines are `events-attention-filter`.

## Boundary contract
### Supervisor prompt session lifecycle
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/plan-ticket-serve.md
- consumers: operators running `clutch prompt plan-ticket-drain` or `clutch prompt plan-ticket-serve`
- observable change: both rendered prompts carry the stop count, the HANDOFF rule, the start-of-session read and the monitor rule above, with identical wording in both
- compatibility: the existing log rule, the tick rule, the stop condition and the `drain-loop` render are unchanged; only the "Keep a log" bullet and the monitor sentence in the tick bullet change
- acceptance: an integration test renders both prompts and asserts each required phrase and its place relative to the tick rule
- tests: `tests/integration/test_ask_plan_handoff.py`
- post-merge source of truth: clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/plan-ticket-serve.md

## Scope in / Scope out
Scope in:
- Edit the "Keep a log the next tick reads" bullet in both specs to add the handoff rule, and the "Run `clutch view events` under your agent's monitor facility" sentence in the tick bullet to add the arm-once rule. Keep the two specs' shared lines identical.
- Add `tests/integration/test_ask_plan_handoff.py`, parametrized over `plan-ticket-drain` and `plan-ticket-serve`, pinning the phrases: `20 merged tickets`, `HANDOFF`, `never wall-clock`, `clutch view snapshot`, `never copies`, `longest timeout`, and `never write a loop`.
- In `docs/how-clutch-works.md`, update only the `prompt plan-ticket-serve` and `prompt plan-ticket-drain` rows of the verb table to say the operator stops for a handoff after 20 merged tickets.

Scope out:
- No clutch verb that relaunches the supervisor, no change to the events stream code or `clutch view events`, no change to the drain-loop prompt spec, and no setting of the operator's own model (the owner picks it at launch).
- Rule home: these are shipped process prompts, so the rules live in the specs and reach every host through `clutch prompt`. No agent rule file changes.

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- tests/integration/test_ask_plan_handoff.py
- docs/how-clutch-works.md

## Acceptance criteria
1. Both rendered prompts contain `20 merged tickets`, `HANDOFF` and `never wall-clock`, and the handoff bullet follows the first tick bullet's "Supervising" rule; checked by `./dev.py test tests/integration/test_ask_plan_handoff.py`.
2. Both rendered prompts say the HANDOFF section never copies ticket stems or queue state and name `clutch view snapshot` and `clutch view status` as where the next session reads them, not "copy the queue"; checked by `./dev.py test tests/integration/test_ask_plan_handoff.py`.
3. Both rendered prompts say to arm `clutch view events` once with the longest timeout the facility allows and never write a loop polling status on a timer; checked by `./dev.py test tests/integration/test_ask_plan_handoff.py`.
4. The two specs' handoff and monitor wording is identical in both rendered prompts; checked by `./dev.py test tests/integration/test_ask_plan_handoff.py`.
5. The existing plan-prompt tests still pass unchanged; checked by `./dev.py test tests/unit/test_ask_plan_drain.py tests/unit/test_ask_plan_serve.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_conduct_covered.py`.

## Verification
```
./dev.py test tests/integration/test_ask_plan_handoff.py tests/unit/test_ask_plan_drain.py tests/unit/test_ask_plan_serve.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_conduct_covered.py
```

## Definition of rejected
The branch adds a clutch verb or flag, edits the drain-loop prompt spec or the events stream code, states the stop trigger as elapsed time, lets the HANDOFF section carry ticket stems or queue state, or words the two prompts differently.

## Time budget
- expected: 15m
- stuck: 30m
