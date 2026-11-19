---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
- dispatch-during-driver-pass-gate
- dispatch-during-driver-pass-drain

## Context
- clutch/serve.py::Serve.select
- clutch/serve.py::Serve.upgrade_idle
- clutch/serve.py::Serve.driver_pending
- clutch/serve.py::Serve.run_driver
- clutch/serve.py::Serve.run
- clutch/drain.py::_Drain.run
- clutch/git.py::Git.main_write
- tests/unit/test_driver_hooks.py
- tests/integration/test_serve_driver.py
- docs/how-clutch-works.md#7.5 Roadmap driver

## Goal / Why
`clutch engine serve` no longer holds up ticket dispatch while the roadmap driver pass runs. Today `Serve.select` refuses every new admission while `driver_pending()` holds, and `Serve.run_driver` runs the whole pass under `self.mutations()` after `upgrade_idle()`, so the pass's Author and requisition-review calls block the next ticket. After this ticket the pass runs as a background task beside in-flight and newly dispatched tickets, and a confirmed eligible ticket dispatches without waiting for it.

This is the third and last ticket of roadmap row 160, `dispatch-during-driver-pass`. The merged `dispatch-during-driver-pass-gate` added `Git.main_write()` (one `asyncio.Lock`, taken by `roadmap._write_row`, `roadmap.ship`, `merge.dirty_overlap` and `Git.merge_squash`), so the pass's main-checkout writes already serialize against merge admission; this ticket adds no lock. The merged `dispatch-during-driver-pass-drain` did the same for `clutch engine drain` (`_Drain.driver_task`, one pass at a time, started when settles differ from `driven`, awaited before `run` returns); serve now matches it.

## Boundary contract
### Serve driver pass scheduling
- disposition: extend
- owner: clutch/serve.py (`Serve.select`, `Serve.run_driver`, `Serve.upgrade_idle`, `Serve.run`)
- consumers: `clutch engine serve` and its self-upgrade handoff; the roadmap driver `roadmap.drive` as called through `Serve.driver`
- observable change: admission is no longer held while a pass is pending or running; the pass runs without `mutations()`; at most one pass runs at a time and a new one starts when `roadmap.settles(...)` differs from `driven`; serve returns only after a running pass has ended; a pass that raises stops serve with a nonzero exit code
- compatibility: retro still holds admission (`retro_pending()` in `select`) and runs under `mutations()`; the digest, the `roadmap_drive` log event and the driver's own behavior are unchanged; `Git.main_write()` stays the only serialization of the pass's main-checkout writes
- acceptance: criteria 1 to 6 below
- tests: tests/unit/test_serve_driver_overlap.py, tests/integration/test_serve_driver_overlap.py
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in, in `clutch/serve.py`:
- `Serve.select`: drop `and not self.driver_pending()` from the admission condition; keep `not self.retro_pending()`.
- `Serve.run_driver`: do not enter `self.mutations()`. Keep the `control.poll()` and stop/kill early return, the `snapshot_config` checkout copy, `self.driven = roadmap.settles(...)` before the call, and `await self.driver(c, self.log)`.
- `Serve.run` driver start condition: remove `self.upgrade_idle()` (the pass must start while a ticket runs); keep `driver_task is None`, `retro_task is None`, `not retro_pending()`, `driver_pending()`, `self.upgrade is None` and `not stop_requested`. `driver_pending()` stays as it is (`settles != self.driven`), so a settle that lands during a pass gets its own pass after it ends.
- `Serve.upgrade_idle`: add `self.driver_task is None`, so retro start and the self-upgrade handoff wait for a running pass. Add `driver_task = None` as a class attribute next to the other defaults, because `tests/unit/test_driver_hooks.py` builds `Serve` with `object.__new__`.
- Shutdown: after the main loop exits (idle upgrade stop, stop request, kill request, or loop failure) and before `cleanup`, wait for a running `driver_task` with no abort, as drain does, through a new `async def Serve.wait_driver(self)` that awaits and clears the task and returns the exception it raised, or `None`, so a unit test can call it with a fake task. `run` calls it and, on a returned exception, logs `serve_failed` and sets a nonzero exit code unless an earlier failure already set one. A finished pass's exception raised in the loop (`driver_task.result()`) already reaches the `serve_failed` path; keep it.

Scope in, tests: in `tests/unit/test_driver_hooks.py`, update `test_serve_driver_pending_and_run` (the `mutations` stub goes, and `run_driver` is shown not to enter it) and `test_serve_select_holds_only_new_admission` (its first assertion flips: select admits a new ticket while `driver_pending()` holds; rename the test). New tests go in the two new files; the serve rig `tests/integration/serve_rig.py` is a hot file, so import it and do not edit it. In `tests/integration/test_serve_driver.py`, update `test_serve_holds_admission_for_the_driver`: its `[0, 1, 2]` pass counts may stay, but its assertion that exactly one implement call precedes the second pass encodes the old hold and must change to the overlap contract.

