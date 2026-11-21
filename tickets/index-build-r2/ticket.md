---
state: draft
priority: P2
kind: feature
source: human
---

## Depends on
- meta-schema-and-refresh-r2
- evidence-envelope
- index-config-touches

## Context
- docs/annotations-index-plan.md#5. The index
- clutch/meta.py
- clutch/config.py::Index
- clutch/git.py::Git.ticket_touches
- clutch/git.py::Git.ls_files
- clutch/evidence/store.py::EvidenceStore
- clutch/journalcache.py
- clutch/seams.py::ProcessExec
- clutch/seams.py::FileSystem

## Goal / Why
Roadmap row 72, the core build of ticket 4 of `docs/annotations-index-plan.md`, split from the rejected `index-build-r1` (5 boundaries, 18 fenced files; its diagnosis names this as split 2). After this ticket `clutch/index.py` exposes `build(...)`, an async function that writes `<state_dir>/index.duckdb` with tables `files`, `chunks`, `embeddings`, `touches` and `calls` and returns a list of findings (empty means clean). Nothing calls it yet: the merge hook is `index-merge-hook` (row 181) and the `clutch index build` verb with its docs is `index-build-verb` (row 182), both later tickets. The `index` config block and `Git.ticket_touches` are already merged and are read, not changed. `duckdb` is already in `pyproject.toml`, so no dependency changes. Without the store nothing can answer which file or section a ticket should name in `## Context`.

Decisions this ticket fixes:
- Signature: `build(config, root, *, fs, git, exec_, env, store, creator, connect=duckdb.connect) -> list[str]`. `config` is the loaded `Config` (`state_dir`, `index.embed`), `root` the repo root, `fs` a `FileSystem`, `git` a `Git`, `exec_` a `ProcessExec`, `env` the child environment mapping, `store` an `EvidenceStore`, `creator` the `IndexCreator`, `connect` the DuckDB opener. All file reads and writes go through `fs`, all processes through `exec_`, all git through `git`. The database path is `config.state_dir / "index.duckdb"`.
- Indexed files are the tracked files from `git.ls_files(root)` whose suffix is `.md` or `.py`, excluding anything under `tickets/` (ticket history reaches the index through `touches`).
- `files`: one row per indexed file with columns `path`, `kind`, `purpose`, `relates` (JSON text list), `owner`, `hash`, `size`, `imports` (JSON text list; `.py` only, else `[]`). `hash` is the SHA-256 of the file's bytes, for every file, and is the change-detection key. A file with a valid `clutch.meta/1.0` block read through `meta.parse` takes `kind`, `purpose`, `relates` and `owner` from it. A file without a block, or whose block raises `meta.Malformed`, has `kind`, `purpose`, `owner` empty strings and `relates` `[]`, except a `.py` file's `purpose` is the first line of its module docstring when it has one. A file that cannot be decoded as UTF-8, or a `.py` file that fails `ast.parse`, still gets its `files` row and has no chunks. None of these is a finding.
- `chunks`: columns `path`, `selector`, `text`, `tokens`. A Markdown file has one chunk per heading, selector `path#Heading` (the heading text without its `#` marks), text from that heading to the next heading of any level; text before the first heading is not a chunk. A `.py` file has one chunk per top-level function or class, selector `path::Name`, and one per method of a top-level class, selector `path::Class.method`; text is the source segment. `tokens` is the whitespace-separated word count of `text`.
- `embeddings`: exists only when `config.index.embed` is set and every embed call succeeded. Columns `path`, `selector`, `vec FLOAT[N]` where N is the length of the first vector. The embed set is every `chunks` row with no `embeddings` row (not only chunks of changed files), so a later build repairs a dropped table. For each chunk the build writes its text with `fs.write` to a temporary file under `config.state_dir`, calls `exec_.run(embed_argv, cwd=root, env=env, timeout=EMBED_TIMEOUT_S, stdin_path=<that file>)` with `EMBED_TIMEOUT_S = 60`, and removes the file with `fs.remove` afterward. The command prints one JSON value on stdout.
- Embed validation covers EVERY value of the reply, not a list of known failures. A reply is accepted only when its exit code is 0, stdout parses as JSON, the JSON is a non-empty list, every element is an `int` or `float` that is not a `bool` and is finite (no NaN, no infinity), and its length equals the length of the first accepted vector and of the existing table's `vec` array size. Anything else is the single closed outcome `embed_failed`.
- Closed outcome table. Each finding is a string; the prefix is the outcome name:
  - `db_open_failed`: `connect` raises. Finding `db_open_failed: <error>`. The build returns exactly this one finding, writes nothing, and calls nothing else.
  - `git_failed`: `ls_files` raises `GitError`: finding `git_failed: <error>`, `files`, `chunks` and `embeddings` are left as they were and `touches` is still attempted. `ticket_touches` raises `GitError`: finding `git_failed: <error>`, `touches` is left as it was and the other tables are still built.
  - `embed_failed`: any embed call that returns nonzero, raises `ExecutableNotFound`, `TimeoutError` or `OSError`, prints non-JSON, or fails the validation above. Finding `embed_failed: <selector>: <reason>` where `<reason>` is `exit <rc>`, `exec <ExceptionClass>`, `not json`, `not a vector`, or `length <n> != <m>`. The build stops embedding at the first failure, so at most one such finding; it drops the `embeddings` table (no partial table is kept) and still writes every other table.
  - `call_unreadable`: a call record whose `read_record` raises (corrupt JSON or schema failure): finding `call_unreadable: <key>`, that call is skipped and the others are indexed. A record `read_record` returns as `SKIP`, or a call with a `start` and no `end` record, is skipped with no finding.
  - `creator`: findings the `IndexCreator` returns are appended unchanged.
