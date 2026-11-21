---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- index-build-r2

## Context
- docs/annotations-index-plan.md#5. The index
- clutch/index.py::build
- clutch/index.py::IndexCreator
- clutch/index.py::default_creator
- clutch/merge.py::write_squash
- clutch/mergequeue.py::MergeQueue._finish
- clutch/enginelog.py
- clutch/providers.py::child_env
- clutch/evidence/store.py::EvidenceStore
- clutch/config.py::Index
- tests/unit/test_merge_admission_params.py
- test-gate.toml

## Goal / Why
Roadmap row 181, the merge hook of ticket 4 of `docs/annotations-index-plan.md` ("`index build` runs at the end of a merge"), split from the rejected `index-build-r1` (its diagnosis names this as split 4). After this ticket, every squash admission refreshes `<state_dir>/index.duckdb` when that file already exists, so the index a ticket author queries is current with main. Without it the index goes stale after each merge until someone runs the verb (`index-build-verb`, row 182, not this ticket).

Decisions this ticket fixes:
- New `async def refresh_index(ctx) -> None` in `clutch/merge.py`. It is called exactly once, from `write_squash`, as a new statement placed after the `ctx.driver.journal.append(EventType.STATE_TRANSITION, body, ticket=stem)` guard that records `to: merged` and before the `return Admission(...)`. Both `write_squash` call sites in `clutch/mergequeue.py` (`MergeQueue._finish` and the inline branch of `MergeQueue._admit`, which `merge.merge` reaches) call `merge.write_squash`, so both reach the hook through that one call. The roadmap row says "at both sites"; one call inside the shared sole merged terminal covers both and cannot drift, which is the simpler form, and is why `clutch/mergequeue.py` is not fenced.
- Outcomes, a closed set; the hook logs one engine-log event `index_refresh` with field `outcome` set to exactly one of these names, except `skipped_no_index`, which logs nothing:
  - `skipped_no_index`: the file `ctx.config.state_dir / "index.duckdb"` does not exist (tested with `ctx.fs.size(path)` raising `FileNotFoundError`; the `FileSystem` seam has no `exists`). The hook then does nothing observable: no build call, no file created, no engine-log line, no journal event, no process. A host that never ran the index build has no such file, so a host with no index setup is this outcome.
  - `built`: the file exists and `index.build` returned `[]`. Logs `index_refresh` with `outcome="built"`.
  - `built_with_findings`: the file exists and `index.build` returned a non-empty list. Logs `index_refresh` with `outcome="built_with_findings"` and `findings=<that list>`.
  - `failed`: any `Exception` raised anywhere in the hook body (attribute errors on a malformed ctx, a `FileNotFoundError` other than from the size probe, `duckdb.Error`, an `OSError`, anything `build` raises). The whole hook body is inside one `try`; the `except Exception` handler logs `index_refresh` with `outcome="failed"`, `error=<exception class name>` and `detail=<str(exception)>`, and that logging is itself inside a second `try ... except Exception: pass`, so a broken log never reaches the merge. `asyncio.CancelledError` and any other `BaseException` that is not an `Exception` are not caught: cancelling the merge is not an index failure.
  The hook returns `None` in every outcome and never raises an `Exception`; `write_squash` returns the same `Admission` and appends the same journal events with or without the hook (its only append is the `to: merged` transition, already done when the hook runs).
