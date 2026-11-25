---
state: confirmed
source: human
priority: P1
kind: bug
---

## Depends on
none

## Runs before
- index-load-extension-before-install

## Context
- clutch/index.py::_extract
- clutch/index.py::neighbors
- clutch/index.py::query
- clutch/index.py::build
- tests/unit/test_index_query.py

## Goal / Why
`clutch/index.py::_extract` emits `(path, f"{path}#{title}", ...)` for every Markdown heading without disambiguating repeated headings in the same file (for example, `AGENTS.md#Engine conduct` and `docs/gemini-graphics-refactor-plan.md#Target design` each appear twice in `.clutch/state/index.duckdb`). Because DuckDB's `PRAGMA create_fts_index('chunks', 'selector', 'text', overwrite=1)` keys `fts_main_chunks` on `selector`, `fts_main_chunks.match_bm25(c.selector, ?)` in `clutch.index.query` and `clutch.index.neighbors` crashes with `Invalid Input Error: More than one row returned by a subquery used as an expression` on any index built from this repository. Guaranteeing unique `chunks.selector` values per file in `_extract` restores working FTS queries across the whole repo.

## Boundary contract
### Project index chunk selector extraction
- disposition: extend
- owner: clutch/index.py
- consumers: `clutch.index.build`, `clutch.index.query`, `clutch.index.neighbors`, `clutch.context.suggest`
- observable change: restore uniqueness of `chunks.selector` per file in `_extract(path, data)` when a Markdown file contains repeated headings: the first occurrence keeps `f"{path}#{title}"` unchanged, and subsequent occurrences of the same heading in the same file receive a deterministic suffix `f"{path}#{title} ({n})"` (starting at `2`).
- compatibility: unique Markdown headings and all Python AST selectors (`path::Name`, `path::Class.method`) keep identical selector strings; existing `index.duckdb` table schemas are unchanged (rebuilding with `clutch index build` refreshes duplicate rows).
- acceptance: building an index containing a Markdown file with duplicate headings produces distinct `chunks.selector` values, `clutch.index.query` returns `found`, and `clutch.index.neighbors` succeeds in FTS mode (`outcome in {"found", "no_match"}`, not `"index_unreadable"`) without raising `More than one row returned by a subquery`.
- tests: `tests/unit/test_index_fts_duplicate_selector.py` and `tests/regress_index_fts_duplicate_selector.py`
- post-merge source of truth: `clutch/index.py`

## Scope in / Scope out
Scope in:
- In `clutch/index.py::_extract`: track per-file heading counts for Markdown headings; emit `f"{path}#{title}"` for the first occurrence and `f"{path}#{title} ({count})"` for the 2nd, 3rd, ... occurrence of the same heading text within that file so every emitted `(path, selector)` in `chunks` is unique.
- Add `tests/unit/test_index_fts_duplicate_selector.py` (using `tmp_path` and in-memory fakes; no repo I/O or subprocesses) verifying:
  - `_extract("doc.md", b"# Top\na\n## Dup\nb\n## Dup\nc\n")` emits selectors `["doc.md#Top", "doc.md#Dup", "doc.md#Dup (2)"]` (not two `"doc.md#Dup"` entries).
  - Building a DuckDB index with a Markdown file that has duplicate headings and running `clutch.index.query(...)` returns `outcome == "found"` (not `"index_unreadable"`), and running `clutch.index.neighbors(...)` in FTS mode returns `outcome in {"found", "no_match"}` (not `"index_unreadable"`).
- Add `tests/regress_index_fts_duplicate_selector.py`: standalone reproducer that builds a temporary DuckDB index in `tempfile.TemporaryDirectory` containing a Markdown file with duplicate headings (`## Engine conduct` twice), creates the FTS index, runs `clutch.index.query(...)`, and prints `{"regression_result": "pass"}` (exit 0) when `outcome == "found"`, `{"regression_result": "defect"}` (exit 1) when `outcome == "index_unreadable"` with the scalar-subquery error, or `{"regression_result": "error"}` (exit 2) if FTS is unavailable or another unexpected error occurs.

Scope out:
- Do not change `clutch.index.build` table schemas, `_Creator.load`, `clutch/__main__.py`, or any Markdown file in the repository.

## Scope fence
- clutch/index.py
- tests/unit/test_index_fts_duplicate_selector.py
- tests/regress_index_fts_duplicate_selector.py

## Acceptance criteria
1. `clutch.index._extract("doc.md", b"# Top\na\n## Dup\nb\n## Dup\nc\n")` returns unique selectors `["doc.md#Top", "doc.md#Dup", "doc.md#Dup (2)"]` (not duplicate `"doc.md#Dup"` entries), `clutch.index.query` returns `outcome == "found"` (not `"index_unreadable"`), and `clutch.index.neighbors` returns `outcome in {"found", "no_match"}` (not `"index_unreadable"`) on an FTS-indexed database built from a file with duplicate Markdown headings; verified by `./dev.py test tests/unit/test_index_fts_duplicate_selector.py tests/unit/test_index_build.py tests/unit/test_index_query.py tests/unit/test_index_neighbors.py`.
2. The carried regression reproducer exits `0` with `{"regression_result": "pass"}` on the branch head and exits non-zero with `{"regression_result": "defect"}` on merge base; verified by `uv run python tests/regress_index_fts_duplicate_selector.py`.

## Verification
```
./dev.py test tests/unit/test_index_fts_duplicate_selector.py tests/unit/test_index_build.py tests/unit/test_index_query.py tests/unit/test_index_neighbors.py
```

## Regression
- carries: tests/regress_index_fts_duplicate_selector.py
```
uv run python tests/regress_index_fts_duplicate_selector.py
```

## Definition of rejected
`chunks.selector` still contains duplicates for repeated Markdown headings, unique headings change their selector string, or `tests/regress_index_fts_duplicate_selector.py` fails to report `defect` on base and `pass` on head.

## Time budget
- expected: 10m
- stuck: 20m
