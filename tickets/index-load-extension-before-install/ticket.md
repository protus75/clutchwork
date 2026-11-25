---
state: draft
source: human
priority: P2
kind: bug
---

## Depends on
none

## Context
- clutch/index.py::_Creator
- clutch/index.py::build
- clutch/index.py::query
- clutch/index.py::neighbors

## Goal / Why
`_Creator.load` in `clutch/index.py` runs `INSTALL <kind>` unconditionally before `LOAD <kind>`. In environments where `$HOME` is read-only (such as sandboxed agent shells), `INSTALL fts` fails with `IO Error: Failed to create directory "<HOME>/.duckdb": Read-only file system` even when DuckDB can already `LOAD fts` directly. Trying `LOAD <kind>` first and only falling back to `INSTALL <kind>` + `LOAD <kind>` when `LOAD` raises `duckdb.Error` restores read-only index queries whenever the extension is already available.

## Boundary contract
### DuckDB extension loader
- disposition: extend
- owner: clutch/index.py
- consumers: `clutch.index.build`, `clutch.index.query`, `clutch.index.neighbors`, `clutch/__main__.py`
- observable change: restore `_Creator.load(connection, kind)` to try `connection.execute(f"LOAD {kind}")` first, and only run `INSTALL {kind}` followed by `LOAD {kind}` if the initial `LOAD` raises `duckdb.Error`.
- compatibility: when `LOAD` fails and `INSTALL` succeeds, the extension still loads transparently; when both fail, the returned finding format `[f"{kind} unavailable: {exc}"]` is unchanged.
- acceptance: when `LOAD` succeeds, `INSTALL` is never executed (not called at all); when `LOAD` fails, `INSTALL` then `LOAD` are attempted; when `INSTALL` or the retry `LOAD` fails, `[f"{kind} unavailable: ..."]` is returned.
- tests: `tests/unit/test_index_load_before_install.py` and `tests/regress_index_load_before_install.py`
- post-merge source of truth: `clutch/index.py`

## Scope in / Scope out
Scope in:
- In `clutch/index.py::_Creator.load`: attempt `connection.execute(f"LOAD {kind}")` first; only on `duckdb.Error`, run `connection.execute(f"INSTALL {kind}")` and retry `connection.execute(f"LOAD {kind}")`, returning `[f"{kind} unavailable: {exc}"]` if the fallback raises `duckdb.Error`.
- Add `tests/unit/test_index_load_before_install.py` (using a fake connection; no disk I/O or subprocesses) verifying:
  - When `LOAD fts` succeeds, executed SQL is `["LOAD fts"]` (never calling `INSTALL fts`) and returns `[]`.
  - When the first `LOAD fts` raises `duckdb.Error`, executed SQL is `["LOAD fts", "INSTALL fts", "LOAD fts"]` and returns `[]` if the fallback succeeds.
  - When `INSTALL fts` raises `duckdb.Error`, returns `[f"fts unavailable: ..."]`.
- Add `tests/regress_index_load_before_install.py`: standalone reproducer using a fake connection where `LOAD fts` succeeds and `INSTALL fts` raises `duckdb.IOException("Failed to create directory ...")`; calls `default_creator.load(conn, "fts")` and prints `{"regression_result": "pass"}` (exit 0) when it returns `[]` without calling `INSTALL`, `{"regression_result": "defect"}` (exit 1) when it fails because `INSTALL` was called first, or `{"regression_result": "error"}` (exit 2) on unexpected errors.

Scope out:
- Do not change `_Creator.create`, `_extract`, `build`, `query`, `neighbors`, or `clutch/__main__.py`.

## Scope fence
- clutch/index.py
- tests/unit/test_index_load_before_install.py
- tests/regress_index_load_before_install.py

## Acceptance criteria
1. `clutch.index.default_creator.load(conn, "fts")` executes only `LOAD fts` (never `INSTALL fts`) and returns `[]` when `LOAD` succeeds, falls back to `INSTALL fts` + `LOAD fts` when `LOAD` raises `duckdb.Error`, and returns `["fts unavailable: ..."]` when fallback fails; verified by `./dev.py test tests/unit/test_index_load_before_install.py tests/unit/test_index_build.py`.
2. The carried regression reproducer exits `0` with `{"regression_result": "pass"}` on the branch head and exits non-zero with `{"regression_result": "defect"}` on merge base; verified by `uv run python tests/regress_index_load_before_install.py`.

## Verification
```
./dev.py test tests/unit/test_index_load_before_install.py tests/unit/test_index_build.py
```

## Regression
- carries: tests/regress_index_load_before_install.py
```
uv run python tests/regress_index_load_before_install.py
```

## Definition of rejected
`_Creator.load` still executes `INSTALL` before `LOAD`, breaks fallback installation when `LOAD` raises `duckdb.Error`, or `tests/regress_index_load_before_install.py` fails to report `defect` on base and `pass` on head.

## Time budget
- expected: 5m
- stuck: 10m
