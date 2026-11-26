---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/config.py::MechanicalCheck
- clutch/config.py::_check_references
- clutch/covgate.py
- clutch/testguard.py
- clutch/testreport.py
- clutch/stages.py::_check_host_results
- clutch/box.py::Box.enqueue
- config.yaml
- test-gate.toml
- clutch/docs/host-contract.md#Python host test setup
- clutch/docs/host-contract.md#Complete field inventory
- clutch/docs/host-contract.md#Checks and injectable seams
- docs/how-clutch-works.md#12. Host projects

## Goal / Why
Replace the single hard `[unit] budget_seconds` timer in `test-gate.toml` / `clutch.testguard` with per-check `soft_budget_seconds` and `hard_budget_seconds` in `config.yaml` (`review.mechanical[]`), timed on the pytest invocation itself via `clutch.testreport` (`elapsed`). When a passing check finishes between `soft_budget_seconds` and `hard_budget_seconds` (e.g. 60s–120s for `unit`), Check passes instead of blocking good code and files a deduplicated Suggestion Box entry to refactor/trim slow tests; above `hard_budget_seconds`, Check fails with the slowest tests and a paved road.

## Boundary contract

### Mechanical check configuration (`review.mechanical[]`)
- disposition: extend
- owner: clutch/config.py
- consumers: clutch/stages.py (`_check_host_results`), config.yaml, hosts implementing `clutch/docs/host-contract.md`
- observable change: `MechanicalCheck` adds optional positive finite float fields `soft_budget_seconds` and `hard_budget_seconds` (default unset). Both require `results` on the same entry; when both are set, `hard_budget_seconds >= soft_budget_seconds` is enforced at config load.
- compatibility: additive; existing `config.yaml` files without budget fields remain valid. `config.yaml` in this repo sets `soft_budget_seconds: 60` and `hard_budget_seconds: 120` on the `unit` check.
- acceptance: invalid values (non-positive, non-finite, missing `results`, or `hard_budget_seconds < soft_budget_seconds`) are refused with `ConfigError` naming the dotted field key.
- tests: unit tests in `tests/unit/test_check_time_budget.py`, `tests/unit/test_check_timing.py`, and contract schema coverage in `tests/integration/test_host_contract.py`.
- post-merge source of truth: clutch/config.py and clutch/docs/host-contract.md

### Test results schema (`clutch.testreport`)
- disposition: replace
- owner: clutch/testreport.py
- consumers: clutch/stages.py (`_check_host_results`), host test commands passing `-p clutch.testreport --clutch-results <path>`
- observable change: bumps results JSON from `schema_version: 2` to `schema_version: 3` and adds top-level `elapsed` (finite nonnegative float measuring wall-clock seconds from `pytest_sessionstart` to `pytest_sessionfinish` via injectable `clock = time.monotonic`). `Results` gains `elapsed: float`.
- compatibility: breaking in-place bump (no dual-path reader); `read_results` accepts only schema 3 and refuses schemas 1 and 2. All in-repo fixtures and docs are updated in this change.
- acceptance: `clutch.testreport` writes valid schema 3 with `elapsed`; `read_results` refuses schema 2 and missing/negative/non-finite/non-float `elapsed`.
- tests: `tests/unit/test_check_time_budget.py`, `tests/unit/test_testreport_reader.py`, and `tests/integration/test_testreport.py`.
- post-merge source of truth: clutch/testreport.py and clutch/docs/host-contract.md

### Check time-budget enforcement (`_check_host_results`)
- disposition: extend
- owner: clutch/stages.py
- consumers: Check stage (`check` / `drain` / `serve`), Suggestion Box (`clutch/box.py`)
- observable change: `_check_host_results` compares `first.elapsed` against `entry.soft_budget_seconds` and `entry.hard_budget_seconds`. Above `hard_budget_seconds`, Check fails the entry with a `Finding` naming elapsed time, hard cap, slowest tests, and paved road (no Suggestion Box entry). When `report.verdict == "pass"` and `soft_budget_seconds < first.elapsed <= hard_budget_seconds`, Check passes and enqueues a `suggestion` via `box.enqueue` with stable dedup `reason` (`f"{entry.code} exceeded soft time budget"`), deterministic `occurrence_id`, and `summary` listing elapsed time, bounds, and slowest tests.
- compatibility: checks without `soft_budget_seconds` or `hard_budget_seconds` behave identically to today.
- acceptance: passing runs below soft create no box entry; passing runs in `(soft, hard]` pass and create/collapse one box suggestion; failing runs in `(soft, hard]` do not create a box suggestion; runs above `hard` fail Check without creating a box suggestion.
- tests: `tests/unit/test_check_time_budget.py` and `tests/integration/test_host_mechanical.py`.
- post-merge source of truth: clutch/stages.py