- The hook calls `index.build(ctx.config, ctx.repo, fs=ctx.fs, git=ctx.git, exec_=ctx.exec_, env=child_env(ctx.env, ctx.config), store=EvidenceStore(ctx.config.state_dir, ctx.fs, ctx.fs.read_bytes, ctx.fs.size, ctx.driver.redactor.scrub), creator=MERGE_CREATOR)`. The config is passed unchanged, so a host's `index.embed` is honored and the incremental, digest-keyed build embeds only chunks lacking vectors. The build is awaited inside the merge, so a slow embed command delays the merge by at most its own 60 s per-chunk timeout and never fails it. The build is whole-tree and digest-keyed, so the hook takes no per-path argument: an unchanged file costs one read and one hash.
- `MERGE_CREATOR` is one object in `clutch/merge.py` with the `IndexCreator` methods. `load(connection, kind)` runs only `LOAD vss` or `LOAD fts` (never `INSTALL`: the merge path must not reach the network) and on `duckdb.Error` returns `["<kind> unavailable: <error>"]`, else `[]`. `create(connection, kind)` returns `[]` and issues no statement (no index DDL on the merge path). `load` is still needed so a persisted HNSW index meets a connection with `vss` loaded while rows are deleted and inserted. The full-text and HNSW indexes are therefore only (re)created by the verb; a merge leaves them as they were, and a stale full-text index is the accepted cost.
- The hook reads and writes nothing in git and neither reads nor writes the journal; it touches only `index.duckdb` (through `build`) and the engine log (through `engine_log(ctx.config, ctx.driver.redactor, ctx.driver.clock).event(...)`).

## Boundary contract
### Merge-path index refresh
- disposition: create
- owner: clutch/merge.py
- consumers: `merge.write_squash`, the sole merged terminal, reached by `MergeQueue._finish` and the inline branch of `MergeQueue._admit` in `clutch/mergequeue.py`
- observable change: after each squash admission whose `index.duckdb` exists, the file is refreshed and one `index_refresh` engine-log line records `built`, `built_with_findings` or `failed`; with no file nothing is observable; the `StageResult`, `Admission` and journal are identical
- compatibility: `write_squash` signature, return value, journal events and every refusal path are unchanged; the hook runs only after the `to: merged` transition and swallows every `Exception`; no existing test asserts on the engine log or on `index.duckdb`
- acceptance: criteria 1-6
- tests: tests/unit/test_merge_index_hook.py, tests/integration/test_merge_index_hook_sites.py
- post-merge source of truth: clutch/merge.py
- closest existing: `clutch/index.py::default_creator` (loads and creates with `INSTALL`) and `merge.retire` (the existing step after the merged terminal)
- earning reason: the merge path needs a creator that never runs `INSTALL` or index DDL, which `default_creator` cannot be told to skip; the hook is the row's deliverable with one production consumer, `write_squash`, and an external-effect seam (`index.build`) that tests replace

### Index build
- disposition: reuse
- owner: clutch/index.py
- consumers: `merge.refresh_index` calls `index.build` and passes an `IndexCreator`
- observable change: none; `build` is called with its merged signature and returns findings
- compatibility: `build(config, root, *, fs, git, exec_, env, store, creator, connect=duckdb.connect)` is not edited
- acceptance: criterion 1 asserts the call arguments
- tests: tests/unit/test_merge_index_hook.py
- post-merge source of truth: clutch/index.py

### Engine log
- disposition: reuse
- owner: clutch/enginelog.py
- consumers: `merge.refresh_index` writes `index_refresh` events through `engine_log(...).event`
- observable change: one new event name `index_refresh` in the engine log, which nothing reads for a gate or dispatch decision
- compatibility: `engine_log` and `EngineLog.event` are not edited
- acceptance: criteria 1-3 read the log line
- tests: tests/unit/test_merge_index_hook.py
- post-merge source of truth: clutch/enginelog.py

