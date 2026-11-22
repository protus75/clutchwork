---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Runs before
- training-export-ship-gate
- regression-command-program-lint
- shared-git-fake
- shared-serve-rig-config
- shared-review-script
- check-rerun-failed-only

## Context
- tests/harness/host_loop.py::FixtureLoop
- tests/harness/host_loop.py::produce
- tests/integration/test_host_loop.py::production
- tests/integration/test_host_loop.py::test_host_loop_drives_supervised_fixture_serve
- tests/fakes.py::until
- tests/integration/serve_rig.py::until
- tests/unit/test_shared_fakes.py::test_until_timeout
- tests/integration/test_serve_rig_fakes.py::test_shared_helpers
- tests/integration/test_serve_rig_fakes.py::test_until_translates_timeout
- clutch/reconcile.py::reconcile
- tests/regress_lint_carries.py

## Goal / Why
Two groups of tests fail in most full-suite `pytest -n auto` runs and pass alone (evidence file in `evidence/`). Both fail for the same reason: they decide success or failure by real elapsed seconds, and since `scheduler.parallel` `max_runs: 2` was enabled on 2026-11-20 two tickets' test runs load the machine at once. A red Check from such a flake blocks unrelated tickets. After this ticket neither group depends on elapsed wall-clock time, so a loaded machine makes them slower, never red.

1. `tests/integration/test_host_loop.py` (all three tests ERROR at setup) runs five `FixtureLoop` members concurrently, each a real `python -m clutch engine serve` subprocess, and a member ends `LoopRefused ... did not merge: [... body={'to': 'abandoned'}]`. The body `{'to': 'abandoned'}` is exactly what `clutch/reconcile.py::reconcile` journals for an orphaned `running` run. The harness makes an orphan from a real-seconds limit: `FixtureLoop.stop` waits `asyncio.wait_for(asyncio.shield(self.task), 5)` for the serve to honor the kill request, and on `TimeoutError` cancels the task and `kill_group`s the process group while a ticket is `running`; `triage_pending` then restarts serve, whose startup reaps that ticket to `abandoned`. Two more real-second limits sit beside it: the serve exec in `start()` and the `box triage` exec in `triage_pending`, both `timeout=self.timeout + 10`, and the `until` deadline `self.clock() + timedelta(seconds=self.timeout)`. This is the most probable cause; the implementer first confirms it from a member's captured engine log or by the reproducer below, and if the log shows a different abandoning path, names it in the run record and removes the real-seconds limit that causes it instead.
2. `tests/integration/test_serve_admission.py::test_serve_admission_refusal_keeps_main_green[precheck|safety|integration|host-red]` fails with `production graph did not reach the scripted boundary`. `tests/integration/serve_rig.py::until` calls `tests/fakes.py::until`, which stops after 60 real seconds (`time.monotonic`); the case runs real git and `python3 -c` host commands while the loop busy-spins, so a loaded machine exceeds 60 s.

Chosen approach, not a longer timeout: remove the wall-clock deadline from the serve waits and let the global `pytest-timeout` (`timeout = 120`, thread method, `pyproject.toml`) be the only hang backstop; a genuine hang still fails.

