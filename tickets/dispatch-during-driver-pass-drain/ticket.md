---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
- dispatch-during-driver-pass-gate

## Context
- clutch/drain.py::_Drain.run
- clutch/drain.py::_Drain._run_driver
- clutch/drain.py::_Drain._await_controlled
- clutch/git.py::Git.main_write
- clutch/roadmap.py::drive
- tests/unit/test_driver_hooks.py
- tests/integration/test_roadmap_driver.py
- docs/roadmap-driver-plan.md

## Goal / Why
`clutch engine drain` no longer holds up the next ticket while the roadmap driver pass runs. Today `_Drain.run` awaits `_run_driver` inline after each settle (`clutch/drain.py`, the `self.driven` block), so the pass's Author and requisition-review calls block selection and dispatch of the next ticket. After this ticket the pass starts as a background task and the loop goes on to select and dispatch the next ticket while it runs.

This is the second of three tickets for roadmap row 160, `dispatch-during-driver-pass`; the merged gate ticket `dispatch-during-driver-pass-gate` added `Git.main_write()` and made `roadmap._write_row`, `roadmap.ship`, `merge.dirty_overlap` and `Git.merge_squash` take it, so the pass's main-checkout writes cannot overlap a merge admission. This ticket adds no lock. The serve side (`clutch/serve.py` `driver_pending` and `run_driver`) is a separate third ticket, `dispatch-during-driver-pass-serve`, which this ticket does not touch.

Shape: `_Drain` holds at most one background pass (`driver_task`). A new pass starts only when settles differ from `driven` and no pass is running; when a pass is running and settles advanced, `driven` stays unchanged so the next loop after it ends starts one. A pass that ends with an exception surfaces at the next loop iteration, or at the end of the run, as before (any non-`Refusal` error stops the engine). `run` waits for a running pass before returning through `_await_controlled`, so a kill or stop request aborts it the same way as before and the report never outlives a running pass.

## Boundary contract
### Drain driver pass scheduling
- disposition: extend
- owner: clutch/drain.py (`_Drain.run`, `_Drain._run_driver`)
- consumers: `clutch engine drain` and its handoff chain; the roadmap driver `roadmap.drive` as called through `Dispatch._driver`
- observable change: the pass overlaps the next ticket's dispatch; at most one pass runs at a time; `run` returns only after the pass has ended or been aborted by a kill
- compatibility: the pass still starts only when `_between_tickets()` holds, the roadmap file exists and settles differ from `driven`; the digest, the `roadmap_drive` engine-log event and the driver's own behavior are unchanged
- acceptance: criteria 1 to 5 below
- tests: tests/unit/test_drain_driver_overlap.py
- post-merge source of truth: clutch/drain.py

## Scope in / Scope out
Scope in: in `clutch/drain.py`, add `driver_task = None` as a class attribute next to `driver = None` and `driven = None`, not only in `__init__`, because `tests/unit/test_drain_report_intake.py` and `tests/unit/test_supervise_idle_hooks.py` build `_Drain` with `__new__` and call `run()`. `_run_driver` creates the task (`asyncio.create_task(self.driver(self.c, log))`) and returns without awaiting it. In `run`, at the existing driver block, first raise a finished pass's exception (`driver_task.result()`) and clear it, then start a pass only when none is running. Rename the body of `run` to a private method and make `run` call it inside `try`/`finally`; the `finally` waits for a running pass with `_await_controlled(task, abort, self.c.sleep)` where `abort` is the existing no-op. The wait must not mask an exception already propagating from the loop. At the `pick is None` branch, before provider and storm waits and before `_settle`, when `driver_task` is running the loop waits for it through `_await_controlled` and `continue`s, and when the driver gates hold (driver set, roadmap file present, `_between_tickets()`) and `roadmap.settles(...)` differs from `driven` it also `continue`s, so tickets a pass authors are dispatched and the last settle gets its pass before drain settles and returns, as with the inline pass today. In `tests/unit/test_driver_hooks.py`, update only `test_drain_runs_driver_between_tickets` for the changed contract (the pass is a task; the final wait completes it). In `tests/integration/test_roadmap_driver.py`, update `test_drain_calls_driver_at_start_and_after_each_settle` only if its expected `calls` list changes; fence it for that reason alone. In `docs/how-clutch-works.md`, edit only the driver paragraph that says drain and serve run the driver at start and after every settle: say drain now runs the pass in the background beside the next ticket, serve unchanged until its own ticket.

