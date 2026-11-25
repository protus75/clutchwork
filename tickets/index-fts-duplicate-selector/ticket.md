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
- clutch/context.py::suggest
- tests/unit/test_index_query.py
- tests/unit/test_context_suggest.py

## Goal / Why
`clutch/index.py::_extract` emits `(path, f"{path}#{title}", ...)` for every Markdown heading without disambiguating repeated headings in the same file (for example, `AGENTS.md#Engine conduct` and `docs/gemini-graphics-refactor-plan.md#Target design` each appear twice in `.clutch/state/index.duckdb`). Because DuckDB's `PRAGMA create_fts_index('chunks', 'selector', 'text', overwrite=1)` keys `fts_main_chunks` on `selector`, `fts_main_chunks.match_bm25(c.selector, ?)` in `clutch.index.query` and `clutch.index.neighbors` crashes with `Invalid Input Error: More than one row returned by a subquery used as an expression` on any index built from this repository. Guaranteeing unique `chunks.selector` values per file in `_extract` restores working FTS queries across the whole repo.

## Boundary contract
### Project index chunk selector extraction and duplicate refresh
- disposition: extend
- owner: clutch/index.py
- consumers: `clutch.index.build`, `clutch.index.query`, `clutch.index.neighbors`, `clutch.context.suggest`
- observable change: restore collision-safe uniqueness of `chunks.selector` per file in `_extract(path, data)` when a Markdown file contains repeated headings (tracking a per-file `used: set[str]` of emitted selectors so the first occurrence keeps `f"{path}#{title}"` and any collision increments `n = 2, 3, ...` until `f"{path}#{title} ({n})"` is not in `used`, e.g. `Dup`, `Dup`, `Dup (2)` -> `doc.md#Dup`, `doc.md#Dup (2)`, `doc.md#Dup (2) (2)`), and in `build(...)` query `dup_paths` (`SELECT path FROM chunks GROUP BY path, selector HAVING COUNT(*) > 1`) before the file loop so unchanged files with pre-existing duplicate rows in `chunks` are re-extracted instead of skipped by the `old.get(path) == digest` check.
- compatibility: unique Markdown headings without collisions and all Python AST selectors (`path::Name`, `path::Class.method`) keep identical selector strings; existing `index.duckdb` table schemas are unchanged, and rebuilding an existing index with `clutch index build` refreshes pre-existing duplicate rows automatically.
- acceptance: criterion 1 and criterion 2
- tests: `tests/unit/test_index_fts_duplicate_selector.py` and `tests/regress_index_fts_duplicate_selector.py`
- post-merge source of truth: `clutch/index.py`

### Context suggestion filter for disambiguated duplicate headings
- disposition: extend
- owner: clutch/context.py
- consumers: `clutch.context.suggest`, `clutch.context.hint_block`, `clutch.context.suggest_for_stem`
- observable change: `suggest(...)` excludes disambiguated duplicate-heading selectors (`path#title (n)` where `path#title` also exists in `chunks`) so unresolvable suffixed selectors never appear in `## Context` suggestions (`clutch/tickets.py` heading resolution requires a single heading match).
- compatibility: unique Markdown headings (including a standalone `## Foo (2)` with no `## Foo`) and all Python AST selectors remain eligible for suggestions.
- acceptance: criterion 1
- tests: `tests/unit/test_index_fts_duplicate_selector.py`, `tests/unit/test_context_suggest.py`
- post-merge source of truth: `clutch/context.py`