### Coverage gate and unit IO guard (`test-gate.toml`, `clutch.covgate`, `clutch.testguard`)
- disposition: replace
- owner: clutch/covgate.py and clutch/testguard.py
- consumers: `clutch coverage gate`, `./dev.py test`, `test-gate.toml`
- observable change: removes `[unit]` / `budget_seconds` from `test-gate.toml` and `clutch.covgate.Gate` / `parse_gate`, and removes wall-clock timing from `clutch.testguard` so `testguard` only guards process and network IO during unit test phases.
- compatibility: breaking in-place removal; `[unit]` in `test-gate.toml` is refused as an unknown table key, and this repo's `test-gate.toml`, docs, and tests are updated in the same change.
- acceptance: `parse_gate` refuses `[unit]`; `testguard` blocks process and network IO without reading `test-gate.toml` or failing sessions on elapsed time.
- tests: `tests/unit/test_check_time_budget.py`, `tests/integration/test_covgate.py`, and `tests/integration/test_testguard.py`.
- post-merge source of truth: clutch/covgate.py, clutch/testguard.py, and clutch/docs/host-contract.md

## Scope in / Scope out
Scope in:
- `clutch/config.py`: add optional `soft_budget_seconds` and `hard_budget_seconds` (`Annotated[float, Field(gt=0)] | None = None`) to `MechanicalCheck`; in `_check_references`, require `results` when either is set and require `hard_budget_seconds >= soft_budget_seconds` when both are set.
- `clutch/testreport.py`: add module-level `clock = time.monotonic` and `_start` captured in `pytest_configure` and `pytest_sessionstart`; write `schema_version: 3` with `"elapsed": max(0.0, float(clock() - _start))`; update `Results` and `read_results` to require schema 3 and validate `elapsed` as a finite nonnegative `float`.
- `clutch/stages.py`: in `_check_host_results`, evaluate `first.elapsed` against `entry.hard_budget_seconds` (fail with `Finding` naming elapsed, hard cap, up to 5 slowest tests from `timing.slow`, and paved road) and, when `report.verdict == "pass"` and not over hard, against `entry.soft_budget_seconds` (keep pass verdict and enqueue a `suggestion` via the existing `box` producer using `origin=f"check/{entry.code}"`, `reason=f"{entry.code} exceeded soft time budget"`, `occurrence_id=arrival_id("test-time-budget", ticket.stem, attempt, entry.code, n)`, and `summary` naming elapsed, bounds, and slowest tests).
- `clutch/covgate.py` and `test-gate.toml`: remove `[unit]` / `budget_seconds` from `Gate`, `parse_gate`, and `test-gate.toml`.
- `clutch/testguard.py`: remove the budget timer, `clock`, `_budget`, `_start`, `_durations`, `pytest_configure`, `pytest_sessionstart`, `pytest_runtest_logreport`, `pytest_sessionfinish`, and `covgate` import; keep all process and network IO phase guards intact.
- `config.yaml`: set `soft_budget_seconds: 60` and `hard_budget_seconds: 120` on the `unit` entry under `review.mechanical`.
- Docs: update `clutch/docs/host-contract.md` (`## Python host test setup`, `config-fields` `MechanicalCheck` defaults, `test-gate` example, and `## Checks and injectable seams`) and `docs/how-clutch-works.md` (`## 12. Host projects` bullets for `clutch.testreport` and `clutch.testguard`).
- Existing forced tests: update schema 2 fixtures to schema 3 with `elapsed` in `tests/integration/test_testreport.py`, `tests/integration/test_host_mechanical.py`, `tests/unit/test_testreport_reader.py`, `tests/unit/test_check_timing.py`, `tests/unit/test_check_flake_declined_release.py`, `tests/unit/test_check_rerun_failed_only.py`, `tests/unit/test_host_check_selection.py` (also adding `soft_budget_seconds=None, hard_budget_seconds=None` on its `NS`), and `tests/unit/test_stages_flake_coverage.py`; update `tests/integration/test_host_contract.py`, `tests/integration/test_covgate.py`, and `tests/integration/test_testguard.py` for the removed `[unit].budget_seconds` and timer.
- New unit tests in `tests/unit/test_check_time_budget.py` covering config validation, `testreport` `elapsed` / schema 3, `_check_host_results` soft/hard/fail/dedup behavior, and `covgate` `[unit]` refusal.

