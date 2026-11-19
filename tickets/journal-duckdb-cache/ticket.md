---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/journal.py
- clutch/status.py::SETTLED
- clutch/status.py::reject_queue
- clutch/status.py::latest_transitions
- clutch/status.py::last_states
- clutch/seams.py::LocalFileSystem
- tests/unit/test_scaffold.py
- tests/unit/test_journal_incremental.py
- docs/journal-sql-refactor-plan.md#Target design
- docs/how-clutch-works.md#10.1 Files
- pyproject.toml
- tickets/snapshot-duckdb-under-one-second/evidence/snapshot-incident-profile.txt

## Goal / Why
Owner request, 2026-11-19. `clutch view snapshot` takes about 40 s on this checkout (27 s in the incident). The profile `tickets/snapshot-duckdb-under-one-second/evidence/snapshot-incident-profile.txt` shows 4,809 `last_states` and 1,572 `reject_queue` calls, each re-scanning the whole journal. Owner direction: merged tickets are static facts, so DuckDB keeps a file instead of re-reading and re-parsing the journal on every invocation.

When this ticket is done, a new module `clutch/journalcache.py` keeps a persistent DuckDB file at `<state_dir>/cache/journal.duckdb`. The file is a rebuildable projection of the journal, never an authority. The JSONL segments stay the source of truth (CLAUDE.md "Files + journal are the source of truth"). On each open the cache loads only the complete lines appended since its last load. It answers three set queries whose results equal the existing Python folds on the same events: the latest state per stem (`status.last_states`), the Reject queue (`status.reject_queue`), and the settled stems (stems whose latest state is in `status.SETTLED`). This ticket builds only the cache. No consumer changes; a later ticket moves the snapshot onto it.

