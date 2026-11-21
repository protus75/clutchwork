---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- index-build-r2
- index-config-touches

## Context
- docs/annotations-index-plan.md#5. The index
- clutch/index.py::build
- clutch/index.py::default_creator
- clutch/__main__.py::_command
- clutch/__main__.py::_run_meta
- clutch/__main__.py::main
- clutch/docs/host-running.md
- tests/unit/test_host_running.py
- tests/unit/test_main_meta_fill.py

## Goal / Why
Roadmap row 182, the verb of ticket 4 of `docs/annotations-index-plan.md`, split from the rejected `index-build-r1` (its diagnosis names this as split 3). After this ticket `clutch index build` exists: it runs the merged `index.build` once over the host checkout and writes `<state_dir>/index.duckdb`, and the three guides that list verbs describe it. Without it the index can only be built by the merge hook, which refreshes a file that already exists and never creates one, so no host can start an index.

The verb takes no arguments: its only inputs are the config (`index.embed` is already validated by `config.Index`) and the checkout, so there is nothing for it to parse. argparse refuses an extra argument with exit 2.

Outcomes are named and closed. `index.build` returns a list of finding strings; the verb takes each finding's prefix as the text before the first `": "` and maps it through one closed table in `clutch/__main__.py`:

| Prefix | Exit | Meaning |
|---|---|---|
| `db_open_failed` | 2 | `index.duckdb` could not be opened; nothing was built |
| `git_failed` | 1 | tracked-file listing or ticket touches failed; the rest was built |
| `embed_failed` | 1 | the `index.embed` command failed; the `embeddings` table was dropped |
| `call_unreadable` | 1 | one evidence call record could not be read; it was skipped |
| `box_unreadable` | 1 | a Suggestion Box file is corrupt (emitted once `index-box-neighbors` merges; mapped now so that merge needs no edit here) |
| `vss unavailable` | 1 | the DuckDB `vss` extension could not load or index |
| `fts unavailable` | 1 | the DuckDB `fts` extension could not load or index |

The verb's exit is the highest exit among its findings. Outcome names and exits: `built` (no findings, exit 0, prints `index build: built`), `built_with_findings` (findings all mapped to 1, exit 1, prints `index build: built_with_findings` then one line per finding), `not_built` (a `db_open_failed` finding, or a finding whose prefix is not in the table, exit 2, refusal line via `_fail`; an unmapped prefix is a fail-closed refusal, never exit 0 or 1), and `refused` (config error, writer lock held, exit 2, through the existing refusal handler). Output goes to stdout, refusals to stderr as `clutch index build: <message> -- <what to do instead>`.

The verb takes the writer lock (it writes `index.duckdb`, which the merge hook also writes under the engine's lock), so it refuses while `serve` or `drain` runs, and it passes `creator=index.default_creator` (the one that runs `INSTALL`; the merge hook's load-only creator is a different object in `clutch/merge.py`). It passes `env=child_env(env, config, serving=None)` so no provider key reaches the embed command. It reads no SQLite file and opens only DuckDB through `build`.

Ordering with unmerged confirmed tickets. `index-box-neighbors` (fences `clutch/index.py`, `tests/unit/test_index_sources.py`, `tests/integration/test_index_sources_scan.py`) keeps `build`'s signature and only adds `box_unreadable`; this ticket calls `build` as it is and maps that prefix already, so either merge order works. `index-merge-hook` (fences `clutch/merge.py` and its tests) neither calls nor is called by the verb; this ticket fences none of those files. `docs/how-clutch-works.md` is shared with other tickets; this ticket appends one section last and adds one row in 2.1.

## Boundary contract
### index build verb
- disposition: create
- owner: clutch/__main__.py
- consumers: the operator, tickets and guides that name the verb; later `context-suggest` and the merge hook assume the file this verb creates
- observable change: new `clutch index build` verb in a new `index` group, with the outcomes and exit codes in Goal; one file `<state_dir>/index.duckdb` created or refreshed; no journal event, no git write
- compatibility: no existing verb, flag, exit code or file changes; `help` lists the new group; the writer lock rules are unchanged
- acceptance: criteria 1-6
- tests: tests/unit/test_index_verb.py, tests/integration/test_index_cli.py
- post-merge source of truth: clutch/__main__.py and `docs/how-clutch-works.md` section 14
- closest existing: `meta` group handler `_run_meta` and `handle_meta` in clutch/__main__.py
- earning reason: the verb is the row's deliverable and the only way to create the index file; `_run_meta` serves a different engine (metadata blocks) and exit table, and `index.build` itself stays untouched in `clutch/index.py`

