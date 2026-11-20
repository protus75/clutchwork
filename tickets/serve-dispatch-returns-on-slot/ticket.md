---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- serve-dispatch-returns-on-slot-settle

## Context
- clutch/scheduler.py::Scheduler
- clutch/serve.py::Serve.dispatch
- clutch/serve.py::Serve.cleanup
- clutch/daemon.py::DaemonAdmission.dispatch
- tests/unit/test_supervise_idle_hooks.py::serve_rig
- docs/parallel-tickets-plan.md#4. Several runs at once in
- docs/how-clutch-works.md#7.2

## Goal / Why
Roadmap row 166, replacing merged row 45. `docs/parallel-tickets-plan.md` section 4 says `dispatch_next` returns once a slot is filled and does not wait for the run. Today `Scheduler.dispatch_next` holds its `_slot` lock across `await self.dispatch(ticket)`, which is the whole run, and `Serve.dispatch` awaits it inside a guard that also requires `admission.busy()` to be false. So serve starts one run at a time even when `scheduler.parallel.max_runs` is above 1, and `DaemonAdmission`'s run set (merged as `serve-parallel-dispatch-r2`) never holds more than one run.

After this ticket:
- `Scheduler.dispatch_next` selects exactly as today, then starts `self.dispatch(ticket)` as its own task and returns the ticket as soon as it occupies a scheduler slot. It does not wait for admission to grant its slot or for the run to end. The ticket stays in `self.flying` until its task is done.
- With `scheduler.parallel.enabled` true the existing `len(self.flying) >= parallel.max_runs` cap is the slot limit. With it false, one ticket in `flying` makes `dispatch_next` return `None`, which keeps serve single-flight.
- A run task that raises does not lose its exception: `Scheduler.raise_failure()` raises the first pending failure and drops it, `dispatch_next` calls it first, and `Serve.dispatch` calls it on every loop iteration before its stopping and pause guard, so a failure surfaces within one poll even while serve is paused or stopping, and `Scheduler.occupied()` stays true until that has happened. This keeps today's rule that a failed dispatch stops serve through the dispatch loop.
- `Scheduler.close()` cancels every outstanding run task and awaits them, then raises the first pending non-cancellation failure, if any. `Serve.cleanup` calls it after the workers are stopped and adds a raised failure to its `errors` list, so a stop or kill still cancels what the cancelled dispatch worker used to cancel by unwinding its await, and a run that failed while serve was paused or stopping still reaches the same re-raise at the end of `cleanup` that a failed dispatch worker reaches today.
- `Serve.dispatch` calls `dispatch_next` (after `raise_failure`) whenever serve is not stopping, not paused and no exclusive admission section is held or waiting, including while runs hold slots. A new read-only `DaemonAdmission.exclusive_pending()` reports that; the watcher's publication window, scans under `mutations()` and the maintenance block therefore still keep selection out, as `busy()` does today. The supervise, calibrate and upgrade-check block stays inside the existing "admission is not busy" condition.

Why: without this, `scheduler.parallel` runs one ticket at a time and the 0.4.0 parallel-serve gate cannot be met.

## Boundary contract
### Scheduler dispatch return
- disposition: replace
- owner: clutch/scheduler.py (`Scheduler.dispatch_next`)
- consumers: `Serve.dispatch` in clutch/serve.py (the only production caller); `Serve.cleanup` and `Serve.upgrade_idle` and `Serve.maintenance` through `Scheduler.close` and `Scheduler.occupied`; the existing tests listed in Scope that await it
- observable change: `dispatch_next` returns the selected ticket once a task running `self.dispatch(ticket)` has been created and the stem is in `flying`; the run's outcome is no longer its return value. A run failure is raised once by `raise_failure()`, which `dispatch_next`, `close()` and the `Serve.dispatch` loop each call. `occupied()` is true while `_slot` is held, while `flying` is non-empty, or while a failure is waiting to be raised. The slot cap is checked before the eligibility pass: right after the `max_unmerged` check the call returns `None` when parallel is off and `flying` is non-empty, or when parallel is on and `len(flying) >= max_runs`, so the `select` hook and `ticket_sha` run only when a slot is free. `close()` cancels and awaits all run tasks, then calls `raise_failure()`.
- compatibility: selection, ordering, `dispatch_skip` logging, `queue.json` content and the `max_unmerged` hold are unchanged, and `select` is still called for each candidate whenever a slot is free; because serve now polls while a run holds a slot, the early cap keeps `select` (which may journal a provider drought park) from running for waiting tickets mid-run, as today. With parallel disabled at most one ticket is in flight, as today. The old await-the-run behavior is removed with no flag or second method; every caller is updated in this change.
- acceptance: with `max_runs` 2, two `dispatch_next` calls return two tickets while both runs are still blocked, and a third returns `None` without calling `select`; with parallel off the second call returns `None` until the first run ends; a raising run is re-raised by the next call, by `raise_failure()`, or by `close()` when no call follows; `close()` cancels a blocked run
- tests: new tests/unit/test_scheduler_returns_on_slot.py, plus the existing tests named in Scope that pin the old contract
- post-merge source of truth: clutch/scheduler.py

