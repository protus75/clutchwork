---
state: rejected
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
---

## Depends on
- parallel-config
- fence-overlap
- chain-order
- active-slot-single-owner

## Context
- docs/parallel-tickets-plan.md#Target design
- clutch/scheduler.py
- clutch/daemon.py
- clutch/merge.py
- clutch/mergequeue.py
- clutch/serve.py
- clutch/drain.py
- clutch/runner.py
- clutch/stages.py::run_host_command

## Goal / Why
When `scheduler.parallel.enabled` is true, `serve` runs up to `scheduler.parallel.max_runs` tickets at once. Today a single `DaemonAdmission` slot and `scheduler.active` allow one run. When it is false, behavior is unchanged.

This ticket delivers plan ticket 6 (section 4 of docs/parallel-tickets-plan.md):
- `DaemonAdmission` owns `running: dict[str, Ticket]` and `max_runs` slots, and one `occupied()` method that says whether any run or task is present.
- One `eligible()` function in `clutch/drain.py` serves both `dispatch_next` and `_Drain._select`. It applies the `fences_overlap` check, the chain order and the starvation guard from the dependency tickets.
- One function, `runner.mark_running`, writes the `running` transition. `run_ticket`, the serve prepared dispatch and `_Drain._run_one` all call it.
- `AdmissionBoundary` stops overwriting `self.queue.ctx`.
- The idle and restart checks in `serve.py` and `__main__.py` call `DaemonAdmission.occupied()`.
- One engine-wide `asyncio.Semaphore(1)` wraps `stages.run_host_command`.

Without this, the config, overlap and ordering work cannot take effect.

## Boundary contract

### Admission running set
- disposition: replace
- owner: clutch/daemon.py (`DaemonAdmission`)
- consumers: clutch/serve.py, clutch/__main__.py, clutch/merge.py, clutch/scheduler.py, and the tests that read `admission.active` or `admission._slot`
- observable change: `active` and the single `_slot` lock become `running: dict[str, Ticket]` plus `max_runs` slots, and a new `occupied()` method returns true when the running set is non-empty or a task is present. `waiting_for_merge` releases only that run's slot. With parallel off, `max_runs` is 1 and the observable ordering and dispatch are unchanged.
- compatibility: no alias for `active` or `_slot`. Every call site and test assertion is updated in the same change.
- acceptance: with `max_runs=2` two non-overlapping tickets run concurrently, and with parallel off a second dispatch waits. `occupied()` is true while either of two runs is active.
- tests: new tests/unit/test_parallel_dispatch.py, plus the updated existing assertions
- post-merge source of truth: clutch/daemon.py

### Eligibility filter
- disposition: create
- owner: clutch/drain.py (`eligible()`)
- consumers: `scheduler.dispatch_next` and `_Drain._select`
- observable change: one function computes the dispatchable list in parallel order. The two copies of the eligibility computation are removed.
- compatibility: with parallel off the result and order are identical to today's.
- acceptance: a candidate that overlaps an in-flight fence is skipped, and one skipped `SKIP_LIMIT` times becomes a barrier.
- tests: tests/unit/test_parallel_dispatch.py and the existing scheduler and drain tests
- post-merge source of truth: clutch/drain.py
- closest existing: `scheduler.dispatch_next` and `_Drain._select`, which compute the same eligibility. Neither can be the shared home: `drain.py` owns the eligibility sort, and `scheduler.py` is a dispatch projection that must not import drain internals.
- earning reason: consolidation of two evidenced duplicate computations with two production consumers.

### Running transition writer
- disposition: create
- owner: clutch/runner.py (`mark_running(journal, stem, sha)`)
- consumers: `runner.run_ticket`, the serve prepared dispatch in clutch/serve.py, and `_Drain._run_one` in clutch/drain.py
- observable change: one function appends the `running` transition. The three inline appends are replaced by calls to it. The journal event body is unchanged.
- compatibility: journal records are byte-compatible with today's. serve and drain keep their own writer lock and do not call `run_ticket`.
- acceptance: exactly one `running` append is journaled per dispatch, through `mark_running`. The unit test checks `mark_running`, `run_ticket` and `_Drain._run_one` with fakes. A structural grep checks the serve path, and the existing serve integration tests observe the transition end to end.
- tests: tests/unit/test_parallel_dispatch.py, plus the existing fenced serve integration tests such as tests/integration/test_serve_admission.py
- post-merge source of truth: clutch/runner.py
- closest existing: the inline `running` appends in `run_ticket`, the serve prepared dispatch and `_Drain._run_one`. `run_ticket` cannot be reused because it is the `run <stem>` verb and takes its own lockfile, which serve and drain already hold.
- earning reason: consolidation of three evidenced duplicate writers with three production consumers.

