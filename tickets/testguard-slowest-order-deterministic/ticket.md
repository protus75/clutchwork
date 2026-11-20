---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Context
- tests/integration/test_testguard.py::test_budget_and_slowest
- tests/integration/test_testguard.py::fake_clock
- clutch/testguard.py::pytest_runtest_logreport
- tests/regress_already_satisfied.py

## Goal / Why
`tests/integration/test_testguard.py::test_budget_and_slowest` decides which of two inner tests is slower from real wall time: `test_slowest` sleeps 0.2s and `test_slower` sleeps 0.1s, and the test asserts the report lists `test_slowest` before `test_slower`. Under the load of the full parallel suite a 0.1s sleep can take longer than a 0.2s one: on 2026-11-20 in `meta-schema-and-refresh-r2` attempt 3 the report printed `test_slower: 0.222s` first, the assertion `assert 118 < 70` failed, the bare rerun and the base run both passed 3519 tests, so Check classified it as a flake, found the quarantine cap full, and stopped a ticket whose diff was sound (evidence file). After this ticket the test never reads real elapsed time for its ordering: the inner project fixes each inner test's reported duration, so the assertion holds at any load.

Why: a load-sensitive test in the suite every ticket runs fails unrelated tickets at random, and a failure with a full quarantine blocks the ticket for good.

## Boundary contract
none
- reason: tests encoding an existing contract; `clutch/testguard.py` and the production report format are unchanged, only the inner test project built by `test_budget_and_slowest` changes how it produces its durations

## Scope in / Scope out
In: in `test_budget_and_slowest`, the inner project written by `pytester.makepyfile` drops `time.sleep` and gains a plugin module (written with `pytester.makepyfile(slow_durations=...)` and loaded by passing `-p slow_durations` to both `run` calls of the test, with `pytester.syspathinsert()` called after the module is written and before the first `run`, because `-p` imports the plugin before any conftest and the in-process `runpytest` does not put the pytester directory on `sys.path`; `run()` itself is unchanged) whose `pytest_runtest_makereport` hook wrapper sets `report.duration` for the `call` phase by test name: `test_slowest` 2.0, `test_slower` 1.0, every other test 0.0. It is a plugin, not a `conftest.py`, because `fake_clock` already writes the inner `conftest.py` with `pytester.makeconftest` and a second `makeconftest` would replace the fake clock. `pytest_runtest_logreport` in `clutch/testguard.py` sums `report.duration`, so the listed order no longer depends on the clock. The two assertions on order and on the ten listed lines stay as written. Create `tests/regress_testguard_slowest_load.py`, the carried reproducer shaped like `tests/regress_already_satisfied.py`: it runs `pytest -q -o addopts= tests/integration/test_testguard.py::test_budget_and_slowest` in a subprocess with `PYTHONPATH` set to a carried directory `tests/regress_sleep_skew/` whose `sitecustomize.py` wraps `time.sleep` so that any sleep shorter than 0.15s lasts 0.2s longer (the 2026-11-20 load inversion). It prints only `{"regression_result": "pass"}` and exits 0 when that run passes, `{"regression_result": "defect"}` and exits 1 when it fails, and `{"regression_result": "error"}` and exits 2 when the run cannot be decided (traceback to stderr).

Out: `clutch/testguard.py`, the other tests in test_testguard.py, the quarantine cap and the five long-held quarantines (filed separately to the Suggestion Box), and any new test in a hot test file.

## Scope fence
- tests/integration/test_testguard.py
- tests/regress_testguard_slowest_load.py
- tests/regress_sleep_skew

## Acceptance criteria
1. With `time.sleep` skewed so a 0.1s sleep lasts 0.3s, `test_budget_and_slowest` passes, where at base it fails with `AssertionError`, checked by `uv run python tests/regress_testguard_slowest_load.py`.
2. The test still asserts `test_slowest` is listed before `test_slower`, still asserts exactly ten listed lines and still asserts the run is `OK` under a 4s fake clock against a 5s budget, so a plugin that stopped sorting by duration would fail it, checked by `./dev.py test tests/integration/test_testguard.py`.
3. The inner project of `test_budget_and_slowest` calls `time.sleep` nowhere, checked by `./dev.py test tests/integration/test_testguard.py`.

## Verification
```
./dev.py test tests/integration/test_testguard.py
uv run python tests/regress_testguard_slowest_load.py
```

## Definition of rejected
- The inner project still orders by real elapsed time, or the test lengthens its sleeps instead of removing them.
- Any edit to `clutch/testguard.py`, or an assertion in the test weakened or removed.
- A new test added to a hot test file.

## Time budget
- expected: 10m
- stuck: 20m

## Regression
```
uv run python tests/regress_testguard_slowest_load.py
```
- carries: tests/regress_testguard_slowest_load.py
- carries: tests/regress_sleep_skew
