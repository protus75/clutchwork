---
priority: P0
kind: chore
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: confirmed
---

## Depends on
none

## Context
- tests/integration/test_daemon_admission.py
- tests/integration/serve_rig.py
- tests/unit/test_supervise_idle_hooks.py

## On-demand
- clutch/daemon.py
- clutch/serve.py

## Goal / Why
A kill sent during a retro is never ignored or delayed because of a lost admission-slot race. Today three skip-if-busy probes read `self.admission._slot.locked()`: `DaemonCore.sweep_orphans` in `clutch/daemon.py` (about line 309), `Serve.maintenance` in `clutch/serve.py` (about line 517), and `Serve.dispatch` in `clutch/serve.py` (about line 386). An `asyncio.Lock` reports `locked() == False` in the window where `release()` has handed the lock to a queued waiter. A probe in that window then proceeds and queues behind the retro (`async with self.admission._slot`, about daemon.py:311). Only the serve main loop runs cleanup and abort, so the kill waits until the retro ends. This hangs `tests/integration/test_serve_dispatch.py::test_kill_aborts_requested_retro` (`await until(rig, run.done)` after the kill, `serve_rig.py:418`). The report measured 51 of 2000 parallel runs hanging with that stack, and 0 of 800 after the fix. The flake has failed Check for `drop-closed-sets-owner-roadmap-test` and broken `cli-group-release`. After this ticket the admission probes treat a slot with queued waiters as busy, so the race cannot occur.

## Scope in / Scope out
Scope in:
- Add a `busy()` method on the admission class that owns `_slot` (`DaemonAdmission`). It returns True when the slot is locked or when any waiter is queued on it. The waiter check uses the lock's internal waiter queue, so the method should say why in a short comment.
- Replace the three `admission._slot.locked()` probes named above with `admission.busy()`. Edit no other line in `clutch/daemon.py` or `clutch/serve.py`. The MergeQueue and scheduler `_slot.locked()` probes stay as they are.
- In `tests/unit/test_supervise_idle_hooks.py`, change only the fake admission built in `serve_rig` from `SimpleNamespace(_slot=SimpleNamespace(locked=lambda: False))` to `SimpleNamespace(busy=lambda: False)`, because `Serve.dispatch` now calls `admission.busy()`. This is the only existing-test edit allowed.
- Add a new unit test for `busy()` and a new integration test that reproduces the handoff.

Scope out: deadline or turn-count changes, the retro logic, any change to how the slot is acquired or released, the MergeQueue and scheduler slot probes, and `tests/integration/serve_rig.py`.

## Scope fence
- clutch/daemon.py
- clutch/serve.py
- tests/unit/test_supervise_idle_hooks.py
- tests/unit/test_daemon_admission_busy.py
- tests/integration/test_sweep_slot_handoff.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_daemon_admission_busy.py` passes. It asserts `busy()` is False on an idle slot, True while the lock is held, and True after the holder releases while a second waiter is queued but before that waiter runs (where `locked()` alone is False). A `busy()` that returns only `locked()` fails the third assertion.
2. `./dev.py test tests/integration/test_sweep_slot_handoff.py` passes. It holds the slot, queues a waiter, releases the slot, then calls `sweep_orphans` and asserts it returns `[]` without acquiring the slot, not a coroutine blocked behind the waiter.
3. `grep -n "admission._slot.locked()" clutch/daemon.py clutch/serve.py` prints no lines.
4. `./dev.py test tests/unit/test_supervise_idle_hooks.py tests/integration/test_serve_dispatch.py::test_kill_aborts_requested_retro tests/integration/test_serve_kill.py tests/integration/test_daemon_admission.py` passes.

## Verification
```
./dev.py test tests/unit/test_daemon_admission_busy.py tests/integration/test_sweep_slot_handoff.py tests/unit/test_supervise_idle_hooks.py tests/integration/test_serve_dispatch.py tests/integration/test_serve_kill.py tests/integration/test_daemon_admission.py
```

## Definition of rejected
Any admission-slot probe (`admission._slot.locked()`) remains in `clutch/daemon.py` or `clutch/serve.py`; `busy()` ignores queued waiters; the regression test passes on a `busy()` that returns only `locked()`; or any existing test file is edited other than the single fake-admission change in `tests/unit/test_supervise_idle_hooks.py`.

## Time budget
- expected: 20m
- stuck: 40m
