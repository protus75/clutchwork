---
state: draft
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- meta-schema-and-refresh-r2
- evidence-envelope

## Context
- docs/annotations-index-plan.md
- clutch/meta.py
- clutch/journalcache.py
- clutch/seams.py
- clutch/evidence/store.py
- clutch/git.py
- clutch/config.py
- clutch/merge.py::write_squash
- clutch/mergequeue.py
- clutch/docs/host-running.md
- tests/unit/test_host_running.py

## Goal / Why
Roadmap row 72 (ticket 4 of `docs/annotations-index-plan.md`). After this ticket `uv run clutch index build` writes `<state_dir>/index.duckdb`, a derived, deletable cache with tables `files`, `chunks`, `embeddings`, `touches` and `calls`, and every real merge to main refreshes it for the changed paths. Today nothing can answer which file or section a ticket should name in `## Context`, so authors fence whole documents. `duckdb` is already a dependency in `pyproject.toml`, so no dependency change is made.

Decisions this ticket fixes:
- `files` holds one row per file: path, kind, purpose, relates, owner, hash, size. Annotated files take these from the meta block read by `clutch/meta.py`; `.py` files take docstring, definitions and imports from the AST.
- `chunks` holds one row per Markdown heading, Python definition or test function: path, selector (`path#Heading` or `path::Name`), text, token count.
- `embeddings` exists only when `index.embed` is set. The build writes each chunk text to a temporary file under `<state_dir>` and runs the embed argv through the `ProcessExec` seam with that file as `stdin_path`. The command prints a JSON array of numbers. A nonzero exit, unparsable JSON, a non-numeric element or a vector whose length differs from the first vector is one finding; it stops the `embeddings` table (no partial table is kept) and makes `clutch index build` exit 1. Other tables are still written.
- The `IndexCreator` seam in `clutch/index.py` is a callable `(connection, kind) -> list[str]` where `kind` is `'vss'` or `'fts'`. It loads that kind's extension and then runs that kind's index DDL on the connection, returning findings (empty list on success). For `'vss'` the DDL is `SET hnsw_enable_experimental_persistence = true` followed by `CREATE INDEX ... USING HNSW` over `embeddings`; for `'fts'` it is `PRAGMA create_fts_index` over `chunks.text`. All index DDL and all `INSTALL`/`LOAD` go only through this seam; the build itself issues none. Unit tests replace the creator with a recording fake, so criteria 3, 5 and 10 test the same seam.
- The HNSW index is persisted (the experimental flag above), so it survives reopening. With `embed` unset, the `'fts'` index over `chunks.text` is built instead.
- `touches` comes from first-parent commits on main carrying a `clutch-ticket` trailer plus their changed paths. `calls` comes from the evidence store records read through `clutch/evidence/store.py`.
- Incremental: the change-detection key is the file's content digest (the meta block's SHA-256 for annotated files, a SHA-256 of the content otherwise), which needs one read of each file per build. A file whose digest equals the stored `files.hash` is skipped: none of its rows in any table is rewritten or re-chunked. Rows of files no longer present are removed.
- The verb's creator runs `INSTALL` then `LOAD`. The merge-path creator only runs `LOAD` with `SET autoinstall_known_extensions = false`; if an extension is not installed it records a finding and skips that index, so no merge ever touches the network.
- Locking: `clutch index build` takes no writer lock and is safe while `serve` runs (host-running column value `Yes`). DuckDB allows one writing process per file, so if the verb and the merge hook open `<state_dir>/index.duckdb` at once, the failed open becomes one finding: the verb exits 1 and the merge hook swallows it.
- Merge path: the hook is called from each `write_squash` call site in `clutch/mergequeue.py` only after the `to: merged` state transition is journaled, and it never changes the returned Admission. The merge-path build never runs the embed command and never touches the `embeddings` table; it refreshes `files`, `chunks`, `touches`, `calls` and the full-text index for the changed paths only. Vectors are refreshed by the verb.
- The `index` config block has one key, `embed` (argv list of strings, default unset). An explicit `embed: null` stays refused by the existing global null rule in `clutch/config.py`. The plan's `implement_hint` key is not added here.

## Boundary contract
### Project index store
- disposition: create
- owner: clutch/index.py
- consumers: the `clutch index build` verb and the merge-path hook in clutch/merge.py
- observable change: `<state_dir>/index.duckdb` is written with the five tables above; build findings are returned as a list and printed by the verb; the `IndexCreator` callable `(connection, kind 'vss'|'fts') -> list[str]` owns extension loading and all index DDL
- compatibility: new file under gitignored `state_dir`; nothing reads it, no gate or dispatch depends on it; deleting it is always safe
- acceptance: a build over a fake filesystem, fake git reader, fake exec and recording creator yields the expected rows; a second build with unchanged digests writes no rows for those files; embed failures produce one finding and no `embeddings` table; a failed open of the database file yields one finding
- tests: tests/unit/test_index_build.py and tests/integration/test_index_extensions.py
- post-merge source of truth: clutch/index.py
- closest existing: clutch/journalcache.py (DuckDB projection of the journal) and clutch/meta.py (block reader); journalcache folds journal events, not files, chunks or vectors, and meta.py only parses one file's block
- earning reason: two production consumers (verb and merge hook) and an external-effect fake for the embed process and extension creator

