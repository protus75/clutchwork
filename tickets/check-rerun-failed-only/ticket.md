---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Runs before
- flake-fix-jumps-queue

## Context
- clutch/stages.py::_check_host_results
- clutch/stages.py::check_hosts
- clutch/stages.py::run_host_command
- clutch/testreport.py
- tests/integration/test_host_mechanical.py
- tests/unit/test_stages_flake_coverage.py
- tests/integration/conftest.py
- clutch/testguard.py

## Goal / Why
When one test fails at random in a Check host command (the integration suite takes about 85 s), Check reruns the whole command (`check/host-NN-rerun.txt`), and when the report still fails it runs the whole command again on the merge base (`check/host-NN-base.txt`). On 2026-11-21 Check went from about 110 s to 300–390 s per ticket. The suite itself did not slow down: `roadmap-meta-resync`, a 2-line change, spent 2 min on the first run, 1.5 min rerunning all 3595 integration tests because `test_serve_admission_refusal_keeps_main_green` timed out, and 2.7 min on the base run. After this ticket the rerun of a host entry with no `coverage` field executes only the test ids that failed on the first run, so a random integration failure costs seconds instead of a second full suite. Entries with `coverage` keep the full rerun, because `clutch coverage gate` skips its thresholds when tests fail (`clutch/covgate.py` `run_gate`) and only the full rerun checks them. The base run is unchanged.

## Boundary contract
### Test selection option
- disposition: extend
- owner: clutch/testreport.py
- consumers: clutch/stages.py Check reruns and base runs
- observable change: new pytest option `--clutch-select PATH`; PATH is a JSON list of node ids, and `pytest_collection_modifyitems` deselects every collected item whose `nodeid` is not in that list (reported through `config.hook.pytest_deselected`)
- compatibility: without the option collection is unchanged; `--clutch-results` output keeps its schema
- acceptance: criterion 1
- tests: tests/unit/test_testreport_select.py
- post-merge source of truth: clutch/testreport.py

### Check rerun and base scope
- disposition: extend
- owner: clutch/stages.py `_check_host_results`
- consumers: every ticket's Check stage for host entries with a `results` file
- observable change: for host entries with a `results` file and no `coverage` field, the rerun appends `--clutch-select <results path with suffix .select.json>` holding the first run's failed node ids to `entry.argv`; entries with `coverage` rerun `entry.argv` unchanged; capture names, flake detection, quarantine, the base run in `check_hosts` and `base_red` rules are unchanged
- compatibility: the line `if result.rc != 0 and "failed" not in last.values(): findings.extend(report.findings)` stays; the quarantine-release loop reads `{**first, **last}` so a passing quarantined test is still released when an unrelated test triggers a selected rerun
- acceptance: criteria 2 and 3
- tests: tests/unit/test_check_rerun_failed_only.py
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
Scope in:
- clutch/testreport.py: add `--clutch-select` as above.
- clutch/stages.py `_check_host_results`: give `run(name)` an optional list of node ids (`run(name, selected=None)`); when given, write them as JSON with `ctx.fs.write` to `path.with_suffix(".select.json")` (where `path` is the results file `run` already reads) and append `["--clutch-select", str(that path)]` to `entry.argv`. The rerun passes the first run's failed ids only when `entry.coverage is None`. Keep the rerun rc-findings line. The quarantine-release loop checks `{**first, **last}`. The function's signature and return value are unchanged.
- New tests/unit/test_check_rerun_select.py runs the changed lines with fakes under `tmp_path`: `pytest_collection_modifyitems` with stand-in items and config, and `_check_host_results` with a recording exec and a results file written by the fake.
- New tests/unit/test_testreport_select.py and tests/unit/test_check_rerun_failed_only.py use only in-memory seams: stand-in items and config for the `clutch.testreport` hooks, and a recording exec plus `ctx.fs` fakes for `_check_host_results`. They start no process and write no real disk, because `clutch/testguard.py` blocks subprocess and disk I/O in unit tests and the I/O guard in `tests/integration/conftest.py` blocks it in integration tests outside `REAL_IO_TESTS`.
Scope out:
- The base run in `check_hosts` (it still runs the whole command), fixing the flaky tests themselves, the flake quarantine rules, `test-gate.toml`, and config.yaml host entries.

## Scope fence
- clutch/testreport.py
- clutch/stages.py
- tests/unit/test_check_rerun_select.py
- tests/unit/test_testreport_select.py
- tests/unit/test_check_rerun_failed_only.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_testreport_select.py` proves, with three stand-in items and a stand-in config whose `--clutch-select` file names one of them, that `pytest_collection_modifyitems` keeps exactly that one and passes the other two to `config.hook.pytest_deselected`, not all three kept.
2. `./dev.py test tests/unit/test_check_rerun_failed_only.py` proves that when the first run records one failed id among many, the rerun argv is `entry.argv + ["--clutch-select", <path>]` and that file holds exactly that id, not the full command again.
3. `./dev.py test tests/unit/test_check_rerun_failed_only.py` proves a selected test that fails again on the rerun still produces the `failed on rerun` finding, and one that passes is treated as flaky exactly as before.
4. `./dev.py test tests/unit/test_check_rerun_select.py` proves the selection hook keeps only listed node ids and the rerun argv carries `--clutch-select`, without starting a process.
5. `./dev.py test tests/unit/test_stages_flake_coverage.py tests/unit/test_check_rerun_failed_only.py` passes with `tests/unit/test_stages_flake_coverage.py` unchanged, and `tests/unit/test_check_rerun_failed_only.py` covers the fail-closed sequence `[(1, {"a": "failed"}), (1, {"a": "passed"}), (0, {})]` (still a finding) and the `check/host-01-rerun.txt` capture name, which `tests/integration/test_host_mechanical.py` pins today but `DISK_IO_SKIP` skips.
6. `./dev.py test tests/unit/test_check_rerun_failed_only.py` proves an entry with `coverage` set reruns exactly `entry.argv` with no `--clutch-select`, and that a quarantined test that passed on the first run is still released when an unrelated test triggers a selected rerun.

## Verification
```
./dev.py test tests/unit/test_check_rerun_select.py tests/unit/test_stages_flake_coverage.py tests/unit/test_testreport_select.py tests/unit/test_check_rerun_failed_only.py
```

## Definition of rejected
Skipping the rerun or base run, changing flake or quarantine rules, adding a config knob, or files outside the fence change.

## Time budget
- expected: 20m
- stuck: 40m