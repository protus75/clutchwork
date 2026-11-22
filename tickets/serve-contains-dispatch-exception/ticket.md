---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Runs before
- shared-git-fake
- shared-review-script
- shared-serve-rig-config
- disk-io-skip-per-file

## Context
- clutch/serve.py::Serve.__init__
- clutch/serve.py::Serve.dispatch
- clutch/serve.py::Serve.run
- clutch/scheduler.py::Scheduler.dispatch_next
- clutch/scheduler.py::Scheduler.raise_failure
- clutch/drain.py::_Drain._run_one
- clutch/runner.py::mark_running
- tests/unit/test_drain_containment.py
- tests/integration/test_drain_containment.py
- tests/unit/test_serve_verdict_owned.py
- tests/unit/test_serve_idle_poll.py
- tests/integration/conftest.py
- tests/integration/test_serve_kill.py
- tests/regress_drain_containment.py
- docs/how-clutch-works.md#7. Drain and serve

## Goal / Why
On 2026-11-22 at 02:11:57Z one ticket's run raised `ValueError: stage already open` (evidence `serve-crash.log`). The bug that raised it is fixed by `check-meta-fill-nested-stage`. The scheduler's run task appended the exception to `Scheduler.failures`, `Serve.dispatch` re-raised it through `raise_failure`, and serve's `guarded` wrapper stopped the whole engine (`engine_stop outcome: error: ValueError`). `implement-skips-full-suites`, which was running fine in the other parallel slot, was interrupted with it.

Drain has contained this since `drain-contains-dispatch-exception` (b17ee265). `_Drain._run_one` journals one `infra_error` terminal with `stage: dispatch`, `reason: dispatch_exception` and `error: "<Type>: <message>"`, then continues. Serve's per-ticket dispatch path never got the same handling, so the two engine verbs now behave differently on the same failure.

After this ticket, an `Exception` raised by one ticket's run under serve ends that ticket with the same single `infra_error` terminal drain writes. Serve keeps running, other in-flight runs continue, and the ticket is re-offered and held at the attempts cap through the existing cap machinery, which is the release path. Failures of serve's own consumers (merge, box intake, verdicts, the dispatch loop itself) and `BaseException` cancellation stay fatal, as `tests/integration/test_serve_kill.py` pins today.

## Boundary contract
### Dispatch exception terminal
- disposition: extend
- owner: clutch/runner.py
- consumers: clutch/drain.py `_Drain._run_one`, clutch/serve.py per-ticket dispatch closure
- observable change: a new `runner` function journals the `infra_error` / `dispatch` / `dispatch_exception` terminal for a stem whose latest transition is not terminal (and does nothing when it already is). Drain's inline append is replaced by a call to it, and serve calls it too.
- compatibility: drain's journaled body is byte-identical to today (`tests/unit/test_drain_containment.py` passes unchanged; `tests/integration/test_drain_containment.py` is in `DISK_IO_SKIP` and does not run)
- acceptance: criteria 1 and 4
- tests: tests/unit/test_dispatch_exception_terminal.py, tests/unit/test_drain_containment.py
- post-merge source of truth: clutch/runner.py

### Serve per-ticket run failure
- disposition: extend
- owner: clutch/serve.py
- consumers: Scheduler (the run task no longer ends with an exception for a contained failure), Serve.run lifetime, operators reading engine.log and status
- observable change: an `Exception` from `callback(ticket)` in serve's dispatch closure is journaled through the runner function, logged as engine-log event `dispatch_exception` with `stem` and `error`, and the closure returns `"infra_error"`. Its existing `finally` then re-offers the ticket through `scheduler.update` as for any failed terminal. Serve does not stop.
- compatibility: while serve is stopping (`self.stopping`) the exception is re-raised as today. `BaseException` (including cancellation) is not caught. Consumer failures still stop serve with `worker_failure`.
- acceptance: criteria 2, 3 and 5
- tests: tests/unit/test_serve_dispatch_containment.py
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in:
- `clutch/runner.py`: add the dispatch-exception terminal function described in the boundary contract, moving the body from `_Drain._run_one`.
- `clutch/drain.py`: `_Drain._run_one` calls that function in place of its inline `require_transition` check and journal append. Nothing else in drain changes.
- `clutch/serve.py`: in the per-ticket `dispatch` closure built in `Serve.__init__`, catch `Exception` around `await callback(ticket)` as described above.
- New `tests/unit/test_dispatch_exception_terminal.py` for the runner function: one terminal is appended when the latest transition is `running`, and none when it is already terminal.
- New `tests/unit/test_serve_dispatch_containment.py`. It builds `Serve` around a `MagicMock` daemon core the way `tests/unit/test_serve_verdict_owned.py` does (no real repo, git, or disk I/O, because the integration I/O guard blocks `tests/integration/serve_rig.py` and `DISK_IO_SKIP` skips the serve and drain containment integration tests), with an in-memory journal. It reaches the per-ticket dispatch closure through the `prepare` callable that `Serve.__init__` passes to the monkeypatched `build_daemon_core`, feeding it a `MagicMock(spec=TicketWriter)` callback, and awaits the closure directly. Ticket A's run callback raises `ValueError("boom")` while ticket B's callback, awaited concurrently through the same closure, returns its scripted terminal. The test name for the A case contains `raises`.
- New carried reproducer `tests/regress_serve_dispatch_containment.py`, modeled on `tests/regress_drain_containment.py`, that runs `tests/unit/test_serve_dispatch_containment.py -k raises` and maps the pytest result to the regression protocol.
- `docs/how-clutch-works.md`: move the sentence "A dispatch exception is journaled as an `infra_error` terminal, re-offered, and held in the Reject queue at the attempts cap." so it covers both drain (7.1) and serve (7.2), and say in 7.2 that consumer failures still stop serve.