### Serve dispatch loop
- disposition: extend
- owner: clutch/serve.py (`Serve.dispatch`, `Serve.cleanup`)
- consumers: serve's dispatch worker, `DaemonAdmission.exclusive_pending` (new read-only accessor in clutch/daemon.py, `self._exclusive or bool(self._exclusive_waiters)`), the cleanup path and operators reading docs/how-clutch-works.md section 7.2
- observable change: `Scheduler.raise_failure()` runs at the top of every loop iteration, before the guard, so a pending run failure stops serve through the existing worker-failure path even while paused; `dispatch_next` is called whenever serve is not stopping, not paused and `admission.exclusive_pending()` is false, also while admission is busy with running tickets; `supervise_idle`, `calibrate_when_due` and `check_upgrade` still run only when admission is not busy; `cleanup` awaits `scheduler.close()` after stopping the workers and appends a failure it raises to `errors`
- compatibility: pause, stop, kill, retro and upgrade gating still come from `Serve.select` and the existing conditions, and selection still never runs during an exclusive admission section; with parallel off the scheduler returns `None` while a run is in flight, so serve starts runs in the same order as today
- acceptance: a unit test with fakes shows `dispatch_next` is called while `admission.busy()` is true and `exclusive_pending()` is false, and is not called when `exclusive_pending()` is true, and `supervise_idle` is not called while busy; a unit test shows `cleanup` calls `scheduler.close()` and re-raises a failure `close()` raises, after the other cleanup steps ran
- tests: new tests/unit/test_serve_scheduler_lifecycle.py; `serve_rig` in tests/unit/test_supervise_idle_hooks.py gains `raise_failure=lambda: None` on its scheduler fake and `exclusive_pending=lambda: False` on its admission fake
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in:
- `clutch/scheduler.py`: in `Scheduler.dispatch_next`, call `raise_failure()` first; keep the selection under `_slot` unchanged; move the slot cap before the eligibility pass, right after the `max_unmerged` check: return `None` when parallel is off and `flying` is non-empty, or when parallel is on and `len(self.flying) >= parallel.max_runs` (the existing in-branch parallel cap is removed, not duplicated); replace `await self.dispatch(ticket)` and its `finally` with `asyncio.create_task(self.dispatch(ticket))`, a done-callback that removes the stem from `flying` and records a non-cancellation exception, and `return ticket`. Update the docstring. Add `failures`, `raise_failure()` (raise and drop the first pending failure, else return) and `close()` (cancel and await every task, clear `flying`, then call `raise_failure()`), and make `occupied()` true while `flying` or a failure is pending. Add an `import` the code needs.
- `clutch/daemon.py`: add `DaemonAdmission.exclusive_pending()` returning `self._exclusive or bool(self._exclusive_waiters)`; nothing else in the file changes.
- `clutch/serve.py`: in `Serve.dispatch`, call `self.core.scheduler.raise_failure()` at the top of each loop iteration before any guard; split the guard so `dispatch_next` runs when not stopping, not paused and `self.core.admission.exclusive_pending()` is false, while the check-upgrade and supervise block keeps the `not self.core.admission.busy()` condition and its order; in `Serve.cleanup`, call `await self.core.scheduler.close()` after `_stop_workers(self.workers)`, catching `Exception` from it into `errors` so the remaining cleanup steps and the final re-raise run as today.
- `docs/how-clutch-works.md` section 7.2, Dispatch bullet: replace "the scheduler still awaits each dispatch" with that the scheduler returns once a ticket occupies a slot and each run is its own task, with parallel off holding one in flight. Edit only that sentence.
- `tests/unit/test_supervise_idle_hooks.py`: only the scheduler fake in `serve_rig` gains `raise_failure=lambda: None` and its admission fake gains `exclusive_pending=lambda: False`.
- New tests `tests/unit/test_scheduler_returns_on_slot.py` and `tests/unit/test_serve_scheduler_lifecycle.py`.
- Existing tests that pin the old contract, rewritten to the new one and nothing else in them: in `tests/integration/test_scheduler.py` the tests that start `dispatch_next` with `asyncio.create_task` and expect a second call to wait for or follow the first run (`test_single_flight_dispatch`, `test_dispatch_failure_and_cancellation_release_slot`, the `max_unmerged` re-read test, the new-urgent ordering test); the matching `create_task` tests in `tests/integration/test_daemon_composition.py`; the `dispatch` task in `tests/harness/reliability_battery.py`; `test_upgrade_waits_between_selection_and_admission` in `tests/integration/test_serve_upgrade.py`; the `dispatch_next` task in `tests/unit/test_admission_parallel_run_set.py`; `test_shared_path_and_dispatch_failure_cleanup` in `tests/unit/test_scheduler_parallel_fill.py` (its `pytest.raises(ValueError)` moves to wrap the `dispatch_next` call after the failing run has finished, not the call that starts it); and any `flying`-clearing assertion in that file that reads state before the run task has finished (use `tests/dispatch_settle.py::dispatch_settled`).