### Merge queue run context
- disposition: extend
- owner: clutch/mergequeue.py (`MergeQueue.offer`)
- consumers: clutch/merge.py (`AdmissionBoundary.__call__`), clutch/serve.py, and the `.offer(` callers in tests
- observable change: `offer` takes the run's ctx explicitly and records it in `contexts[stem]`. `AdmissionBoundary` no longer assigns `self.queue.ctx`.
- compatibility: `process()` already reads `contexts`, so its behavior is preserved. Test callers pass the new argument.
- acceptance: two offered stems with different contexts each get their own context in `process()`.
- tests: tests/unit/test_parallel_dispatch.py and the updated mergequeue tests
- post-merge source of truth: clutch/mergequeue.py

### Host command lock
- disposition: create
- owner: clutch/stages.py (`run_host_command`)
- consumers: Check and both merge tiers, all of which call `run_host_command`
- observable change: one engine-wide `asyncio.Semaphore(1)` serializes host commands. Model calls are not wrapped.
- compatibility: with one run at a time the lock is never contended, so behavior is unchanged.
- acceptance: two concurrent `run_host_command` calls never overlap in execution.
- tests: tests/unit/test_parallel_dispatch.py
- post-merge source of truth: clutch/stages.py
- closest existing: `run_host_command` itself, which is the single runner but has no mutual exclusion; there is no existing lock to reuse.
- earning reason: an external-effect fake exercises it, and Check, the safety tier and the integration tier all consume it.

## Scope in / Scope out
In:
- Replace `DaemonAdmission.active` and `_slot` with `running` and `max_runs` slots. Keep no alias.
- Add `DaemonAdmission.occupied()`: true when the running set is non-empty or a task is present. This is the one home of the busy rule. The serve.py idle and restart checks (`restart.owned`, `upgrade_idle`, the merge writer prune) and the clutch/__main__.py `Restart(..., owned=...)` lambda call it. Re-check the `__main__.py` coverage floor in test-gate.toml against the new tests. The unit test drives `occupied()` with fakes, so no test composes real `Serve` or `build_daemon_core`.
- Add `eligible()` in drain.py. Make `scheduler.dispatch_next` and `_Drain._select` call it. It uses `fences_overlap`, `chain` and the starvation guard from the dependency tickets and reads `scheduler.parallel`.
- Add `mark_running(journal, stem, sha)` in clutch/runner.py, appending the unchanged `running` event body. `run_ticket`, the serve prepared dispatch (clutch/serve.py) and `_Drain._run_one` (clutch/drain.py) each call it in place of their inline append. The serve prepared dispatch is a closure inside `Serve.__init__`, so the unit test does not reach it; a structural grep and the existing serve integration tests cover it.
- Remove the `self.queue.ctx = ctx` assignment from merge.py. `MergeQueue.offer` takes the run's ctx explicitly and records it in `contexts[stem]`. merge.py and serve.py pass it, and every `.offer(` caller in the fenced tests is updated.
- Add the `asyncio.Semaphore(1)` around `stages.run_host_command`.
- Update the existing assertions on `admission.active` and `admission._slot` to the running-set form in each fenced test file, including tests/unit/test_daemon_admission_busy.py, tests/integration/serve_rig.py (`admission.active is None` becomes an empty `running` set), tests/integration/test_checkpoint.py, tests/integration/test_daemon_pause.py and tests/integration/test_sweep_slot_handoff.py (`_slot` assertions become slot-count assertions on the new form). Re-grep `tests/` for `.active`, `_slot` and `.offer(` before editing, and fence any further hit that the change forces.
- Update docs/how-clutch-works.md section 7.2 only, to describe the run set, slots and host command lock.
- Add tests in the new file tests/unit/test_parallel_dispatch.py.

Out:
- Config, `fences_overlap` and `chain` themselves. They come from the dependency tickets.
- The conflict steps. Drain and `run` keep their single-flight behavior; the only drain.py edits are the `eligible()` call and the `mark_running` call site in `_Drain._run_one`.
- Do not edit docs/parallel-tickets-plan.md or docs/roadmap.md.