Scope out:
- `./dev.py` (stays stdlib-only; does not read `config.yaml` or enforce time budgets locally).
- `TestTiming.seconds` semantics (continues to record `result.seconds` command wall time).
- Historical carried reproducer `tests/regress_testguard_slowest_load.py`.
- Adding soft/hard budgets to `integration`, `lint`, or `format` in `config.yaml` (left unset).

## Scope fence
- clutch/config.py
- clutch/covgate.py
- clutch/stages.py
- clutch/testguard.py
- clutch/testreport.py
- config.yaml
- test-gate.toml
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_check_time_budget.py
- tests/unit/test_check_timing.py
- tests/unit/test_testreport_reader.py
- tests/unit/test_check_flake_declined_release.py
- tests/unit/test_check_rerun_failed_only.py
- tests/unit/test_host_check_selection.py
- tests/unit/test_stages_flake_coverage.py
- tests/integration/test_testreport.py
- tests/integration/test_host_mechanical.py
- tests/integration/test_host_contract.py
- tests/integration/test_covgate.py
- tests/integration/test_testguard.py

## Acceptance criteria
1. `MechanicalCheck` accepts optional positive finite `soft_budget_seconds` and `hard_budget_seconds`, rejects either without `results`, and rejects `hard_budget_seconds < soft_budget_seconds` (not silently accepting inverted or unlinked budgets), verified by `./dev.py test tests/unit/test_check_time_budget.py tests/unit/test_check_timing.py`.
2. `clutch.testreport` writes `schema_version: 3` with session wall-clock `elapsed` from `clock`, and `read_results` accepts schema 3 while refusing schema 2 and invalid/missing/negative/non-finite `elapsed` (not defaulting `elapsed` to `0.0`), verified by `./dev.py test tests/unit/test_check_time_budget.py tests/unit/test_testreport_reader.py tests/integration/test_testreport.py`.
3. In `_check_host_results`, a passing run with `elapsed <= soft_budget_seconds` passes with no Suggestion Box entry; a passing run with `soft_budget_seconds < elapsed <= hard_budget_seconds` passes and enqueues one deduplicated `suggestion` box entry naming elapsed time, bounds, and slow tests (a second run collapses into the same box item rather than creating a duplicate); a failing run in `(soft, hard]` does not enqueue a soft-budget suggestion; and a run with `elapsed > hard_budget_seconds` fails Check with a paved-road finding and no soft-budget suggestion, verified by `./dev.py test tests/unit/test_check_time_budget.py tests/integration/test_host_mechanical.py`.
4. `test-gate.toml` has no `[unit]` table, `clutch.covgate.parse_gate` refuses `[unit]` as an unknown key (not ignoring it), and `clutch.testguard` blocks process and network IO without enforcing any time budget, verified by `./dev.py test tests/unit/test_check_time_budget.py tests/integration/test_covgate.py tests/integration/test_testguard.py`.
5. `config.yaml` declares `soft_budget_seconds: 60` and `hard_budget_seconds: 120` on `review.mechanical` entry `unit`, and `clutch/docs/host-contract.md` and `docs/how-clutch-works.md` match the updated schema and plugin contracts, verified by `./dev.py test tests/integration/test_host_contract.py` and `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_check_time_budget.py tests/unit/test_check_timing.py tests/unit/test_testreport_reader.py tests/unit/test_check_flake_declined_release.py tests/unit/test_check_rerun_failed_only.py tests/unit/test_host_check_selection.py tests/unit/test_stages_flake_coverage.py
./dev.py test tests/integration/test_testreport.py tests/integration/test_host_mechanical.py tests/integration/test_host_contract.py tests/integration/test_covgate.py tests/integration/test_testguard.py
```

## Definition of rejected
- Any dual-path reader accepting both schema 2 and schema 3 in `clutch/testreport.py`, or keeping `[unit].budget_seconds` as a fallback in `clutch/covgate.py` or `clutch/testguard.py`.
- Comparing soft/hard budgets against `result.seconds` (wrapper command time) instead of `first.elapsed` (pytest invocation wall time).
- Enqueueing a new un-deduplicated Suggestion Box entry on every soft-budget overrun instead of collapsing via a stable `reason` signature.
- Failing a passing check when `soft_budget_seconds < elapsed <= hard_budget_seconds`, or passing a check when `elapsed > hard_budget_seconds`.

## Time budget
- expected: 25m
- stuck: 50m
