---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- docs/annotations-index-plan.md
- clutch/seams.py::FileSystem
- clutch/git.py::Git.ls_files
- clutch/git.py::Git.rev_parse
- clutch/config.py::TrainingData
- clutch/specs/__init__.py::_FRONTMATTER

## On-demand
- clutch/__main__.py

## Goal / Why
Roadmap row 69, ticket 1 of `docs/annotations-index-plan.md`. After this ticket a Markdown or Python file under a configured root can carry a `clutch.meta/1.0` block, and `clutch meta refresh` and `clutch meta check` maintain and report on it. This repo's `config.yaml` names the roots `docs/`, `clutch/docs/` and `tests/`; annotating the files under them is split into the shard tickets `meta-annotate-docs-support`, `meta-annotate-tests-unit-a`, `meta-annotate-tests-unit-b`, `meta-annotate-tests-integration-a` and `meta-annotate-tests-integration-b`, because the first attempt inserted 5512 lines and failed the 1500-line diff budget.

Key count, stated once so every section agrees: a block is one version line, `schema: clutch.meta/1.0`, plus exactly six keys: `kind`, `purpose`, `relates`, `owner`, `verified`, `hash`. That is seven lines in the block. A seventh key (an eighth line) is refused.

Block shapes:
- Markdown: an HTML comment `<!-- clutch:meta` ... `-->` at the top of the file. When the file opens with a `---` frontmatter fence, the block goes right after the closing fence, so frontmatter stays at byte 0.
- Python: a contiguous run of `# clutch:meta` comment lines (header line, then `# schema: ...` and the six `# key: value` lines) placed after the module docstring, or at the top when there is none.

Rules:
- `kind` is closed: `doc`, `guide`, `spec`, `test`, `fixture`, `plan`. It comes from the `meta.paths` root; a `tests/` file under a `fixtures/` or `harness/` directory takes `fixture`.
- `purpose` is free text, one line; refresh inserts it empty and never edits it.
- `relates` is a list of repo paths that exist in the tracked file list. For a Python file the generated line (`# relates: [...]`) is at most 160 characters: entries are sorted and trailing entries that do not fit are left out, so no block needs a ruff line-length exemption (the project line length is 200). Refresh generates it only when the block's list is empty: for a Python file from its imports of repo modules, for Markdown from relative links and `path::` selectors. A non-empty list is never rewritten.
- `owner` is generated only when empty: the one `relates` module that more than half of the entries share, else `engine`.
- `verified` is the first 8 characters of the commit sha, stamped when refresh inserts a block or changes `hash`.
- `hash` is the SHA-256 of the file bytes with the block (and its line break) removed.

`clutch/specs/` is left out of this repo's `meta.paths` in v1: twelve spec files open with YAML frontmatter that `_FRONTMATTER` in `clutch/specs/__init__.py` must match at byte 0, and spec bodies are model prompt text under a line cap. This is a stated departure from the plan's default root list, not work promised elsewhere.

Why: nothing says what a document or test is for or what it relates to; the plan's later index and context features need this block first.

## Boundary contract
### Meta block format and verbs
- disposition: create
- owner: clutch/meta.py
- consumers: `clutch meta refresh`, `clutch meta check`, and their unit and integration tests
- observable change: files under `meta.paths` gain blocks; `meta refresh` writes them and `meta check` lists files with `missing`, `empty_purpose` or `drifted` and exits 1 when any
- compatibility: files outside `meta.paths` and non-`.md`/`.py` files are never read or written; `meta.paths: []` means nothing is expected, so existing configs load unchanged
- acceptance: parser, hash, generated fields, idempotent refresh and check findings are covered by `tests/unit/test_meta_block.py` and `tests/unit/test_meta_refresh.py`
- tests: `tests/unit/test_meta_block.py`, `tests/unit/test_meta_refresh.py`, `tests/unit/test_meta_cli.py`
- post-merge source of truth: clutch/meta.py
- closest existing: `clutch/tickets.py` frontmatter parser reads ticket files only and has no hash or comment-block form; `clutch/hostfiles.py` managed-block rendering is for agent rule files, not per-file metadata
- earning reason: two production consumers (refresh and check) share the parser and hash, and the plan's later gate and index reuse them; the format is a new storage format
- failure and side effects: refresh writes only through the `FileSystem` seam; a malformed block (unknown key, extra key, bad `kind`, missing `schema`) is reported by check as `malformed` and refused by refresh with exit 2 without writing that file
- seam: `meta.py` functions take the tracked file list, the commit sha string and a `FileSystem`; they start no process

### Meta config
- disposition: extend
- owner: clutch/config.py
- consumers: `clutch/meta.py` callers in `clutch/__main__.py`, `clutch/docs/host-contract.md` inventory
- observable change: new `meta.paths` list of `{root, kind}` entries with `kind` in the closed set; default `[]`
- compatibility: configs without `meta` load unchanged
- acceptance: `Config` with no `meta` key has `meta.paths == []`; an unknown `kind` is refused
- tests: `tests/unit/test_meta_config.py`
- post-merge source of truth: clutch/config.py