- The `IndexCreator` seam is a callable `(connection, kind) -> list[str]` where `kind` is `'vss'` or `'fts'`; it loads that kind's extension and runs that kind's index DDL, returning findings (empty on success). The build calls it exactly once per build after all table writes, with `'vss'` when the `embeddings` table exists at that point and `'fts'` otherwise, and issues no `INSTALL`, `LOAD` or `CREATE INDEX` itself (creating and dropping the plain tables is the build's). `default_creator` in `clutch/index.py` is the one real creator: `INSTALL` then `LOAD` of the kind's extension (`vss` or `fts`); for `'vss'` then `SET hnsw_enable_experimental_persistence = true` and `CREATE INDEX IF NOT EXISTS ... USING HNSW` over `embeddings.vec`; for `'fts'` `PRAGMA create_fts_index('chunks', 'selector', 'text', overwrite=1)`. It turns a `duckdb.Error` into a finding `<kind> unavailable: <error>`. A load-only creator for the merge path belongs to `index-merge-hook`.
- Incremental by digest. A file whose digest equals the stored `files.hash` is skipped: no row of it in `files`, `chunks` or `embeddings` is inserted, updated or deleted and it is not re-parsed or re-chunked. A changed file has its rows in those three tables deleted and rewritten. A path stored but no longer in the tracked set has its rows deleted from those three tables. `touches` holds columns `ticket`, `commit_sha`, `path`; the build inserts only `(ticket, commit_sha)` pairs not already present. `calls` holds columns `key`, `stem`, `surface`, `tree_before`, `tree_after`, `changed_paths` (list of text), one row per call key (`store.call_keys("")`) taken from its `start` record (`stem`, `surface`, `repo.tree_before`) and `end` record (`repo.tree_after`, `repo.changed_paths`; empty strings and an empty list when `repo` is null); only keys not already present are inserted. Tool events are not read.
- `files.purpose` is not embedded here, only chunk text; whoever needs it adds it with its consumer.

## Boundary contract
### Project index store
- disposition: create
- owner: clutch/index.py
- consumers: `index-merge-hook` (row 181) and `index-build-verb` (row 182), later tickets; in this ticket only its tests call it
- observable change: `build(...)` writes `<state_dir>/index.duckdb` with `files`, `chunks`, `embeddings`, `touches`, `calls`; returns findings named by the closed outcome table in the Goal; the `IndexCreator` callable owns extension loading and index DDL
- compatibility: a new file under gitignored `state_dir`; nothing in the engine reads it, no gate or dispatch depends on it; deleting it is always safe
- acceptance: criteria 1-9 below
- tests: tests/unit/test_index_build.py, tests/unit/test_index_embeddings.py, tests/integration/test_index_extensions.py
- post-merge source of truth: clutch/index.py
- closest existing: clutch/journalcache.py (a DuckDB projection of the journal, rebuilt by folding events) and clutch/meta.py (parses one file's block). Neither indexes files, chunks, vectors, touches or calls, and journalcache owns journal segments and its own schema version, so neither can hold these tables
- earning reason: two later production consumers (the verb and the merge hook) and an external-effect fake for the embed process and the extension creator

### Index config
- disposition: reuse
- owner: clutch/config.py
- consumers: clutch/index.py reads `config.index.embed`
- observable change: none
- compatibility: `Index.embed` (argv list or unset) is read unchanged
- acceptance: criterion 4 builds with `embed` set and unset
- tests: tests/unit/test_index_embeddings.py
- post-merge source of truth: clutch/config.py

### Ticket-touch reader
- disposition: reuse
- owner: clutch/git.py
- consumers: clutch/index.py calls `Git.ticket_touches` and `Git.ls_files`
- observable change: none
- compatibility: both methods are called unchanged and faked in tests
- acceptance: criterion 1 asserts `touches` rows from a fake returning `(stem, commit, paths)` tuples
- tests: tests/unit/test_index_build.py
- post-merge source of truth: clutch/git.py

### Evidence call records
- disposition: reuse
- owner: clutch/evidence/store.py
- consumers: clutch/index.py reads `call_keys` and `read_record`
- observable change: none; read only
- compatibility: no record is written; `SKIP` records are skipped
- acceptance: criterion 1 asserts `calls` rows and criterion 5 the `call_unreadable` outcome
- tests: tests/unit/test_index_build.py
- post-merge source of truth: clutch/evidence/store.py

## Scope in / Scope out
Scope in:
- New `clutch/index.py` with `build`, `default_creator`, `EMBED_TIMEOUT_S` and the `IndexCreator` type, as the Goal states. Every filesystem, process and git use goes through the injected seams. Because the module is new, `test-gate.toml` applies its default 90% unit coverage floor to it: the unit tests run every line except the two extension branches in `default_creator`, which they run through a recording fake connection, so no `test-gate.toml` edit is made.
- New tests: `tests/unit/test_index_build.py` (tables, incremental, outcomes), `tests/unit/test_index_embeddings.py` (embed paths), `tests/integration/test_index_extensions.py` (real `vss` and `fts`). Fixtures and fakes live in those files; no shared fixture is edited.
- No documentation is changed: the project index docs are delivered with the verb in `index-build-verb`, and the module has no CLI surface here.

Scope out: the merge hook (`index-merge-hook`), the `clutch index build` verb, its exit codes and docs (`index-build-verb`), any search or `context suggest` code, embedding `files.purpose`, call tool events, any edit to `clutch/config.py`, `clutch/git.py`, `clutch/evidence/store.py`, `clutch/meta.py`, `clutch/__main__.py`, `clutch/stages.py` or any hot test file. `clutch/evidence/store.py` is fenced by the unmerged `evidence-captures` ticket and only read here; `clutch/serve.py` and `clutch/daemon.py` are fenced by the unmerged `serve-polls-block-parallel-runs` and untouched here, so merge order changes nothing.

## Scope fence
- clutch/index.py
- tests/unit/test_index_build.py
- tests/unit/test_index_embeddings.py
- tests/integration/test_index_extensions.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_index_build.py` builds over a fake `FileSystem`-backed tree (a `tmp_path` root through `LocalFileSystem`), a fake `git` (`ls_files`, `ticket_touches`) and a fake `EvidenceStore`, and asserts exact `files`, `chunks`, `touches` and `calls` rows, including selectors `path#Heading`, `path::Name` and `path::Class.method`, a `.py` file's `purpose` taken from its docstring, an annotated file's `kind` and `purpose` taken from its block, and that nothing under `tickets/` is indexed; a build whose `chunks` is empty, or that indexes `tickets/x.md`, fails it.
2. `./dev.py test tests/unit/test_index_build.py` asserts the build opens `config.state_dir / "index.duckdb"` through the injected `connect` and that the file exists afterward; a `connect` that raises yields exactly the one finding `db_open_failed: ...`, no exception, and no table written; a build that also returns any other finding fails it.
3. `./dev.py test tests/unit/test_index_build.py` asserts a file with a malformed block, an undecodable file and a `.py` file with a syntax error each get a `files` row, produce no finding, and the latter two have no chunks; a build that raises or drops the row fails it.
4. `./dev.py test tests/unit/test_index_embeddings.py` runs with `embed: ["fake"]` and a fake `exec_` returning a 3-element JSON list per chunk, and asserts one `embeddings` row per chunk, that every call used `stdin_path` under `state_dir`, `cwd=root` and `timeout=60`, that the temporary files are removed through `fs.remove`, and that the recording creator was called exactly once with `'vss'`; with `embed` unset it asserts no `embeddings` table, `exec_` never called, and the creator called exactly once with `'fts'`; a build calling the creator twice or with the wrong kind fails it.
5. `./dev.py test tests/unit/test_index_embeddings.py` asserts each of these replies yields exactly one finding of the form `embed_failed: <selector>: <reason>` with the named reason, no `embeddings` table, the other tables still written, and the creator called with `'fts'`: nonzero exit (`exit 2`), `ExecutableNotFound` and `TimeoutError` (`exec <ExceptionClass>`), non-JSON stdout (`not json`), JSON that is a string, an object, `[]`, a list holding a string, a list holding `true`, a list holding `NaN` (`not a vector`), and a second vector of another length (`length 2 != 3`); a partial table, a second finding, or a reply accepted from any of these fails it.
6. `./dev.py test tests/unit/test_index_embeddings.py` asserts that after an embed failure a next build with a working embed command embeds every chunk (including chunks of unchanged files) and that a build whose new vectors differ in length from the existing table yields one `embed_failed: ...: length ...` finding and drops the table.
7. `./dev.py test tests/unit/test_index_build.py` asserts that a second build over unchanged files reads each tracked `.md` or `.py` file exactly once through `fs.read_bytes` and issues no INSERT, UPDATE or DELETE statement touching `files`, `chunks` or `embeddings` (counted on a recording connection wrapper passed through `connect`), that `touches` and `calls` gain no duplicate rows, that editing one file rewrites only that file's rows, and that a file removed from the tracked set has its rows deleted from all three tables; a full rebuild fails the statement-count assertion.
8. `./dev.py test tests/unit/test_index_build.py` asserts the `git_failed` outcome for each of `ls_files` raising `GitError` and `ticket_touches` raising `GitError` (one `git_failed: ...` finding, the named tables unchanged, the others built), the `call_unreadable: <key>` outcome (one finding for that key, other calls indexed), and that a `SKIP` record and a start-only call add no row and no finding.
9. `./dev.py test tests/unit/test_index_build.py` asserts that the build issues no statement beginning with `INSTALL`, `LOAD` or `CREATE INDEX` and no `PRAGMA create_fts_index` on the connection, that the creator is the only source of them (the recording creator's own statements are the only ones seen), that creator findings are returned unchanged after the build's own, and that `default_creator` driven with a recording connection issues `INSTALL` then `LOAD` of `vss` then the `hnsw_enable_experimental_persistence` `SET` then an HNSW `CREATE INDEX IF NOT EXISTS` for `'vss'`, and `INSTALL`, `LOAD` of `fts`, `PRAGMA create_fts_index` for `'fts'`, and returns `<kind> unavailable: ...` when the connection raises `duckdb.Error`; a creator that returns `[]` after a raise fails it.
10. `./dev.py test tests/integration/test_index_extensions.py` runs `build` with `default_creator` against real DuckDB, a real `vss` and `fts` load, and a 3-dimensional fake embed, then builds a second time after editing one file and asserts the second build returns `[]` and the index still answers a nearest-vector query; it skips with the reason "vss/fts extensions unavailable offline" when the extensions cannot be installed. Opening any SQLite file anywhere in `clutch/index.py` is ruled out by `grep -n sqlite clutch/index.py` printing nothing, checked by the same test reading the source.
11. `./dev.py test tests/unit/test_stage_events_seam.py tests/integration/test_vocabularies.py tests/integration/test_thresh.py tests/integration/test_projection_helpers_source.py` pass with `clutch/index.py` present; a raw clock, process or filesystem call in the new module fails them.

## Verification
```
./dev.py test tests/unit/test_index_build.py tests/unit/test_index_embeddings.py tests/integration/test_index_extensions.py tests/unit/test_stage_events_seam.py tests/integration/test_vocabularies.py tests/integration/test_thresh.py tests/integration/test_projection_helpers_source.py
```

## Definition of rejected
The branch is thrown away if any code opens a SQLite file, if `build` issues `INSTALL`, `LOAD` or index DDL outside the `IndexCreator`, if a partial `embeddings` table survives an embed failure, if a build calls the creator more than once, if an unchanged file's rows are rewritten, if any file outside the Scope fence is edited (in particular `clutch/config.py`, `clutch/git.py`, `clutch/evidence/store.py`, `clutch/__main__.py`, `clutch/merge.py`, `clutch/mergequeue.py`, `docs/how-clutch-works.md`), or if anything in the engine reads `index.duckdb`.

## Time budget
- expected: 30m
- stuck: 60m
