---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- clutch/stages.py::coverage_contexts
- clutch/stages.py::_check_host_results
- clutch/stages.py::_changed_lines
- clutch/config.py::MechanicalCheck
- clutch/covmap.py
- clutch/covgate.py::percentages
- config.yaml
- pyproject.toml
- tests/integration/test_host_mechanical.py::test_coverage_changed_lines
- tests/integration/test_host_mechanical.py::test_coverage_fail_closed
- tests/integration/test_covmap.py
- clutch/docs/host-contract.md#Onboarding a host

## Goal / Why
The `unit` check stops recording per-test coverage contexts on every run. Today the `unit` argv in `config.yaml` passes `--cov-context=test` and `pyproject.toml` sets `[tool.coverage.json] show_contexts = true`, so every unit check writes a coverage.py JSON report that lists, for every covered line, every test that ran it. Measured on 2026-11-19 on this repo (22k lines of `clutch/`, ~1,130 unit tests): that `coverage.json` is 906 MB and the unit pytest run takes 22.8 s, against 7.0 s for the same run with `--cov=clutch --cov-branch` and no contexts (coverage's own `.coverage` data is 11 MB). Leftover reports had filled 9.3 GB of scratch space.

The only Check reader of those contexts is the flaky-test classification in `_check_host_results`: when a test fails and then passes on the rerun, Check decides whether the flake "touches edited code" by looking up which tests' contexts cover a changed line. That happens rarely, yet every run pays for it. After this ticket, Check gets that answer only when a flake actually occurs: it reruns just the flaky test with coverage (no contexts) through a new optional per-check command, and treats the flake as edited when that run's executed lines include a changed line (or a line adjacent to a pure deletion, as `_changed_lines` computes today). Per-file coverage percentages and every `test-gate.toml` floor stay identical, since `percentages` never read contexts.

`clutch coverage map` keeps working through its own `review.coverage_map` run, which keeps contexts via a dedicated coverage config file instead of `pyproject.toml`. It still stores only the file-level `coverage-map.json`; no per-test map is stored, so no database is added. Owner rule: if a per-test map is ever stored it uses DuckDB, never SQLite, and clutch code never reads coverage.py's `.coverage` data file.

## Boundary contract
### Mechanical check config
- disposition: extend
- owner: clutch/config.py (`MechanicalCheck`)
- consumers: Check (`_check_host_results` in clutch/stages.py), `config.yaml`, the `config-fields` and `python-host` blocks in clutch/docs/host-contract.md
- observable change: optional `flake_coverage_argv` (argv list, default unset); config load refuses it on an entry whose `coverage` is unset, naming the field
- compatibility: configs without the field load unchanged
- acceptance: a `MechanicalCheck` with `flake_coverage_argv` and no `coverage` raises a validation error; one with both loads
- tests: tests/unit/test_stages_flake_coverage.py
- post-merge source of truth: clutch/config.py

### Flake edit classification in Check
- disposition: replace
- owner: clutch/stages.py (`_check_host_results`)
- consumers: Check stage findings and flake quarantine (clutch/flake.py via `flake.detect`)
- observable change: old contract read per-test contexts from the entry's `coverage` JSON. New contract: for each failed-then-passed test, when the entry declares `coverage`, Check runs `flake_coverage_argv + [test_id]` in the worktree through `run_host_command` (log `check/host-NN-flake-K.txt`), ignores its exit status, reads the entry's `coverage` JSON it wrote, and marks the test edited when that report's `executed_lines` for a changed file include a line from `_changed_lines`. A test whose own file changed is still edited without a run. When a flake needs classification and `flake_coverage_argv` is unset, or the rerun's report is missing or not coverage.py JSON with `executed_lines`, the entry fails closed with a finding whose paved road names `flake_coverage_argv`
- compatibility: breaking for hosts relying on contexts; the paved road and clutch/docs/host-contract.md name the replacement field; no host other than this repo configures `coverage` today
- acceptance: changed-line, deletion-adjacent, uncovered and fail-closed cases decide as today's `test_coverage_changed_lines` and `test_coverage_fail_closed` cases do, driven by `executed_lines`
- tests: tests/integration/test_host_mechanical.py, tests/unit/test_stages_flake_coverage.py
- post-merge source of truth: clutch/stages.py

### Coverage map build
- disposition: reuse
- owner: clutch/covmap.py
- consumers: `clutch coverage map`, requisition review via `<state_dir>/coverage-map.json`
- observable change: none; the context parser moves from clutch/stages.py into clutch/covmap.py (its only remaining consumer), and this repo's `review.coverage_map.argv` adds `--cov-config=coverage-map.toml` so its report still carries contexts
- compatibility: `reduce_map` input and `coverage-map.json` output unchanged
- acceptance: tests/integration/test_covmap.py passes unchanged
- tests: tests/integration/test_covmap.py
- post-merge source of truth: clutch/covmap.py

## Scope in / Scope out
- In: `config.yaml`: drop `--cov-context=test` from the `unit` argv; add to the `unit` entry `flake_coverage_argv: [uv, run, python, -m, pytest, --cov=clutch, --cov-branch, --cov-report=json:coverage.json, -n, "0"]`; append `--cov-config=coverage-map.toml` to `review.coverage_map.argv`.
- In: `pyproject.toml`: delete the `[tool.coverage.json]` table (`show_contexts = true`). `[tool.coverage.run] core = "ctrace"` stays.
- In: new `coverage-map.toml` at the repo root with `[tool.coverage.run] core = "ctrace"` and `[tool.coverage.json] show_contexts = true`, read only by the coverage map run.
- In: `clutch/config.py`: `MechanicalCheck.flake_coverage_argv` and its validation.
- In: `clutch/stages.py`: remove `coverage_contexts`; replace the contexts lookup in `_check_host_results` with the per-flake rerun; a pure helper `flake_covered(report: dict, changed: dict[str, set[int]]) -> bool` that validates `executed_lines` (raising `ValueError` on a malformed report) so a unit test can run it; replace the paved road that told hosts to set `show_contexts` and `--cov-context=test`.
- In: `clutch/covmap.py`: own the context parser formerly imported from stages.py; its refusal text keeps saying the map report needs test contexts.
- In: `clutch/docs/host-contract.md`: the `python-host` block (drop `--cov-context=test`, add `flake_coverage_argv`), the onboarding sentence telling hosts to set `show_contexts = true` (remove it), the `config-fields` `MechanicalCheck` defaults row (add `flake_coverage_argv: unset`), and the flaky-test paragraph (describe the per-flake rerun).
- In: `docs/how-clutch-works.md`: only the flaky-test coverage sentences in the paragraph that requires `--cov-context=test` and `show_contexts`.
- In: `tests/integration/test_host_mechanical.py`: `test_coverage_changed_lines` and `test_coverage_fail_closed` drive the new flow (fake exec writes `executed_lines` for the flake run; add the missing-`flake_coverage_argv` fail-closed case). `tests/integration/test_host_contract.py`: the `--cov-context=test` assertion flips to its absence plus a `flake_coverage_argv` check.
- In: new `tests/unit/test_stages_flake_coverage.py` for `flake_covered` and the config validation.
- Out: `test-gate.toml` floors (unchanged), `clutch/covgate.py`, the integration check, slow-test timing, the quarantine and release logic, and DuckDB storage for the coverage map (not needed: no per-test map is stored).

## Scope fence
- config.yaml
- pyproject.toml
- coverage-map.toml
- clutch/config.py
- clutch/stages.py
- clutch/covmap.py
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/integration/test_host_mechanical.py
- tests/integration/test_host_contract.py
- tests/integration/test_covmap.py
- tests/unit/test_stages_flake_coverage.py

## Acceptance criteria
1. The `unit` argv in `config.yaml` contains no `--cov-context` argument and `pyproject.toml` has no `[tool.coverage.json]` table; checked by the `uv run python -c` command in `## Verification`, which fails on either.
2. `flake_covered({"files": {"pkg/m.py": {"executed_lines": [3]}}}, {"pkg/m.py": {3}})` returns `True` and with `{"pkg/m.py": {4}}` returns `False`, not `True`; a report whose file entry lacks `executed_lines` raises `ValueError`, not `False`; checked in `tests/unit/test_stages_flake_coverage.py`.
3. `MechanicalCheck(code="u", argv=["t"], trigger="always", severity="hard", flake_coverage_argv=["t"])` with no `coverage` raises a validation error naming `flake_coverage_argv`, and the same call with `coverage="c.json"` loads; checked in `tests/unit/test_stages_flake_coverage.py`.
4. In `tests/integration/test_host_mechanical.py`, a failed-then-passed test whose flake run reports a changed line in `executed_lines` yields `gate_failed` with a finding naming the test, and one whose executed lines miss every changed line yields `ok` with a `flake_detected` event, including the deletion-adjacent cases; a flake on an entry with `coverage` but no `flake_coverage_argv` yields `gate_failed` with a finding whose paved road names `flake_coverage_argv`, not `ok`; and no Check finding or paved road contains `show_contexts`; checked by `./dev.py test tests/integration/test_host_mechanical.py`.
5. A green unit run (no flake) runs only the `unit` argv: the fake exec in `tests/integration/test_host_mechanical.py` records no `flake_coverage_argv` call, not one per test; checked by `./dev.py test tests/integration/test_host_mechanical.py`.
6. `grep -rn "show_contexts" clutch/stages.py clutch/docs/host-contract.md docs/how-clutch-works.md pyproject.toml` prints nothing, and `grep -n "coverage_contexts" clutch/stages.py` prints nothing; checked in review against the merged branch.
7. `tests/unit/test_stages_flake_coverage.py` calls `stages._check_host_results` with a fake ctx (as `tests/unit/test_host_check_selection.py::test_invalid_coverage` does: fake exec writing `results.json` and the coverage report under `tmp_path`, fake `ctx.git.diff` returning a one-line edit to `pkg/m.py`, `daemon.storm_producer` and `daemon.flake_detection` monkeypatched) and drives a failed-then-passed test through three cases: the flake run's `executed_lines` include the edited line, so the report fails with a finding naming the test, not a pass; the entry has `coverage` but no `flake_coverage_argv`, so it fails with a finding whose paved road names `flake_coverage_argv` and the fake exec records no extra run; the flake run writes a report lacking `executed_lines`, so it fails closed rather than classifying the test unedited; checked by `./dev.py test tests/unit/test_stages_flake_coverage.py`. The unedited `flake.detect` path stays covered in `tests/integration/test_host_mechanical.py`.
8. `tests/integration/test_covmap.py` and `tests/integration/test_host_contract.py` pass, the latter asserting the `python-host` `unit` argv has no `--cov-context=test` and declares `flake_coverage_argv`; checked by `./dev.py test tests/integration/test_covmap.py tests/integration/test_host_contract.py`.

## Verification
```
./dev.py test tests/unit/test_stages_flake_coverage.py tests/integration/test_host_mechanical.py tests/integration/test_covmap.py tests/integration/test_host_contract.py
uv run python -c "import sys, tomllib, yaml; u = next(c for c in yaml.safe_load(open('config.yaml'))['review']['mechanical'] if c['code'] == 'unit'); p = tomllib.load(open('pyproject.toml', 'rb')); sys.exit(0 if not any(a.startswith('--cov-context') for a in u['argv']) and u.get('flake_coverage_argv') and 'json' not in p['tool']['coverage'] else 1)"
```

## Definition of rejected
- Any `test-gate.toml` floor changes, or per-file percentages are computed from anything other than the `coverage` JSON `percentages` already reads.
- Check, covmap, or any clutch code reads coverage.py's `.coverage` data file, or any SQLite storage is added.
- The unit check still records per-test contexts on a run with no flaky test.
- A flaky test is classified unedited when its flake-coverage report is missing or malformed.

## Time budget
- expected: 15m
- stuck: 30m