## Scope fence
- clutch/scheduler.py
- clutch/daemon.py
- clutch/merge.py
- clutch/mergequeue.py
- clutch/serve.py
- clutch/drain.py
- clutch/runner.py
- clutch/stages.py
- clutch/__main__.py
- docs/how-clutch-works.md
- tests/unit/test_parallel_dispatch.py
- tests/unit/test_commit_lock.py
- tests/unit/test_admission_running_set.py
- tests/unit/test_daemon_admission_busy.py
- tests/integration/serve_rig.py
- tests/integration/test_checkpoint.py
- tests/integration/test_daemon_pause.py
- tests/integration/test_sweep_slot_handoff.py
- tests/integration/test_restart_timers.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_scheduler.py
- tests/integration/test_serve_admission.py
- tests/integration/test_daemon_admission.py
- tests/integration/test_serve_kill.py
- tests/integration/test_mergequeue.py
- tests/integration/test_rework.py
- tests/integration/test_serve_upgrade.py
- tests/integration/test_merge.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/test_bug_gate.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_triage.py
- tests/harness/daemon_soak.py

## Acceptance criteria
1. With `max_runs=2` and two tickets with disjoint fences, `./dev.py test tests/unit/test_parallel_dispatch.py` shows both in `admission.running` at once. It rules out the second waiting for the first.
2. With `parallel.enabled` false, a second dispatch is refused while one run is in `running`. `./dev.py test tests/unit/test_parallel_dispatch.py` rules out two concurrent runs.
3. A candidate whose fence overlaps an in-flight ticket is not dispatched, and one skipped `SKIP_LIMIT` times blocks later candidates. `./dev.py test tests/unit/test_parallel_dispatch.py` rules out dispatching a later non-overlapping ticket past the barrier.
4. `dispatch_next` and `_Drain._select` both call `drain.eligible`. `./dev.py test tests/unit/test_parallel_dispatch.py` rules out a second inline eligibility computation.
5. `mark_running` appends exactly one `running` transition per call, and the `run_ticket` and `_Drain._run_one` paths each journal exactly one through it. `./dev.py test tests/unit/test_parallel_dispatch.py` rules out zero appends on the `_Drain._run_one` path and rules out two appends on either path. The serve prepared dispatch is checked structurally: `grep -rlE '"to": "running"' clutch` prints only clutch/runner.py, and `grep -n 'mark_running' clutch/serve.py` exits 0.
6. `waiting_for_merge` frees only its own run's slot while the other run stays in `running`. `./dev.py test tests/unit/test_parallel_dispatch.py` rules out clearing the whole set.
7. Two stems offered with different ctx objects are each processed with their own context from `MergeQueue.contexts`. `./dev.py test tests/unit/test_parallel_dispatch.py` rules out the last offered ctx being used for both.
8. `DaemonAdmission.occupied()` returns true while either of two runs is in `running` and while only a task is present, and false when both are empty. `./dev.py test tests/unit/test_parallel_dispatch.py` rules out reporting idle while one of two runs is active. serve.py and the `__main__.py` restart lambda call `occupied()`, checked by `grep -n "occupied()" clutch/serve.py clutch/__main__.py` exiting 0.
9. Two concurrent `run_host_command` calls never run at the same time. `./dev.py test tests/unit/test_parallel_dispatch.py` rules out interleaved start and finish events.
10. No `.active` or `_slot` access on admission remains, and merge.py no longer assigns the queue ctx. `grep -rnE "admission\.active|admission\._slot" clutch tests` exits 1 with no output, and `grep -n "self\.queue\.ctx =" clutch/merge.py` exits 1 with no output.
11. The full suite passes with the updated assertions. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_parallel_dispatch.py
./dev.py test
```

## Definition of rejected
- A compat alias for `DaemonAdmission.active` or `_slot`, or a second eligibility computation left in place.
- Changed behavior with `scheduler.parallel.enabled` false.
- A `running` transition appended inline anywhere other than `runner.mark_running`, or serve or drain removed from writing one.
- New tests added to hot test files rather than tests/unit/test_parallel_dispatch.py.

## Time budget
- expected: 25m
- stuck: 50m
- reason: the change is one coupled refactor of the run-set owner and its callers. Splitting it would leave main with two inconsistent running-set owners, and most of the time is mechanical test-assertion updates.
