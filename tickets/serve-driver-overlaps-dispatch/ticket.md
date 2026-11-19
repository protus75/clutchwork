---
state: rejected
source: human
priority: P0
kind: feature
---

## Depends on
- main-checkout-write-gate

## Context
- clutch/serve.py::Serve.select
- clutch/serve.py::Serve.upgrade_idle
- clutch/serve.py::Serve.driver_pending
- clutch/serve.py::Serve.run_driver
- clutch/serve.py::Serve.scan
- clutch/serve.py::Serve.merge
- clutch/serve.py::Serve.abort
- clutch/daemon.py::DaemonAdmission
- tests/unit/test_driver_hooks.py
- tests/integration/serve_rig.py::graph
- tests/integration/serve_rig.py::script
- tests/integration/serve_rig.py::write
- tests/integration/serve_rig.py::until
- tests/integration/serve_rig.py::finish
- tests/integration/test_serve_dispatch.py::test_refused_uncommitted_bug_does_not_stop_serve

## On-demand
- docs/how-clutch-works.md

## Goal / Why
In `clutch engine serve` the roadmap driver pass (Author and requisition-review LLM calls, roadmap row commits, `ship`, digest) runs while ticket runs are in flight, and a confirmed eligible ticket is admitted without waiting for the pass. Today `Serve.select` refuses new admission while `driver_pending()` holds, the main loop launches the pass only when `upgrade_idle()` (no run in flight), and `run_driver` runs the whole pass under `self.mutations()`, the exclusive admission gate that waits for every run slot and blocks new dispatch. On 2026-11-19 `graphics-kind` was authored and requisition-reviewed by the driver while the confirmed tickets `document-agent-roadmap-prompt`, `graphics-kind` and `conflict-rerun-accounting` waited; the owner requires authoring to overlap implementation. Main-checkout writes stay serialized: `main-checkout-write-gate` makes the driver's row commits, ticket commits, decision-record commits and `ship` hold `Checkout.main_writes`; this ticket makes serve's watcher intake and merge-queue admission hold the same lock, so a driver commit never lands between a queued merge's rebase and its tree check (which would raise a tree-mismatch hold) or between an Author ticket write and its commit (which intake would otherwise take as a hand-authored ticket).

## Boundary contract
### Serve driver scheduling
- disposition: extend
- owner: clutch/serve.py
- consumers: `clutch engine serve`, `tests/unit/test_driver_hooks.py`, docs/how-clutch-works.md section 7.2
- observable change: `select` no longer has the `not self.driver_pending()` term (a pending driver pass no longer holds new admission). `run_driver` no longer enters `self.mutations()`; it keeps its stop/kill early return, sets `driven`, and awaits the driver. The main loop launches `run_driver` without the `self.upgrade_idle()` condition; its other conditions (no driver task, no retro task, no retro pending, driver pending, no upgrade, no stop requested) stay. `upgrade_idle()` also requires `self.driver_task is None`, so a stop, self-upgrade handoff, retro launch or idle supervise waits for an in-flight pass instead of overlapping it. `abort()` includes a pending `driver_task` in the operations it cancels and awaits on kill
- compatibility: the pass still runs once per settle count after any retro; retro scheduling and pause/stop/kill semantics are otherwise unchanged; a serve with no `docs/roadmap.md` behaves exactly as before
- acceptance: a confirmed ticket's Implement starts while a blocked driver pass is in flight
- tests: tests/unit/test_serve_driver_overlap.py, tests/integration/test_serve_driver_overlap.py, tests/unit/test_driver_hooks.py
- post-merge source of truth: clutch/serve.py

