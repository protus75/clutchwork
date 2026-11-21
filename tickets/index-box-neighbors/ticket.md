---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- index-build-r2

## Context
- docs/annotations-index-plan.md#5. The index
- clutch/index.py
- clutch/box.py::Message
- clutch/box.py::Box.messages
- clutch/box.py::DecisionRecord
- clutch/box.py::parse_record
- clutch/roadmap.py::Row
- clutch/roadmap.py::parse
- tests/unit/test_index_build.py

## Goal / Why
Roadmap row 110, first of three slices: the index half. Row 110 also asks that Triage and Author receive the nearest messages, rows, open tickets and decision records as data; that half is later tickets, not this one (see Scope out). After this ticket `index.build(...)` (signature unchanged) also writes rows for Suggestion Box messages, roadmap rows and decision records into the existing `files` and `chunks` tables, so the existing embed step embeds them with the host `index.embed` command and the existing full-text step covers them. Without these rows a recurring report (box-000457, box-000529, box-000531, box-000574 were one flaky test) or a duplicate of a roadmap row (box-000582 duplicated row 94) can only be matched by the exact summary `Box.enqueue` compares.

Decisions this ticket fixes. No new table, column, config key, signature or CLI verb:
- Roadmap rows: when the tracked file `docs/roadmap.md` is (re)processed, `roadmap.parse(text)` runs on its text and each returned row (struck rows included; `parse` already strips `~~`) adds one chunk to that file's existing heading chunks: `path` `docs/roadmap.md`, `selector` `docs/roadmap.md#row <number>`, `text` `<stem>: <content>`, `tokens` the whitespace word count of `text`. Worked example: row 110 gives selector `docs/roadmap.md#row 110`, text `index-box-neighbors: Owner request (2026-11-17): ...`. Row chunks follow the file's digest like its heading chunks and are embedded with them. If `parse` raises `Refusal` (no master table, duplicate number or stem) or `ValueError` (for example a row number such as `²`, which `str.isdigit()` accepts and `int()` rejects), or the file's bytes are not UTF-8 (`UnicodeDecodeError`; this branch decodes the file itself, separately from `_extract`), the file has its heading chunks and no row chunks, and that is not a finding, as a malformed block is not. Any other exception from `roadmap.parse` or this decode is not caught here.
- Decision records: tracked files whose directory is exactly `tickets/decisions` and whose suffix is `.md` (the one `tickets/` subtree now indexed; every other `tickets/` path stays excluded) get a `files` row with `kind` `decision`, `purpose` the first non-blank line of the record body stripped of whitespace (`""` when the body is blank), `relates` `[]`, `owner` `""`, `hash` the SHA-256 of the file bytes, `size` the byte length. `box.parse_record(text)` gives the record and body; the record gets exactly one chunk: `selector` `<path>#<record.id>`, `text` the body, `tokens` its word count. Worked example: `tickets/decisions/declined-box-000002-306cb481.md` gives selector `tickets/decisions/declined-box-000002-306cb481.md#declined-box-000002-306cb481` and the body paragraph as text. A blank body or a file that is not UTF-8 or that `parse_record` raises `BoxError` on has its `files` row and no chunk, and that is not a finding.
- Box messages: `Box(config.state_dir / BOX_DIR, fs).messages()` (the build derives the box itself, so no parameter is added and `index-merge-hook` and `index-build-verb` call `build` unchanged). Each message, resolved or pending, gets a virtual file with `path` `box:<message.id>`, `kind` `box`, `purpose` the first line of `summary` stripped, `relates` `[]`, `owner` `message.origin`, `hash` the SHA-256 of `summary` encoded as UTF-8, `size` that byte length, and one chunk: `selector` `box:<id>#summary`, `text` `summary`, `tokens` its word count. Worked example: message `box-000582-ab12cd34` with summary `Duplicate of row 94` gives path `box:box-000582-ab12cd34`, selector `box:box-000582-ab12cd34#summary`, 4 tokens. Messages with equal summaries get separate rows because ids differ; two box files that carry the same `message.id` write one `box:<id>` row, from the last of them in the order `Box.messages()` returns; an absent or empty box directory gives no box rows, and a message no longer in the box has its rows deleted from `files`, `chunks` and `embeddings`. The hash covers only the summary, so a status or resolution change does not rewrite rows or re-embed.
- One write path: tracked files and box messages both go through one helper, `_write_entry(conn, path, files_row, chunks, has_embeddings)` in `clutch/index.py`, which deletes the path's rows from `files`, `chunks` and (when present) `embeddings` and inserts the new ones; deleting vanished paths uses the same delete. The incremental rule is unchanged: an entry whose digest equals the stored `files.hash` is not touched.
- The set of paths for deletion is the tracked-and-allowed paths plus the virtual `box:` paths of the current messages, so a virtual row is never deleted as "no longer tracked". Neither is touched when `ls_files` raises `GitError` (the existing `git_failed` outcome), because the box and roadmap work lives in the same branch as the listing.
- New closed outcome: `box_unreadable: <error>`, when `Box.messages()` raises `BoxError` (a corrupt box file). The finding is returned, existing `box:` rows are left as they were: the deletion set excludes every `box:` path whenever `Box.messages()` raised, so the keep-set is never computed from an empty list and no `box:` row is deleted on a failed read, and every other table is built as before. It joins the existing outcomes `db_open_failed`, `git_failed`, `embed_failed`, `call_unreadable` and creator findings, and is appended after the build's own earlier findings and before the creator findings, as `call_unreadable` is.