Scope in, docs: in `docs/how-clutch-works.md` section 7.5, the paragraph beginning "With a roadmap present, drain starts the driver" says drain and serve both start the pass in the background beside the next ticket (serve at start and after every settle, no longer at its idle point). In the serve section, the sentence "the roadmap driver (section 7.5) holds new admission at start and after each settle, runs at the next idle point after any retro, then resumes admission" is false after this change; reword it to say the pass runs beside tickets and does not hold admission, and that retro still does. Section 6.6 and the retro paragraph are unchanged.

Simpler approach rejected: keeping `upgrade_idle()` as the start gate and only dropping the `select` hold. The pass would then start only when no ticket runs and would still block the next dispatch while it runs under `mutations()`, so the overlap never happens.

Scope out: no new lock; no change to `clutch/drain.py`, `clutch/roadmap.py`, `clutch/git.py` or `clutch/merge.py`; retro, scan and supervise-idle stay under `mutations()`; no change to `tests/integration/serve_rig.py`.

## Scope fence
- clutch/serve.py
- docs/how-clutch-works.md
- tests/unit/test_driver_hooks.py
- tests/unit/test_serve_driver_overlap.py
- tests/integration/test_serve_driver.py
- tests/integration/test_serve_driver_overlap.py

## Acceptance criteria
1. `tests/unit/test_serve_driver_overlap.py::test_select_admits_while_pass_pending`: with a roadmap file present and settles different from `driven`, `Serve.select` returns `True` for a new ticket, not `False`; with `retro_pending()` true it still returns `False`. Checked by `./dev.py test tests/unit/test_serve_driver_overlap.py`.
2. `tests/unit/test_serve_driver_overlap.py::test_run_driver_does_not_take_mutations`: a `mutations` stub that records entry is never entered by `run_driver`, and `driven` equals the settle count before the fake driver returns, not after. Checked by `./dev.py test tests/unit/test_serve_driver_overlap.py`.
3. `tests/unit/test_serve_driver_overlap.py::test_main_write_orders_pass_and_merge`: a fake git whose `main_write()` returns one real `asyncio.Lock`; the fake driver holds it while blocked, and a fake merge step that takes it enters only after the driver releases it, not while the driver holds it. Checked by `./dev.py test tests/unit/test_serve_driver_overlap.py`.
4. `tests/integration/test_serve_driver_overlap.py::test_dispatch_starts_while_pass_runs`: a driver blocked on an `asyncio.Event` while a second confirmed ticket reaches implement; the implement call is recorded before the event is set, not after the driver returned. Checked by `./dev.py test tests/integration/test_serve_driver_overlap.py`.
5. `tests/integration/test_serve_driver_overlap.py::test_one_pass_at_a_time_and_shutdown_waits`: settles advance twice while a pass is blocked and the driver is entered once; after release a second pass runs, so the driver ran twice in all, never concurrently; a stop requested while a pass is blocked does not let `Serve.run` return until the pass is released. Checked by `./dev.py test tests/integration/test_serve_driver_overlap.py`.
6. `tests/integration/test_serve_driver_overlap.py::test_pass_failure_stops_serve`: a driver that raises `RuntimeError` makes `Serve.run` return a nonzero code and log `serve_failed`, not return 0; the same holds when the failure surfaces only at the shutdown wait. Checked by `./dev.py test tests/integration/test_serve_driver_overlap.py`.
7. `tests/unit/test_serve_driver_overlap.py::test_upgrade_idle_and_wait_driver`: `upgrade_idle()` is `False` while `driver_task` is a pending task and `True` once it is `None`; `wait_driver()` returns `None` for a task that succeeds and the `RuntimeError` for one that raises, and leaves `driver_task` as `None` in both cases, not the stale task. Checked by `./dev.py test tests/unit/test_serve_driver_overlap.py`.
8. The updated tests keep the existing contract elsewhere: no pass without a roadmap file, one pass per settle count, retro still holds admission. Checked by `./dev.py test tests/unit/test_driver_hooks.py tests/integration/test_serve_driver.py`.

## Verification
```
./dev.py test tests/unit/test_driver_hooks.py tests/unit/test_serve_driver_overlap.py tests/integration/test_serve_driver.py tests/integration/test_serve_driver_overlap.py
```

## Definition of rejected
- A new lock, flag, or knob, or any change to `drain.py`, `roadmap.py`, `git.py` or `merge.py`.
- `run_driver` still entered through `mutations()`, or `select` still consulting `driver_pending()`.
- Two passes running at once, or `Serve.run` returning while a pass is still running.
- A pass failure swallowed (exit code 0).
- Tests added to the hot test files, or an edit to `tests/integration/serve_rig.py`.

## Time budget
- expected: 25m
- stuck: 50m