### Index config
- disposition: extend
- owner: clutch/config.py
- consumers: clutch/index.py, `clutch config` verbs, clutch/docs/host-contract.md
- observable change: optional `index:` block with `embed: [argv]`; omitted `embed` means no vectors
- compatibility: configs without the block load unchanged; `embed: "x"` and `embed: null` are refused (null by the existing global rule)
- acceptance: see criterion on config validation
- tests: tests/unit/test_index_config.py
- post-merge source of truth: clutch/config.py

### Ticket-touch reader
- disposition: extend
- owner: clutch/git.py
- consumers: clutch/index.py
- observable change: a new `Git` method returning (ticket stem, commit, changed paths) from first-parent commits with a `clutch-ticket` trailer
- compatibility: existing methods and their output formats unchanged
- acceptance: parsing of canned `git log` output via a fake runner
- tests: tests/unit/test_git_ticket_touches.py
- post-merge source of truth: clutch/git.py

### Merge-path index hook
- disposition: extend
- owner: clutch/merge.py
- consumers: each `write_squash` call site in clutch/mergequeue.py
- observable change: after the `to: merged` transition is journaled, the changed paths are re-indexed with the load-only creator and no embed run; any failure is swallowed
- compatibility: merge outcome, returned Admission, journaled transition and commit content unchanged
- acceptance: hook runs after the merged transition, issues no INSTALL statement, runs no embed, and cannot fail a merge
- tests: tests/unit/test_index_merge_hook.py
- post-merge source of truth: clutch/merge.py

### Index verb
- disposition: create
- owner: clutch/__main__.py
- consumers: operators and hosts
- observable change: new command group `index` with subcommand `build`; no writer lock; exit 0 with no findings, exit 1 with any finding (including a concurrent open of the database file)
- compatibility: no existing command changes
- acceptance: handler exit codes and help/doc parity
- tests: tests/unit/test_index_verb.py, tests/integration/test_index_cli.py
- post-merge source of truth: clutch/__main__.py
- closest existing: the `meta` group in clutch/__main__.py (verbs over annotated files); it reads and writes blocks and has no cache or search store, so the index verbs need their own group
- earning reason: rule "Command groups" requires every command in a fitting group, and no existing group owns the derived cache

## Scope in / Scope out
Scope in:
- New `clutch/index.py` with the build, the `IndexCreator` seam, and the merge-path entry that takes the load-only creator. All process, filesystem and clock use goes through the existing seams.
- `clutch/config.py`: add the `index` block with `embed`. `clutch/docs/host-contract.md`: add the `index` block to the config inventory.
- `clutch/git.py`: add the ticket-touch reader. A new `tests/unit/test_git_ticket_touches.py` runs it against a fake runner returning canned `git log` output, so the lines run offline.
- `clutch/merge.py`: define the merge-path hook function, wrapped so no exception escapes; it builds its own load-only creator. `clutch/mergequeue.py`: call it at each `write_squash` call site (`MergeQueue._finish`, and the inline `not receipt and not tree_check` branch of `MergeQueue._admit`) only after the `to: merged` transition is journaled, ignoring its result. `clutch/stages.py` and `StageContext` are not changed.
- `clutch/__main__.py`: add group `index` with `build` (no writer lock), with description, subcommand list and examples through `_command`. `tests/unit/test_index_verb.py` calls the handler with the build replaced by a fake and checks exit 0 versus 1.
- Docs: add the `index` rows to the verb table in `clutch/docs/host-running.md` (works while serve runs: Yes), to the README command list in `README.md`, and to the verb table in section 2 of `docs/how-clutch-works.md`. Add the "Project index" section to `docs/how-clutch-works.md` as a new top-level numbered section placed after the last existing numbered section and numbered one higher, so no existing heading number or anchor changes (`clutch/help.py` links and `tests/unit/test_help.py` pin those anchors). `tests/unit/test_host_running.py` and `tests/unit/test_readme.py` check these rows against the parser; they are not edited.
- `tests/integration/test_host_contract.py` is edited only if its config inventory lists top-level blocks and the new block forces a change there.
- New tests: `tests/unit/test_index_build.py`, `tests/unit/test_index_config.py`, `tests/unit/test_index_verb.py`, `tests/unit/test_index_merge_hook.py`, `tests/unit/test_git_ticket_touches.py`, `tests/integration/test_index_cli.py`, `tests/integration/test_index_extensions.py` (loads `vss` and `fts` for real; skips with the named reason "vss/fts extensions unavailable offline" when they cannot be installed).

Scope out: no search or suggestion verb, no change to Author or Implement prompts, no `meta` verb changes, no `implement_hint`, no embedding of call transcripts, no edit to `tests/unit/test_main_verb_groups.py` or `tests/integration/test_main_verb_groups.py` (neither holds a group set), no edit to the existing hot merge test files.

