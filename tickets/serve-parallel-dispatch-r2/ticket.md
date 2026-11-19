---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- parallel-config
- fence-overlap
- chain-order
- active-slot-single-owner

## Context
- docs/parallel-tickets-plan.md

## On-demand
- clutch/daemon.py
- clutch/scheduler.py
- clutch/serve.py
- clutch/__main__.py

## Goal / Why
When `scheduler.parallel.enabled` is true, `DaemonAdmission` holds a run set of up to `max_runs` tickets, each with its own task, instead of one `_slot` lock, one `active` ticket and one `task`. `occupied()` reports whether any run is in flight. With parallel off, `max_runs` is 1 and behavior is identical to today.

Semantics, stated once: `DaemonAdmission.dispatch` beyond `max_runs` waits for a free slot, as it waits on `_slot` today. Nothing is refused or dropped. `DaemonAdmission` is the only owner of `max_runs`. `daemon_core` receives the count and gives it to `DaemonAdmission` alone; the `Scheduler` constructor signature does not change, and `Scheduler.dispatch_next` still awaits its run exactly as today. Concurrent filling of slots from the scheduler belongs to the dispatch work that follows this ticket, not here.

The single `_slot` also serializes work that is not a ticket run: maintenance (`mutations()`), merge handoffs, watch publication, startup and the sweep. Those stay exclusive: each takes an admission-wide exclusive gate that waits for the slot-holding runs to finish and blocks new run admission until released.

A run in `waiting_for_merge` stays in the stem-keyed run dict, which serve's writer retention and the kill and upgrade `occupied()` checks read, but it holds no slot and does not block the exclusive gate. The gate waits only for slot-holding runs. When the run leaves `waiting_for_merge` it reacquires its slot and gate access. This is what lets the serve merge poll take `mutations()` and complete that run's offer without deadlocking, even with `max_runs` 1.

The running-transition writer, the merge-queue run context, the host-command lock and the shared `eligible()` filter are separate tickets and are out of scope.

## Boundary contract
### Admission run set
- disposition: replace
- owner: clutch/daemon.py (DaemonAdmission)
- consumers: clutch/__main__.py (`Restart.owned`, `build_daemon_core`), clutch/serve.py idle, restart, maintenance and watch-publication paths, clutch/daemon.py startup and sweep, tests and harness that read admission state
- observable change: admission tracks running tickets as a stem-keyed dict of tasks bounded by `max_runs`; `occupied()` is true while any run is in the dict; `waiting_for_merge` frees only that run's slot, keeps the run in the dict, and exempts it from the exclusive gate's wait until it leaves `waiting_for_merge` and reacquires its slot; the `_slot` lock and the `active` and `task` attributes of `DaemonAdmission` are removed and every caller is moved to `occupied()` in the same change; an exclusive gate (used by `mutations()`, startup, the sweep and watch publication) waits for slot-holding runs to finish and blocks new admission while held
- compatibility: with parallel disabled `max_runs` is 1, so at most one run is in flight and a second dispatch waits as it does today; ordering, journal events and status output are unchanged; no shim keeps the old attributes
- acceptance: with `max_runs` 2 two runs are in flight and a third dispatch waits until one releases; releasing at `waiting_for_merge` admits the next; an exclusive section never overlaps a slot-holding run; `mutations()` is granted while the only run is in `waiting_for_merge`
- tests: new tests/unit/test_admission_parallel_run_set.py using fakes, plus updated assertions in the fenced existing tests that read `admission._slot`, `.active` or `.task`
- post-merge source of truth: clutch/daemon.py

### Scheduler idle probe
- disposition: extend
- owner: clutch/scheduler.py (Scheduler)
- consumers: clutch/serve.py maintenance and idle checks
- observable change: `Scheduler.occupied()` returns true while its `_slot` lock is held, replacing serve's two reads of `scheduler._slot.locked()` (`clutch/serve.py` idle and maintenance probes); no new Scheduler state
- compatibility: the constructor, `dispatch_next` and its await-the-run behavior are unchanged
- acceptance: `occupied()` is true during a dispatch and false after it
- tests: tests/unit/test_admission_parallel_run_set.py
- post-merge source of truth: clutch/scheduler.py

