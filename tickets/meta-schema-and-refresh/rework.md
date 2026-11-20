# Supervisor Rework escalated

- trigger: premise_failed
- outcome: gate_failed
- action: update

## Findings

- `supervise_edit`: the proposal changes `## Goal / Why` -- escalate to the operator: the stem stays in the Reject queue; edit tickets/meta-schema-and-refresh/ticket.md, then `clutch ticket confirm meta-schema-and-refresh`, or retire it with `clutch ticket reject meta-schema-and-refresh`

## Proposed ticket

````markdown
---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
none

## Context
- docs/annotations-index-plan.md#File annotations and the project index: plan
- clutch/config.py::TrainingData
- clutch/config.py::Config
- clutch/git.py::Git.ls_files
- clutch/git.py::Git.rev_parse
- clutch/seams.py::FileSystem
- clutch/docs/host-contract.md#Complete field inventory
- tests/unit/test_main_training_group.py
- tests/unit/test_training_config.py

## Goal / Why
Roadmap row 69 (annotations plan, ticket 1). Today no file without a parser (documents, guides, specs, tests) carries any statement of what it is for, so a ticket author fences a whole document because nothing says which file relates to which. After this ticket a host can list roots under a new `meta.paths` config key, and `clutch meta refresh [PATH ...]` inserts into every tracked Markdown and Python file under those roots a seven-key `clutch.meta/1.0` block, and keeps its generated fields true when the file changes. `clutch meta check [PATH ...]` lists the files whose block is missing, has an empty `purpose`, or whose `hash` no longer matches. This is the smallest slice the later tickets (`meta-fill-surface`, `meta-drift-lint`, `index-build`) build on; nothing in the pipeline reads a block yet.

The block (plan section 1), the same seven keys (`schema`, `kind`, `purpose`, `relates`, `owner`, `verified`, `hash`) in both families:

```markdown
<!-- clutch:meta
schema: clutch.meta/1.0
kind: doc
purpose: ...
relates: [path, path]
owner: engine
verified: ...
hash: <sha256>
-->
```

Python files carry the same seven keys as consecutive `# key: value` comment lines under a `# clutch:meta` line.

Rules:
- `meta.paths` is a list of `{root, kind}`, `kind` one of `doc`, `guide`, `spec`, `test`, `fixture`, `plan`; the default is the empty list, so a host with no `meta` key sees no change. A tracked file (from `git ls-files`) is managed when its path is under a root and its name ends `.md` or `.py`. Excluded always: any path under `tickets/`, and files named `README.md`, `CLAUDE.md` or `AGENTS.md`. A `test`-root file with `fixtures` or `harness` as a path component takes kind `fixture`.
- `hash` is the SHA-256 hex digest of the file's bytes with the block removed, so inserting or rewriting the block never changes it and any other edit does.
- `refresh` on a file with no block inserts one: Markdown at the top of the file, Python right after the module docstring (annotations plan open decision 1, decided 2026-11-16), or after the leading shebang and coding lines (if any) when the file has no docstring; `schema` is `clutch.meta/1.0`, `kind` from the root, `purpose` empty, `verified` empty, `hash` computed; `relates` and `owner` are generated once, at insert: `relates` is the sorted, deduplicated tracked repo paths the file names (for Python, `import clutch.x` and `from clutch.x import ...` resolving to a tracked `clutch/x.py`; for Markdown, relative link targets and backticked `path.ext` or `path.ext::Name` tokens that name a tracked file), never the file itself; `owner` is that path when `relates` holds exactly one `clutch/*.py` file, else empty. On a file whose block hash no longer matches, `refresh` rewrites only `schema`, `kind` and `hash`; it never changes `purpose`, `relates`, `owner` or `verified` (a model or person owns those; `verified` is stamped by `meta-fill-surface` after a confirmation). A file whose block already matches is left byte-identical.
- `check` is read-only and prints one `path: missing`, `path: empty purpose` or `path: drifted` line per problem (a file with a block that has an empty purpose and a stale hash prints both lines), sorted by path; exit 1 when any line printed, 0 otherwise. `refresh` prints one `path: inserted` or `path: updated` line per file it wrote and exits 0.
- Both verbs read `meta.paths` and tracked files only; naming a PATH that is not under a configured root is a refusal (exit 2) naming that path and the configured roots. With `meta.paths` empty they print `meta.paths is empty; nothing to do` and exit 0.
- A malformed block (opening marker with no closing marker, an unknown key, a missing key, a `schema` whose major is not 1) is reported by `check` as `path: malformed block` and left untouched by `refresh`, which prints `path: malformed block` and exits 2 after processing the other files. Reader tolerance: a `schema` of `clutch.meta/1.<n>` for any `n` parses; the writer always writes `1.0`.