Simpler approach rejected: awaiting the pass only when the next dispatch needs the main checkout. It needs the lock call sites to be known by drain, which the gate ticket already hid behind `Git.main_write()`; a background task with a final wait needs nothing else.

Scope out: no new lock; no change to `clutch/roadmap.py`, `clutch/git.py`, `clutch/merge.py` or `clutch/serve.py`; no change to `driver_pending` or `run_driver`; the retro check stays inline; new tests go in a new file (see fence), not the hot test files.

## Scope fence
- clutch/drain.py
- tests/unit/test_drain_driver_overlap.py
- tests/unit/test_driver_hooks.py
- tests/integration/test_roadmap_driver.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `tests/unit/test_drain_driver_overlap.py::test_dispatch_starts_while_pass_runs`: a fake driver blocks on an `asyncio.Event` while a fake dispatch for the next ticket is called; the dispatch is called before the event is set and the driver has not finished at that point, not after the driver returned. Checked by `./dev.py test tests/unit/test_drain_driver_overlap.py`.
2. `tests/unit/test_drain_driver_overlap.py::test_main_write_orders_pass_and_admission`: fakes whose `git.main_write()` returns one real `asyncio.Lock`; the fake driver holds it while blocked and a fake admission step that takes it records that it entered only after the driver released it, not while the driver held it. Checked by `./dev.py test tests/unit/test_drain_driver_overlap.py`.
3. `tests/unit/test_drain_driver_overlap.py::test_one_pass_at_a_time`: settles advance twice while a pass is blocked; the driver fake is entered once, and after it is released a second pass starts, so the driver ran twice in all, not twice at once and not once. Checked by `./dev.py test tests/unit/test_drain_driver_overlap.py`.
4. `tests/unit/test_drain_driver_overlap.py::test_run_waits_for_pass_and_surfaces_error`: `run` does not return while the pass is blocked and returns after its release; a driver that raises `RuntimeError` makes `run` raise it, not return a report. Checked by `./dev.py test tests/unit/test_drain_driver_overlap.py`.
5. `tests/unit/test_drain_driver_overlap.py::test_idle_exit_waits_for_pass`: a pass still blocked when `_select` returns `None` commits a new ticket on release, and that ticket is dispatched before `run` returns, not left undispatched; a settle that lands while a pass runs gets its own pass before `run` returns, not skipped. Checked by `./dev.py test tests/unit/test_drain_driver_overlap.py`.
6. The updated `test_drain_runs_driver_between_tickets` and the integration drain test still show one pass per settle count and no pass without a roadmap file or a driver, checked by `./dev.py test tests/unit/test_driver_hooks.py tests/integration/test_roadmap_driver.py`.

## Verification
```
./dev.py test tests/unit/test_drain_driver_overlap.py tests/unit/test_driver_hooks.py tests/integration/test_roadmap_driver.py tests/unit/test_drain_containment.py tests/unit/test_drain_deadline.py tests/unit/test_drain_reoffer.py tests/unit/test_drain_report_intake.py tests/unit/test_supervise_idle_hooks.py
```

## Definition of rejected
The branch is rejected if it adds a lock, flag or config knob, edits `clutch/serve.py`, `clutch/roadmap.py`, `clutch/git.py` or `clutch/merge.py`, lets two passes run at once, lets `run` return while a pass still runs, or leaves a pass failure unraised.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one source file with a task-lifecycle change that needs four new async tests; splitting would separate the change from its proof.