## Scope in / Scope out
Scope in:
- `clutch/daemon.py`: replace `DaemonAdmission._slot`, `active` and `task` with a run dict of up to `max_runs` entries, one task per run; add `occupied()`; add the exclusive gate and use it in `mutations()`, `DaemonCore.startup()` and the sweep (the two `async with self.admission._slot` sites); `waiting_for_merge` releases the run's slot but keeps it in the dict; `daemon_core` takes `max_runs` and passes it to `DaemonAdmission` only.
- `clutch/__main__.py`: `build_daemon_core` reads `checkout.config.scheduler.parallel` and passes `max_runs` (1 when `enabled` is false); the `owned` lambda for `Restart` uses `core.admission.occupied()`. Add `tests/unit/test_admission_parallel_run_set.py` cases that call `build_daemon_core` (or the helper it uses to compute the count) with fakes and assert it passes 1 when `scheduler.parallel.enabled` is false and the configured `max_runs` when true.
- `clutch/scheduler.py`: add `occupied()` only.
- `clutch/serve.py`: idle and restart checks use `occupied()`; the maintenance check uses the scheduler and admission `occupied()`; writer retention keeps reading the stem-keyed run dict; watch publication takes the exclusive gate.
- `docs/how-clutch-works.md`: update only the section that describes the single-flight slot and idle checks.
- Existing tests and harness files that assert on `admission._slot`, `admission.active` or `admission.task` move to `occupied()`; these are forced edits to assertions and stand-ins, not new tests, so the hot files `tests/integration/test_daemon_composition.py` and `tests/integration/serve_rig.py` are fenced for those edits only. This includes `tests/integration/test_scheduler.py`, where the assertion `rig.core.admission.task is None` becomes `not rig.core.admission.occupied()`.
- `docs/roadmap.md`: this ticket delivers only the admission run set of row 45, so add two rows directly after row 45 in the same release table, each with the next row number unused anywhere in the file at the base commit, owner `parallel plan 6`, kind `chore`, priority `P2`, no runs-before, carrying no link until authored: (1) stem `parallel-dispatch-run-context`, Depends on `serve-parallel-dispatch-r2`: one `runner.mark_running(journal, stem, sha)` called from `runner.run_ticket`, the serve dispatch closure and `_Drain._run_one`; `MergeQueue.offer` takes `ctx` and records `contexts[stem]` and `AdmissionBoundary` stops setting `queue.ctx` (fence the `offer` stand-ins in `tests/integration/test_serve_admission.py` and `tests/integration/test_daemon_soak_runner.py`); a `Semaphore(1)` in `stages.run_host_command`. (2) stem `parallel-dispatch-eligible`, Depends on `serve-parallel-dispatch-r2`: one `drain.eligible()` used by `Scheduler.dispatch_next` and `_Drain._select`, keeping today's storm, budget, drought and park side effects and `order_tickets` order, with today's order pinned with parallel off. Edit no other roadmap row; row 45 itself is linked and struck by the driver.