## Scope fence
- clutch/index.py
- clutch/config.py
- clutch/git.py
- clutch/merge.py
- clutch/mergequeue.py
- clutch/__main__.py
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- README.md
- docs/how-clutch-works.md
- tests/integration/test_host_contract.py
- tests/unit/test_index_build.py
- tests/unit/test_index_config.py
- tests/unit/test_index_verb.py
- tests/unit/test_index_merge_hook.py
- tests/unit/test_git_ticket_touches.py
- tests/integration/test_index_cli.py
- tests/integration/test_index_extensions.py

## Acceptance criteria
1. `tests/unit/test_index_build.py` builds over a fake filesystem and fake git reader and asserts the `files`, `chunks`, `touches` and `calls` rows, including selectors `path#Heading` and `path::Name`; a build that leaves `chunks` empty fails the test.
2. `tests/unit/test_index_build.py` asserts the build opens `<state_dir>/index.duckdb` through `duckdb.connect` and that the file exists afterward; a build that writes no file or any other path fails. It also asserts that a connect that raises on open yields exactly one finding and no exception, not a crash.
3. With a fake embed exec returning a 3-element JSON vector per chunk and a recording creator `(connection, kind)`, `tests/unit/test_index_build.py` asserts an `embeddings` row per chunk, that the embed input was passed as `stdin_path` under `<state_dir>`, and that the creator was called with kind `'vss'` and recorded the HNSW `CREATE INDEX` and the persistence `SET`; a build that issues index DDL outside the creator fails it.
4. `tests/unit/test_index_build.py` asserts that a nonzero embed exit, non-JSON output, and a wrong-length vector each yield exactly one finding, no `embeddings` table, and the other tables still present; a partial `embeddings` table fails it.
5. `tests/unit/test_index_build.py` asserts that with `embed` unset no `embeddings` table exists and the recording creator was called with kind `'fts'` only, never `'vss'`.
6. `tests/unit/test_index_build.py` asserts that a second build over unchanged files reads each file once to compute its digest but issues no INSERT, UPDATE or DELETE statement for those files' rows in any table (counted on a recording connection) and does not re-chunk them, and that a file removed from the tree has its rows deleted; a full rebuild fails the statement-count assertion.
7. `tests/unit/test_index_config.py` asserts `index` accepts `embed: ["x"]` and an omitted `embed` (unset), rejects `embed: "x"` and `embed: null`, and that a config without the block loads; accepting `embed: null` fails it.
8. `tests/unit/test_git_ticket_touches.py` feeds canned `git log` output through a fake runner and asserts stem, commit and changed paths, and that a commit without a `clutch-ticket` trailer is omitted.
9. `tests/unit/test_index_verb.py` calls the `index build` handler through `entry.main` with the build replaced by a fake: no findings returns exit 0, one finding returns exit 1, and the handler acquires no writer lock.
10. `tests/unit/test_index_merge_hook.py` runs the merge-path build with a recording connection and asserts no statement starting with `INSTALL` is issued, that `autoinstall_known_extensions` is set false, that a missing extension becomes a finding, that no embed exec call is made, and that an exception raised inside the build does not propagate out of the hook.
11. `tests/unit/test_index_merge_hook.py` drives both `write_squash` call sites in `clutch/mergequeue.py`: `MergeQueue._finish`, and the inline branch of `MergeQueue._admit(..., receipt=False, tree_check=False)`. It monkeypatches `merge.write_squash`, `merge.retire` and the hook to ordered event recorders, using the pattern of `tests/unit/test_merge_admission_params.py::rig` copied into the new file, not edited. For each path it asserts the hook runs after the `to: merged` transition is journaled and that the returned Admission equals the one returned when the hook is replaced by a no-op; a hook that runs before the journal append, or a call site that never calls the hook, fails it.
12. `tests/integration/test_index_extensions.py` loads `vss` and `fts` for real and builds both indexes, or skips with the reason "vss/fts extensions unavailable offline"; `tests/integration/test_index_cli.py` runs `uv run clutch index build` in a temp repo with `embed` unset and asserts `index.duckdb` is created.
13. `./dev.py test tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_main_help.py` pass with the `index` rows and help added; a missing doc row or missing group description fails them.

## Verification
```
./dev.py test tests/unit/test_index_build.py tests/unit/test_index_config.py tests/unit/test_index_verb.py tests/unit/test_index_merge_hook.py tests/unit/test_git_ticket_touches.py tests/integration/test_index_cli.py tests/integration/test_index_extensions.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_main_help.py tests/integration/test_host_contract.py tests/integration/test_merge.py tests/integration/test_mergequeue.py
```

## Definition of rejected
The branch is thrown away if any code opens a SQLite file, if a merge-path build runs `INSTALL` or can change or prevent the merge outcome or its journaled transition, if any gate, dispatch or other code reads `index.duckdb`, if `clutch/stages.py` or a hot test file is edited, if any existing heading number in `docs/how-clutch-works.md` changes, or if `clutch index build` is added without its help, docs and group entry.

## Time budget
- expected: 30m
- stuck: 60m