## Boundary contract
### Project index sources
- disposition: extend
- owner: clutch/index.py
- consumers: the embed step and the full-text step inside `build` (unchanged); later tickets `index-merge-hook`, `index-build-verb` and the neighbors query call `build` or read its tables
- observable change: `files` and `chunks` (and `embeddings` when `index.embed` is set) also hold rows for box messages, roadmap rows and decision records as defined in Goal; one new finding `box_unreadable`; nothing else about `build` differs
- compatibility: `build`'s signature, the table schemas and every existing outcome are unchanged; a repo with no box directory, no `docs/roadmap.md` and no `tickets/decisions/` indexes exactly as before
- acceptance: criteria 1-7 below
- tests: tests/unit/test_index_sources.py, tests/integration/test_index_sources_scan.py
- post-merge source of truth: clutch/index.py

### Box and roadmap readers
- disposition: reuse
- owner: clutch/box.py and clutch/roadmap.py
- consumers: `index.build`
- observable change: none; `Box.messages`, `parse_record` and `roadmap.parse` are called, not changed
- compatibility: unchanged
- acceptance: criteria 1-4 call them through the build
- tests: tests/unit/test_index_sources.py
- post-merge source of truth: clutch/box.py and clutch/roadmap.py

## Scope in / Scope out
Scope in: in `clutch/index.py`, add the three sources above, the `_write_entry` helper, the allowance for `tickets/decisions/*.md`, and the `box_unreadable` outcome, importing `BOX_DIR`, `Box`, `BoxError`, `parse_record` from `clutch.box` at module level (`clutch.box` does not reach `clutch.merge`), and `from clutch import roadmap` inside the roadmap-row branch only (the refusal is `roadmap.Refusal`, so `clutch.runner` is not imported here), with a comment saying why: `clutch.roadmap` leads to `clutch.runner` and then `clutch.merge`, which `index-merge-hook` makes import `clutch.index`, so a module-level import would be a cycle; the roadmap file path is `roadmap.ROADMAP`. Add `tests/unit/test_index_sources.py` (reuses `rig`, `run`, `rows`, `Exec` from `tests/unit/test_index_build.py`) and `tests/integration/test_index_sources_scan.py` (reads `clutch/index.py` through a `Path(__file__)` anchor). Each new test file starts with a `# clutch:meta` header whose `# purpose:` is a non-empty one-line sentence; run `uv run clutch meta refresh` on the two files to generate the rest. The existing tests in `tests/unit/test_index_build.py` and `tests/unit/test_index_embeddings.py` stay valid unchanged (their rig has no box directory, no roadmap and no decisions, and `tickets/x.md` stays excluded); nothing in them is edited.
Scope out: the nearest-neighbor query over these rows, the nearest open tickets, and the Triage and Author data blocks are separate tickets (follow-up roadmap rows to be filed after this merges: `index-box-neighbors-query`, then `index-box-neighbors-prompts` carrying the Triage and Author prompt changes). No `docs/` change: no document describes the index yet (`index-build-verb` writes its section). No change to `clutch/merge.py`, `clutch/mergequeue.py` (`index-merge-hook`), `clutch/__main__.py`, `clutch/evidence/store.py` or `clutch/box.py`. Open tickets stay out of the index. Order with `index-merge-hook`: that ticket calls `build` as-is and this one changes only what `build` writes; the one coupling is the import cycle above, which the function-local roadmap imports remove for either merge order.

## Scope fence
- clutch/index.py
- tests/unit/test_index_sources.py
- tests/integration/test_index_sources_scan.py