## Boundary contract
### Meta block format and parser
- disposition: create
- owner: clutch/meta.py
- consumers: the `meta refresh` and `meta check` handlers in clutch/__main__.py; later `meta-fill-surface`, `meta-drift-lint` and `index-build`
- observable change: new module with pure functions over file text and a list of tracked paths: parse a block, strip it, hash, build a block, insert or rewrite, generate `relates` and `owner`, and report a file's problems; it does no I/O
- compatibility: no existing file changes; a file with no block is a valid file today and stays one
- acceptance: criteria 1 to 7
- tests: tests/unit/test_meta_block.py
- post-merge source of truth: clutch/meta.py
- closest existing: clutch/tickets.py (ticket frontmatter parser) and clutch/evidence/schema.py (schema string with strict writer and tolerant reader); the first parses a YAML frontmatter of a different closed key set inside a ticket file only, the second defines record models, and neither handles an embedded comment block in an arbitrary Markdown or Python file or hashes the file without it
- earning reason: three later production consumers named above (fill, drift gate, index build) read the same block, so the format has one owner instead of a copy per consumer

### Meta configuration
- disposition: extend
- owner: clutch/config.py::Config
- consumers: the two handlers, clutch/docs/host-contract.md field inventory
- observable change: `Config.meta` with `paths: list[{root, kind}]`, default empty; a bad `kind`, an empty `root` or an extra key is a config load refusal
- compatibility: `schema_version` stays 1; every existing config loads unchanged because the key is optional
- acceptance: criterion 8
- tests: tests/unit/test_meta_config.py
- post-merge source of truth: clutch/config.py::Meta and the `config-fields` block in clutch/docs/host-contract.md

### Meta command group
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators, `clutch help`, the verb tables in the run guide and how-clutch-works
- observable change: new top-level group `meta` with subcommands `refresh` and `check`, each with description, reads, writes, lock, exit codes and examples through `_command`
- compatibility: no existing command changes
- acceptance: criteria 9 to 11
- tests: tests/unit/test_main_meta_group.py, tests/unit/test_main_help.py, tests/unit/test_host_running.py
- post-merge source of truth: the parser in clutch/__main__.py

## Scope in / Scope out
Scope in:
- New `clutch/meta.py`, pure (no I/O, no clock, no git): the `Meta` field set and kind vocabulary stay in `clutch/config.py`, which `meta.py` does not import (it takes `(root, kind)` tuples). It holds the block parse and render for both families, the content hash, the generators for `relates` and `owner`, insert and rewrite, and `problems(text) -> list[str]`; and `managed(paths_config, tracked) -> dict[path, kind]` applying the root, extension, exclusion and `fixtures`/`harness` rules.
- `clutch/config.py`: `MetaPath` (`root`, non-empty; `kind`, a closed `Literal`), `Meta` with `paths: list[MetaPath] = []`, and `Config.meta: Meta = Meta()`.
- `clutch/__main__.py`: the `meta` group with `refresh` and `check`, each taking an optional `PATH` list, and the handlers. A handler lists tracked files with `checkout.git.ls_files(repo)`, reads each managed file with `checkout.fs.read_bytes`, calls `clutch.meta`, and writes changed files with `checkout.fs.write`; it takes no lock (it edits tracked files in the working tree only and writes no journal event or commit). It prints with `print` to stdout; no new `print(..., file=sys.stderr)`. Refusals use `runner.Refusal` as `handle_training` does.
- Documents: `clutch/docs/host-contract.md` inventory gets `meta: {paths: []}` in `Config` defaults and `Meta` and `MetaPath` entries; `clutch/docs/host-running.md` gets `meta refresh` and `meta check` rows (works while serve runs: `Yes`; both are working-tree only); `docs/how-clutch-works.md` gets the two rows in the section 2.1 verb table and one `meta` row in the section 11 config table. Only those rows change.
- New tests in new files named in the fence.

Scope out:
- Applying blocks to this repo: `config.yaml` is not changed, so no file in this repo gets a block from this ticket. A repo-wide insert would edit hundreds of files other tickets fence; `meta-drift-lint` adds blocks only to changed files, and a bulk fill belongs to `meta-fill-surface`.
- `meta fill`, `clutch/specs/meta.md` and the `meta` model surface (`meta-fill-surface`); the `meta_drift` gate and Check's refresh step (`meta-drift-lint`); the index, `context suggest` and the "Project index" section of `docs/how-clutch-works.md` (`index-build`); `clutch/help.py` (the verbs are not extension surfaces); the extension directory, and any agent rule change.
- Block formats for other file types (YAML, JSON, TOML); such files under a root are skipped, not errors.

Merge order: this ticket and `one-parser-per-provider` share no file. Other confirmed unmerged tickets that add a command fence `clutch/__main__.py` and the two verb tables too; each adds its own rows and group, so either order merges without a changed assertion.

## Scope fence
- clutch/meta.py
- clutch/config.py
- clutch/__main__.py
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_meta_block.py
- tests/unit/test_meta_config.py
- tests/unit/test_main_meta_group.py

