---
priority: P2
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
- docs/roadmap.md#4. Analysis: drift

## Goal / Why
`test-gate.toml` has no entry of its own for `clutch/graph.py`, which is held only by `coverage.default` (90), and eight modules (`audit`, `covmap`, `doctor`, `observe`, `seams`, `stats`, `thresh`, `watchdog`) sit at floor 0, so their coverage can fall to nothing without any gate failing. After this change `clutch/graph.py` has its own floor of at least 90 (never below the 90 default it is held to today), and each of the eight floor-0 modules has a positive floor taken from its measured unit coverage, so the ratchet ("thresholds only rise") protects all nine. This is roadmap row 22.

## Scope in / Scope out
Scope in:
- Measure per-file coverage of the `unit` check by running the `unit` check from `config.yaml` through `clutch covgate`, using that check's argv. `./dev.py test` runs pytest without `--cov` and does not read `test-gate.toml`, so it is only the suite-pass check and never measures coverage.
- Add `"clutch/graph.py"` to `[coverage.files]` with floor max(90, measured integer percent minus 2), so it never falls below the existing 90 default. Raise the eight floor-0 entries to the measured integer percent, minus 2 points of margin (never below 1), because `covgate-repeatable-unit-coverage` records run-to-run variance on unchanged code. A module that measures at or below 2% takes floor 1.
- Record the nine measured percentages and chosen floors in the implementer's reply `summary`, and as a one-line comment beside each of the nine entries in `test-gate.toml`.
- Add a new test file `tests/integration/test_gate_floors.py` that parses `test-gate.toml` and checks the nine floors. It reads a repo file, so it lives under `tests/integration/`.

Scope out: every other floor, `default`, `repository`, `[unit]`; any source or test change to raise coverage; lowering any floor; anything under `tickets/`.

## Scope fence
- test-gate.toml
- tests/integration/test_gate_floors.py

## Acceptance criteria
1. `test-gate.toml` `[coverage.files]` contains `clutch/graph.py` with a value of at least 90, and `clutch/audit.py`, `clutch/covmap.py`, `clutch/doctor.py`, `clutch/observe.py`, `clutch/seams.py`, `clutch/stats.py`, `clutch/thresh.py`, `clutch/watchdog.py` each have a value of at least 1, not 0 (checked by `./dev.py test tests/integration/test_gate_floors.py`).
2. `tests/integration/test_gate_floors.py` fails if any of those nine entries is missing, fails if any of the eight equals 0, and fails if `clutch/graph.py` is below 90.
3. No floor that existed before this change is lower than it was: the test asserts the floors of `clutch/__main__.py` (13), `clutch/redact.py` (50), and `clutch/gates.py` (38) are still at least those values.
4. No new floor exceeds the measured unit coverage of its file: the `uv run clutch covgate -- python -m pytest tests/unit -p clutch.testguard --cov=clutch --cov-branch --cov-report=json:coverage.json -n auto` command in Verification exits 0 with the new floors in place, and each of the nine entries has a one-line comment giving its measured percentage.
5. The same covgate command exits 0 on unchanged source code with the new floors, not exit non-zero, and `./dev.py test` exits 0 as the suite-pass check.

## Verification
```
./dev.py test tests/integration/test_gate_floors.py
./dev.py test
uv run clutch covgate -- python -m pytest tests/unit -p clutch.testguard --cov=clutch --cov-branch --cov-report=json:coverage.json -n auto
```

## Definition of rejected
Any existing floor lowered or removed, any floor above measured coverage (so unchanged code fails the gate), `clutch/graph.py` given a floor below 90, any of the eight modules left at 0 or absent, or edits outside the fence.

## Time budget
- expected: 25m
- stuck: 60m