### index.build
- disposition: reuse
- owner: clutch/index.py
- consumers: the verb calls `build(config, root, fs=, git=, exec_=, env=, store=, creator=)` as merged
- observable change: none
- compatibility: signature, tables and findings unchanged
- acceptance: criteria 1-3 call it through the verb seam
- tests: tests/unit/test_index_verb.py, tests/integration/test_index_cli.py
- post-merge source of truth: clutch/index.py

### Verb documentation
- disposition: extend
- owner: clutch/docs/host-running.md, README.md, docs/how-clutch-works.md
- consumers: operators and `tests/unit/test_host_running.py`
- observable change: one `index build` row in the host run guide verb table and in section 2.1, a sentence in README, and a new last section 14 "Project index"
- compatibility: other rows and sections unchanged
- acceptance: criteria 5-6
- tests: tests/unit/test_host_running.py (unchanged, must pass), `uv run clutch meta check`
- post-merge source of truth: the three documents

## Scope in / Scope out
Scope in:
- `clutch/__main__.py`: an `index` group (parser `index` with description listing the subcommand, summary, and examples, built like the `meta` group) holding one command `build` created through `_command` with `summary`, `does`, `reads` (config, tracked files, git history, evidence store, Suggestion Box, the `index.embed` command's output), `writes` (`<state_dir>/index.duckdb`), `lock` (writer lock), `exits` (`0` built; `1` built with findings; `2` not built or refused) and an example `clutch index build`; one module constant holding the prefix-to-exit table above; `async def _run_index(config, root, *, fs, git, exec_, env, store, creator, build=index.build)` that calls `build` with `env=child_env(env, config, serving=None)`, prints per Goal and returns the exit code (the injectable `build` is the seam through which `tests/unit/test_index_verb.py` runs these lines with a fake and no disk or process); `handle_index` that takes the writer lock with `_locked(config.state_dir, "index build", ...)` and calls `_run_index` with `creator=index.default_creator` and an `EvidenceStore` built as `handle_evidence` builds it; an `"index": handle_index` entry in `handlers`; the imports they need (`from clutch import index` inside the handler or at module level, whichever avoids an import cycle; `EvidenceStore` is already imported where used).
- `clutch/docs/host-running.md`: add the row `index build` with `Works while serve runs?` = `No` (it needs the writer lock) in the verb table. `tests/unit/test_host_running.py` requires the row and the parser to match, and passes unchanged.
- `README.md`: one sentence in the "Run its verbs" paragraph naming `clutch index build`.
- `docs/how-clutch-works.md`: add the row `index build` (lock yes) in the section 2.1 table, and append a new last section `## 14. Project index` (after section 13) describing what the index is, `<state_dir>/index.duckdb` as a rebuildable cache never read by a gate or dispatch, the five tables, that the verb builds it (outcome and exit table from Goal), that a merge refreshes an existing file (`index-merge-hook`), and that `index.embed` unset means no `embeddings` table. Edit nothing else in the document.
- After the document edits run `uv run clutch meta refresh clutch/docs/host-running.md docs/how-clutch-works.md` so their block hashes match, and `uv run clutch meta check` must be clean.
- New tests, both starting with a `# clutch:meta` header with a NON-EMPTY one-line `# purpose:` (`# purpose: index build verb outcomes and exit codes` in `tests/unit/test_index_verb.py`, `# purpose: clutch index build end to end through main` in `tests/integration/test_index_cli.py`); run `uv run clutch meta refresh` on the two files to generate the other keys.
Scope out: `clutch/index.py`, `clutch/merge.py` and their tests (other tickets); any change to `index.build`'s behavior or findings; `clutch/help.py` (the extension shows no `index` surface); `vscode-clutchwork/`; a `./dev.py` subcommand; arguments or flags on the verb; `context suggest` (a later row). Tests that pin verb sets by reading the parser or the guide (`tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_main_meta_group.py`) are dynamic and pass without edit; none is fenced.

## Scope fence
- clutch/__main__.py
- clutch/docs/host-running.md
- README.md
- docs/how-clutch-works.md
- tests/unit/test_index_verb.py
- tests/integration/test_index_cli.py

## Acceptance criteria
1. `tests/unit/test_index_verb.py` calls `_run_index` with a fake `build` returning `[]` and asserts exit 0 and stdout exactly `index build: built\n`; a fake returning `["git_failed: x", "call_unreadable: k"]` gives exit 1 and stdout `index build: built_with_findings` followed by both lines; a verb that returns 0 for findings fails it. Check: `./dev.py test tests/unit/test_index_verb.py`.
2. `tests/unit/test_index_verb.py` parametrizes every prefix in Goal's table (`db_open_failed`, `git_failed`, `embed_failed`, `call_unreadable`, `box_unreadable`, `vss unavailable`, `fts unavailable`) and asserts its exit equals the table (2 for `db_open_failed`, 1 for the rest), that a mix of a 1 and a 2 gives 2, and that a finding `mystery: x` and a finding with no `": "` give exit 2 and a refusal on stderr naming the finding, not 0 or 1. Check: `./dev.py test tests/unit/test_index_verb.py`.
3. `tests/unit/test_index_verb.py` asserts `_run_index` passes `build` the exact keyword set `fs, git, exec_, env, store, creator` with `creator` the object it was given, and that the `env` `build` received has the configured provider secret names removed (a config with a provider `auth` env var set in the `env` argument does not appear in what `build` received); passing the raw env fails it. Check: `./dev.py test tests/unit/test_index_verb.py`.
4. `tests/unit/test_index_verb.py` asserts the `index` group parses `["index", "build"]` with `index_verb == "build"`, refuses `["index", "build", "extra"]` and `["index"]` with SystemExit 2, that the group and `build` carry a description, `Reads:`, `Writes:`, `Lock:`, `Exit codes:` and an `Examples:` line `clutch index build`, and that `format_help()` of the top parser lists `index build`. Check: `./dev.py test tests/unit/test_index_verb.py tests/unit/test_main_help.py`.
5. `tests/integration/test_index_cli.py` monkeypatches `clutch.index.default_creator` with a fake whose `load` and `create` record their calls and return `[]` (so no `INSTALL` or network runs; `handle_index` reads `index.default_creator` when it runs, not at import), then runs `main(["index", "build"], cwd=<git repo with one tracked .md file>)` with `index.embed` unset and asserts exit 0, `<state_dir>/index.duckdb` exists and its `files` table (read with `duckdb`) has a row for that file; the fake's `load` was called (the handler passed `index.default_creator`); a second run exits 0; with the writer lock held by another `Lockfile` it exits 2 with stderr starting `clutch index build: ` and containing ` -- `; an exit 0 with no file, or a run under a held lock that exits 0, fails it. Check: `./dev.py test tests/integration/test_index_cli.py`.
6. `tests/unit/test_host_running.py` and `tests/unit/test_main_help.py` pass unchanged with the new group; `clutch/docs/host-running.md` has exactly one `index build` row, `docs/how-clutch-works.md` has exactly one `index build` row in 2.1 and its last `## ` heading is `## 14. Project index`; `README.md` contains `clutch index build`. Check: `./dev.py test tests/unit/test_host_running.py tests/unit/test_main_help.py` and `uv run clutch meta check`.

## Verification
```
./dev.py test tests/unit/test_index_verb.py tests/integration/test_index_cli.py tests/unit/test_host_running.py tests/unit/test_main_help.py tests/unit/test_main_meta_group.py tests/unit/test_main_verb_groups.py tests/unit/test_index_build.py
uv run clutch meta check
uv run ruff format --check .
```

## Definition of rejected
The branch is thrown away if any code opens a SQLite file, if `clutch/index.py` or any file outside the Scope fence is edited, if the verb accepts an argument or flag, if an unmapped finding prefix exits 0 or 1, if the verb runs without the writer lock, if the provider key reaches the embed command, if a new test goes into `tests/integration/test_cli.py` or another hot file, or if a document describing the verb is left stale.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one command, one handler, three document edits and two test files; the core build and its tests are already merged, so no further split earns its overhead.
