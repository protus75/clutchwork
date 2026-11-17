---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: draft
---

## Depends on
none

## Context
- test-gate.toml
- config.yaml
- docs/roadmap.md#3.5 Dev surface and tests

## Goal / Why
`test-gate.toml` has no entry for `clutch/graph.py`, which is held only by `coverage.default` (90). Six modules (`audit`, `observe`, `seams`, `stats`, `thresh`, `watchdog`) sit at floor 0, so their coverage can fall to nothing without any gate failing. After this change `clutch/graph.py` and those six modules each have a positive floor, equal to their coverage under the `unit` check measured at the base commit minus 2 points of margin. The ratchet ("thresholds only rise") then protects all seven. `clutch/thresh.py` measured 0% when row 22 was rejected, but since `evidence-envelope` merged (`73d04785`), `tests/unit/test_evidence_envelope.py` runs it through the provider session and the unit check measures it at 66.81%. `clutch/covmap.py` and `clutch/doctor.py` still measure 0% under the unit check because their tests are integration tests. They stay at 0 with a comment saying so. This replaces roadmap row 22, whose ticket was rejected because "measured minus 2, never below 1" cannot hold for those three modules.

## Scope in / Scope out
Scope in:
- Measure per-file coverage by running the `unit` check from `config.yaml` with its own argv (the `clutch covgate` command listed in Verification). Measure at the base commit, before editing `test-gate.toml`. `./dev.py test` runs pytest without `--cov` and never measures coverage.
- Add `"clutch/graph.py"` to `[coverage.files]` with floor max(90, measured integer percent minus 2), so it never falls below the 90 default it is held to today.
- Raise `clutch/audit.py`, `clutch/observe.py`, `clutch/seams.py`, `clutch/stats.py`, `clutch/thresh.py` and `clutch/watchdog.py` from 0 to measured integer percent minus 2. A module that measures 3% or less takes floor 1.
- Leave `clutch/covmap.py` and `clutch/doctor.py` at 0. Put a comment beside each saying its tests are integration tests, so it measures 0% under the unit check.
- Put a one-line comment beside each of the seven raised or added entries giving its measured percentage.
- Add a new test file `tests/integration/test_gate_floors.py` that parses `test-gate.toml` and checks the floors. It reads a repo file, so it lives under `tests/integration/`.

Scope out: every other floor, `default`, `repository`, `[unit]`; any source or test change to raise coverage; lowering any floor; anything under `tickets/`.

## Scope fence
- test-gate.toml
- tests/integration/test_gate_floors.py

## Acceptance criteria
1. `test-gate.toml` `[coverage.files]` has `clutch/graph.py` with a value of at least 90, and each of `clutch/audit.py`, `clutch/observe.py`, `clutch/seams.py`, `clutch/stats.py`, `clutch/thresh.py`, `clutch/watchdog.py` with a value of at least 1, not 0 (checked by `./dev.py test tests/integration/test_gate_floors.py`).
2. `clutch/covmap.py` and `clutch/doctor.py` are each present in `[coverage.files]` with value exactly 0, not raised to 1 or more, and each has a comment on its line containing `integration` (checked by `./dev.py test tests/integration/test_gate_floors.py`).
3. `tests/integration/test_gate_floors.py` fails if `clutch/graph.py` is absent or below 90, and fails if any of the six modules equals 0 or is absent (checked by `./dev.py test tests/integration/test_gate_floors.py`).
4. No existing floor is lowered: the test asserts `clutch/__main__.py` is at least 13, `clutch/redact.py` at least 50 and `clutch/gates.py` at least 38 (checked by `./dev.py test tests/integration/test_gate_floors.py`).
5. No new floor exceeds measured unit coverage: the unit check's own argv, run via `uv run python -m clutch covgate -- ...` as in Verification, exits 0 with the new floors in place, not non-zero. Each of the seven raised or added entries has a one-line comment containing its measured percentage.

## Verification
```
./dev.py test tests/integration/test_gate_floors.py
./dev.py test
uv run python -m clutch covgate -- python -m pytest tests/unit -p clutch.testguard -p clutch.testreport --clutch-results .clutch/results/unit.json --cov=clutch --cov-branch --cov-context=test --cov-report=json:coverage.json -n auto
```

## Definition of rejected
Any existing floor lowered or removed, any floor above measured coverage (so unchanged code fails the gate), `clutch/graph.py` given a floor below 90, any of the six modules left at 0 or absent, `covmap` or `doctor` raised above 0, or edits outside the fence.

## Time budget
- expected: 25m
- stuck: 60m