Scope out:
- `DaemonAdmission` changes only by the read-only accessor above. A run waiting for merge still counts in `flying` and so in the scheduler's `max_runs` cap although admission has released its slot.
- `supervise_idle` and `calibrate_when_due` still run only at full idle; with continuous refill they run when the slots drain, as before.
- The drain path (`clutch/drain.py`), `clutch/config.py` and the plan and roadmap documents are unchanged.

## Scope fence
- clutch/scheduler.py
- clutch/serve.py
- clutch/daemon.py
- docs/how-clutch-works.md
- tests/unit/test_scheduler_returns_on_slot.py
- tests/unit/test_serve_scheduler_lifecycle.py
- tests/integration/test_scheduler.py
- tests/integration/test_daemon_composition.py
- tests/harness/reliability_battery.py
- tests/integration/test_serve_upgrade.py
- tests/unit/test_admission_parallel_run_set.py
- tests/unit/test_scheduler_parallel_fill.py
- tests/unit/test_supervise_idle_hooks.py

## Acceptance criteria
1. With `scheduler.parallel` enabled and `max_runs` 2, two `dispatch_next` calls each return a ticket while both `dispatch` callables are still blocked, the third call returns `None`, and `flying` holds both stems; the old code blocks on the first call forever, checked by `./dev.py test tests/unit/test_scheduler_returns_on_slot.py`.
2. With parallel disabled, a second `dispatch_next` returns `None` while the first run is blocked, without calling the `select` hook or `ticket_sha` (a counting hook sees no call), and returns the next ticket after the first run ends; it never starts a second run beside the first, checked by `./dev.py test tests/unit/test_scheduler_returns_on_slot.py`.
3. A `dispatch` callable that raises `ValueError` makes the next `dispatch_next` raise that `ValueError`, `occupied()` is true until then, and the call after that does not raise again, checked by `./dev.py test tests/unit/test_scheduler_returns_on_slot.py`.
4. `Scheduler.close()` cancels a blocked run, awaits it, and leaves `flying` empty and `occupied()` false; a cancelled run records no failure, checked by `./dev.py test tests/unit/test_scheduler_returns_on_slot.py`.
5. A run that raises `ValueError` with no `dispatch_next` call after it makes `close()` raise that `ValueError` once, not return quietly, and a second `close()` does not raise, checked by `./dev.py test tests/unit/test_scheduler_returns_on_slot.py`.
6. With `pause_id` set and a scheduler fake whose `raise_failure` raises `ValueError`, `Serve.dispatch` raises that `ValueError` and does not call `dispatch_next`, checked by `./dev.py test tests/unit/test_serve_scheduler_lifecycle.py`.
7. `Serve.dispatch` called with fakes whose `admission.busy()` is true and `exclusive_pending()` is false calls `scheduler.dispatch_next` and does not call `supervise_idle`; with `exclusive_pending()` true it does not call `dispatch_next`, and `DaemonAdmission.exclusive_pending()` is true while an `exclusive()` section is held or waiting and false while only runs hold slots; with `busy()` false it still supervises first inside the lock and dispatches after, as `tests/unit/test_supervise_idle_hooks.py` pins, checked by `./dev.py test tests/unit/test_serve_scheduler_lifecycle.py tests/unit/test_supervise_idle_hooks.py tests/unit/test_calibration_idle.py`.
8. `Serve.cleanup` with fakes calls `scheduler.close()` after the workers are stopped, and when `close()` raises `ValueError` the notifications close and writer clearing still ran and `cleanup` raises that `ValueError`, not returns, checked by `./dev.py test tests/unit/test_serve_scheduler_lifecycle.py`.
9. The existing scheduler, composition, serve, admission and reliability tests pass against the new contract, checked by `./dev.py test tests/unit tests/integration/test_scheduler.py tests/integration/test_daemon_composition.py tests/integration/test_serve_upgrade.py tests/integration/test_reliability_battery.py tests/integration/test_serve_dispatch.py tests/integration/test_serve_kill.py tests/integration/test_serve_admission.py tests/integration/test_serve_lifecycle.py`.
10. `docs/how-clutch-works.md` section 7.2 no longer says the scheduler awaits each dispatch, checked by reading the Dispatch bullet in `docs/how-clutch-works.md`.

## Verification
```
./dev.py test tests/unit tests/integration/test_scheduler.py tests/integration/test_daemon_composition.py tests/integration/test_serve_upgrade.py tests/integration/test_reliability_battery.py tests/integration/test_serve_dispatch.py tests/integration/test_serve_kill.py tests/integration/test_serve_admission.py tests/integration/test_serve_lifecycle.py
```

## Definition of rejected
A second method or flag that keeps the old await-the-run path, a run failure that is swallowed, a `dispatch_next` that starts a second run with parallel disabled, or a change to the drain path or to `DaemonAdmission` beyond the read-only `exclusive_pending()` accessor.

## Time budget
- expected: 55m
- stuck: 110m
- reason: one behavior change in the scheduler and serve loop plus the few tests that pin the old contract; the mechanical test rewrite is split into `serve-dispatch-returns-on-slot-settle`.