Scope out: `Scheduler` constructor and `Scheduler._slot`/`active` internals, `runner.mark_running` and the other `running` writers, `MergeQueue.offer` context and `AdmissionBoundary` ctx assignment, the `Semaphore(1)` in `stages.run_host_command`, the shared `drain.eligible()` filter, `queue._slot` and `queue.active` in merge-queue code (including `consume_handoff`), and conflict steps. `drain` and `run` stay single-flight. No new test goes into `test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `test_cli.py`, `test_watch.py` or `serve_rig.py`.

## Scope fence
- clutch/daemon.py
- clutch/scheduler.py
- clutch/serve.py
- clutch/__main__.py
- docs/how-clutch-works.md
- tests/unit/test_admission_parallel_run_set.py
- tests/unit/test_admission_running_set.py
- tests/unit/test_daemon_admission_busy.py
- tests/harness/daemon_soak.py
- tests/integration/serve_rig.py
- tests/integration/test_checkpoint.py
- tests/integration/test_daemon_admission.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_config.py
- tests/integration/test_daemon_pause.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_merge.py
- tests/integration/test_reliability_battery.py
- tests/integration/test_restart_timers.py
- tests/integration/test_scheduler.py
- tests/integration/test_serve_admission.py
- tests/integration/test_serve_kill.py
- tests/integration/test_serve_upgrade.py
- tests/integration/test_sweep_slot_handoff.py
- docs/roadmap.md

## Acceptance criteria
1. With `max_runs` 2, two dispatched stems are in flight and a third dispatch is still waiting, not started, until one releases; a test that sees the third start early fails: `./dev.py test tests/unit/test_admission_parallel_run_set.py`.
2. A run that reaches `waiting_for_merge` frees only its own slot; `occupied()` stays true while the other run is in flight, not false: `./dev.py test tests/unit/test_admission_parallel_run_set.py`.
3. `mutations()`, the sweep, `DaemonCore.startup()` and the watch-publication gate path each wait for slot-holding runs to finish and block new admission while they hold the gate; a test that starts a run during any of the four fails: `./dev.py test tests/unit/test_admission_parallel_run_set.py`.
4. With `max_runs` 1 a second dispatch waits for the first to finish, as today, and is not refused: `./dev.py test tests/integration/test_daemon_admission.py tests/integration/test_serve_admission.py`.
5. `DaemonAdmission` has no `_slot`, `active` or `task` attribute and no caller reads them: `grep -rnE "admission\._slot|admission\.active|admission\.task|scheduler\._slot" clutch tests` prints nothing (`queue._slot` and `queue.active` are not matched and stay).
6. Serve idle, restart and self-upgrade checks wait on `occupied()`, and `build_daemon_core` passes 1 when parallel is disabled and `max_runs` when enabled: `./dev.py test tests/integration/test_restart_timers.py tests/integration/test_serve_kill.py tests/integration/test_serve_upgrade.py tests/integration/test_daemon_config.py`.
7. With `max_runs` 1 and the only run inside `waiting_for_merge`, `mutations()` is granted, `occupied()` is still true, and the run is still in the stem-keyed run dict; a gate that waits for that run, and so never returns, fails the test: `./dev.py test tests/unit/test_admission_parallel_run_set.py`.

## Verification
```
./dev.py test tests/unit/test_admission_parallel_run_set.py tests/unit/test_admission_running_set.py tests/unit/test_daemon_admission_busy.py tests/integration/test_daemon_admission.py tests/integration/test_serve_admission.py tests/integration/test_serve_kill.py tests/integration/test_serve_upgrade.py tests/integration/test_restart_timers.py tests/integration/test_daemon_tasks.py tests/integration/test_daemon_config.py tests/integration/test_daemon_pause.py tests/integration/test_checkpoint.py tests/integration/test_sweep_slot_handoff.py tests/integration/test_daemon_composition.py tests/integration/test_daemon_soak_runner.py tests/integration/test_merge.py tests/integration/test_reliability_battery.py tests/integration/test_scheduler.py
```

## Definition of rejected
The branch is rejected if with parallel off ordering, dispatch waiting or journal output differ from today; if maintenance, watch publication, startup or the sweep can run while a slot-holding ticket run is in flight; if serve deadlocks with a run in `waiting_for_merge`; if it touches the writer, merge-queue context, host-command lock, `eligible()` or `Scheduler`'s constructor; or if any dual path keeps the old `_slot`, `active` or `task` on `DaemonAdmission`.

## Time budget
- expected: 30m
- stuck: 60m
