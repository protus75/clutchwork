---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- host-loop-scenarios-concurrent
- watch-tests-fixture-repo

## Context
- clutch/stages.py::_check_host_results
- clutch/config.py::MechanicalCheck
- clutch/config.py::_check_references
- clutch/testreport.py::slow_tests
- clutch/docs/host-contract.md#Complete field inventory
- clutch/docs/host-contract.md#Checks and injectable seams
- docs/how-clutch-works.md#5.4 Host checks
- tests/unit/test_host_check_selection.py
- tests/unit/test_check_timing.py
- tests/integration/test_fixture_host.py::test_fixture_profile_loads
- tests/harness/daemon_soak.py::produce
- tests/harness/daemon_soak.py::_run_member
- tests/integration/test_daemon_soak_runner.py::evidence
- tests/integration/test_daemon_soak_runner.py::test_daemon_soak_is_rederivable
- tests/integration/test_daemon_soak_runner.py::test_daemon_soak_runs_production_serve
- tests/integration/test_fault_injection.py

## Goal / Why
Nothing limits how long one test may take, so slow tests merge unnoticed and stretch every Check stage. On 2026-11-19 at `c407fcd6`, `./dev.py test tests/integration --durations=25` showed `test_host_loop_drives_supervised_fixture_serve` at 34 s, three `test_watch.py` snapshot tests at 28 s each, `test_daemon_soak_is_rederivable` at 16.8 s, the `test_daemon_soak_runner.py` module fixture `evidence` at 9.4 s of setup, and `test_fault_injection.py` crash shards at 5-9 s. The integration check took 100-117 s against a 66 s ideal for the summed test time spread over 20 workers, because a few long tests decide when it finishes. The owner chose a 10 second cap.

When done, a mechanical check entry may declare `max_test_seconds`. Check fails that entry when any test's first-run recorded seconds exceed the cap. Recorded seconds are the setup + call + teardown sum that `clutch.testreport` already writes, so they include xdist contention and module-fixture setup charged to the first test that uses the fixture. Each finding names the test, its seconds and the cap, with a paved road. This repo's `integration` entry sets `max_test_seconds: 10`. Main stays green: the two `Depends on` tickets fix the four slowest tests, and this ticket brings the soak fixture and fault-injection shards to at most 5 s recorded and `test_daemon_soak_is_rederivable` to at most 7 s, so contention does not tip them over.

## Boundary contract
### Mechanical check config
- disposition: extend
- owner: clutch/config.py
- consumers: Check stage host-results reading in clutch/stages.py, host config files, clutch/docs/host-contract.md field inventory
- observable change: `MechanicalCheck` gains optional `max_test_seconds` (positive float, default unset); `_check_references` refuses it without `results` on the same entry, as it does `slow_test_seconds`
- compatibility: existing configs stay valid; with the key unset Check behaves exactly as today
- acceptance: `max_test_seconds: 0` and `max_test_seconds` without `results` are refused with the field's key path
- tests: tests/unit/test_check_test_cap.py
- post-merge source of truth: clutch/config.py

### Check stage test-time cap
- disposition: extend
- owner: clutch/stages.py
- consumers: checks.json readers, the Check verdict, run records
- observable change: when the entry sets `max_test_seconds`, every first-run test whose recorded seconds exceed it adds a finding with `code` = the entry code, `path` = the entry's `results` path, a message naming the test, its seconds and the cap, and the paved road `make the test faster: fake the clock and IO, share a module fixture, or run independent scenarios concurrently`; any such finding fails the entry
- compatibility: entries without the key are unchanged; merge-time integration checks keep using exit status alone; timing, slow-test and coverage recording are unchanged
- acceptance: a test at exactly the cap passes; one above it fails
- tests: tests/unit/test_check_test_cap.py
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
Scope in:
- `clutch/config.py`: add `max_test_seconds: Annotated[float, Field(gt=0)] | None = None` to `MechanicalCheck`, and add `max_test_seconds` to the field tuple `_check_references` checks for a missing `results`.
- `clutch/stages.py` `_check_host_results`: after the first run's results are read, when `entry.max_test_seconds` is set, add one finding per test in `first.seconds` whose value is greater than the cap, sorted by seconds descending then node id. Every report the entry returns carries these findings, and the verdict is `fail` when there are any.
- `config.yaml`: add `max_test_seconds: 10` to the `integration` mechanical entry only.
- `tests/harness/daemon_soak.py` `produce`: run the members of `DAEMON_SOAK_MEMBERS` concurrently with `asyncio.gather` instead of one after another, keeping `entries` in `DAEMON_SOAK_MEMBERS` order. Each member already has its own root under `root / name`. If members share state that makes concurrent runs unsafe, fix that shared state in the harness.
- `tests/integration/test_daemon_soak_runner.py`: the `evidence` fixture keeps `members` in `DAEMON_SOAK_MEMBERS` order (sort by `DAEMON_SOAK_MEMBERS.index(m.name)`), so the tests that index `members` by position are unchanged. `test_daemon_soak_runs_production_serve` compares `offers` and `consumed` per member instead of as one global sequence: within each member the pairs keep their exact order, and across members they make up exactly the same five pairs. `test_daemon_soak_is_rederivable` runs its two `produce` calls together with `asyncio.gather`. Both read HEAD first, so every merge-base and equality assertion still holds. Nothing else in the file changes.
- `tests/integration/test_fault_injection.py`: raise `SHARDS` so each crash shard records at most 5 s. `test_shards_partition_every_crash_case` keeps proving that the shards partition every case.
- `tests/unit/test_host_check_selection.py`: add `max_test_seconds=None` to the `NS` entry; nothing else changes.
- `tests/integration/test_fixture_host.py` `test_fixture_profile_loads`: add `"max_test_seconds": None` to the expected `model_dump()`; nothing else changes.
- `clutch/docs/host-contract.md`: add `max_test_seconds: unset` to the `MechanicalCheck` defaults row in "Complete field inventory", and one sentence on the cap in "Checks and injectable seams".
- `docs/how-clutch-works.md` section 5.4: one sentence on the cap after the slow-test sentence.
- New `tests/unit/test_check_test_cap.py` covering the criteria below with fakes, built the way `tests/unit/test_host_check_selection.py` drives `_check_host_results`.