- Host loop: `FixtureLoop.__init__` accepts `timeout=None`, meaning no deadline. `until` skips its deadline check, one derived `exec_timeout` (`None` when `self.timeout is None`, else `self.timeout + 10`) replaces `self.timeout + 10` in both the serve exec in `start()` and the `box triage` exec in `triage_pending`, and `stop` waits for the serve task to exit after publishing the kill request without a limit (keep the `ValueError` branch for a missing lifecycle and the `finally` group kill). The `production` fixture passes `timeout=None`. The negative case in `test_host_loop_drives_supervised_fixture_serve` that proves a stuck member raises `LoopRefused` is restructured: it builds the loop with `timeout=None` and runs `initialize()` and `start()` on the real clock, so `start()` waits for the real serve to write `control/active.json` without a deadline; then, just before `await loop.until(lambda: False)`, it assigns `loop.timeout = 0.3`, `loop.clock` to a fake clock and `loop.sleep` to a fake sleep that advances that clock by its argument. The deadline then expires after a fixed number of polls with no real waiting, and `loop.pgid` is already set. The injected-failure branch (`RuntimeError`) keeps `timeout=None`. `produce` and its caller `tests/integration/test_gates.py` keep their numeric default unchanged.
- Serve rig: `tests/fakes.py::until` accepts `timeout=None`, meaning no wall-clock deadline (default stays 60, so `test_until_timeout` and other callers are unchanged); `tests/integration/serve_rig.py::until` passes `timeout=None`. Because the rig no longer has a deadline, `tests/integration/test_serve_rig_fakes.py::test_until_translates_timeout` (which fakes `time.monotonic` to jump to 61 and waits on an always-false predicate) would hang; it is rewritten to `monkeypatch.setattr(fakes, "until", ...)` with an async stand-in that raises `AssertionError`, then still asserts that `serve_rig.until` raises `AssertionError` with the message `production graph did not reach the scripted boundary`. No deadline is involved in that test.

Rejected simpler approach: raising 30 and 60 to larger numbers. It only moves the load level at which the flake returns, and the evidence shows it already fails 1 of 3 runs on older commits.

Class prevention (named, in scope because the carried reproducer is the same file): the reproducer pins both waits as injected-delay cases, so a future real-seconds limit on these two waits turns Check red. A repo-wide lint for `time.monotonic` deadlines in tests is not cheap or certain; it goes to the Suggestion Box via `clutch box suggest`, not this diff.

Item 3 of the same report, `test_live_keep_dispatches_again_without_restart` seeing two keep signals, is a different cause (a test premise race, not a deadline) and has its own ticket `serve-live-keep-single-verdict`.

## Boundary contract
### Fixture loop wait contract
- disposition: extend
- owner: tests/harness/host_loop.py
- consumers: tests/integration/test_host_loop.py (production fixture and the stuck-member case) and `produce` used by tests/integration/test_gates.py
- observable change: `FixtureLoop(timeout=None)` waits for evidence, for serve exit and for the `box triage` exec without a real-seconds limit; a numeric timeout is still measured by the injected `clock` and `sleep`, so a fake clock makes it expire deterministically; `stop` no longer cancels a serve that is slow to honor the kill request
- compatibility: restores the intended behavior that a loaded machine only slows the harness; `produce` and the numeric default of 60 are unchanged, and a stuck member still raises `LoopRefused`
- acceptance: the carried reproducer's stop case and the existing member tests pass; no member ends `abandoned`
- tests: tests/regress_serve_flaky_waits.py and tests/integration/test_host_loop.py
- post-merge source of truth: tests/harness/host_loop.py

