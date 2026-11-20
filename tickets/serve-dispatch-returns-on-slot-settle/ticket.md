---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
none

## Context
- clutch/scheduler.py::Scheduler.dispatch_next
- tests/fakes.py::turn
- docs/parallel-tickets-plan.md#4. Several runs at once in

## Goal / Why
Prepares roadmap row 166 (`serve-dispatch-returns-on-slot`). Today `Scheduler.dispatch_next` in `clutch/scheduler.py` awaits the whole run, so tests write `await scheduler.dispatch_next()` and then assert on the finished run. Row 166 makes `dispatch_next` return once the ticket is handed to admission, so every such site would then read a run that has not finished. After this ticket those sites go through one new helper, `dispatch_settled(scheduler)` in `tests/dispatch_settle.py`: it awaits `scheduler.dispatch_next()`, then yields (`tests/fakes.py::turn`) until the dispatched stem has left `scheduler.flying`, and returns the ticket. Against today's scheduler `flying` is already clear when `dispatch_next` returns, so the helper changes nothing; against the row 166 scheduler it restores "the run has finished". Landing the mechanical rewrite first keeps the row 166 diff to the behavior change and the few tests that pin the old contract.

Only plain awaited calls are rewritten. A call inside `asyncio.create_task(...)`, a test that wraps or replaces `dispatch_next`, and any test that pins the old "second call waits for the first run" contract stay as they are for row 166.

## Boundary contract
none
- reason: tests encoding an existing contract. The helper is a new test-only module; no file under `clutch/` changes, and every converted test asserts what it asserted before.

## Scope in / Scope out
Scope in:
- Create `tests/dispatch_settle.py` with `async def dispatch_settled(scheduler)`: `ticket = await scheduler.dispatch_next()`; while `ticket is not None and ticket.stem in scheduler.flying`, `await turn()`; return `ticket`. It reads `scheduler.dispatch_next` at call time, so a test that monkeypatches that attribute still works through it.
- In each fenced existing test or harness file, replace every plain `await <scheduler>.dispatch_next()` (including `while await ... is not None` loops) with `dispatch_settled(<scheduler>)`, and add the import. Nothing else in those files changes. The sites are in `tests/harness/reliability_battery.py` (`_Member.dispatch` and the drought check in `exercise`), `tests/unit/test_drain_eligible.py`, `tests/unit/test_admission_running_set.py`, `tests/unit/test_scheduler_write_queue_seams.py`, `tests/unit/test_scheduler_parallel_fill.py`, `tests/integration/test_daemon_core_queue_seams.py`, `tests/integration/test_storm_notification_activation.py`, `tests/integration/test_requisition_gate.py`, `tests/integration/test_provider_cooldown_failover.py`, `tests/integration/test_daemon_composition.py` and `tests/integration/test_scheduler.py`.
- Add `tests/unit/test_dispatch_settle.py`.

Scope out:
- Every `asyncio.create_task(<scheduler>.dispatch_next())` site, the `delayed_dispatch` wrapper in `tests/integration/test_reliability_battery.py` and the `dispatch` task in `tests/harness/reliability_battery.py`: left for `serve-dispatch-returns-on-slot`.
- `tests/regress_serve_reoffer_dispatch.py`: it only reads the returned ticket's stem and runs as a script, so it needs no conversion.
- `clutch/` code and docs: unchanged.

## Scope fence
- tests/dispatch_settle.py
- tests/unit/test_dispatch_settle.py
- tests/harness/reliability_battery.py
- tests/unit/test_drain_eligible.py
- tests/unit/test_admission_running_set.py
- tests/unit/test_scheduler_write_queue_seams.py
- tests/unit/test_scheduler_parallel_fill.py
- tests/integration/test_daemon_core_queue_seams.py
- tests/integration/test_storm_notification_activation.py
- tests/integration/test_requisition_gate.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_scheduler.py

## Acceptance criteria
1. `dispatch_settled` returns the ticket `dispatch_next` returned, and returns `None` without waiting when `dispatch_next` returns `None`, checked by `./dev.py test tests/unit/test_dispatch_settle.py`.
2. `dispatch_settled` does not return while the dispatched stem is still in `scheduler.flying`, so a scheduler whose `flying` entry clears only after several turns makes the helper return after that clearing, not on the first return of `dispatch_next`, checked by `./dev.py test tests/unit/test_dispatch_settle.py`.
3. `dispatch_settled` calls the scheduler's current `dispatch_next` attribute, so a test that monkeypatches it is still observed, checked by `./dev.py test tests/unit/test_dispatch_settle.py`.
4. Every converted file still passes against today's scheduler with its assertions unchanged, checked by `./dev.py test tests/unit tests/integration/test_scheduler.py tests/integration/test_daemon_composition.py tests/integration/test_provider_cooldown_failover.py tests/integration/test_requisition_gate.py tests/integration/test_storm_notification_activation.py tests/integration/test_daemon_core_queue_seams.py tests/integration/test_reliability_battery.py`.

## Verification
```
./dev.py test tests/unit tests/integration/test_scheduler.py tests/integration/test_daemon_composition.py tests/integration/test_provider_cooldown_failover.py tests/integration/test_requisition_gate.py tests/integration/test_storm_notification_activation.py tests/integration/test_daemon_core_queue_seams.py tests/integration/test_reliability_battery.py
```

## Definition of rejected
A converted test whose assertion changed, any change under `clutch/`, or a helper that returns before the dispatched stem has left `scheduler.flying`.

## Time budget
- expected: 30m
- stuck: 60m
