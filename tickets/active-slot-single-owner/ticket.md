---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/daemon.py::DaemonAdmission
- clutch/daemon.py::TicketWriter
- clutch/scheduler.py

## On-demand
- clutch/serve.py
- tests/integration/test_scheduler.py
- tests/integration/test_daemon_composition.py
- tests/integration/serve_rig.py
- tests/harness/daemon_soak.py

## Goal / Why
`DaemonAdmission` is the one owner of "what is running". Today other fields track the same fact: `Scheduler.active`, `TicketWriter.active`, `Serve.mutating`, and the reads in `Serve.upgrade_idle`. After this change `Scheduler.active`, `TicketWriter.active` and `Serve.mutating` no longer exist. Their facts are read from `DaemonAdmission` (`active`, `task`, and a new `mutating` task set by a new `mutations()` context manager). `Serve.upgrade_idle` reads one admission predicate, the selection lock that `Scheduler.dispatch_next` already holds, writer continuations and the merge queue. `serve-parallel-dispatch` replaces the single running slot with a run set, and it needs one owner to change rather than copies that can disagree.

## Scope in / Scope out
Scope in:
- `DaemonAdmission` gains `mutating: asyncio.Task | None`, an `@asynccontextmanager` `mutations()` that acquires `_slot`, sets `mutating` to the current task, and clears it in `finally`, and a method `idle()` that is true only when `active`, `task` and `mutating` are all `None`.
- `Serve.mutations` delegates to `self.core.admission.mutations()`; `Serve.mutating` is deleted. `Serve.abort` reads `self.core.admission.mutating`. `Serve.upgrade_idle` becomes `self.core.admission.idle()` and `not self.core.scheduler._slot.locked()` plus the existing writer-continuation and merge-queue checks, with no read of `scheduler.active` or `writer.active`. The `_slot` lock is held for the whole of `dispatch_next`, so it covers the window between ticket selection and `admission.active` being set, which `Scheduler.active` covered before. `idle()` alone does not cover that window.
- The writer-pruning check on `writer.active` in `Serve.merge` (its inner `poll()` pruning loop) becomes a check that `admission.active` is not that stem.
- Delete `Scheduler.active` and its set/clear in `dispatch_next`, and `TicketWriter.active` with its set/clear in `__call__`.
- Existing tests that read the deleted fields are changed to read `admission.active` or `admission.mutating`, or to record the active ticket inside the dispatch stub. The only expectation that changes is which object is read; no test's behavioral assertion changes.
- New tests go in a new unit test file, plus one new test in the already fenced `tests/integration/test_serve_upgrade.py` for the selection window.

Scope out: `Scheduler._slot` stays and is only read, never changed. It serializes selection from the projections before dispatch, and `Serve.maintenance` reads it. It is not a running-set field. `MergeQueue.active`, `Driver`, `Restart._slot`, and any run-set or parallel behavior are unchanged. No documentation names the deleted fields, so no document changes.

## Scope fence
- clutch/daemon.py
- clutch/scheduler.py
- clutch/serve.py
- tests/unit/test_admission_running_set.py
- tests/integration/test_scheduler.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_serve_upgrade.py
- tests/integration/test_serve_kill.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/serve_rig.py
- tests/harness/daemon_soak.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_admission_running_set.py` passes. A test there shows `DaemonAdmission.idle()` is `False` inside `async with admission.mutations()` and while a dispatch is in flight, and `True` after each exits. A result of `True` during either window is the wrong result the test rules out. It also shows `admission.mutating` is the entering task inside `mutations()` and `None` afterward.
2. A test in that file shows `"active" not in vars(scheduler)` and `"active" not in vars(writer)` for a `Scheduler` and a `TicketWriter` instance, including after `dispatch_next` runs. A leftover `active` attribute is the wrong result the test rules out.
3. A test in `tests/integration/test_serve_upgrade.py` holds `admission._slot` (or blocks `before_dispatch`) while `dispatch_next` has selected a ticket but not yet set `admission.active`, and asserts `upgrade_idle()` is `False`. An `upgrade_idle()` that reads only `admission.idle()` returns `True` there, and that is the wrong result the test rules out.
4. `grep -n "self\.mutating\|self\.active\|scheduler\.active\|writer\.active" clutch/serve.py clutch/scheduler.py` prints nothing, and `grep -rn "scheduler\.active\|writer\.active\|serve\.mutating" tests` prints nothing. `DaemonAdmission`'s own `self.mutating` in `clutch/daemon.py` is allowed.
5. `./dev.py test tests/integration/test_scheduler.py tests/integration/test_daemon_composition.py tests/integration/test_serve_upgrade.py tests/integration/test_serve_kill.py tests/integration/test_daemon_soak_runner.py tests/integration/test_daemon_admission.py` passes, with no assertion removed or weakened beyond the field each now reads.
6. `./dev.py test` passes in full.

## Verification
```
./dev.py test tests/unit/test_admission_running_set.py
./dev.py test tests/integration/test_scheduler.py tests/integration/test_daemon_composition.py tests/integration/test_serve_upgrade.py tests/integration/test_serve_kill.py tests/integration/test_daemon_soak_runner.py tests/integration/test_daemon_admission.py tests/integration/test_serve_admission.py
./dev.py test
```

## Definition of rejected
Any of the three fields (`Scheduler.active`, `TicketWriter.active`, `Serve.mutating`) is kept alongside the admission-owned read, or any change to dispatch ordering, lock acquisition order, or `Scheduler._slot` behavior (reading `_slot.locked()` is allowed). A rejected result also includes an `upgrade_idle` that is `True` between ticket selection and admission, any weakened or deleted behavioral assertion, and any new test added to `test_daemon_composition.py`.

## Time budget
- expected: 45m
- stuck: 90m
