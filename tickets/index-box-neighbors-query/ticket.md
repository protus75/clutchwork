---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- index-box-neighbors

## Context
- docs/annotations-index-plan.md#5. The index
- clutch/index.py::build
- clutch/index.py::_embed
- clutch/index.py::IndexCreator
- clutch/index.py::default_creator
- clutch/roadmap.py::ROADMAP
- clutch/seams.py::ProcessExec
- clutch/config.py::Index
- tests/unit/test_index_build.py
- tests/unit/test_index_sources.py

## Goal / Why
Roadmap row 187, slice 2 of 3 of row 110: the nearest-neighbor query over the index that `index-box-neighbors` filled. After this ticket `clutch/index.py` exports `neighbors(...)`: given a message text it returns the nearest Suggestion Box messages, roadmap rows and decision records, ranked by embedding when `config.index.embed` is set and by DuckDB full-text search otherwise. Without it a recurring report (box-000457, box-000529, box-000531, box-000574 were one flaky test) or a duplicate of a roadmap row (box-000582 duplicated row 94) can only be matched by the exact summary `Box.enqueue` compares. The Triage and Author data blocks that consume it are row 188 (`index-box-neighbors-prompts`), not this ticket. No CLI verb is added.

Decision on open tickets (stated, not left open): the query returns NO open tickets and takes no open-ticket input. `tickets/` (except `tickets/decisions`) is not indexed, so there are no index rows to rank; ranking caller-supplied ticket texts would need a second corpus (one embed exec per ticket, or a second full-text index whose scores are not comparable with the index's), which is a different mechanism and not "the query over the index". An open ticket authored from a roadmap row is still matched through that row's chunk. Open tickets with no row stay unmatched until row 188 or a later ticket supplies them, by indexing them in `build` or by ranking them itself; this ticket does not close that gap.

### The function
```
async def neighbors(config, root, text, *, fs, exec_, env, creator, limit=5, kinds=KINDS, exclude=(), connect=duckdb.connect) -> Neighbors
```
`KINDS = ("box", "roadmap", "decision")`. `config`, `root`, `fs`, `exec_`, `env`, `creator` and `connect` are the seams `build` takes, with the same meaning (`config.state_dir / "index.duckdb"` is the file, `config.index.embed` the embed argv, `creator.load(conn, kind)` loads an extension and returns finding strings). `neighbors` never writes a table, never calls `creator.create`, and never calls `duckdb.connect(...)` by name (the existing scan test `test_index_source_uses_seams` forbids it); it opens the file with `connect(str(path), read_only=True)` and closes it in a `finally`.

Parameters, each validated by rule before any I/O, in this order; the first failure returns outcome `invalid_input` and nothing else runs:

| Parameter | Rule | Finding on failure |
|---|---|---|
| `text` | a `str`; `text.strip()` non-empty; at most 8000 characters (the embed argv has a 60 s timeout and a longer text is the caller's to cut). The stripped text is what is embedded or searched | `invalid_input: text: not a string`, `invalid_input: text: blank`, `invalid_input: text: longer than 8000 characters` |
| `limit` | exactly an `int` (a `bool` is refused), 1 to 50 inclusive, default 5; the cap on total hits across kinds | `invalid_input: limit: not an integer in 1..50` |
| `kinds` | a list, tuple, set or frozenset (never a `str`, which would iterate as characters), non-empty, every member one of `KINDS`, no member repeated; default all three; only chunks of those kinds are candidates; order of members does not change the result | `invalid_input: kinds: not a non-empty collection of distinct members of box, roadmap, decision` |
| `exclude` | a list, tuple, set or frozenset (never a `str`) of at most 50 members, each a non-empty `str`; each member is a hit `ref` (below) to drop before the limit applies; a member matching no chunk is ignored. It exists so a caller whose message is already in the index (`box:<id>` rows are written by `build`) can drop itself | `invalid_input: exclude: not a collection of at most 50 non-empty strings` |
| `root`, `config`, `fs`, `exec_`, `env`, `creator`, `connect` | not validated; programmer-supplied seams, as in `build` | none |

### Candidate chunks and the hit shape
A candidate is one row of `chunks` of exactly one of these kinds; every other chunk (document headings, Python definitions) is never returned:
- `box`: `files.kind = 'box'` (selector `box:<id>#summary`). `ref` is `<id>` (the path without `box:`).
- `roadmap`: path `roadmap.ROADMAP` and selector starting `<roadmap.ROADMAP>#row ` (selector `docs/roadmap.md#row <n>`; struck rows included, as `build` indexes them). `ref` is `row <n>`. `roadmap` is imported inside `neighbors`, not at module level, with a comment giving the cycle reason `build` gives (`clutch.roadmap` leads to `clutch.runner` and `clutch.merge`, which imports `clutch.index`); the existing scan test `tests/integration/test_index_sources_scan.py` fails a module-level import.
- `decision`: `files.kind = 'decision'` (selector `<path>#<record id>`). `ref` is the file path, for example `tickets/decisions/declined-box-000002-306cb481.md`.

`Hit` is a frozen dataclass with five fields: `kind` (one of `KINDS`), `ref` (as above), `selector` (the chunk's `selector`, unique per hit), `text` (the chunk's `text` unmodified; the caller truncates), `score` (a `float`, higher is nearer, defined per mode below). `Neighbors` is a frozen dataclass with four fields: `outcome` (closed set below), `mode` (`"embedding"`, `"fulltext"`, or `""` when no search ran), `hits` (a tuple of `Hit`, at most `limit`, ordered by `score` descending then `selector` ascending by code point; `()` unless the outcome is `found`), `findings` (a tuple of strings, each starting with a closed prefix named below, `()` when there is nothing to report). `neighbors` never raises for any outcome named here.

### Search modes
- Embedding mode runs when `config.index.embed` is set. After the file opens, `creator.load(conn, "vss")` runs (the persisted HNSW index needs it to open the table); a non-empty return, a missing `embeddings` table, or a failed embed exec falls back to full-text (below). Otherwise the stripped text goes through the same embed exec as `build` (one `exec_.run` of `config.index.embed` with `cwd=root`, `env=env`, `timeout=EMBED_TIMEOUT_S`, text on stdin through `fs`, temp file removed in a `finally`), with the same vector validation, from ONE helper that `_embed` and `neighbors` both call (the exec-and-validate block extracted from `_embed`, producing the same reason strings and the same `embed_failed` text for `build`; no second copy). A vector whose length differs from the `embeddings.vec` length gives reason `length <n> != <m>`. The embed exec runs after the file opens, so a build holding the file fails the open first. `score` is `1 - array_cosine_distance(vec, query)`, computed in plain SQL by joining `embeddings` to `chunks` on `path` and `selector`; rows whose score is NULL or NaN (a zero-norm vector) are dropped. No vss index is required: the brute-force scan runs without it.
- Full-text mode runs when `config.index.embed` is unset, or as the fallback. `creator.load(conn, "fts")` runs; a non-empty return gives outcome `fulltext_unavailable` with that return as `findings`. Then, if the schema `fts_main_chunks` does not exist, outcome `fulltext_unavailable` with finding `fts unavailable: index missing`. Otherwise `score` is `fts_main_chunks.match_bm25(selector, <stripped text>)` from the index `build` creates (`selector` is its key column); NULL scores (no query term matches) are dropped.
- A fallback adds one finding `embed_failed: <reason>` as the first entry of `findings`, `<reason>` being one of `exit <n>`, `exec <ExceptionClass>`, `not json`, `not a vector`, `length <n> != <m>` (the existing reasons), `vss unavailable: <error>` (the creator's text, verbatim after the prefix `embed_failed: `), or `embeddings table missing`. It never changes the ordering rules. Exceptions the embed exec raises beyond the three `build` catches (`ExecutableNotFound`, `TimeoutError`, `OSError`) propagate, as in `build`. With `embed` unset there is no `embed_failed` finding and a stale `embeddings` table is ignored.
- A search that ran and returned no candidate after filters, drops and `exclude` keeps its mode and is `no_match`; it does not fall back to the other mode.

### Outcomes (closed), checked in this order
| Outcome | When | `mode` | `hits` | `findings` |
|---|---|---|---|---|
| `invalid_input` | a parameter rule above failed | `""` | `()` | that one finding |
| `no_index` | `fs.size(config.state_dir / "index.duckdb")` raises `FileNotFoundError` (the check `merge.refresh_index` uses) | `""` | `()` | `()` |
| `index_unreadable` | `connect` raises, a `files` or `chunks` table is missing, or any `duckdb.Error` is raised by a query | `""` | `()` | `index_unreadable: <error>` |
| `fulltext_unavailable` | full-text mode was needed and could not run (above) | `""` | `()` | the load or missing-index finding, after any `embed_failed` finding |
| `no_match` | a search ran and no candidate remains | its mode | `()` | `()` or the fallback finding |
| `found` | one or more hits | its mode | the hits | `()` or the fallback finding |

### Worked example
The index holds three candidate chunks with embeddings and the query vector is `[1, 0, 0]`:

| Chunk selector | vector | score |
|---|---|---|
| `box:box-000582-ab12cd34#summary` (summary `Duplicate of row 94`) | `[1, 0, 0]` | `1.0` |
| `docs/roadmap.md#row 94` | `[0.8, 0.6, 0]` | `0.8` |
| `tickets/decisions/declined-box-000002-306cb481.md#declined-box-000002-306cb481` | `[0, 1, 0]` | `0.0` |

`neighbors(..., "dup of row 94")` returns outcome `found`, mode `embedding`, hits `(Hit("box","box-000582-ab12cd34",...,1.0), Hit("roadmap","row 94",...,0.8), Hit("decision","tickets/decisions/declined-box-000002-306cb481.md",...,0.0))`. `limit=2` drops the decision. `kinds=("roadmap",)` returns only row 94. `exclude=("box-000582-ab12cd34",)` returns row 94 then the decision. A tie in score orders by `selector` ascending. With `index.embed` unset the same call ranks by `match_bm25`; with `embed` set and the embed exec exiting 3 it returns mode `fulltext` and findings `("embed_failed: exit 3",)`.

## Boundary contract
### Neighbor query
- disposition: create
- owner: clutch/index.py
- consumers: none yet; row 188 (`index-box-neighbors-prompts`) calls it for the Triage data block and the Author data block, two production consumers
- observable change: new exported `neighbors`, `Neighbors`, `Hit` and `KINDS` in `clutch/index.py`; reads `index.duckdb` read-only; runs the host embed argv once per call when `index.embed` is set; no write, no CLI verb, no config key, no new table
- compatibility: `build`, the table schemas, every `build` finding and the shipped `embed_failed: <selector>: <reason>` text are unchanged
- acceptance: criteria 1-9
- tests: tests/unit/test_index_neighbors.py, tests/integration/test_index_neighbors_fulltext.py
- post-merge source of truth: clutch/index.py
- closest existing: `build` and `_embed` in `clutch/index.py`, and `IndexCreator`
- earning reason: `build` only writes tables and `_embed` embeds stored chunks; neither reads nearest rows, and both consumers (Triage, Author) need the same ranking, so it lives once beside the tables it reads

### Embed exec helper
- disposition: extend
- owner: clutch/index.py (`_embed`)
- consumers: `build` (through `_embed`) and `neighbors`
- observable change: none for `build`; the exec-and-validate block moves into one private helper both call
- compatibility: preservation: `_embed` returns the same findings, the same reason strings and writes the same rows; `tests/unit/test_index_embeddings.py` passes unchanged
- acceptance: criterion 8
- tests: tests/unit/test_index_embeddings.py (unchanged), tests/unit/test_index_neighbors.py
- post-merge source of truth: clutch/index.py

## Scope in / Scope out
Scope in: in `clutch/index.py`, add `KINDS`, `Hit`, `Neighbors`, `neighbors`, and extract the embed exec-and-validate block of `_embed` into one private helper called by `_embed` and `neighbors`, importing `dataclass` from `dataclasses` and `Collection`/`Sequence` from `collections.abc` only if used. Add `tests/unit/test_index_neighbors.py` (builds a real index with `rig` and `run` from `tests/unit/test_index_build.py` and a fake `exec_` defined in the new file that answers by the text it reads from `stdin_path`; embedding mode, every outcome, validation, ordering) and `tests/integration/test_index_neighbors_fulltext.py` (real `default_creator`, the real DuckDB `fts` and `vss` extensions; skips with `pytest.skip` when a build finding contains `unavailable:`, as `tests/integration/test_index_extensions.py` does). Each new test file starts with a `# clutch:meta` header whose `# purpose:` is a NON-EMPTY one-line sentence (nothing else in the header is hand-written: run `uv run clutch meta refresh` on the two files to generate it). Both test files reuse `rig`, `run`, `rows`, `Exec`, `Creator` from `tests/unit/test_index_build.py`; nothing is added to an existing test file and nothing in them is edited, because the rig has `embed` unset and every existing assertion on `_embed` findings keeps passing.
Scope out: open tickets (decision above); the Triage and Author data blocks, specs and prompt changes (row 188 `index-box-neighbors-prompts`); any CLI verb, config key, table or `build` change beyond the helper extraction; any thresholds or "nearest enough" cutoff (row 188 chooses what to show); documentation: no document describes the query, and the index documentation belongs to the running ticket `index-build-verb-r1`, which fences none of this ticket's files, so either merge order works; `index-merge-hook` and `index-box-neighbors` share `clutch/index.py` only through code already merged. Documenting `neighbors` belongs to the consumer ticket that makes it reachable from a verb or a prompt.

## Scope fence
- clutch/index.py
- tests/unit/test_index_neighbors.py
- tests/integration/test_index_neighbors_fulltext.py

## Acceptance criteria
1. `tests/unit/test_index_neighbors.py` builds an index with `embed: ["fake"]` holding the worked example's three chunks plus one heading chunk and asserts `neighbors` returns outcome `found`, mode `embedding`, exactly three hits in order box, roadmap, decision with scores `1.0`, `0.8`, `0.0` (to `pytest.approx`) and the `ref` and `selector` values of the table; a result that returns the heading chunk, orders by `selector` instead of score, or reports `score` as the distance fails it. Check: `./dev.py test tests/unit/test_index_neighbors.py`.
2. `tests/unit/test_index_neighbors.py` asserts `limit=2` returns two hits (the decision dropped, not the box hit), `kinds=("roadmap",)` returns only `row 94` whatever the member order, `exclude=("box-000582-ab12cd34",)` returns row 94 then the decision with a box hit never present, an unknown `exclude` member changes nothing, and two chunks with equal scores come back in `selector` ascending order; a limit applied before `exclude`, or a tie broken by insertion order, fails it. Check: `./dev.py test tests/unit/test_index_neighbors.py`.
3. `tests/unit/test_index_neighbors.py` asserts every validation row returns `invalid_input` with its exact finding and `exec_` never called (no embed, no connect call): `text` of `None`, `""`, `"  \n"`, and 8001 characters (8000 passes); `limit` of `0`, `51`, `True`, `2.0`, `"3"` (1 and 50 pass); `kinds` of `"box"`, `()`, `("box","box")`, `("ticket",)`; `exclude` of `"box-1"`, 51 members, `("",)`, `(1,)`; and that with two bad parameters the finding names `text` before `limit` before `kinds` before `exclude`; a `bool` accepted as `limit` or a bare string accepted as `kinds` fails it. Check: `./dev.py test tests/unit/test_index_neighbors.py`.
4. `tests/unit/test_index_neighbors.py` asserts `no_index` for a `state_dir` with no `index.duckdb` (`findings == ()`, `exec_` never called) and `index_unreadable` with a finding starting `index_unreadable: ` for a `connect` that raises, for an `index.duckdb` that is not a database, and for a database with no `chunks` table; `no_index` for a present but unreadable file, or an exception raised out of `neighbors`, fails it. Check: `./dev.py test tests/unit/test_index_neighbors.py`.
5. `tests/unit/test_index_neighbors.py` asserts embedding fallback: with `embed` set and the embed exec returning exit 3, then non-JSON, then `[]`, then a vector of the wrong length, then a creator whose `load(conn, "vss")` returns `["vss unavailable: x"]`, then a database with no `embeddings` table, `neighbors` returns mode `fulltext` and `findings[0]` equals `embed_failed: exit 3`, `embed_failed: not json`, `embed_failed: not a vector`, `embed_failed: length 2 != 3`, `embed_failed: vss unavailable: x`, `embed_failed: embeddings table missing` respectively (with a creator whose `load(conn, "fts")` also fails, the outcome is `fulltext_unavailable` and `findings` is the `embed_failed` entry then `fts unavailable: ...` text), and that `embed` unset gives no `embed_failed` finding and no `exec_` call even when a stale `embeddings` table exists; a fallback that raises, loses the finding, or runs the embed exec with `embed` unset fails it. Check: `./dev.py test tests/unit/test_index_neighbors.py`.
6. `tests/unit/test_index_neighbors.py` asserts a zero query vector `[0,0,0]` returns outcome `no_match`, mode `embedding`, `hits == ()`, not `found` and not a fallback; a kinds filter that leaves no chunk also gives `no_match`; and `fulltext_unavailable` with finding `fts unavailable: index missing` when `embed` is unset and the build used the fake creator (no `fts_main_chunks` schema). Check: `./dev.py test tests/unit/test_index_neighbors.py`.
7. `tests/integration/test_index_neighbors_fulltext.py` builds with the real `default_creator` and `embed` unset, over a box message `flaky test timeout in drain`, a box message `rename the doctor verb`, a roadmap row and a decision record, and asserts `neighbors(..., "the drain test is flaky")` returns outcome `found`, mode `fulltext`, the flaky message as the first hit with a `score` above the second, no hit whose terms do not match (`rename the doctor verb` absent), `findings == ()`, and that the same build with `embed: ["fake"]` and a failing embed exec returns the same first hit with `findings == ("embed_failed: exit 2",)`; also that the real embedding path with the real `vss` extension and a persisted HNSW index returns the nearest chunk. A mode that ranks by length, or a result that raises on the read-only open, fails it. Check: `./dev.py test tests/integration/test_index_neighbors_fulltext.py`.
8. `tests/unit/test_index_neighbors.py` asserts the embed exec seam: `neighbors` makes exactly one `exec_.run` call per search with argv `config.index.embed`, `cwd=root`, the passed `env`, `timeout=60`, a `stdin_path` whose content is the stripped text, and the temp file removed afterwards even when the exec raises `TimeoutError`; and `tests/unit/test_index_embeddings.py` and `tests/unit/test_index_build.py` pass unchanged, so `build` reasons are preserved. A second copy of the validation block, or a changed `build` finding, fails it. Check: `./dev.py test tests/unit/test_index_neighbors.py tests/unit/test_index_embeddings.py tests/unit/test_index_build.py`.
9. `tests/unit/test_index_neighbors.py` asserts `neighbors` writes nothing: the file's bytes and every table's rows are identical before and after, `creator.create` is never called, and no statement beginning `INSERT`, `DELETE`, `CREATE`, `DROP` or `PRAGMA` is issued; and `tests/integration/test_index_sources_scan.py` and `tests/integration/test_index_extensions.py` pass unchanged (no module-level `clutch.roadmap` import, one `INSERT INTO files` site, no `duckdb.connect(` call, no `sqlite` in the source). Check: `./dev.py test tests/unit/test_index_neighbors.py tests/integration/test_index_sources_scan.py tests/integration/test_index_extensions.py`.

## Verification
```
./dev.py test tests/unit/test_index_neighbors.py tests/integration/test_index_neighbors_fulltext.py tests/unit/test_index_build.py tests/unit/test_index_embeddings.py tests/unit/test_index_sources.py tests/integration/test_index_sources_scan.py tests/integration/test_index_extensions.py tests/unit/test_merge_index_hook.py
uv run clutch meta check
uv run ruff format --check .
```

## Definition of rejected
The branch is thrown away if any code opens a SQLite file, if `neighbors` writes a table or creates an index, if a file outside the Scope fence is edited, if `build`'s signature, tables or findings change, if open tickets are ranked in this ticket, if a CLI verb, config key or `docs/` change is added, if the embed argv is run through anything but `exec_`, or if a new `.py` test file lacks a non-empty `# purpose:` header line.

## Time budget
- expected: 28m
- stuck: 56m
