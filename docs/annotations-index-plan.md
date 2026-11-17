# File annotations and the project index: plan

Give every file that has no parser (documents, tests, fixtures, guides) a small, closed metadata block: what the file is for, what it relates to, who owns it, and a hash that says whether the block still matches the content. Generate the deterministic fields; let a model fill the one or two judgment fields, and only for blocks that are missing or drifted. Build one index over those blocks, the structure a parser already gives source files, and the records the evidence and journal stores already hold, in DuckDB with vector search, so an agent can find the right file, section, or past ticket without reading the whole project. The index feeds ticket authoring (which files belong in `## Context`), the Implement prompt, the document agent's drafting, and the training export, from one store instead of each keeping its own.

## Status

Draft plan. Nothing in it is in effect and no ticket is authored. Written 2026-11-14 at commit `0ef95269` for `docs/roadmap.md`.

## Roadmap

Release 0.5.0 (`docs/roadmap.md` rows 69-74), beside the training flywheel, because the index and the training export read the same stores. Needs from other plans: `evidence-envelope` (0.3.0) for the call records the index joins; `duckdb` arrives with `journal-query-layer` (0.6.0) when that window runs, else `index-build` adds it with the same D3 justification. What needs this plan: the document agent's `doc-draft` uses `context-suggest` to find sources; the training plan's "retrieval first" advice becomes a clutch feature. Shared budgets: none in CORE_TEMPLATE; one new config block `index` and one `meta`.

## Current state

- Structure clutch already reads: ticket frontmatter (`clutch/tickets.py`); `## Context` selectors `path.py::Name`, `path.py::Class.method`, `path.md#Heading`, resolved by the engine for Implement; Python imports and definitions through the AST (the same resolver); `tests/` imports; `engine.log` and the journal as JSON. The document agent adds a per-folder `docset.yaml`. The evidence store adds per-call records.
- Structure nothing reads: a document's purpose, which documents and tests belong to which module or plan, which guide a rule lives in. A ticket author finds these by grep and memory; the audit's "172 of 539 fences include `docs/how-clutch-works.md`" is what that costs: authors fence the whole document because nothing says which section a change affects.
- No index, no search beyond grep, no embeddings. `config.context_files` is a hand-kept list.
- The owner runs a comparable system in `~/source/boardgameui`: it works, and it grew past its original shape through additions. That history is this plan's main constraint: a closed field set, versioned, extended only with a schema bump and an incident.

## Departures from the design record

| Record says | This plan | Why |
|---|---|---|
| §18.1 refuses "metadata taxonomies/lints" and "semantic history search" | A closed six-key block on parser-less files, a soft drift lint, and a search index over files, calls, and history | The owner asked for it on 2026-11-14. The refusal's target was free taxonomy and search for its own sake; this is one fixed schema whose fields are generated where they can be, and the measured incident is the fence contention above. The index is a rebuildable cache under `state_dir`, never an authority |

`CLUTCH_PLAN.md` stays frozen. The tickets add a "Project index" section to `docs/how-clutch-works.md` and two config rows.

## Target design

### 1. The block

One format per file family, the same six keys:

```markdown
<!-- clutch:meta
schema: clutch.meta/1.0
kind: doc
purpose: What clutch does today, section by section; tickets keep it current.
relates: [clutch/docs/host-contract.md, clutch/docs/host-authoring.md]
owner: engine
verified: 0ef95269
hash: 3f9a1c...
-->
```

```python
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Proves a later process never overwrites an earlier capture.
# relates: [clutch/providers.py, clutch/seams.py]
# owner: clutch/providers.py
# verified: 0ef95269
# hash: 5be1...
```

| Key | Filled by | Meaning |
|---|---|---|
| `schema` | generator | `clutch.meta/<major>.<minor>`; strict writer, tolerant reader, as the evidence schemas |
| `kind` | generator | closed: `doc`, `guide`, `spec`, `test`, `fixture`, `plan` (from the path allowlist in config) |
| `purpose` | model, once | one sentence; the only free text |
| `relates` | generator where it can (imports for tests, links and `path::` selectors for documents), model for the rest | repo paths this file is about or depends on; validated to exist |
| `owner` | generator from `relates` when one module dominates, else model | the module, plan, or `engine` the file serves |
| `verified` | generator | the commit at which the block was last confirmed against the content |
| `hash` | generator | SHA-256 of the file content with the block removed; a mismatch is `drifted` |

