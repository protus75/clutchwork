---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- serve-parallel-dispatch-r2

## Context
- clutch/mergequeue.py::MergeQueue.offer
- clutch/stages.py::run_host_command

## On-demand
- clutch/runner.py
- clutch/drain.py
- clutch/serve.py
- clutch/merge.py
- tests/integration/test_serve_admission.py
- tests/integration/test_daemon_soak_runner.py

## Goal / Why
Three things are true after this ticket that are not true now, and each removes a single-flight assumption so several serve runs can coexist (docs/parallel-tickets-plan.md section 4):

1. One writer of the `running` state transition. Today `runner.run_ticket`, the serve `dispatch` closure in `clutch/serve.py`, and `_Drain._run_one` in `clutch/drain.py` each append the `STATE_TRANSITION` event with `{"to": "running", "ticket_sha": sha}` themselves. They call a new `runner.mark_running(journal, stem, sha)` instead.
2. `MergeQueue.offer` takes the run's `StageContext` as `ctx` and records it in `contexts[stem]`. `AdmissionBoundary.__call__` passes its `ctx` to `offer` and stops assigning `self.queue.ctx`. Today it overwrites the shared `queue.ctx` per offer, which is only correct when one run is in flight.
3. `stages.run_host_command` runs under one engine-wide `asyncio.Semaphore(1)`, so two Check or merge-tier suites never run at once (plan section 4, host command lock).

## Boundary contract
### Running transition writer
- disposition: create
- owner: clutch/runner.py
- consumers: runner.run_ticket, the serve dispatch closure in clutch/serve.py, `_Drain._run_one` in clutch/drain.py
- observable change: the journal receives the same `state_transition` event body (`to: running`, `ticket_sha`) from one function instead of three inline appends; no event shape change
- compatibility: event type, body, ticket field and journal fold are unchanged; serve's current `key=None` append is preserved by the helper so serve's event key does not change
- acceptance: all three call sites call `mark_running`; no other `"to": "running"` append remains in clutch/
- tests: new unit test for `mark_running` event body and key, plus the existing drain, runner and serve suites
- post-merge source of truth: clutch/runner.py::mark_running
- closest existing: the three inline appends in clutch/runner.py, clutch/serve.py and clutch/drain.py, which are the consolidated duplicates
- earning reason: consolidation of three evidenced duplicates (roadmap rows 7 and 9 in the parallel plan) with three production consumers

