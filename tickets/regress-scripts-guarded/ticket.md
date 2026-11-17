---
state: confirmed
source: box:roadmap_row
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- docs/roadmap.md
- tests/regress_premise_park_keep.py
- tests/regress_requisition_stage_events.py

## Goal / Why
Ten `tests/regress_*.py` scripts have no `if __name__ == "__main__":` guard, so importing one runs its reproducer, prints JSON and raises `SystemExit`. After this ticket every one of them runs only when executed as a script, and a test proves that importing any `tests/regress_*.py` module runs nothing. Bug tickets' `## Regression` commands run these files as scripts, so they must keep printing the same single JSON object with the same exit code.

The ten unguarded files are:
- `tests/regress_engine_flag_only_drain_serve.py`
- `tests/regress_implement_premise_path.py`
- `tests/regress_premise_overruled_escalates.py`
- `tests/regress_premise_park_keep.py`
- `tests/regress_requisition_events_owner_stem.py`
- `tests/regress_requisition_park_not_attempt.py`
- `tests/regress_requisition_prior_review.py`
- `tests/regress_requisition_stage_events.py`
- `tests/regress_review_intakes_own_stem.py`
- `tests/regress_snapshot_verdict_menu_parity.py`

## Scope in / Scope out
Scope in: in each of the ten files, move the module-level reproducer code into a `def main() -> None:` function and end the file with `if __name__ == "__main__":` calling `main()`. Constants, imports and helper definitions stay at module level. The printed JSON and exit code are unchanged.

Scope in: add `tests/integration/test_regress_scripts_guarded.py`. It imports every `tests/regress_*.py` module (found by glob, so a future unguarded script fails it) with stdout captured. For each module it asserts that stdout is empty and that no `SystemExit` is raised. It lives under `tests/integration/` because it reads repo files.

Scope out: the 44 already-guarded scripts are not edited. If one of them runs code at import and fails the new test, stop and report it as a second problem. No `## Regression` command, doc or other test changes.

## Scope fence
- tests/regress_engine_flag_only_drain_serve.py
- tests/regress_implement_premise_path.py
- tests/regress_premise_overruled_escalates.py
- tests/regress_premise_park_keep.py
- tests/regress_requisition_events_owner_stem.py
- tests/regress_requisition_park_not_attempt.py
- tests/regress_requisition_prior_review.py
- tests/regress_requisition_stage_events.py
- tests/regress_review_intakes_own_stem.py
- tests/regress_snapshot_verdict_menu_parity.py
- tests/integration/test_regress_scripts_guarded.py

## Acceptance criteria
1. Importing each of the ten modules prints nothing to stdout and does not raise `SystemExit`; the check is `./dev.py test tests/integration/test_regress_scripts_guarded.py`, which fails on the current unguarded files because the import exits or prints.
2. Running `python tests/regress_premise_park_keep.py` from the repo root prints exactly one line, `{"regression_result": "pass"}`, and exits 0, not an empty output and not an import error; check it with `./dev.py test tests/integration/test_regress_scripts_guarded.py`, which runs the script as a subprocess and parses the line.
3. `grep -L '__main__' tests/regress_*.py` lists no file other than the 2 files that import `clutch.__main__` without a guard being fixed; after the change each of the ten files contains the line `if __name__ == "__main__":`, checked by the same test reading each file's text.

## Verification
```
./dev.py test tests/integration/test_regress_scripts_guarded.py
```

## Definition of rejected
Any of the ten scripts changes its printed JSON or exit code when run as a script, any already-guarded script or `## Regression` command is edited, or the new test lists the ten files by name instead of globbing `tests/regress_*.py`.

## Time budget
- expected: 20m
- stuck: 40m
