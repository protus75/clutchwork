---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
none

## Context
- clutch/index.py::Hit
- clutch/index.py::Neighbors
- clutch/index.py::neighbors
- clutch/__main__.py::_run_context_suggest
- clutch/__main__.py::_run_index
- docs/how-clutch-works.md#2.1 Verbs
- docs/how-clutch-works.md#14. Project index
- clutch/docs/host-running.md
- README.md#Install

## Goal / Why
`clutch context suggest <stem>` only queries `<state_dir>/index.duckdb` for an existing ticket draft, so operators and chat agents exploring the repository have no read-only command to search indexed file metadata (`purpose`, `relates`, `owner`, `kind`) and chunks (`path#Heading`, `path::Name`) by topic. Adding `clutch index query <text> [--limit N]` exposes lock-free, read-only search over the project index while `engine serve` runs.

## Boundary contract
### Project index query API
- disposition: extend
- owner: clutch/index.py
- consumers: clutch/__main__.py
- observable change: add frozen dataclasses `QueryHit(path, kind, selector, purpose, relates, owner, score)` and `QueryResult(outcome, mode="", hits=(), findings=())`, and `async def query(config, root, text, *, fs, exec_, env, creator, limit=10, connect=duckdb.connect) -> QueryResult` that searches tracked repository chunks joined with `files` (excluding `box:` and `tickets/` paths), using embeddings when `config.index.embed` and `embeddings` are available else DuckDB FTS `match_bm25`, returning closed outcomes `found`, `no_match`, `invalid_input`, `no_index`, `index_unreadable`, or `fulltext_unavailable`.
- compatibility: existing `build` and `neighbors` functions and `index.duckdb` table schemas remain unchanged.
- acceptance: valid queries return hits ranked by `(-score, selector)` with parsed `relates` tuples; invalid inputs, missing index, unreadable index, and missing FTS return their closed outcomes without raising.
- tests: `tests/unit/test_index_query.py`
- post-merge source of truth: `clutch/index.py`

### CLI index query verb
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators and chat agents running `clutch index query`
- observable change: add `clutch index query <text> [--limit N]` under the existing `index` command group, running read-only without taking the writer lock, printing `index query: found` followed by `- <selector>  # <detail>` lines or `index query: none`, exiting `0` on `found`/`no_match` and `2` with `clutch index query: <message> -- <remedy>` on stderr for `invalid_input`, `no_index`, `index_unreadable`, or `fulltext_unavailable`.
- compatibility: `clutch index build` behavior, lock, output, and exit codes remain unchanged; `index` group help lists both `build` and `query`.
- acceptance: parser help, examples, exit codes, output format, and lock-free dispatch are verified by unit tests.
- tests: `tests/unit/test_index_query_verb.py` and `tests/unit/test_main_help.py`
- post-merge source of truth: `clutch/__main__.py`

## Scope in / Scope out
Scope in:
- In `clutch/index.py`:
  - Add frozen dataclasses `QueryHit(path: str, kind: str, selector: str, purpose: str, relates: tuple[str, ...], owner: str, score: float)` and `QueryResult(outcome: str, mode: str = "", hits: tuple[QueryHit, ...] = (), findings: tuple[str, ...] = ())`.
  - Add `async def query(config, root, text, *, fs, exec_, env, creator, limit=10, connect=duckdb.connect) -> QueryResult`:
    - Validate `text` (must be `str`, non-blank, `<= 8000` characters) and `limit` (`type(limit) is int and 1 <= limit <= 50`), returning `QueryResult("invalid_input", findings=(...,))` on failure.
    - Check `<state_dir>/index.duckdb` via `fs.size(path)` and open read-only with `connect(str(path), read_only=True)` (no lock). Return `no_index` on `FileNotFoundError` and `index_unreadable` on `OSError`, `duckdb.Error`, or missing `files`/`chunks` columns.
    - When `config.index.embed` is set, attempt `creator.load(conn, "vss")`, check `_exists(conn, "embeddings")`, and call `_embed_vector(...)`; on failure, append `embed_failed: ...` to `findings` and fall back to FTS.
    - In FTS mode, call `creator.load(conn, "fts")` and verify `fts_main_chunks` schema exists; if unavailable, return `QueryResult("fulltext_unavailable", findings=...)`.
    - Query `chunks c JOIN files f ON c.path = f.path` for tracked repo files (`NOT c.path LIKE 'box:%' AND NOT c.path LIKE 'tickets/%'`), excluding `None` or non-finite scores. Parse `f.relates` JSON list into a tuple of strings (empty tuple if malformed). Sort by `(-score, selector)`, slice to `limit`, and return `found` if non-empty else `no_match`.
