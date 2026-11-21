---
state: draft
source: human
priority: P3
kind: feature
---

## Depends on
- context-suggest

## Context
- docs/annotations-index-plan.md#6. Consumers
- clutch/training.py::render
- clutch/training.py::_safe
- clutch/training.py::_identity
- clutch/index.py::neighbors
- clutch/__main__.py::_command
- tests/unit/test_training_export.py

## Goal / Why
Roadmap row 74 (now `index-consumers-training-join`), ticket 6 of `docs/annotations-index-plan.md`, split in three because its three consumers are separate boundaries: this ticket is the training export join; `index-consumers-doc-draft` (`doc draft --from <topic>`) and `index-consumers-implement-hint` (`index.implement_hint` in the Implement prompt, the hot path of every ticket, so last) are new rows 196 and 197 that this ticket adds to `docs/roadmap.md`. Plan section 6 says the export "joins `files.purpose` and `touches` onto its records so a tuned model sees what each file is for"; the `calls` table is not used, because the plan's join names only `files` and `touches` and no record field needs a call row.

After this ticket `clutch training export` adds, to each `implement` record whose diff changes a path the merged index knows, a `file_purposes` list saying what each changed file is for and how often other tickets changed it. A model tuned on `sft.jsonl` then sees purpose text with the diff it learns to write. Today a record carries the prompt and the diff only.

Source. `<state_dir>/index.duckdb` (`config.state_dir / "index.duckdb"`), opened read-only, tables `files(path, kind, purpose, relates, owner, hash, size)` and `touches(ticket, commit_sha, path)` as `clutch/index.py::build` creates them. No new CLI option, no config key, no new file; the index is a derived cache and the export never builds it.

Inputs, validated by rule (every one):
- `database`: the path above. Missing file (`fs.size` raises `FileNotFoundError`), any other `OSError`, a connection error (a writer holding the lock), a query error (`duckdb.Error`, such as a missing table), all give an empty join. Nothing raises, nothing is printed, the export result, its counts line and its exit code are what they are today.
- `files.path`: a non-NULL string; a row with NULL path is ignored. `files.purpose`: a string or NULL; NULL becomes `""`.
- `touches.ticket`, `touches.path`: non-NULL strings; a row with either NULL is ignored.
- A record's changed paths: each line of the record's assistant diff that starts with `diff --git ` is split with `shlex.split` (as `_safe` does); a line that does not split into exactly `["diff", "--git", "a/<p>", "b/<q>"]` is ignored; the path is `<q>`. Paths are de-duplicated.
- The record's `stem`: the ticket the record is for; its own touches are not counted.

Field `file_purposes` (implement records only; preference, review, diagnosis, ticket and conflict records are unchanged): a JSON list, one object per changed path that has a `files` row, sorted ascending by `path` (plain string order), each object `{"path": <str>, "purpose": <str>, "touches": <int>}`. `touches` is the number of distinct `touches.ticket` values for that path other than the record's `stem`, 0 when none. A changed path with no `files` row is omitted. Empty case: when the join is empty (no index, unreadable index, no changed path found in `files`) the key is absent from the record, so every record is byte-identical to today's. The key is added to the record before `_safe` runs, so redaction and the exclude globs cover purpose text; a record whose purpose text fails the scrub is dropped and counted, as any record is.

Worked example. Record stem `t0`, diff lines `diff --git a/clutch/b.py b/clutch/b.py`, `diff --git a/clutch/a.py b/clutch/a.py`, `diff --git a/docs/x.md b/docs/x.md`, `diff --git a/new.py b/new.py`. `files`: `clutch/a.py` purpose `parse a`, `clutch/b.py` purpose NULL, `docs/x.md` purpose `guide`; no row for `new.py`. `touches`: `clutch/a.py` by `t1`, `t2`, `t0`; `clutch/b.py` by `t1`; none for `docs/x.md`. Then `file_purposes` is `[{"path": "clutch/a.py", "purpose": "parse a", "touches": 2}, {"path": "clutch/b.py", "purpose": "", "touches": 1}, {"path": "docs/x.md", "purpose": "guide", "touches": 0}]`; `new.py` is absent. With an empty index the key is absent.

Outcomes (the export has no new exit code): `joined` (at least one path matched; field present), `empty` (index readable, nothing matched; field absent), `no_index` and `index_unreadable` (field absent). All four exit 0 as today; refusals are only the existing ones.

Docs. The `training export` row and help text say implement records carry `file_purposes` when the index is built; `clutch/docs/host-training.md` Export section says how to get it (`clutch index build` first) and that a stale or missing index only omits the field.

