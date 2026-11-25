---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Context
- tests/integration/test_engine_text_verbs.py

## Goal / Why
`antigravity-plugin-logo` replaced `clutch/assets/logo.svg` with the binary PNG `clutch/assets/logo.png`. `tests/integration/test_engine_text_verbs.py::test_no_engine_text_names_dev_py` walks every file under `clutch/` (pruning only `__pycache__`) and fails with `AssertionError: clutch/assets/logo.png is not UTF-8; prune it deliberately`, leaving `main` red and blocking the `0.7.0` release gate. Deliberately pruning `clutch/assets/logo.png` in `test_no_engine_text_names_dev_py` restores green integration tests while continuing to scan all UTF-8 engine and installed-doc files.

## Boundary contract
none
- reason: tests encoding an existing contract; only `tests/integration/test_engine_text_verbs.py` and a carried regression reproducer under `tests/fixtures/` change, with no production code or public boundary modified.

## Scope in / Scope out
Scope in:
- In `tests/integration/test_engine_text_verbs.py::test_no_engine_text_names_dev_py`, deliberately skip `root / "clutch" / "assets" / "logo.png"` before reading UTF-8 text, while keeping the rest of the `clutch/` walk (including `clutch/docs/`) and UTF-8 enforcement unchanged.
- Add `tests/fixtures/repro_engine_text_verbs_logo_png.py` implementing the `## Regression` JSON protocol: verify `clutch/assets/logo.png` exists (emit `{"regression_result": "error"}` with exit 2 if absent), call `tests.integration.test_engine_text_verbs.test_no_engine_text_names_dev_py()`, emit `{"regression_result": "defect"}` with exit 1 when it raises `AssertionError` naming `clutch/assets/logo.png is not UTF-8`, emit `{"regression_result": "pass"}` with exit 0 when it succeeds, and emit `{"regression_result": "error"}` with exit 2 on any other exception.

Scope out:
- Do not modify `clutch/assets/logo.png`, `clutch/` production modules, or any other test file.

## Scope fence
- tests/integration/test_engine_text_verbs.py
- tests/fixtures/repro_engine_text_verbs_logo_png.py

## Acceptance criteria
1. `test_no_engine_text_names_dev_py` skips `clutch/assets/logo.png` and passes instead of raising `AssertionError: clutch/assets/logo.png is not UTF-8; prune it deliberately`, while still visiting `clutch/docs` and failing if any scanned file names `dev.py`; verified by `./dev.py test tests/integration/test_engine_text_verbs.py`.
2. `uv run python tests/fixtures/repro_engine_text_verbs_logo_png.py` prints `{"regression_result": "pass"}` and exits `0` on the branch head, and prints `{"regression_result": "defect"}` with non-zero exit on the merge base; verified by Check's regression gate on `tests/fixtures/repro_engine_text_verbs_logo_png.py`.

## Verification
```
./dev.py test tests/integration/test_engine_text_verbs.py
```

## Definition of rejected
`tests/integration/test_engine_text_verbs.py` still fails on `clutch/assets/logo.png`, silently catches `UnicodeDecodeError` for arbitrary files instead of pruning `clutch/assets/logo.png` deliberately, or stops scanning `clutch/docs/`.

## Time budget
- expected: 5m
- stuck: 10m

## Regression
```
uv run python tests/fixtures/repro_engine_text_verbs_logo_png.py
```
- carries: tests/fixtures/repro_engine_text_verbs_logo_png.py