## Acceptance criteria
1. `tests/unit/test_index_sources.py` builds over a `tmp_path` repo whose `docs/roadmap.md` holds a master table with rows 1 and 2 (row 2 struck) and a heading, and asserts exactly two row chunks with selectors `docs/roadmap.md#row 1` and `docs/roadmap.md#row 2`, text `<stem>: <content>`, alongside the heading chunk; a build that omits the struck row, gives row chunks to another file, or drops the heading chunk fails it. Check: `./dev.py test tests/unit/test_index_sources.py`.
2. `tests/unit/test_index_sources.py` asserts a roadmap whose table is absent or has duplicate numbers yields the heading chunks only, returns `[]`, and does not raise, and so do a roadmap row number `²` (the `ValueError` from `parse`) and a non-UTF-8 `docs/roadmap.md`; a build that raises or returns a finding fails it. Check: `./dev.py test tests/unit/test_index_sources.py`.
3. `tests/unit/test_index_sources.py` asserts `tickets/decisions/d1.md` (valid record, body `Body text here.`) gives a `files` row with kind `decision` and purpose `Body text here.` (and a record whose body is `\n\nBody text here.` gives the same purpose, not `""`) and one chunk with selector `tickets/decisions/d1.md#d1`; that a blank-body record, a record with no frontmatter and a non-UTF-8 record each have a `files` row, no chunk and no finding; and that `tickets/decisions/sub/d2.md`, `tickets/decisions/d3.txt` and `tickets/other.md` get no row; indexing nested or other `tickets/` paths fails it. Check: `./dev.py test tests/unit/test_index_sources.py`.
4. `tests/unit/test_index_sources.py` writes two box messages with identical summaries and one resolved message into `<state_dir>/box/` and asserts three `box:<id>` `files` rows (kind `box`, owner the origin, hash the SHA-256 of the summary) and three `box:<id>#summary` chunks, no row dropped as a duplicate, and two box files carrying the same `message.id` give exactly one `box:<id>` row; a build that merges equal summaries fails it. Check: `./dev.py test tests/unit/test_index_sources.py`.
5. `tests/unit/test_index_sources.py` asserts, with `embed: ["fake"]` and a fake `exec_`, one `embeddings` row per chunk including box, decision and roadmap-row chunks; a second build issues no INSERT or DELETE on `files`, `chunks` or `embeddings` for unchanged entries (a recording `connect`), a changed summary rewrites only that message's rows, a status change alone writes nothing, and deleting a message file removes its rows from all three tables while no tracked-file row is removed; an unchanged `box:` row deleted as untracked fails it. Check: `./dev.py test tests/unit/test_index_sources.py`.
6. `tests/unit/test_index_sources.py` asserts a corrupt `.json` in the box returns exactly the finding `box_unreadable: ...`, leaves existing `box:` rows untouched (a build whose deletion set is computed from an empty message list fails it), still builds tracked files, and that with `ls_files` raising `GitError` the box rows and roadmap and decision rows are all left as they were and the single finding is `git_failed: ...`; deleting box rows on a failed read fails it. Check: `./dev.py test tests/unit/test_index_sources.py`.
7. `tests/integration/test_index_sources_scan.py` parses `clutch/index.py` with `ast` and asserts the string `INSERT INTO files` appears in exactly one `ast.Constant` (inside `_write_entry`) and that `_write_entry` is called from both the tracked-file loop and the box loop (two call sites), so no path writes `files` rows outside the helper; a second INSERT site fails it. The same test walks the module-level `ast.Import` and `ast.ImportFrom` nodes of `clutch/index.py` and asserts none names `clutch.roadmap`, `clutch.runner`, `clutch.author`, `clutch.merge` or `clutch.mergequeue` either as the module or, for `ImportFrom` nodes, through an alias (`from clutch import roadmap` has module `clutch` and alias `roadmap`); a module-level import of one fails it. Check: `./dev.py test tests/integration/test_index_sources_scan.py`.

## Verification
```
./dev.py test tests/unit/test_index_sources.py tests/integration/test_index_sources_scan.py tests/unit/test_index_build.py tests/unit/test_index_embeddings.py tests/integration/test_index_extensions.py tests/unit/test_stage_events_seam.py tests/integration/test_vocabularies.py tests/integration/test_thresh.py tests/integration/test_projection_helpers_source.py
uv run clutch meta check
uv run ruff format --check .
```

## Definition of rejected
The branch is thrown away if any code opens a SQLite file, if a new table, column, config key or `build` parameter is added, if a file outside the Scope fence is edited, if a `box:` row is deleted by the vanished-path rule, if a failed box read or failed `ls_files` deletes rows, or if tickets other than `tickets/decisions/*.md` enter the index.

## Time budget
- expected: 25m
- stuck: 50m