### Serve rig until
- disposition: extend
- owner: tests/fakes.py
- consumers: tests/integration/serve_rig.py::until, every serve test that imports it, and tests/integration/test_serve_rig_fakes.py (`test_until_translates_timeout` is rewritten to inject a failing `fakes.until` instead of relying on the rig's old 60 s deadline)
- observable change: `fakes.until(..., timeout=None)` has no wall-clock deadline and `serve_rig.until` uses it
- compatibility: default `timeout=60` and the raised `AssertionError` are unchanged for every other caller; `serve_rig.until` still translates an `AssertionError` from `fakes.until` into `production graph did not reach the scripted boundary`; restores the passing-when-loaded behavior of the admission cases
- acceptance: the reproducer's until case returns although the monotonic clock leaps past 60 s, and `test_until_translates_timeout` still sees the translated message
- tests: tests/regress_serve_flaky_waits.py, tests/unit/test_shared_fakes.py and tests/integration/test_serve_rig_fakes.py
- post-merge source of truth: tests/fakes.py

## Scope in / Scope out
In: the two extensions above, the `production` fixture and the stuck-member case in `tests/integration/test_host_loop.py` (forced: the case passes a numeric `timeout` and must now inject a fake clock and sleep), the rewrite of `test_until_translates_timeout` in `tests/integration/test_serve_rig_fakes.py` (forced: it relies on the rig's removed 60 s deadline and would hang), and a new reproducer `tests/regress_serve_flaky_waits.py`. The reproducer prints one JSON object and works in two parts, each reporting `defect` when its old behavior is present:
- until part: replace `tests.fakes.time` with an object whose `monotonic()` adds 100 s per call, then await `tests.integration.serve_rig.until(SimpleNamespace(time=FakeClock()), predicate)` where the predicate turns true on its 300th call. Old code raises `AssertionError` (defect); fixed code returns (pass).
- stop part: build a `FixtureLoop` under a temp root with a recording fake exec, write `control/active.json` as `{"lifecycle_id": "x", "hold_id": null}` under its state dir, set `loop.task` to a task that sleeps 5.5 real seconds then returns `(0, "", "")`, and await `loop.stop()`. Old code times out at 5 s and cancels the task (defect: `task.cancelled()`); fixed code lets it finish (pass). The 5.5 s is a fixed injected delay larger than the old constant, not a load-dependent race.
Any import failure or unexpected exception prints `{"regression_result": "error"}` with the traceback on stderr. Model it on `tests/regress_lint_carries.py`.
Out: other `until` helpers (`tests/waiting.py`), `tests/integration/test_serve_admission.py` itself, `tests/integration/test_gates.py`, other tests in `tests/integration/test_serve_rig_fakes.py`, serve production code, the scheduler config, and any skip, xfail, retry loop or raised timeout. The fix to `test_live_keep_dispatches_again_without_restart` is `serve-live-keep-single-verdict`.

## Scope fence
- tests/harness/host_loop.py
- tests/integration/test_host_loop.py
- tests/fakes.py
- tests/integration/serve_rig.py
- tests/integration/test_serve_rig_fakes.py
- tests/regress_serve_flaky_waits.py

## Acceptance criteria
1. `uv run python tests/regress_serve_flaky_waits.py` prints `{"regression_result": "pass"}`, not `defect`, so neither the 5 s stop limit nor the 60 s `until` deadline decides the result.
2. `./dev.py test tests/integration/test_host_loop.py` passes, and the stuck-member case, which starts the loop with `timeout=None` and swaps in a numeric `loop.timeout`, a fake `loop.clock` and a fake `loop.sleep` only before `until(lambda: False)`, raises `LoopRefused` (not a hang, not `RuntimeError`) without a real-time wait.
3. `./dev.py test tests/integration/test_serve_admission.py -k refusal_keeps_main_green` passes, and `./dev.py test tests/unit/test_shared_fakes.py tests/integration/test_serve_rig_fakes.py` passes, so `fakes.until` with the default `timeout=60` still raises `AssertionError` for a predicate that never becomes true, and `test_until_translates_timeout`, with `fakes.until` monkeypatched to raise `AssertionError`, still sees `production graph did not reach the scripted boundary` without any deadline.
4. A search of the fenced harness and rig files with `grep -n "wait_for\|timedelta(seconds=self.timeout)" tests/harness/host_loop.py` finds no unconditional real-seconds wait in `stop`; a numeric deadline appears only behind the `timeout is not None` check.
5. `./dev.py test tests/integration/test_gates.py` passes, so `produce` and its numeric default are unchanged.

## Verification
```
uv run python tests/regress_serve_flaky_waits.py
./dev.py test tests/integration/test_host_loop.py tests/integration/test_serve_admission.py tests/integration/test_gates.py tests/unit/test_shared_fakes.py tests/integration/test_serve_rig_fakes.py
```

## Definition of rejected
Reject the branch if it raises a timeout number instead of removing the deadline, adds skip, xfail, a retry loop or a quarantine, removes a test from the gate, changes serve production code, edits `tests/integration/test_serve_admission.py`, makes any other caller's `fakes.until` default unbounded, or deletes `test_until_translates_timeout` instead of rewriting it.

## Time budget
- expected: 25m
- stuck: 50m

## Regression
```
uv run python tests/regress_serve_flaky_waits.py
```
- carries: tests/regress_serve_flaky_waits.py