### Serve main-checkout write gate holders
- disposition: extend
- owner: clutch/serve.py
- consumers: the watcher scan, the merge-queue poll, the driver writers from `main-checkout-write-gate`
- observable change: in `scan`, the `intake(...)` call runs inside `async with self.checkout.main_writes:` (nested inside the existing `self.mutations()`); in `merge`'s `poll`, the `await self.queue.process()` call runs inside `async with self.checkout.main_writes:` (nested inside the existing `self.mutations()`). Lock order is always `mutations()` then `main_writes`; the driver takes only `main_writes`, so no cycle exists
- compatibility: scan results, merge results and journal events are unchanged; a long `ship` release gate now delays queued merges and watcher scans, never the reverse
- acceptance: intake and `queue.process()` each observe `main_writes.locked()` as held
- tests: tests/unit/test_serve_driver_overlap.py
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in:
- `clutch/serve.py`: the scheduling and gate-holder changes declared above; nothing else in serve.py changes.
- `tests/unit/test_driver_hooks.py::test_serve_select_holds_only_new_admission`: its first `assert not s.select(ticket, "implement")` (driver pending) flips to `assert s.select(ticket, "implement")`; rename the test to `test_serve_select_ignores_pending_driver`; change nothing else in that file.
- `docs/how-clutch-works.md` section 7.2: replace the sentence saying the roadmap driver (section 7.5) holds new admission at start and after each settle, runs at the next idle point after any retro, then resumes admission, with one saying the driver runs at start and after each settle, after any retro, alongside in-flight runs without holding admission, and that its main-checkout writes share one lock with watcher intake and merge admission; a stop or self-upgrade waits for an in-flight pass. Change nothing else in the document.
- New `tests/unit/test_serve_driver_overlap.py` (fakes and `tmp_path` only, built like the `object.__new__(serve.Serve)` rigs in `tests/unit/test_driver_hooks.py`) and new `tests/integration/test_serve_driver_overlap.py` (imports helpers from `tests/integration/serve_rig.py`, such as `graph`, `script`, `write`, `until`, `finish`, without editing it).

Scope out: drain (`driver-pass-overlaps-dispatch`), the driver-side holders and the `Checkout.main_writes` field (`main-checkout-write-gate`), `clutch/daemon.py` `DaemonAdmission`, retro scheduling, and the hot files `tests/integration/serve_rig.py` and `tests/integration/test_daemon_composition.py` (do not edit them).

## Scope fence
- clutch/serve.py
- tests/unit/test_serve_driver_overlap.py
- tests/integration/test_serve_driver_overlap.py
- tests/unit/test_driver_hooks.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `tests/unit/test_serve_driver_overlap.py` asserts `select(ticket, "implement")` returns `True` while `driver_pending()` is `True` and nothing else holds admission (wrong result: `False`); checked by `./dev.py test tests/unit/test_serve_driver_overlap.py`.
2. The same file asserts `run_driver` awaits the driver without entering `mutations()` (a fake `mutations` that records entry records nothing), and still returns without calling the driver when `stopping` is set.
3. The same file asserts `upgrade_idle()` is `False` while `driver_task` is a pending task and `True` once it is `None`, with every other idle condition faked true.
4. The same file asserts `abort()` cancels and awaits a pending `driver_task` (the task is `cancelled()` afterwards, not pending).
5. The same file asserts `scan()` calls a monkeypatched `serve.intake` while `checkout.main_writes.locked()` is `True`, and that the merge poll calls `queue.process()` while it is `True`.
6. `tests/integration/test_serve_driver_overlap.py` runs the production serve graph with `docs/roadmap.md` present, a driver (monkeypatched `clutch.__main__.build_driver`) that blocks on an `asyncio.Event`, and one confirmed ticket, and asserts the ticket's scripted `implement` call is recorded while the driver is still blocked (wrong result: no `implement` until the event is set); then it sets the event and finishes serve cleanly; checked by `./dev.py test tests/integration/test_serve_driver_overlap.py`.
7. `./dev.py test tests/unit/test_driver_hooks.py` passes with only the flip and rename Scope in names.

## Verification
```
./dev.py test tests/unit/test_serve_driver_overlap.py tests/integration/test_serve_driver_overlap.py tests/unit/test_driver_hooks.py
./dev.py test
```

## Definition of rejected
A pending driver pass still holds serve admission or still runs under `mutations()`; the driver is launched only when no run is in flight; serve can stop or hand off while a driver task is pending; watcher intake or merge-queue admission runs without holding `main_writes`; any code path takes `main_writes` before `mutations()`; drain code changes; or `tests/integration/serve_rig.py` or `tests/integration/test_daemon_composition.py` is edited.

## Time budget
- expected: 25m
- stuck: 50m