Nothing else. A seventh key needs a schema minor bump, an incident, and a reader that uses it. Source files get no block: the AST and the module docstring are their annotation, and the index derives the same record from them at build time. Logs and the journal get no block: they are records already.

### 2. Verbs

- `clutch meta refresh [paths]`: for every file under `meta.paths`, compute the generated fields and the hash, insert a block where none exists (with `purpose` empty), and update generated fields where the hash shows drift. Never touches `purpose` or a model-filled `relates`. Deterministic; runs in Check on changed files (section 4).
- `clutch meta check [paths]`: lists files with no block, an empty `purpose`, or a `hash` that does not match. Exit 1 when any; read-only. `doctor` does not run it (it is project state, not setup).
- `clutch meta fill [paths]`: for files `check` lists, one read-only model call per batch of up to 20 files on a new `meta` surface (`clutch/specs/meta.md`): the model receives each file's content and generated fields and returns `purpose` and, where the generator left it empty, `relates` and `owner`, as JSON under a schema. The engine validates paths exist, writes the blocks, and sets `verified`. Routed by `(tier, meta)`; falls back to the `review` row as every surface does.

### 3. Scope, v1

`meta.paths` is an allowlist of roots with their kinds, this repo's default:

```yaml
meta:
  paths:
    - {root: docs/, kind: plan}
    - {root: clutch/docs/, kind: guide}
    - {root: clutch/specs/, kind: spec}
    - {root: tests/, kind: test}
```

`tests/` files under `fixtures/` or `harness/` take `kind: fixture`. Ticket files are excluded: `ticket.md` has its own frontmatter and `tickets/` is engine-written. `README.md`, `CLAUDE.md`, and `AGENTS.md` are excluded in v1 because their first lines are read by tools and people who expect prose there.

### 4. Drift

- A new soft Check gate `meta_drift`: for every changed file under `meta.paths`, the block exists and the hash matches after `meta refresh` ran on the branch (Check runs `refresh` on changed files before the gate, the way it runs autofix, and commits the generated changes as `clutch(<stem>): meta`). A drifted `purpose` cannot be detected mechanically; the gate reports `purpose` as `unverified` when the content hash moved and the block was not re-filled, and Review sees it in the diff.
- Soft by default. It becomes hard, per the usual rule, only after an incident where a drifted block misled an agent.

### 5. The index

`clutch index build` writes `<state_dir>/index.duckdb`, a derived cache: deleted and rebuilt at any time, never read by a gate or by dispatch, gitignored like everything under `state_dir`.

| Table | From | Rows |
|---|---|---|
| `files` | meta blocks; for `.py`, the AST (module docstring, definitions, imports) | one per file: path, kind, purpose, relates, owner, hash, size |
| `chunks` | headings of documents; definitions of Python files; test functions | one per section or definition: path, selector (`path#Heading`, `path::Name`), text, token count |
| `embeddings` | `chunks.text` and `files.purpose` through the host's embedding command | one vector per chunk, DuckDB VSS index |
| `touches` | squash commits on `main` (`clutch-ticket` trailers) and their changed paths | which ticket changed which file, when |
| `calls` | the evidence store's call records | which call read or edited which path (`tree_before`/`tree_after`, tool events), for which stem and surface |

- Embeddings come from a host-declared command, `index.embed: [argv]`, that reads text on stdin and prints a JSON vector; a host points it at a local model (Ollama `nomic-embed-text`, or anything else). clutch ships no embedding model and no ML dependency; with `embed` unset the index builds without the `embeddings` table and search falls back to DuckDB full-text.
- Incremental: a file whose hash is unchanged since the last build is skipped. `index build` runs at the end of a merge in `serve` and `drain` for the changed paths, and by hand.

### 6. Consumers

- `clutch context suggest <stem>`: from a ticket's Goal and Scope text, the top matching chunks as ready-to-paste `## Context` selectors with one line each on why. The author (a person or the Author stage) decides what to keep. Author's prompt gets the same list as a data block, so engine-written tickets fence sections, not whole documents.
- Implement: with `index.implement_hint: true`, the prompt gets a `related_files` data block, the top matches for the ticket's Goal that are not already in Context, capped at 10 lines. Off by default; the incident that turns it on is a run that failed for want of a file the index would have named.
- The document agent's `doc draft --from` resolves source material through the index when given a topic instead of paths.
- The training export joins `files.purpose` and `touches` onto its records so a tuned model sees what each file is for.