## Scope in / Scope out
Scope in:
- In `clutch/index.py::_extract`: track a per-file `used: set[str]` of emitted selectors for Markdown headings; start with `candidate = f"{path}#{title}"`, and while `candidate in used` try `f"{path}#{title} ({n})"` (`n = 2, 3, ...`), then record `candidate` in `used` so every emitted `(path, selector)` in `chunks` is collision-free even if the document contains literal `Dup (2)` after `Dup`, `Dup`.
- In `clutch/index.py::build`: before the file loop, query `dup_paths = {row[0] for row in conn.execute("SELECT path FROM chunks GROUP BY path, selector HAVING COUNT(*) > 1").fetchall()}` and skip a file only when `old.get(path) == digest and path not in dup_paths`, so `clutch index build` refreshes pre-existing databases that already contain duplicate selectors without changing table schemas.
- In `clutch/context.py::suggest`: collect `chunk_selectors = {selector for _, selector, _ in chunks}` and skip any `selector` matching `^(.+#.+) \(\d+\)$` whose base group `m.group(1)` is also in `chunk_selectors`, keeping disambiguated duplicate-heading selectors out of `## Context` suggestions.
- Add `tests/unit/test_index_fts_duplicate_selector.py` (using `tmp_path` and in-memory fakes; no repo I/O or subprocesses) verifying:
  - `_extract("doc.md", b"# Top\na\n## Dup\nb\n## Dup\nc\n## Dup (2)\nd\n")` emits collision-free unique selectors `["doc.md#Top", "doc.md#Dup", "doc.md#Dup (2)", "doc.md#Dup (2) (2)"]` (zero duplicates).
  - Pre-populating `index.duckdb` with matching `files.hash` and duplicate `chunks.selector` rows and running `clutch.index.build(...)` re-extracts that file and eliminates the duplicates (not skipped by hash equality).
  - Building a DuckDB index with a Markdown file that has duplicate headings and running `clutch.index.query(...)` returns `outcome == "found"` (not `"index_unreadable"`), and running `clutch.index.neighbors(...)` in FTS mode returns `outcome in {"found", "no_match"}` (not `"index_unreadable"`).
  - `clutch.context.suggest(...)` omits disambiguated duplicate selectors like `doc.md#Dup (2)` when `doc.md#Dup` exists in `chunks`, while still returning a standalone unique `doc.md#Solo (2)` when `doc.md#Solo` does not exist.
- Add `tests/regress_index_fts_duplicate_selector.py`: standalone reproducer that builds a temporary DuckDB index in `tempfile.TemporaryDirectory` containing a Markdown file with duplicate headings (`## Engine conduct` twice), creates the FTS index, runs `clutch.index.query(...)`, and prints `{"regression_result": "pass"}` (exit 0) when `outcome == "found"`, `{"regression_result": "defect"}` (exit 1) when `outcome == "index_unreadable"` with the scalar-subquery error, or `{"regression_result": "error"}` (exit 2) if FTS is unavailable or another unexpected error occurs.

Scope out:
- Do not change `clutch.index.build` table schemas, `_Creator.load`, `clutch/tickets.py`, `clutch/__main__.py`, or any Markdown file in the repository.

## Scope fence
- clutch/index.py
- clutch/context.py
- tests/unit/test_index_fts_duplicate_selector.py
- tests/regress_index_fts_duplicate_selector.py

## Acceptance criteria
1. `clutch.index._extract("doc.md", b"# Top\na\n## Dup\nb\n## Dup\nc\n## Dup (2)\nd\n")` returns collision-free unique selectors `["doc.md#Top", "doc.md#Dup", "doc.md#Dup (2)", "doc.md#Dup (2) (2)"]`; `clutch.index.build` re-extracts unchanged files that have pre-existing duplicate `chunks.selector` rows; `clutch.index.query` returns `outcome == "found"` (not `"index_unreadable"`); `clutch.index.neighbors` returns `outcome in {"found", "no_match"}` (not `"index_unreadable"`) in FTS mode; and `clutch.context.suggest` excludes disambiguated duplicate selectors when their base selector exists while preserving unique `Solo (2)` headings. Verified by `./dev.py test tests/unit/test_index_fts_duplicate_selector.py tests/unit/test_index_build.py tests/unit/test_index_query.py tests/unit/test_index_neighbors.py tests/unit/test_context_suggest.py`.
2. The carried regression reproducer exits `0` with `{"regression_result": "pass"}` on the branch head and exits non-zero with `{"regression_result": "defect"}` on merge base; verified by `uv run python tests/regress_index_fts_duplicate_selector.py`.

## Verification
```
./dev.py test tests/unit/test_index_fts_duplicate_selector.py tests/unit/test_index_build.py tests/unit/test_index_query.py tests/unit/test_index_neighbors.py tests/unit/test_context_suggest.py
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