- In `clutch/__main__.py`:
  - Update `index_parser` `help`, `description` (`Build and query the project index. Subcommands: build, query.`), and `epilog` to include both `clutch index build` and `clutch index query`.
  - Add `query` subcommand via `_command(index_sub, "query", ...)` with positional `text`, optional `--limit` (`type=int`, default `10`), and complete `summary`, `does`, `reads`, `writes`, `lock` (`None; read-only, works while serve runs.`), `exits` (`0 found or none; 2 invalid_input, no_index, index_unreadable or fulltext_unavailable.`), and `examples`.
  - Add `async def _run_index_query(config, root, text, *, fs, exec_, env, creator, limit=10, query=index.query)` and dispatch `args.index_verb == "query"` in `handle_index()` without entering `_locked(...)`.
  - Format output: print `index query: found` and one line per hit `- <selector>  # <detail>` (joining non-empty `[kind]`, `purpose`, `owner: <owner>`, `relates: <a, b>` cleanly on one line), or `index query: none` on `no_match`. On `invalid_input`, `no_index`, `index_unreadable`, or `fulltext_unavailable`, print `clutch index query: <message> -- <remedy>` via `_fail` and return `2`.
- Update documentation per Docs-follow-commands:
  - `README.md` (`## Install`): mention `clutch index query <text>` beside `clutch index build`.
  - `docs/how-clutch-works.md`: add `index query <text> [--limit N]` row (Lock: no) to `### 2.1 Verbs`, and describe its behavior, output, and exit codes in `## 14. Project index`.
  - `clutch/docs/host-running.md`: add `index query` row (Works while serve runs: Yes) to the verb table.
- Add unit tests in `tests/unit/test_index_query.py` and `tests/unit/test_index_query_verb.py` using `tmp_path` and fakes (covering the new lines in `clutch/__main__.py` and `clutch/index.py` with no repo-file I/O or subprocesses).

Scope out:
- Do not change `clutch index build`, `clutch.index.neighbors`, `clutch context suggest`, `index.duckdb` table schemas, `clutch/help.py`, `vscode-clutchwork/`, or `tests/integration/test_cli.py`.

## Scope fence
- clutch/index.py
- clutch/__main__.py
- README.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/unit/test_index_query.py
- tests/unit/test_index_query_verb.py

## Acceptance criteria
1. `clutch.index.query` returns `QueryResult(outcome="found", mode="fulltext", ...)` with tracked repo chunks ranked by `(-score, selector)` and populated `kind`, `purpose`, `relates`, and `owner`, while excluding `box:` and `tickets/` paths (not returning them even when they match the query text); verified by `./dev.py test tests/unit/test_index_query.py`.
2. `clutch.index.query` uses `mode="embedding"` when `config.index.embed` and `embeddings` succeed, falls back to `mode="fulltext"` with an `embed_failed:` finding when embedding fails, and returns closed outcomes `no_match`, `invalid_input` (blank text, `>8000` chars, or `limit` outside `1..50`), `no_index`, `index_unreadable`, and `fulltext_unavailable` without raising; verified by `./dev.py test tests/unit/test_index_query.py`.
3. `_run_index_query` and `clutch index query` print `index query: found` with `- <selector>  # ...` lines (exit `0`), `index query: none` on `no_match` (exit `0`), and `clutch index query: ... -- ...` on stderr (exit `2`) for refusal outcomes, and `handle_index` dispatches `index query` without acquiring the writer lock (not calling `_locked`); verified by `./dev.py test tests/unit/test_index_query_verb.py`.
4. `clutch index` and `clutch index query` parser help, examples, and `clutch index build` behavior pass existing and new CLI help checks; verified by `./dev.py test tests/unit/test_index_verb.py tests/unit/test_main_help.py`.
5. `README.md`, `docs/how-clutch-works.md`, and `clutch/docs/host-running.md` document `clutch index query` with its read-only/no-lock contract; verified by reviewing the diff on those three files.

## Verification
```
./dev.py test tests/unit/test_index_query.py tests/unit/test_index_query_verb.py tests/unit/test_index_verb.py tests/unit/test_main_help.py
```

## Definition of rejected
`clutch index query` acquires the writer lock, modifies `index.duckdb`, breaks `clutch index build` or `tests/unit/test_main_help.py`, or omits any required documentation update in `README.md`, `docs/how-clutch-works.md`, or `clutch/docs/host-running.md`.

## Time budget
- expected: 15m
- stuck: 30m