## Scope in / Scope out
Scope in:
- `clutch/merge.py`: add the imports `duckdb`, `from clutch import index`, `from clutch.enginelog import engine_log`, `from clutch.evidence.store import EvidenceStore` and `from clutch.providers import child_env` (if `clutch.providers` cannot be imported at module level without a cycle, import `child_env` inside `refresh_index`), the `MERGE_CREATOR` object, `refresh_index`, and the one call from `write_squash`. Nothing else in the file changes.
- Tests, all new files, each starting with the `clutch.meta/1.0` block: run `uv run clutch meta refresh` in the worktree, fill a NON-EMPTY one-line `# purpose:` (`# purpose: merge-path index refresh outcomes` in `tests/unit/test_merge_index_hook.py`, `# purpose: write_squash is the single index hook call site` in `tests/integration/test_merge_index_hook_sites.py`), then rerun `uv run clutch meta refresh` so the hash matches; `uv run clutch meta check` must be clean.
  - `tests/unit/test_merge_index_hook.py` (unit; runs every new line of `clutch/merge.py`, which has a coverage floor in `test-gate.toml`): `refresh_index` with `tmp_path` as `state_dir`, a `SimpleNamespace` ctx and `merge.index.build` replaced by a recording async fake (monkeypatch) for the outcome tests; one test running the real `index.build` through `LocalFileSystem` over a `tmp_path` repo with a fake git and fake store; `MERGE_CREATOR` driven with a recording fake connection; and `write_squash` driven with a fake ctx (`driver.effects.run` awaiting its callable, a recording `driver.journal`, a fake `git` with `diff_names`, `merge_squash`, `rev_parse`, and a `human`-source ticket so `retro_bridge` is `None`).
  - `tests/integration/test_merge_index_hook_sites.py` (integration; reads repo source through a `Path(__file__)` anchor): the AST call-site checks of criterion 5.
- Documentation: none. The user-facing index docs are delivered with the verb in `index-build-verb`; this ticket adds no command, flag or config key.