## Boundary contract
### Journal cache
- disposition: create
- owner: clutch/journalcache.py
- consumers: none in this ticket; the snapshot and admission port that follows (`snapshot-from-duckdb-cache`) is the first production consumer, and the journal plan's port tickets the next
- observable change: `open_journal_cache(state_dir)` is a context manager. It takes an exclusive advisory `flock` on `<state_dir>/cache/journal.duckdb.lock`, creating `<state_dir>/cache/` if needed, then opens `<state_dir>/cache/journal.duckdb` read-write and loads new journal lines. It yields a `JournalCache` with `last_states() -> dict[str, str]`, `reject_queue() -> dict[str, dict]` and `settled() -> frozenset[str]`. On exit it closes the connection and releases the lock. Schema: `meta(schema_version)`; `segments(name, offset, lines, fingerprint)`; and `events(seq, v, type, ts, ticket, key, body)`, where `seq` is the global append order (segment name order, then line order) and `body` is JSON text.
- compatibility: the journal format, its writers and `Journal`'s readers are unchanged. The JSONL segments stay the only authority, and deleting `cache/` loses nothing. `clutch/journal.py` changes only by renaming `Journal._segments` to the public `Journal.segments` in place, with every call site in that file updated; there are no callers outside it.
- acceptance: a load reads only complete lines from each segment's recorded offset, through `clutch.journal._parse_complete_lines` (the one line parser; a malformed line raises `JournalCorruption` and the load's transaction commits nothing). An unterminated last line is left for a later open. The cache rebuilds from an empty database when any of these holds: the file is missing; DuckDB cannot open it or its schema; `meta.schema_version` differs from the module's `SCHEMA_VERSION`; a recorded segment is missing; a recorded segment is smaller than its recorded offset; or a recorded segment's fingerprint differs. The fingerprint is the sha256 of the first and last up to 4096 bytes of the loaded prefix `[0, offset)`. Segments new since the last load are read from offset 0. Event inserts and offset updates commit in one transaction.
- tests: tests/unit/test_journal_duckdb_cache.py (equality, incremental load and rebuild triggers, under `tmp_path`); tests/integration/test_journal_duckdb_cache.py (two processes opening one cache, and a real `Journal` appending between opens)
- post-merge source of truth: the JSONL journal through `clutch/journal.py`; `clutch/journalcache.py` owns only the cache file's schema, load and queries
- closest existing: `Journal.read_segments` and its in-process `_cache` in clutch/journal.py parse each byte once per process, but they die with the process, and every CLI invocation re-parses about 18 MB. `status.last_states` and `status.reject_queue` are full-history Python folds; the snapshot calls them thousands of times.
- earning reason: a storage and package boundary. A persistent on-disk file that survives across processes needs the new `duckdb` package (journal plan, D3's named trigger, roadmap decision 12), and the incident profile measures the repeated full-history folds it removes.

### Journal segment listing
- disposition: extend
- owner: clutch/journal.py
- consumers: `Journal` itself (append, read_segments) and `clutch/journalcache.py`
- observable change: `Journal._segments` becomes the public `Journal.segments`, with the same return value and `JournalCorruption` refusals
- compatibility: preserved behavior; the rename is in place with every call site in clutch/journal.py updated, and a grep finds no caller outside it
- acceptance: the existing journal tests pass unchanged
- tests: tests/unit/test_journal_incremental.py and tests/integration/test_journal_roll.py, unchanged
- post-merge source of truth: clutch/journal.py

## Scope in / Scope out
Scope in:
- Add `duckdb` to `[project].dependencies` in `pyproject.toml` with `uv add duckdb` (2.0.0 installs on Python 3.14), which also updates `uv.lock`. In `tests/unit/test_scaffold.py::test_pyproject_pins_python_floor_and_runtime_deps`, change the pinned set to `{"pyyaml", "pydantic", "duckdb"}`. The earning incident is the snapshot profile above.
- Rename `Journal._segments` to `Journal.segments` in `clutch/journal.py` and update its call sites in that file. Nothing else changes in `clutch/journal.py`.
- Create `clutch/journalcache.py` as described in the Boundary contract. It imports `_parse_complete_lines` from `clutch.journal`, as `tests/unit/test_journal_incremental.py` already does, and never writes a second line parser. It lists segments with `Journal(state_dir, clock).segments()`. Segment bytes past the recorded offset are read with `open`/`seek`, as `Journal._read_active` reads them; the `FileSystem` seam has no ranged read. The cache directory is created through `LocalFileSystem.mkdir`. The module needs no clock beyond the one `Journal` takes, and it passes a clock that is never called for reads.
- Queries are SQL over `events`, ordered by `seq`, never `ts`, so colliding timestamps resolve by append order exactly as the Python folds do.
  - `last_states`: the latest `state_transition` per stem whose body has `to`.
  - `reject_queue`: the `status.reject_queue` fold expressed as a set query. Return each waiting stem's latest terminal body, parsed back to a `dict`.
  - `settled`: the stems whose latest state is in `status.SETTLED`. Import `SETTLED` from `clutch.status`; never copy it.
  Split dependencies (`rework.settled_dependencies`, the supersedes maps) stay Python and out of this ticket.
- Concurrency: DuckDB lets one process open a database file read-write, or several processes open it read-only, never both at once. Every open therefore holds an exclusive blocking `flock` on `cache/journal.duckdb.lock` for the whole open, load, query and close cycle, so concurrent readers serialize and none writes beside another. The kernel frees the lock when a holder dies. An engine appending to the journal meanwhile is safe: the cache reads only complete lines, and the writer's `_truncate_torn_tail` touches only bytes after the last newline.
- docs/how-clutch-works.md section 10.1: add a table row for `cache/journal.duckdb` (rebuildable projection of the journal, never authoritative; delete it to force a rebuild) and its `cache/journal.duckdb.lock`.
- docs/journal-sql-refactor-plan.md, Target design: amend the "Single source of truth" bullet, which says nothing derived is saved to disk, to describe this persistent rebuildable cache and its rebuild triggers.
- docs/roadmap.md, decision 15: change only the sentence that says `duckdb` enters `pyproject.toml` with `journal-query-layer` or `index-build`, to say `journal-duckdb-cache` added it.
- New tests:
  - `tests/unit/test_journal_duckdb_cache.py` uses disk only under `tmp_path`. It writes segment files directly with events in the journal envelope.
  - `tests/integration/test_journal_duckdb_cache.py` covers the multi-process cases.

Scope out:
- No consumer changes: `clutch/observe.py`, `clutch/status.py`, `clutch/drain.py`, `clutch/serve.py`, `clutch/rework.py`, `clutch/__main__.py` and every journal call site stay as they are (`snapshot-from-duckdb-cache` owns the port).
- No CLI verb, no config key, and no change to `Journal.append` or `Journal.read_segments`.
- No in-memory fallback when the cache cannot open: a lock wait blocks, and an unreadable file rebuilds.

## Scope fence
- pyproject.toml
- uv.lock
- tests/unit/test_scaffold.py
- clutch/journal.py
- clutch/journalcache.py
- tests/unit/test_journal_duckdb_cache.py
- tests/integration/test_journal_duckdb_cache.py
- docs/how-clutch-works.md
- docs/journal-sql-refactor-plan.md
- docs/roadmap.md

## Acceptance criteria
1. `tests/unit/test_scaffold.py` passes with the runtime set `{"pyyaml", "pydantic", "duckdb"}`, and `uv.lock` lists `duckdb`. The `./dev.py test` run in `## Verification` checks both.
2. In `tests/unit/test_journal_duckdb_cache.py`, the cache's results equal the Python folds on the same segment files. `last_states()` equals `status.last_states(events)`, `reject_queue()` equals `status.reject_queue(events)`, and `settled()` equals `{s for s, st in status.last_states(events).items() if st in status.SETTLED}`. The histories cover: an empty journal; sequential transitions to running, merged and rejected; a `routed: reject_queue` terminal followed by `reject_verdict`; a `reject_arrival` before and after a terminal; a re-run that leaves the queue; a settled stem with a stale routed body; two segments; and two transitions for one stem with an identical `ts`. On the identical-`ts` case, a cache that orders by `ts` instead of append order fails.
3. `tests/unit/test_journal_duckdb_cache.py` shows an incremental load. After a first open, appending one complete line and an unterminated partial line, then reopening, the cache contains exactly one new event, and its recorded offset ends at the last newline. Completing the partial line and reopening adds it. Wrapping `clutch.journal._parse_complete_lines` with a counting wrapper (patched where `clutch.journalcache` looks it up) shows the second open parses only the appended line, not the whole segment. A test that also passes with a full re-parse on every open fails this check.
4. `tests/unit/test_journal_duckdb_cache.py` shows each rebuild trigger produces results equal to the Python folds. The triggers: a deleted cache file; a garbage cache file; a changed `schema_version`; a removed segment; a segment truncated below its recorded offset; and a segment rewritten in place to the same length with different bytes. After the rewrite case, `last_states()` reflects the new bytes, not the stale rows.
5. `tests/unit/test_journal_duckdb_cache.py` shows a malformed complete line raises `JournalCorruption`, and a following open after the line is fixed returns fold-equal results. The failed load committed no partial rows.
6. `tests/integration/test_journal_duckdb_cache.py` shows two concurrent processes each open the same cache over a shared journal and both return results equal to `status.last_states` on that journal. Neither process raises DuckDB's lock error.
7. `tests/integration/test_journal_duckdb_cache.py` appends events through a real `Journal` between cache opens, including across a forced segment roll. Each open returns results equal to the folds over `Journal.read()`.
8. Review checks that `docs/how-clutch-works.md` section 10.1 lists `cache/journal.duckdb` and its lock, and that `docs/journal-sql-refactor-plan.md` Target design no longer says nothing derived is saved to disk. `git diff` shows `clutch/observe.py`, `clutch/status.py`, `clutch/drain.py` and `clutch/serve.py` unchanged.

## Verification
```
./dev.py test tests/unit/test_journal_duckdb_cache.py tests/integration/test_journal_duckdb_cache.py tests/unit/test_scaffold.py tests/unit/test_journal_incremental.py tests/integration/test_journal_roll.py
```

## Definition of rejected
Reject if the cache becomes an authority: any code path reads the cache in place of the journal for a decision in this ticket, or the cache is written outside `<state_dir>/cache/`. Also reject if a second line parser is written, if query results differ from the Python folds on any tested history, if two processes can hold the cache file read-write at once, or if any consumer module (observe, status, drain, serve) changes.

## Time budget
- expected: 25m
- stuck: 50m