Scope out: the stage-nesting bug itself (`check-meta-fill-nested-stage`), `Scheduler.failures` semantics for non-ticket failures, `caps.poison`, and serve consumer supervision.

## Scope fence
- clutch/runner.py
- clutch/drain.py
- clutch/serve.py
- tests/unit/test_dispatch_exception_terminal.py
- tests/unit/test_serve_dispatch_containment.py
- tests/regress_serve_dispatch_containment.py
- docs/how-clutch-works.md

## Acceptance criteria
1. The runner function appends exactly one `{"to": "infra_error", "stage": "dispatch", "reason": "dispatch_exception", "error": "ValueError: boom"}` transition when the stem's latest transition is `running`, and appends nothing when it is already terminal (not a second terminal); checked by `./dev.py test tests/unit/test_dispatch_exception_terminal.py`.
2. With two tickets dispatched concurrently through serve's per-ticket dispatch closure, ticket A's `ValueError("boom")` journals that same single `infra_error` terminal for A, the closure returns `"infra_error"` for A and re-offers it through `scheduler.update`, ticket B's closure still returns its scripted terminal, `Scheduler.failures` stays empty, serve is not stopping, and the engine log records `dispatch_exception` with `stem` and `error` and no `worker_failure`; checked by `./dev.py test tests/unit/test_serve_dispatch_containment.py`.
3. Serve consumer failures still stop serve: `Serve.run`'s consumer supervision and `Scheduler.raise_failure` are unchanged, so a non-ticket failure still reaches `Scheduler.failures`; checked by `./dev.py test tests/unit/test_serve_dispatch_containment.py`, which appends a non-ticket exception to `Scheduler.failures` and asserts `Scheduler.raise_failure` re-raises it.
4. Drain containment is unchanged; checked by `./dev.py test tests/unit/test_drain_containment.py`.
5. When the scripted `check` raises `ValueError("boom")` after `serve.stop()` has set `stopping`, ticket A gets no `dispatch_exception` terminal (not an `infra_error` with reason `dispatch_exception`). When the scripted `check` raises `asyncio.CancelledError`, ticket A also gets no `dispatch_exception` terminal and the cancellation is not converted into a return value. Both are checked by `./dev.py test tests/unit/test_serve_dispatch_containment.py`.
6. `uv run python tests/regress_serve_dispatch_containment.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `{"regression_result": "defect"}` with a non-zero exit on the merge base.

## Verification
```
uv run python tests/regress_serve_dispatch_containment.py
./dev.py test tests/unit/test_dispatch_exception_terminal.py tests/unit/test_serve_dispatch_containment.py tests/unit/test_drain_containment.py
```

## Definition of rejected
- Serve catches `BaseException`, or swallows a consumer failure or an exception raised while stopping.
- Drain and serve journal different bodies for a dispatch exception, or keep two copies of the journaling code.
- Edits to any file outside the fence, including `tests/integration/conftest.py` (`REAL_IO_TESTS`, `DISK_IO_SKIP`).

## Time budget
- expected: 25m
- stuck: 50m

## Regression
```
uv run python tests/regress_serve_dispatch_containment.py
```
- carries: tests/regress_serve_dispatch_containment.py
- carries: tests/unit/test_serve_dispatch_containment.py