### MergeQueue.offer context
- disposition: extend
- owner: clutch/mergequeue.py
- consumers: AdmissionBoundary in clutch/merge.py, serve reconstruct_admissions in clutch/serve.py, tests that call `queue.offer`
- observable change: `offer(ticket, *, attempt, ctx=None)` records `contexts[stem] = ctx` when given, else the queue's own `ctx`; AdmissionBoundary passes `ctx` and no longer sets `queue.ctx`
- compatibility: callers that omit `ctx` (reconstruct_admissions, which offers on the writer's own queue, and tests that build a queue directly) keep the queue's constructor context; `process()` still sets `queue.ctx` from `contexts[stem]` while admitting
- acceptance: two offers with different `ctx` values keep each stem's own context; the boundary no longer mutates `queue.ctx` before process
- tests: new unit test for offer context recording; offer stand-ins in the two named integration files accept `ctx`
- post-merge source of truth: clutch/mergequeue.py::MergeQueue.offer

### Host command lock
- disposition: extend
- owner: clutch/stages.py
- consumers: Check, both merge tiers, every caller of `run_host_command`
- observable change: concurrent `run_host_command` calls execute one at a time; a single call behaves as before, including timeout and not-found findings
- compatibility: signature, return value and findings are unchanged; the lock is held only around the exec call, not model calls
- acceptance: two concurrent calls never overlap in the exec seam
- tests: new unit test with a fake exec seam recording overlap; it monkeypatches `stages.HOST_COMMAND_LOCK` with a fresh `asyncio.Semaphore(1)` created inside the test's own running loop, so the module-level semaphore is never bound to a test loop and no later test in another `asyncio.run` loop can hit a different-event-loop error
- post-merge source of truth: clutch/stages.py::HOST_COMMAND_LOCK

## Scope in / Scope out
Scope in:
- Add `runner.mark_running(journal, stem, sha)`; replace the inline appends in `runner.run_ticket`, the serve dispatch closure, and `_Drain._run_one`.
- Add the `ctx` keyword to `MergeQueue.offer`; pass it from `AdmissionBoundary.__call__` and delete the `self.queue.ctx = ctx` assignment and its single-flight comment in clutch/merge.py.
- Update the offer stand-ins in tests/integration/test_serve_admission.py and tests/integration/test_daemon_soak_runner.py to accept `ctx` (keyword) and read the context from it where they read `queue.ctx` today.
- Add one module-level `HOST_COMMAND_LOCK = asyncio.Semaphore(1)` in clutch/stages.py; `run_host_command` looks it up as a module attribute at call time and holds it around the exec call only, so tests can replace it with `monkeypatch.setattr`. tests/unit/test_stages_host_lock.py must replace it with a fresh `asyncio.Semaphore(1)` created inside the test's running loop and never contend on the module-level original.
- docs/how-clutch-works.md: update only a sentence made false by this change (single `queue.ctx`, or host command concurrency); if none is false, leave it unchanged.

Scope out: the scheduler or admission run set, `eligible()`, overlap and chain ordering, config, conflict steps, the `tests/integration/test_mergequeue.py` and `test_daemon_composition.py` files, and any test that calls `queue.offer` without `ctx`.

## Scope fence
- clutch/runner.py
- clutch/drain.py
- clutch/serve.py
- clutch/merge.py
- clutch/mergequeue.py
- clutch/stages.py
- tests/integration/test_serve_admission.py
- tests/integration/test_daemon_soak_runner.py
- tests/unit/test_runner_mark_running.py
- tests/unit/test_mergequeue_offer_ctx.py
- tests/unit/test_stages_host_lock.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_runner_mark_running.py` passes: `mark_running(journal, 'a', 'sha1')` appends exactly one `state_transition` event for ticket `a` with body `{"to": "running", "ticket_sha": "sha1"}` and `key` None, not zero events or a different body.
2. `grep -rn '"to": "running"' clutch/` matches only the body inside `mark_running` in clutch/runner.py, not clutch/serve.py or clutch/drain.py.
3. `./dev.py test tests/unit/test_mergequeue_offer_ctx.py` passes: after `offer(t1, attempt=0, ctx=c1)` and `offer(t2, attempt=0, ctx=c2)`, `contexts['t1'] is c1` and `contexts['t2'] is c2`, not both the queue's constructor context; `offer(t3, attempt=0)` records the queue's own `ctx`.
4. `grep -n 'queue.ctx = ' clutch/merge.py` prints nothing, and `./dev.py test tests/integration/test_serve_admission.py tests/integration/test_daemon_soak_runner.py` passes with their offer stand-ins taking `ctx`.
5. `./dev.py test tests/unit/test_stages_host_lock.py` passes: the test monkeypatches `stages.HOST_COMMAND_LOCK` with a fresh `asyncio.Semaphore(1)` created inside the test's running loop, two concurrent `run_host_command` calls against a fake exec seam never have more than one run in flight (max in-flight 1, not 2), and a single call returns the same `CommandResult` and `GateReport` as before; the test never contends on the original module-level semaphore, so it leaves no loop-bound state that fails a later test run under another `asyncio.run` loop.
6. `./dev.py test tests/integration/test_drain.py tests/integration/test_mergequeue.py tests/integration/test_merge.py tests/integration/test_hostfiles.py` passes unchanged, proving callers that omit `ctx` and assertions on `queue.ctx` after `process()` still hold.

## Verification
```
./dev.py test tests/unit/test_runner_mark_running.py tests/unit/test_mergequeue_offer_ctx.py tests/unit/test_stages_host_lock.py tests/integration/test_serve_admission.py tests/integration/test_daemon_soak_runner.py tests/integration/test_drain.py tests/integration/test_mergequeue.py tests/integration/test_merge.py tests/integration/test_hostfiles.py
```

## Definition of rejected
The branch is rejected if any call site still appends its own `running` transition, if `AdmissionBoundary` still assigns `queue.ctx`, if the semaphore wraps more than the exec call in `run_host_command` (for example model calls), or if the diff adds scheduler, config, overlap or conflict-step changes.

## Time budget
- expected: 25m
- stuck: 50m