Scope out: the `clutch index build` verb, its help and docs (`index-build-verb`, row 182); any edit to `clutch/index.py`, `clutch/mergequeue.py`, `clutch/config.py`, `clutch/git.py`, `clutch/enginelog.py`, `clutch/providers.py`, `clutch/evidence/store.py`, `clutch/__main__.py`; any hot test file (`tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_drain.py`, `tests/integration/test_daemon_composition.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`); creating `index.duckdb` when it does not exist (the verb's job); a per-path argument to the build. Existing `write_squash` tests need no edit: `tests/integration/test_merge.py` builds its ctx from a real config with a `state_dir` and no `index.duckdb`, so the hook ends in `skipped_no_index`, and `tests/unit/test_merge_admission_params.py` replaces `write_squash` with an `AsyncMock`, so the hook never runs there. `spools-capture-keys` (running) fences `clutch/evidence/store.py`, `clutch/__main__.py`, `tests/unit/test_evidence_*.py` and `tests/integration/test_evidence_captures_verb.py`; this ticket only reads `EvidenceStore` and fences none of them, so merge order changes nothing.

## Scope fence
- clutch/merge.py
- tests/unit/test_merge_index_hook.py
- tests/integration/test_merge_index_hook_sites.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_merge_index_hook.py` asserts that with the index file present and a fake `build` returning `[]`, `refresh_index` calls `build` exactly once with `config` equal to `ctx.config` (not a copy), `root` equal to `ctx.repo`, `creator` the `MERGE_CREATOR` object, `fs`, `git` and `exec_` the ctx's, `env` equal to `child_env(ctx.env, ctx.config)` (a configured secret name is absent), and `store` an `EvidenceStore`, and that the engine log gains exactly one line with `event` `index_refresh` and `outcome` `built`; a hook that calls `build` twice, passes a copy of the config, or logs another outcome fails it.
2. `./dev.py test tests/unit/test_merge_index_hook.py` asserts `skipped_no_index`: with no `index.duckdb` under `state_dir` the fake `build` is never called, the engine log file does not exist afterward, `index.duckdb` is not created, and `refresh_index` returns `None`; a hook that calls `build`, creates the file or writes a log line fails it.
3. `./dev.py test tests/unit/test_merge_index_hook.py` asserts `built_with_findings` (fake `build` returns `["git_failed: x"]`: one log line with `outcome` `built_with_findings` and `findings` `["git_failed: x"]`, no raise) and `failed` for each of `RuntimeError`, `duckdb.Error` and `OSError` raised from `build`, and for a ctx whose `config` has no `state_dir`; each logs one line with `outcome` `failed` and `error` the class name, and none raises; a fake `build` raising `asyncio.CancelledError` propagates out of `refresh_index`; a hook that raises on any `Exception`, that swallows `CancelledError`, or whose own log failure (an unwritable engine log path) raises fails it.
4. `./dev.py test tests/unit/test_merge_index_hook.py` asserts `MERGE_CREATOR.load(conn, "vss")` and `load(conn, "fts")` on a recording fake connection each issue exactly one statement, `LOAD vss` and `LOAD fts`, and no `INSTALL`; that a connection raising `duckdb.Error` yields `["vss unavailable: <error>"]` (resp. `fts`), not `[]`; that `create(conn, kind)` returns `[]` and issues no statement for both kinds; a creator that installs or creates an index fails it.
5. `./dev.py test tests/unit/test_merge_index_hook.py` drives `write_squash` with a fake ctx and asserts: the recorded call order is the journal append of `to: merged`, then the hook (so the hook never runs before the merged transition); the returned `Admission` and the journal events are equal whether the hook finds no file or `build` raises `RuntimeError`; a `write_squash` that lets the `RuntimeError` out, or calls the hook before the append, fails it. `./dev.py test tests/integration/test_merge_index_hook_sites.py` parses `clutch/merge.py` and `clutch/mergequeue.py` with `ast` and asserts: `refresh_index` is called exactly once in `clutch/merge.py` and that call is a statement in `write_squash`; `clutch/mergequeue.py` contains no reference to `refresh_index` or `index`; it contains exactly two `merge.write_squash` calls (in `MergeQueue._finish` and `MergeQueue._admit`); a second call site, or a hook call added in `mergequeue.py`, fails it.
6. `./dev.py test tests/unit/test_merge_index_hook.py` also runs the real `index.build` through `refresh_index` with `LocalFileSystem` over a `tmp_path` repo, an `index.duckdb` created with `duckdb.connect(path).close()`, `MERGE_CREATOR.load` wrapped by a recorder that returns `[]` (so the result does not depend on whether the `vss`/`fts` extensions are installed on the machine) while `duckdb.connect` and all table writes stay real, a fake `git` (`ls_files` returning one `.md` file, `ticket_touches` returning `[]`) and a fake store (`call_keys` returning `[]`), and asserts afterward that a `files` row for that path exists (read with `duckdb.connect`), the recorder saw `load` for `fts` and no `INSTALL` statement was issued (statements counted on a recording `connect` passed through a wrapper around `index.build`), and the log line says `built`; a hook that builds nothing fails it.
7. `./dev.py test tests/unit/test_merge_admission_params.py tests/integration/test_merge.py` still pass unedited, showing the hook's `skipped_no_index` outcome (real `state_dir`, no `index.duckdb`) and its absence under the mocked `write_squash` change no existing merge test.

## Verification
```
./dev.py test tests/unit/test_merge_index_hook.py tests/integration/test_merge_index_hook_sites.py tests/unit/test_merge_admission_params.py tests/integration/test_merge.py
uv run clutch meta check
uv run ruff format --check .
```

## Definition of rejected
The branch is thrown away if any `Exception` from the index build can escape `write_squash`; if the hook runs before the `to: merged` journal append; if `INSTALL`, index DDL or any network access happens on the merge path; if the hook creates `index.duckdb`; if code opens a SQLite file; if a second call site of the hook exists or `clutch/mergequeue.py` is edited; if the journal, the `Admission` or any `write_squash` refusal path changes; or if a file outside the Scope fence is edited (in particular `clutch/index.py`, `clutch/__main__.py`, `clutch/evidence/store.py` and every doc).

## Time budget
- expected: 20m
- stuck: 40m