Scope out: the unit suite's whole-suite `[unit] budget_seconds` in `test-gate.toml` and `clutch/testguard.py`, which stay as they are; `test_host_loop.py` (`host-loop-scenarios-concurrent`); `test_watch.py` (`watch-tests-fixture-repo`); the integration tests that read the live checkout (`integration-test-repo-isolation`); the unit coverage-context cost; any retry or contention allowance for the cap; and the hot integration test files.

## Scope fence
- clutch/config.py
- clutch/stages.py
- config.yaml
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/harness/daemon_soak.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/test_fault_injection.py
- tests/integration/test_fixture_host.py
- tests/unit/test_host_check_selection.py
- tests/unit/test_check_test_cap.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_check_test_cap.py` passes, with a case where results `{"a": 10.0, "b": 10.5, "c": 12.0}` and `max_test_seconds=10.0` give a `fail` report with exactly two cap findings, for `c` then `b`, each naming its test, seconds and the cap. This rules out a `>=` comparison that would also flag `a`, and a missing sort.
2. `./dev.py test tests/unit/test_check_test_cap.py` passes, with a case where the same results and `max_test_seconds` unset give a `pass` report with no findings. The cap is not applied by default.
3. `./dev.py test tests/unit/test_check_test_cap.py` passes, with cases where `MechanicalCheck(code="x", argv=["test"], trigger="always", severity="hard", results="r.json", max_test_seconds=0)` raises a validation error whose location names `max_test_seconds` while the same entry with `max_test_seconds=10` loads, and `_check_references` given an entry with `max_test_seconds` but no `results` raises `ConfigError` with key `review.mechanical.0.max_test_seconds`.
4. `./dev.py test tests/integration/test_host_contract.py tests/integration/test_fixture_host.py tests/unit/test_host_check_selection.py` passes with the new field in the inventory and dumps.
5. `./dev.py test tests/integration --durations=40` passes, and in its durations list every phase of `test_daemon_soak_is_rederivable` is at most 7.00 s, and every phase of the first test that uses the `evidence` fixture and of each `test_crash_at_every_write_point_tolerates_torn_tail_and_keeps_once_semantics` case is at most 5.00 s.
6. The branch's own Check stage `integration` report in `tickets/integration-test-time-cap/checks.json` has verdict `pass` with `max_test_seconds: 10` set in `config.yaml`.

## Verification
```
./dev.py test tests/unit/test_check_test_cap.py tests/unit/test_host_check_selection.py tests/unit/test_check_timing.py
./dev.py test tests/integration/test_host_contract.py tests/integration/test_fixture_host.py tests/integration/test_host_mechanical.py
./dev.py test tests/integration/test_daemon_soak_runner.py tests/integration/test_daemon_soak.py tests/integration/test_reliability_battery.py tests/integration/test_fault_injection.py --durations=40
```

## Definition of rejected
- Any test that existed before this ticket is skipped, deleted, marked slow, or has assertions weakened to meet the cap.
- The cap allows contention, retries a test that ran over, or applies to entries that do not set `max_test_seconds`.
- `max_test_seconds` is set on the `unit` entry, or `[unit] budget_seconds` changes.
- The cap is enforced in a pytest plugin instead of the Check stage.
- The only allowed assertion changes are the per-member `offers`/`consumed` comparison and the `members` ordering in `test_daemon_soak_runner.py` described in Scope in.

## Time budget
- expected: 25m
- stuck: 50m
