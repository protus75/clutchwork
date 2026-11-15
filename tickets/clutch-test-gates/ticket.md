---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- clutch-ruff-reclean
- clutch-ruff-reclean-tests-a-l
- clutch-ruff-reclean-tests-m-z
- tests-split
- autofix-file-globs
- clutch-ruff-tests-l-z
- covgate-runs-tests
- testguard
- testreport
- flake-edit-coverage
- test-rules-prompt
- autofix-step

## Context
- config.yaml
- pyproject.toml
- .gitignore
- docs/host-contract.md

## Goal / Why
Clutch's own `config.yaml` declares no host checks: its `review` holds only `coverage_map`. Its tickets are judged only by their own `## Verification` commands, so clutch does not live by the test rules it now ships to hosts. After this change clutch adopts the Python host setup from `docs/host-contract.md` `## Python host test setup`:
- autofix runs ruff fix and format on changed files;
- Check runs the unit suite under `clutch.testguard` with coverage, gated by `test-gate.toml`, then the integration suite, whole-repo ruff lint, and the format check;
- `test-gate.toml` is in the safety inventory, so lowering a threshold goes through a human.

## Scope in / Scope out
- In: `config.yaml`, copying the `review.autofix` and `review.mechanical` entries of the `python-host` block in `docs/host-contract.md` verbatim with package `clutch` (on any difference in those entries, the block wins), beside the existing `review.coverage_map`, which stays unchanged; `merge` stays `{}`, and `engine_plane_safety_inventory` keeps its existing entries and appends `test-gate.toml`:
  - `review.autofix`: `ruff-fix` `[uv, run, ruff, check, --fix, --exit-zero]` and `ruff-format` `[uv, run, ruff, format]`, each with `files: ["*.py"]`.
  - `review.mechanical`, all `trigger: always`, `severity: hard`, in this order:
    - `unit`: `[uv, run, python, -m, clutch, covgate, --, python, -m, pytest, tests/unit, -p, clutch.testguard, -p, clutch.testreport, --clutch-results, .clutch/results/unit.json, --cov=clutch, --cov-branch, --cov-context=test, --cov-report=json:coverage.json, -n, auto]`, with `results: .clutch/results/unit.json` and `coverage: coverage.json`;
    - `integration`: `[uv, run, python, -m, pytest, tests/integration, -p, clutch.testreport, --clutch-results, .clutch/results/integration.json, -n, auto]`, with `results: .clutch/results/integration.json`;
    - `lint`: `[uv, run, ruff, check, .]`;
    - `format`: `[uv, run, ruff, format, --check, .]`.
  - `engine_plane_safety_inventory` gains `test-gate.toml`.
- In: new `test-gate.toml`.
  - `[coverage] default = 90`.
  - `[unit] budget_seconds = 60`.
  - A `[coverage.files]` entry for each `clutch/` file whose unit-run coverage is below 90 when this ticket runs, set to that file's measured percent rounded down to an integer.
  - `repository` set the same way when the repository total is below 90.

  This is the initial baseline. The comment at the top says thresholds only rise, and lowering one is a human ticket's decision.
- In: `pyproject.toml`:
  - `pytest-cov` in the `dev` group, with `uv.lock` updated;
  - `[tool.coverage.run] core = "ctrace"` (Python 3.14's default `sysmon` core drops per-test contexts);
  - `[tool.coverage.json] show_contexts = true`.
- In: `.gitignore`: `coverage.json` (`.clutch/` is already ignored).
- In: `docs/how-clutch-works.md` section 11: clutch's own `config.yaml` uses the Python host test setup.
- Out: moving or rewriting tests; raising any threshold above the measured baseline; `merge.safety_checks`; any engine code.

## Scope fence
- config.yaml
- test-gate.toml
- pyproject.toml
- uv.lock
- .gitignore
- docs/how-clutch-works.md

## Acceptance criteria
1. `config.yaml` loads: `uv run python -c "from pathlib import Path; from clutch.config import load_config; c = load_config(None, cwd=Path('.')); assert [m.code for m in c.review.mechanical] == ['unit', 'integration', 'lint', 'format']; assert [a.code for a in c.review.autofix] == ['ruff-fix', 'ruff-format']; assert 'test-gate.toml' in c.engine_plane_safety_inventory; assert c.review.coverage_map is not None"` exits 0.
2. The `unit` entry's exact argv passes: `uv run python -m clutch covgate -- python -m pytest tests/unit -p clutch.testguard -p clutch.testreport --clutch-results .clutch/results/unit.json --cov=clutch --cov-branch --cov-context=test --cov-report=json:coverage.json -n auto` exits 0. That means the unit suite passes within the 60-second budget, every file meets its threshold, and `coverage.json` carries per-test contexts. If the unit suite cannot finish within 60 seconds, reply `premise_failed` with the slowest tests testguard lists; never raise the budget.
3. The other entries pass:
   - `uv run python -m pytest tests/integration -p clutch.testreport --clutch-results .clutch/results/integration.json -n auto` exits 0;
   - `uv run ruff check .` exits 0;
   - `uv run ruff format --check .` exits 0.
4. Baseline integrity, checked by the Verification command starting `uv run python -c "import json,math,tomllib` against the `coverage.json` from criterion 2:
   - every file below 90% has a `[coverage.files]` entry equal to its measured percent rounded down;
   - no file at or above 90% has an entry;
   - `repository` is absent when the total is at least 90, and otherwise equals the total rounded down.

   It fails if any threshold is below or above the measured floor.
5. `uv run pytest -q` exits 0.

## Verification
```
uv run python -c "from pathlib import Path; from clutch.config import load_config; c = load_config(None, cwd=Path('.')); assert [m.code for m in c.review.mechanical] == ['unit', 'integration', 'lint', 'format']; assert [a.code for a in c.review.autofix] == ['ruff-fix', 'ruff-format']; assert 'test-gate.toml' in c.engine_plane_safety_inventory; assert c.review.coverage_map is not None"
uv run python -m clutch covgate -- python -m pytest tests/unit -p clutch.testguard -p clutch.testreport --clutch-results .clutch/results/unit.json --cov=clutch --cov-branch --cov-context=test --cov-report=json:coverage.json -n auto
uv run python -c "import json,math,tomllib; g=tomllib.load(open('test-gate.toml','rb'))['coverage']; r=json.load(open('coverage.json')); pct=lambda s: 100.0 if s['num_statements']+s.get('num_branches',0)==0 else 100*(s['covered_lines']+s.get('covered_branches',0))/(s['num_statements']+s.get('num_branches',0)); files={k:pct(v['summary']) for k,v in r['files'].items()}; e=g.get('files',{}); assert all(e.get(k)==math.floor(v) for k,v in files.items() if v<90), 'missing or wrong baseline'; assert all(files.get(k,100)<90 for k in e), 'entry at or above 90'; tot=pct(r['totals']); assert ('repository' not in g) if tot>=90 else g.get('repository')==math.floor(tot), 'repository baseline'"
uv run python -m pytest tests/integration -p clutch.testreport --clutch-results .clutch/results/integration.json -n auto
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

## Definition of rejected
A threshold is below the measured baseline or a file at 90% or above gets an entry; the unit budget is raised; a test moves or changes; engine code changes; the `review.autofix` or `review.mechanical` entries differ from the `python-host` block's beyond the package name; `review.coverage_map` is removed or changed; `merge` changes; an existing safety-inventory entry is removed.

## Time budget
- expected: 45m
- stuck: 120m
