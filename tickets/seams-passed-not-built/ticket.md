---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
none

## Context
- clutch/scheduler.py
- clutch/daemon.py::daemon_core
- clutch/__main__.py::build_daemon_core
- clutch/drain.py::write_queue

## On-demand
- tests/integration/test_scheduler.py
- tests/integration/test_requisition_gate.py
- tests/unit/test_admission_running_set.py

## Goal / Why
Today `Scheduler.dispatch_next` calls `write_queue(self.journal.dir.parent, self.journal._fs, self.journal._clock, ordered)`. It reaches through the journal's private `_fs` and `_clock` and derives the state directory from `dir.parent`. After this change the scheduler receives `state_dir`, `fs` and `clock` from its caller, and `daemon_core` passes them down from `build_daemon_core`'s checkout. The seams are then passed in and never rebuilt from another object's private fields. This is the scheduler half of roadmap row 98, which finishes row 14.

## Scope in / Scope out
Scope in:
- `Scheduler.__init__` gains keyword-only `state_dir: Path`, `fs: FileSystem` and `clock: Clock`. Its `write_queue` call uses them and no longer touches `self.journal._fs`, `self.journal._clock` or `self.journal.dir`.
- `daemon_core` gains keyword-only `state_dir` and `fs` and forwards them, with its existing `clock`, to `Scheduler`.
- `build_daemon_core` in `clutch/__main__.py` passes `checkout.config.state_dir` and `checkout.fs`.
- The three existing tests that construct `Scheduler` directly (`tests/integration/test_scheduler.py`, `tests/integration/test_requisition_gate.py`, `tests/unit/test_admission_running_set.py`) add the three new keyword arguments, plus any import those arguments need, and nothing else. In `tests/integration/test_scheduler.py` the `Rig` constructor passes `state_dir=root / 'state'`, `fs=LocalFileSystem()` and `clock=self.time`, and adds `from clutch.seams import LocalFileSystem`; the existing `root/state/queue.json` read at line 484 stays unchanged. The other two files pass fakes or equivalent values and add only the imports they need.
- Two new test files hold all new tests: `tests/unit/test_scheduler_write_queue_seams.py` (fake-driven, `tmp_path` and fakes only) and `tests/integration/test_scheduler_seam_source.py` (reads `clutch/scheduler.py` source), plus `tests/integration/test_daemon_core_queue_seams.py` (production wiring).

Scope out:
- `Driver`, `Journal` and `EngineLog` still build `LocalFileSystem()` themselves. Their constructors have about 100 call sites across tests and need their own ticket with a separate fence. Name that follow-up in the run record and file it with `clutch suggest`.
- No change to `write_queue` itself or to `queue.json` content.
- No docs change: no document describes this wiring.

## Scope fence
- clutch/scheduler.py
- clutch/daemon.py
- clutch/__main__.py
- tests/unit/test_scheduler_write_queue_seams.py
- tests/integration/test_scheduler_seam_source.py
- tests/integration/test_daemon_core_queue_seams.py
- tests/integration/test_scheduler.py
- tests/integration/test_requisition_gate.py
- tests/unit/test_admission_running_set.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_scheduler_write_queue_seams.py` passes. It builds a `Scheduler` over a journal fake that has only `read()`, so no `dir`, `_fs` or `_clock`. It passes a recording fake `fs`, a fixed `clock` and `state_dir=Path('/state')`. After `dispatch_next()` it asserts the fake `fs` received exactly one write to `/state/queue.json`. The `at` field must equal the fixed clock's rendered time, and `order` must list the dispatched stem. The old code fails this test with `AttributeError`, not with a wrong value.
2. `./dev.py test tests/integration/test_scheduler_seam_source.py` passes. It asserts the source of `clutch/scheduler.py` contains none of the strings `journal._fs`, `journal._clock` or `journal.dir`; the old source fails it by containing all three.
3. `./dev.py test tests/integration/test_daemon_core_queue_seams.py` passes. It builds `build_daemon_core` over a `runner.Checkout` with a recording fs, dispatches one confirmed ticket, and asserts exactly one write to `checkout.config.state_dir / 'queue.json'` on `checkout.fs` whose `order` lists that stem, not a write under the journal's directory parent.
4. `./dev.py test tests/integration/test_scheduler.py tests/integration/test_requisition_gate.py tests/unit/test_admission_running_set.py tests/integration/test_daemon_composition.py tests/integration/test_storm_notification_activation.py` passes, so the existing direct and composed `Scheduler` callers still work.
5. `./dev.py test` passes in full, so no other caller of `Scheduler` or `daemon_core` was missed.

## Verification
```
./dev.py test tests/unit/test_scheduler_write_queue_seams.py tests/integration/test_scheduler_seam_source.py tests/integration/test_daemon_core_queue_seams.py tests/integration/test_scheduler.py tests/integration/test_requisition_gate.py tests/unit/test_admission_running_set.py tests/integration/test_daemon_composition.py tests/integration/test_storm_notification_activation.py
```

## Definition of rejected
The branch is rejected if `Journal`, `Driver` or `EngineLog` constructors change. It is also rejected if `Scheduler` still falls back to the journal's private fields, if a default `fs` or `clock` is added so both paths exist, or if tests are added to `tests/integration/test_daemon_composition.py`.

## Time budget
- expected: 30m
- stuck: 60m