## Acceptance criteria
1. A Markdown text with no block, passed to the insert function with kind `doc`, returns the original text with a block at the top whose `schema` is `clutch.meta/1.0`, `kind` is `doc`, `purpose` and `verified` are empty and `hash` equals the SHA-256 of the original bytes; stripping the block returns the original text exactly, not the text with a leftover blank line; checked by `./dev.py test tests/unit/test_meta_block.py`.
2. A Python text with a shebang, a coding line and a module docstring gets its block on the line after the docstring's closing quotes, and `ast.parse` of the result succeeds with `ast.get_docstring` unchanged and the docstring still the first statement; a text with a shebang and no docstring gets the block after the shebang line; a text with neither gets it on line 1; stripping the block returns the original text exactly; checked by `./dev.py test tests/unit/test_meta_block.py`.
3. Changing one body character changes `hash`, and rewriting only the block (a new `purpose`) leaves `hash` unchanged, so a file whose `purpose` was filled is not reported `drifted`; checked by `./dev.py test tests/unit/test_meta_block.py`.
4. Refresh on a file with a stale hash returns text where `schema`, `kind` and `hash` are updated and `purpose`, `relates`, `owner` and `verified` are byte-identical to the input; refresh on a file whose block is current returns the input unchanged, not a rewritten equal; checked by `./dev.py test tests/unit/test_meta_block.py`.
5. For a Python file importing `clutch.providers` and `clutch.seams`, with both tracked, `relates` is `[clutch/providers.py, clutch/seams.py]` and `owner` is empty; importing only `clutch.providers` gives `owner` `clutch/providers.py`; an import of an untracked module and the file's own path never appear; for Markdown, a link `[x](other.md)`, a backticked `clutch/seams.py::FileSystem` and a backticked untracked path give `relates` holding the first two only; checked by `./dev.py test tests/unit/test_meta_block.py`.
6. `problems` returns `["missing"]` for a file with no block, `["empty purpose"]` for a current block with empty `purpose`, `["drifted"]` for a nonempty `purpose` with a stale hash, `["empty purpose", "drifted"]` for both, `[]` for a current block with a purpose, and `["malformed block"]` for an unclosed Markdown block, an unknown (eighth) key, a missing one of the seven keys or `schema: clutch.meta/2.0`, whereas `clutch.meta/1.3` parses; checked by `./dev.py test tests/unit/test_meta_block.py`.
7. `managed` with roots `docs/` (kind `plan`) and `tests/` (kind `test`) over tracked paths `docs/a.md`, `docs/b.txt`, `docs/README.md`, `tests/unit/test_x.py`, `tests/fixtures/f.py`, `tests/harness/h.py`, `tickets/t/ticket.md`, `src/c.py` returns exactly `docs/a.md` as `plan`, `tests/unit/test_x.py` as `test`, and the two fixture and harness paths as `fixture`; checked by `./dev.py test tests/unit/test_meta_block.py`.
8. A config with `meta: {paths: [{root: docs/, kind: plan}]}` loads; a config without `meta` loads with `paths == []`; `kind: other`, `root: ""` and an extra key under `meta` each raise `ConfigError`; checked by `./dev.py test tests/unit/test_meta_config.py`.
9. `clutch meta refresh` and `clutch meta check` parse with optional PATH arguments, and `clutch meta` alone exits 2; checked by `./dev.py test tests/unit/test_main_meta_group.py`.
10. With a fake git listing and filesystem, `meta check` over one file without a block prints `path: missing` and exits 1, and over only current files prints nothing and exits 0; `meta refresh` then writes the block and prints `path: inserted`, and a following `meta check` finds only `empty purpose`; a PATH outside the configured roots exits 2 naming the path; empty `meta.paths` prints `meta.paths is empty; nothing to do` and exits 0; refresh with one malformed file still writes the others and exits 2; checked by `./dev.py test tests/unit/test_main_meta_group.py`.
11. Every `meta` command has a description, reads, writes, lock, exit codes and examples, the top-level help lists the group, and the verb tables in `clutch/docs/host-running.md` match the parser; checked by `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py`.
12. `clutch/meta.py` and the new `meta` handler lines in `clutch/__main__.py` are run by the fenced `tests/unit` files, and `clutch/config.py` keeps its `test-gate.toml` floor; checked by `./dev.py test tests/unit`.

## Verification
```
./dev.py test tests/unit/test_meta_block.py tests/unit/test_meta_config.py tests/unit/test_main_meta_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_help.py tests/integration/test_host_contract.py
```

## Definition of rejected
`refresh` writes any file outside `meta.paths`, under `tickets/`, or named `README.md`, `CLAUDE.md` or `AGENTS.md`; `refresh` changes `purpose`, `relates`, `owner` or `verified` of an existing block; `meta.py` performs I/O; a repo file gains a block in this diff; or an eighth block key (beyond `schema`, `kind`, `purpose`, `relates`, `owner`, `verified`, `hash`) is introduced.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one pure module, one config model and one two-verb group with their tests and doc rows; the parser, generators and handlers are small and share one fixture
````