## Boundary contract
### Training export record
- disposition: extend
- owner: clutch/training.py
- consumers: `clutch training export` (`clutch/__main__.py::handle_training`) and the people and tools reading `sft.jsonl`
- observable change: `render` takes a keyword-only `index` mapping (default `None`) and adds `file_purposes` to implement records as defined above; a new `index_files(database, size, connect=duckdb.connect)` returns `{path: (purpose, frozenset(tickets))}` or `{}` on any failure; `handle_training` passes it for `export` only
- compatibility: with `index=None` or `{}` every record, count and file is unchanged; the `eval` verb and its `render(... only=...)` call pass no index; no record key is renamed or removed
- acceptance: criteria 1-6
- tests: tests/unit/test_training_index_join.py
- post-merge source of truth: clutch/training.py and the Export section of clutch/docs/host-training.md

## Scope in / Scope out
Scope in:
- `clutch/training.py`: add `index_files` (opens read-only, `duckdb` import added) and the `index` keyword to `render`; a small private helper builds `file_purposes` from the diff and is called at the two places that build an implement record (the merged-diff record and the per-attempt record). Add nothing else.
- `clutch/__main__.py`: in `handle_training`, the export branch builds `index` with `index_files(config.state_dir / "index.duckdb", checkout.fs.size)` and passes `index=`; update the `training export` `_command` `does` and `reads` strings (reads gains the index). The eval branch is untouched.
- Docs, each only the part the change makes false: the `training export` row in `clutch/docs/host-running.md` and in `docs/how-clutch-works.md` section 2 (add that implement records carry `file_purposes` when the index exists), and the Export paragraph of `clutch/docs/host-training.md`. The top-level readme does not name the verb and is not touched.
- New test file `tests/unit/test_training_index_join.py`. The implementer creates its header with `uv run clutch meta refresh tests/unit/test_training_index_join.py` and then edits only the `# purpose:` line to a non-empty one-line purpose; it never hand-writes the header. Then run `uv run clutch meta refresh` on each edited `.md` file listed above.
Scope out: `clutch/index.py` and the tables (unchanged); `doc draft --from` and `index.implement_hint` (the rows above); every prompt spec (no spec version changes); the `calls` table; preference and other record kinds; the counts report line; `clutch/config.py` (no key). The existing training unit tests stay unchanged: they pass no index, so their assertions still hold.

## Scope fence
- clutch/training.py
- clutch/__main__.py
- clutch/docs/host-running.md
- clutch/docs/host-training.md
- docs/how-clutch-works.md
- tests/unit/test_training_index_join.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_training_index_join.py` runs `render` with a tmp_path DuckDB index holding the worked example's rows and asserts the implement record's `file_purposes` equals the worked example list exactly, sorted by path, with `touches` 2, 1 and 0 and `new.py` absent, not `touches` 3 for `clutch/a.py`.
2. `./dev.py test tests/unit/test_training_index_join.py` asserts that with `index=None`, with `{}`, and with an index containing no changed path, the implement record has no `file_purposes` key and equals the record produced without the keyword, not an empty list.
3. `./dev.py test tests/unit/test_training_index_join.py` asserts `index_files` returns `{}`, without raising, for a missing file, a directory in place of the file, a database lacking `touches`, and a connect function raising `duckdb.IOException`, not an exception.
4. `./dev.py test tests/unit/test_training_index_join.py` asserts a preference record and a review record built from the same stems carry no `file_purposes` key, and that a purpose containing a configured secret drops the record and counts it in `dropped`, not writes the secret.
5. `./dev.py test tests/unit/test_training_index_join.py` runs `entry.main(["training", "export", "--out", ...])` as `test_training_export.py::test_handler_success` does (monkeypatched `load_config` and `Git`), with the worked-example index at `<config.state_dir>/index.duckdb` under tmp_path and `training.render` monkeypatched to record its keyword arguments and return empty files and zero counts; it asserts `render` received `index` equal to the loaded mapping for `clutch/a.py`, and that with no index file `render` received `{}` and the exit code is 0, not `index=None` and not a refusal.
6. `./dev.py test tests/unit/test_training_export.py tests/unit/test_training_trajectory.py tests/unit/test_training_export_kinds.py tests/unit/test_main_help.py` passes unchanged, so no existing record or help assertion flipped.

## Verification
```
./dev.py test tests/unit/test_training_index_join.py tests/unit/test_training_export.py tests/unit/test_training_trajectory.py tests/unit/test_training_export_kinds.py tests/unit/test_main_help.py
```

## Definition of rejected
- A missing, locked, stale or unreadable index changes the export's exit code, counts line, stdout, or any record other than adding `file_purposes`.
- `file_purposes` appears on a non-implement record, or as an empty list, or is built by a path other than a read-only DuckDB open.
- Any file outside the fence changes, including prompt specs, `clutch/index.py` or `clutch/config.py`, or an edit to `doc draft`, Implement rendering or `index.implement_hint`.
- SQLite is opened, or the export writes to the index.

## Time budget
- expected: 25m
- stuck: 50m