### Meta command group
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators and `clutch help`
- observable change: new top-level group `meta` with subcommands `refresh` and `check`, each with `_command` help and examples; handler `_run_meta` takes config, root, `FileSystem`, tracked files and sha as parameters; `handle_meta` only resolves files with `Git.ls_files` and the sha with `Git.rev_parse` on HEAD and calls it
- compatibility: existing verbs and groups are unchanged
- acceptance: `main` parses `meta refresh` and `meta check`; `_run_meta` returns 0, 1 or 2 as documented
- tests: `tests/unit/test_meta_cli.py`, `tests/unit/test_main_meta_group.py`
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- New `clutch/meta.py`: block parser and writer for Markdown and Python, hash, generated fields, `refresh(...)` and `check(...)` taking the tracked file list, sha and `FileSystem`.
- `clutch/config.py`: `Meta` model and `meta` field on `Config`, beside `training_data`. `tests/unit/test_meta_config.py` runs these lines.
- `clutch/__main__.py`: `meta` group with `refresh` and `check`, `_run_meta`, `handle_meta`, group listing in help. Both verbs take optional `paths` that narrow to files under `meta.paths`. Refresh takes the writer lock; check takes none. `tests/unit/test_meta_cli.py` and `tests/unit/test_main_meta_group.py` run these lines through the injected parameters, with no process.
- `config.yaml`: `meta.paths` with `docs/` as `plan`, `clutch/docs/` as `guide`, `tests/` as `test`.
- Docs, same change: `README.md` and the verb tables in `docs/how-clutch-works.md` section 2 and `clutch/docs/host-running.md` add the `meta` verbs; `docs/how-clutch-works.md` config table and `clutch/docs/host-contract.md` inventory add `meta`.

Scope out: running `clutch meta refresh` over the repo (the five `meta-annotate-*` shard tickets named in Goal / Why do that), `meta fill`, a `meta` model surface, the `meta_drift` gate, Check-time refresh, the index and `index` config, `context suggest`, annotating `clutch/specs/`, other root-level documents, ticket files and source files outside `tests/`.

## Scope fence
- clutch/meta.py
- clutch/config.py
- clutch/__main__.py
- config.yaml
- README.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- tests/unit/test_meta_block.py
- tests/unit/test_meta_refresh.py
- tests/unit/test_meta_cli.py
- tests/unit/test_meta_config.py
- tests/unit/test_main_meta_group.py

## Acceptance criteria
1. Parsing a Markdown block and a Python block with the seven lines yields `schema == "clutch.meta/1.0"` and the six keys; a block with an eighth key is reported `malformed`, not accepted. Check: `./dev.py test tests/unit/test_meta_block.py`.
2. The hash of a file equals SHA-256 of its bytes with the block removed, and changing only block text leaves it unchanged while changing body text changes it. Check: `./dev.py test tests/unit/test_meta_block.py`.
3. A Markdown file opening with `---` frontmatter gets its block after the closing fence and still starts with `---\n`; a Python file with a docstring gets the block after the docstring. Check: `./dev.py test tests/unit/test_meta_refresh.py`.
4. `refresh` inserts a block with `purpose` empty, never changes a non-empty `purpose`, `relates` or `owner`, and a second `refresh` with the same sha writes nothing (the returned changed list is `[]`, not the file list). Check: `./dev.py test tests/unit/test_meta_refresh.py`.
5. `check` returns `missing` for a file without a block, `empty_purpose` for an empty purpose and `drifted` for a hash mismatch, and `_run_meta` returns 1 when any finding exists and 0 when none, with a fixed sha and a fake `FileSystem`, no process started. Check: `./dev.py test tests/unit/test_meta_cli.py`.
6. `relates` entries that do not exist in the tracked file list are dropped, and `kind` follows the root with `fixture` under `fixtures/` or `harness/` in `tests/`. Check: `./dev.py test tests/unit/test_meta_refresh.py`.
7. `Config` with no `meta` key has `meta.paths == []`, and a `kind` outside the closed six is refused. Check: `./dev.py test tests/unit/test_meta_config.py`.
8. `clutch meta` appears in the help group list with description and examples for both subcommands. Check: `./dev.py test tests/unit/test_main_meta_group.py tests/unit/test_main_help.py`.
9. `config.yaml` sets `meta.paths` to the three roots with kinds `plan`, `guide` and `test`, and the repo loads, so `uv run clutch meta check tests/unit/test_meta_block.py` runs and reports `missing` for that unannotated file, not an error; `docs/roadmap.md` still parses with `parse` and `choose`. No repo-wide freshness test is added: annotating the files and any `meta_drift` gate belong to later tickets. Check: `./dev.py test tests/unit/test_meta_config.py tests/integration/test_roadmap_table.py`.
10. A Python file whose imports would generate more than 160 characters of `relates` gets a `# relates:` line of at most 160 characters made of the sorted leading entries, never a longer one. Check: `./dev.py test tests/unit/test_meta_refresh.py`.
11. Every shipped spec still loads: `./dev.py test tests/unit/test_specs.py`.

## Verification
```
./dev.py test tests/unit/test_meta_block.py tests/unit/test_meta_refresh.py tests/unit/test_meta_cli.py tests/unit/test_meta_config.py tests/unit/test_main_meta_group.py tests/unit/test_main_help.py tests/unit/test_specs.py tests/integration/test_roadmap_table.py
./dev.py test
```

## Definition of rejected
A block key beyond `schema` plus the six listed keys; any edit under `clutch/specs/`; `refresh` changing a non-empty `purpose`; a meta unit test that starts a process; a second `refresh` that rewrites files; any file under `docs/`, `clutch/docs/` or `tests/` annotated by this ticket, a diff over 1499 inserted lines, or any existing test left failing.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one new module plus a repo-wide mechanical refresh whose output is the proof; the pieces cannot merge separately.
