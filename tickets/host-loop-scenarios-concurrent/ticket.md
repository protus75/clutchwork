---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- tests/integration/test_host_loop.py
- tests/harness/host_loop.py::FixtureLoop

## Goal / Why
The module fixture `production` in `tests/integration/test_host_loop.py` runs the five scenarios in `hosts.fixture.scaffold.SCENARIOS` one after another. Each scenario starts a real `python -m clutch engine serve` subprocess and polls until it merges, so the fixture takes about 35s; a cProfile run on 2026-11-19 showed 33.8s of that spent in `select.epoll.poll` waiting on those subprocesses. Its first test, `test_host_loop_drives_supervised_fixture_serve`, is the slowest integration test (36-39s) and alone sets the floor on the integration check's wall time under `-n auto`.

When done, the fixture runs the five scenarios concurrently with `asyncio.gather`, so it takes about as long as the slowest single scenario (about 7-8s), and every `test_host_loop` test still passes with the same evidence.

## Boundary contract
none
- reason: tests encoding an existing contract; only the test fixture's scheduling changes, and the harness, the engine, and the report schema are unchanged.

## Scope in / Scope out
Scope in, all in `tests/integration/test_host_loop.py`:
- In the `production` fixture's `exercise()`, build one `FixtureLoop` per scenario (each under its own `root / name`, sharing the one `RecordingExec`), then run each loop's `initialize()`, `exercise()`, and `stop()` (in a `finally`) concurrently with `asyncio.gather`.
- Keep `members` in `SCENARIOS` order, not completion order: the tests index `report.entries[:3]` and `members[-2:]`, and `HostLoopReport` requires three merge entries followed by regression and escape.
- If concurrency reorders the shared `RecordingExec` lists, compare `exec_.spawned` and `exec_.killed` as sorted lists in `test_host_loop_drives_supervised_fixture_serve`; the assertion still requires every spawned process group to be killed. Nothing else in that test changes.

Scope out: `tests/harness/host_loop.py`, `hosts/fixture/`, the engine, the per-scenario `timeout=30`, and the `failure()` block at the end of `test_host_loop_drives_supervised_fixture_serve`.

## Scope fence
- tests/integration/test_host_loop.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_host_loop.py` passes every test in the file, with entries still in `SCENARIOS` order (a completion-order report fails `HostLoopReport` validation and the `entries[:3]` producing-run assertion).
2. `./dev.py test tests/integration/test_host_loop.py --durations=5` reports setup of `test_host_loop_drives_supervised_fixture_serve` (the `production` fixture) at most 8s on a 20-core machine, not the current ~35s, so the test fits the 10s per-test cap in `integration-test-time-cap`.
3. `./dev.py test tests/integration/test_host_loop.py` still fails when a spawned serve process group is never killed: the spawned-equals-killed check compares the full sets of process groups, not just their counts.

## Verification
```
./dev.py test tests/integration/test_host_loop.py --durations=5
```

## Definition of rejected
- The fixture still runs scenarios one after another, or shares one root between scenarios.
- `members` or `report.entries` follow completion order instead of `SCENARIOS` order.
- Any assertion is dropped or weakened other than comparing the spawned and killed lists as sorted.
- Any file outside the fence changes, including raising a timeout to hide contention.

## Time budget
- expected: 15m
- stuck: 30m