### 7. Config

```yaml
meta:
  paths: []              # allowlist of {root, kind}; empty means no blocks are expected
index:
  embed: null            # argv reading text on stdin, printing a JSON vector; null disables vectors
  implement_hint: false
```

Both blocks have defaults, so existing configs load unchanged. A host with `meta.paths: []` never sees `meta_drift`.

## Where each piece lives

| Piece | Home |
|---|---|
| Block format, parser, hash, generated fields | new `clutch/meta.py` (pure apart from the `FileSystem` seam) |
| `meta` surface spec | `clutch/specs/meta.md` |
| Verbs `meta refresh/check/fill`, `index build`, `context suggest` | `clutch/__main__.py`, plus `./dev.py` subcommands |
| `meta_drift` gate and the refresh step | `clutch/gates.py`, `clutch/stages.py` (Check, beside autofix) |
| Index tables, VSS, incremental build | new `clutch/index.py` (DuckDB) |
| Config | `clutch/config.py` (`Meta`, `Index`); `clutch/docs/host-contract.md` inventory |
| Docs | `docs/how-clutch-works.md` new section "Project index", config table; `clutch/docs/host-authoring.md` (how `context suggest` feeds `## Context`) |

## Ticket breakdown

Each ticket puts its tests in new files (`docs/parallel-tickets-plan.md` §7).

| # | Stem | Kind | P | Depends on | Content |
|---|---|---|---|---|---|
| 1 | `meta-schema-and-refresh` | feature | P2 | | Block format for Markdown and Python, parser, hash, generated fields, `meta refresh` and `meta check`, `meta` config. Release 0.5.0. |
| 2 | `meta-fill-surface` | feature | P2 | 1 | `clutch/specs/meta.md`, `meta fill` in batches, path validation, `verified` stamping. Release 0.5.0. |
| 3 | `meta-drift-lint` | feature | P3 | 1 | Soft `meta_drift` gate; Check runs `refresh` on changed files and commits `clutch(<stem>): meta`. Release 0.5.0. |
| 4 | `index-build` | feature | P2 | 1, `evidence-envelope` | `clutch/index.py`: tables, host embed command, VSS, incremental build, post-merge build; adds `duckdb` if `journal-query-layer` has not. Release 0.5.0. |
| 5 | `context-suggest` | feature | P2 | 4 | The verb, and the data block in the Author prompt. Release 0.5.0. |
| 6 | `index-consumers` | feature | P3 | 5 | `index.implement_hint`, `doc draft --from <topic>`, the training export join. Release 0.5.0. |

`Runs before`: `contention-authoring-rules` (roadmap row 13) before every ticket here. Ticket 1 fills blocks for this repo's `docs/`, `clutch/docs/`, `clutch/specs/`, and `tests/` as part of its own change, so the repo ships annotated.

## Risks

- **Schema sprawl**, the boardgameui lesson. Six keys, closed `kind`, one free-text field, and a rule that a new key needs a schema bump, an incident, and a reader. Extensions a host wants go in a host-owned sidecar, never in the block.
- **Drift noise.** A soft gate that fires on every documentation edit trains people to ignore it. Refresh runs first, so only an unfilled `purpose` after a content change fires, and only on files the ticket changed.
- **Embedding quality is the host's.** clutch ships none; a weak local model gives weak suggestions. Full-text search is the floor.
- **Index staleness.** It is a cache; a build after every merge keeps it current for the next ticket, and `index build` is idempotent.
- **The model writes into tracked files.** `meta fill` writes blocks the engine composed from a JSON reply; the model never edits a file. The write is one commit a person reviews like any other.

## Open decisions

Decided 2026-11-16 (`docs/roadmap.md` §6, decision 19): items 1 and 2 take their Proposed option. Item 3 has none; a recorded AI design panel settles it before any row that builds it is authored.

1. **Block placement in Python test files.** Proposed: a comment block after the module docstring. The alternative, inside the docstring, is read by tools that show docstrings.
2. **Who may run `meta fill`.** Proposed: an agent task and Author for files it creates; never Implement, so a ticket's diff carries no model-written metadata it did not ask for.
3. **Embedding of past calls.** The `calls` table joins by path; embedding call transcripts for semantic search over "what did an agent do when it last touched this" is a second step, once the evidence store has a release of data.
