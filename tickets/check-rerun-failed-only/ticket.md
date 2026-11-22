---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/stages.py::_check_host_results
- clutch/stages.py::check_hosts
- clutch/stages.py::run_host_command
- clutch/testreport.py
- tests/integration/test_host_mechanical.py

## Goal / Why
When one test fails at random in a Check host command (the integration suite takes about 85 s), Check reruns the whole command (`check/host-NN-rerun.txt`), and when the report still fails it runs the whole command again on the merge base (`check/host-NN-base.txt`). On 2026-11-21 Check went from about 110 s to 300–390 s per ticket. The suite itself did not slow down: `roadmap-meta-resync`, a 2-line change, spent 2 min on the first run, 1.5 min rerunning all 3595 integration tests because `test_serve_admission_refusal_keeps_main_green` timed out, and 2.7 min on the base run. After this ticket the rerun executes only the test ids that failed on the first run, so a random failure costs seconds instead of a second full suite. The base run is unchanged.

## Boundary contract
### Test selection option
- disposition: extend
- owner: clutch/testreport.py
- consumers: clutch/stages.py Check reruns and base runs
- observable change: new pytest option `--clutch-select PATH`; PATH is a JSON list of node ids, and `pytest_collection_modifyitems` deselects every collected item whose `nodeid` is not in that list (reported through `config.hook.pytest_deselected`)
- compatibility: without the option collection is unchanged; `--clutch-results` output keeps its schema
- acceptance: criterion 1
- tests: tests/integration/test_testreport_select.py
- post-merge source of truth: clutch/testreport.py

### Check rerun and base scope
- disposition: extend
- owner: clutch/stages.py `_check_host_results`
- consumers: every ticket's Check stage for host entries with a `results` file
- observable change: the rerun appends `--clutch-select <results path with suffix .select.json>` holding the first run's failed node ids to `entry.argv`; capture names, flake detection, quarantine, the base run in `check_hosts` and `base_red` rules are unchanged
- compatibility: timing and coverage still come from the first run
- acceptance: criteria 2 and 3
- tests: tests/integration/test_check_rerun_failed_only.py
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
Scope in:
- clutch/testreport.py: add `--clutch-select` as above.
- clutch/stages.py `_check_host_results`: give `run(name)` an optional list of node ids; when given, write them as JSON with `ctx.fs.write` to `path.with_suffix(".select.json")` (where `path` is the results file `run` already reads) and append `["--clutch-select", str(that path)]` to `entry.argv`. The rerun passes the first run's failed ids. The function's signature and return value are unchanged.
- New tests/unit/test_check_rerun_select.py runs the changed lines with fakes under `tmp_path`: `pytest_collection_modifyitems` with stand-in items and config, and `_check_host_results` with a recording exec and a results file written by the fake.
- New tests/integration/test_testreport_select.py runs pytest in a `tmp_path` project with `-p clutch.testreport --clutch-select`, and new tests/integration/test_check_rerun_failed_only.py drives Check with a recording exec.
Scope out:
- The base run in `check_hosts` (it still runs the whole command), fixing the flaky tests themselves, the flake quarantine rules, `test-gate.toml`, and config.yaml host entries.

## Scope fence
- clutch/testreport.py
- clutch/stages.py
- tests/unit/test_check_rerun_select.py
- tests/integration/test_testreport_select.py
- tests/integration/test_check_rerun_failed_only.py
- tests/integration/test_host_mechanical.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_testreport_select.py` proves that with `--clutch-select` naming one of three tests, pytest runs exactly that one and the `--clutch-results` file lists only it, not all three.
2. `./dev.py test tests/integration/test_check_rerun_failed_only.py` proves that when the first run records one failed id among many, the rerun argv is `entry.argv + ["--clutch-select", <path>]` and that file holds exactly that id, not the full command again.
3. `./dev.py test tests/integration/test_check_rerun_failed_only.py` proves a selected test that fails again on the rerun still produces the `failed on rerun` finding, and one that passes is treated as flaky exactly as before.
4. `./dev.py test tests/unit/test_check_rerun_select.py` proves the selection hook keeps only listed node ids and the rerun argv carries `--clutch-select`, without starting a process.
5. `./dev.py test tests/integration/test_host_mechanical.py` passes, including its `check/host-01-rerun.txt` capture assertion.

## Verification
```
./dev.py test tests/unit/test_check_rerun_select.py tests/integration/test_testreport_select.py tests/integration/test_check_rerun_failed_only.py tests/integration/test_host_mechanical.py tests/integration/test_flake.py
```

## Definition of rejected
Skipping the rerun or base run, changing flake or quarantine rules, adding a config knob, or files outside the fence change.

## Time budget
- expected: 20m
- stuck: 40m
