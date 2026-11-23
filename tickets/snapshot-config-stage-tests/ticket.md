---
state: draft
source: box:suggestion
priority: P1
kind: chore
---

## Depends on
none

## Context
- clutch/config.py::snapshot_config
- clutch/config.py::ConfigSnapshot
- clutch/stages.py::_check_host_results
- tests/unit/test_check_rerun_failed_only.py
- tests/unit/test_training_config.py
- tests/config_fixture.py

## Goal / Why
Serve and drain hand stages and the runner a `ConfigSnapshot` from `snapshot_config`: every list becomes a tuple, every dict a read-only mapping, and every model a fields-only view. Unit tests build real `Config` models, so list-only operations on those fields (for example `entry.argv + [...]`, fixed in 1dff4d00) passed Check and then crashed under serve, spending ticket attempts as infra_error. This is the second such crash in one day. It is the cause fix for that class, and the instance is already fixed. Declined record declined-box-001107 turned down only a narrow method-call guard when one incident existed. This incident has a different trigger, so a method guard would not have caught it.

After this ticket, a new unit test runs the Check host-results path (rerun argv, `MechanicalCheck.argv`) and the `training_data` reading path (`.enabled`, `training_exclude`) on `snapshot_config(config)`, where `config` is a real `Config` loaded from `tests/config_fixture.build_config` text. A future list-only operation on a snapshot field fails the unit suite at Check, not under serve. `tests/unit/test_check_rerun_failed_only.py` already freezes one `MechanicalCheck`; this ticket covers the Config-level fields that test does not reach and changes no shared fixtures.

## Boundary contract
### Config snapshot test coverage
- disposition: reuse
- owner: clutch/config.py::snapshot_config
- consumers: stage and runner code that reads `ctx.config` under serve and drain
- observable change: none in production; a new unit test fails when a stage applies a list-only operation to a snapshot field
- compatibility: `snapshot_config`, `clutch/stages.py` and `clutch/runner.py` are unchanged, so existing behavior is preserved
- acceptance: the new test passes on current code and fails when `entry.argv + [...]` is reinstated
- tests: tests/unit/test_stages_snapshot_config.py
- post-merge source of truth: clutch/config.py::snapshot_config for the frozen shape, and the new test for what stages may do with it

## Scope in / Scope out
Scope in: one new unit test file, `tests/unit/test_stages_snapshot_config.py`. It writes config text with `build_config` under `tmp_path`, loads it with `load_config`, takes `snapshot_config(config)`, and uses the snapshot as `ctx.config` / the check entry in two cases: (a) `stages._check_host_results` with a rerun selection (argv extended with `--clutch-select`), modelled on the `run_check` helper in `tests/unit/test_check_rerun_failed_only.py` but written in the new file, not imported from it; (b) the `training_data` reads that `clutch/runner.py` performs on `ctx.config.training_data`. It also asserts that every list-valued field of the loaded `Config` is a tuple in the snapshot, so a change of the frozen type must update this test knowingly.
Scope out: any change to `clutch/config.py`, `clutch/stages.py` or `clutch/runner.py`; edits to existing tests, `tests/config_fixture.py`, `conftest.py` or shared helpers; freezing lists into a list-compatible type, which would weaken immutability.

## Scope fence
- tests/unit/test_stages_snapshot_config.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_stages_snapshot_config.py` passes, with the rerun case run on a `ConfigSnapshot` check entry: the second call's argv equals `[*argv, "--clutch-select", <path>]` as a list, not a `TypeError`.
2. The training case reads `snapshot.training_data.enabled` and calls `training_exclude(snapshot.training_data)` and returns a value, not an `AttributeError` or `TypeError`; checked by `./dev.py test tests/unit/test_stages_snapshot_config.py`.
3. A test asserts `isinstance(snapshot.providers, tuple)` and that no list-valued `Config` field survives as a `list` in the snapshot, so it fails if freezing changes; checked by `./dev.py test tests/unit/test_stages_snapshot_config.py`.
4. The new test fails when the `--clutch-select` line in `clutch/stages.py::_check_host_results` is temporarily changed back to `entry.argv + [...]` (tuple plus list `TypeError`); the implementer confirms this once and records it in the run record, checked by `./dev.py test tests/unit/test_stages_snapshot_config.py`.
5. The unit suite stays green: `./dev.py test tests/unit`.

## Verification
```
./dev.py test tests/unit/test_stages_snapshot_config.py
./dev.py test tests/unit
```

## Definition of rejected
The branch edits any file outside the fence, changes production code, or adds a test that passes with the `entry.argv + [...]` regression reinstated.

## Time budget
- expected: 15m
- stuck: 30m
