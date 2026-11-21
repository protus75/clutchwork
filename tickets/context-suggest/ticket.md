---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- index-build-verb-r1
- index-box-neighbors

## Context
- docs/annotations-index-plan.md#6. Consumers
- clutch/index.py::build
- clutch/tickets.py::_sections
- clutch/tickets.py::in_fence
- clutch/tickets.py::context_path
- clutch/__main__.py::_command
- clutch/__main__.py::_run_index
- clutch/__main__.py::_fail
- clutch/docs/host-running.md
- tests/unit/test_host_running.py

## Goal / Why
Roadmap row 73, ticket 5 of `docs/annotations-index-plan.md`, first of two slices. After this ticket `clutch context suggest <stem>` prints, for a drafted ticket, the files and sections the author should consider naming in `## Context`, read from the merged `<state_dir>/index.duckdb`. Today an author (a person or the Author stage) picks Context by memory, so tickets name whole documents or miss the file that past tickets always changed together with their fence. The second slice, row 73's Author prompt data block (the Author prompt spec, its builder and the authoring guide), is a separate boundary and a later ticket `context-suggest-author-block`, which calls the function this ticket creates. This slice ships the query as `clutch/context.py::suggest` and the verb. It uses only the `files`, `chunks` and `touches` tables, so it needs no embed command and no extension; `embeddings` and the `neighbors` function of the unmerged `index-box-neighbors-query` are not used.

Argument, validated by rule: `<stem>` is exactly one positional argument. It must match `tickets.STEM` (`^[a-z0-9][a-z0-9-]{1,63}$`) and not be in `tickets.RESERVED_STEMS`, and `tickets/<stem>/ticket.md` must be a readable UTF-8 file. The verb has no flags; argparse refuses a missing or extra argument with exit 2.

The ticket is read tolerantly, because it is a draft: its body is split into `## ` sections with `tickets._sections` (as `clutch/rework.py` does); it needs a `## Goal / Why` and a `## Scope fence` section, each non-blank, and the fence is read with `tickets._bullets` (backticks stripped). An unfilled skeleton fails here by name, not by lint. `## Context` is optional; its bullets are the entries already named.

Two suggestion lists come from the index, each capped at 5 lines:

1. Co-changed files (`touches`). A past ticket is a `touches.ticket` value other than `<stem>` with at least one `touches.path` for which `tickets.in_fence(path, fence)` is true. A candidate is a distinct `touches.path` of such a past ticket that (a) is a `files.path` row, (b) does not start with `tickets/`, (c) is not in the fence by `in_fence`, and (d) is not already a Context entry's `tickets.context_path`. The score is the count of distinct past tickets that touched both the candidate and some fenced path. Order: score descending, then path ascending (byte order). Reason text: `changed with <fence entry> in <n> past tickets`, where `<fence entry>` is the fence bullet with the most shared past tickets with the candidate, ties broken by the bullet that sorts first, and `<n>` is the score (always `tickets`, even for 1).
2. Matching sections (`chunks`). Terms are the distinct lowercase word tokens (`[a-z0-9_]{4,}`) found inside backtick spans of the Goal text; a Goal with no backtick span has no terms and gives no chunk lines. A chunk is a `chunks` row whose path is a `files.path` row and does not start with `tickets/` or `box:`, whose selector is not already an exact Context entry, and whose lowercased text (the selector is not searched) contains at least 2 distinct terms; its score is that count. Order: score descending, then selector ascending. Reason text: `matches <t1>, <t2>, ...` with up to 5 matched terms in ascending order.

Worked example. Goal backticks `index.build` and `clutch/index.py`: terms are `index`, `build`, `clutch`. Fence `clutch/index.py`. Past tickets A and B changed `clutch/index.py` and `clutch/merge.py`; ticket C changed only `clutch/merge.py`. Co-changed list: `clutch/merge.py` with score 2, reason `changed with clutch/index.py in 2 past tickets`. A chunk `clutch/index.py::build` whose text (not its selector) contains `index` and `build` scores 2 and prints with reason `matches build, index`.

Output (stdout, nothing else). When at least one line exists the verb prints `context suggest: suggested`, then each line as `- <selector>  # <reason>` (two spaces before `#`): co-changed files first (a bare path as selector), then sections (`path#Heading` or `path::Name`). The author deletes the `  # <reason>` tail when pasting a bullet into `## Context`. Selector bytes are exactly the `touches.path` or `chunks.selector` value.

Outcomes are named and closed:

| Outcome | Exit | Stream | Meaning |
|---|---|---|---|
| `suggested` | 0 | stdout | at least one line printed |
| `none` | 0 | stdout | the index has nothing to suggest; prints `context suggest: none` |
| `refused` | 2 | stderr | invalid stem, ticket file missing or not UTF-8, missing or blank Goal or Scope fence section, config error |
| `no_index` | 2 | stderr | `<state_dir>/index.duckdb` does not exist; the road is `run clutch index build` |
| `index_unreadable` | 2 | stderr | the file exists but opening it read-only or querying `files`, `chunks` or `touches` raised `duckdb.Error` (a refresh writing at that instant, or a table the index lacks); the road is `retry after the running refresh finishes, or run clutch index build if the index lacks a table` |

Exit 1 is not used. Every refusal prints `clutch context suggest: <message> -- <what to do instead>`; a config error prints `clutch context: ` per the existing handler. No stack trace. The verb is read-only: no writer lock (it works while `serve` runs; a refresh that is writing at that instant yields `index_unreadable`), no journal event, no git write, no file written. It opens the database read-only through an injectable `connect` argument, and never runs `INSTALL` or `LOAD`. No SQLite file is read or written.

## Boundary contract
### context suggest query
- disposition: create
- owner: clutch/context.py
- consumers: the `context suggest` verb; the later `context-suggest-author-block` ticket
- observable change: new `suggest(conn, stem, fence, context, goal)` returning the two ordered lists above; `_run_context_suggest` passes the validated stem; it runs three SQL reads against an open connection and does no I/O of its own
- compatibility: `clutch/index.py`, the table schemas and every `index build` finding are unchanged
- acceptance: criteria 1-3
- tests: tests/unit/test_context_suggest.py
- post-merge source of truth: clutch/context.py
- closest existing: `index.build` in clutch/index.py writes these tables; no module reads them yet
- earning reason: the row's deliverable; a new module avoids a collision with the confirmed unmerged `index-box-neighbors-query`, which fences `clutch/index.py`

### context suggest verb
- disposition: create
- owner: clutch/__main__.py
- consumers: the operator, authors, and the later Author data block ticket (which calls the query, not the verb)
- observable change: new `context` group with one command `suggest`, outcomes and exits above
- compatibility: no existing verb, flag, exit code or file changes; `help` lists the new group
- acceptance: criteria 4-6
- tests: tests/unit/test_context_suggest_verb.py, tests/integration/test_context_suggest_cli.py
- post-merge source of truth: clutch/__main__.py and `docs/how-clutch-works.md` section 14
- closest existing: `index` group and `_run_index` in clutch/__main__.py
- earning reason: the row names the verb; `_run_index` writes and takes a lock, this one is read-only with other outcomes

### verb documentation
- disposition: extend
- owner: clutch/docs/host-running.md, README.md, docs/how-clutch-works.md
- consumers: operators and `tests/unit/test_host_running.py`
- observable change: one `context suggest` row in the host run guide and in section 2.1, one README sentence, one paragraph in section 14
- compatibility: other rows and sections unchanged
- acceptance: criterion 6
- tests: tests/unit/test_host_running.py (unchanged, must pass), `uv run clutch meta check`
- post-merge source of truth: the three documents

## Scope in / Scope out
Scope in:
- `clutch/context.py` (new): module docstring; `def suggest(conn, stem, fence, context, goal) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]` returning `(files, sections)`, each a list of `(selector, reason)` already capped at 5 and ordered as in Goal; the term extraction and the three queries (parameterized SQL, no string-built SQL). It imports `tickets.in_fence` and `tickets.context_path` and nothing from `clutch/index.py`. It carries no meta header (source files get none).
- `clutch/__main__.py`: a `context` group built like the `index` group (parser `context` with description `Subcommands: suggest.`, help and examples) holding `suggest` created through `_command` (the index is opened with `connect(path, read_only=True)`, the one call the fake `connect` in criterion 4 asserts; ticket and context files are read with `fs.read_bytes` and decoded as UTF-8, since the `FileSystem` seam has no `read_text`) with `summary`, `does`, `reads` (the ticket file and `<state_dir>/index.duckdb`), `writes` (`Nothing; prints suggestions.`), `lock` (`None; read-only, works while serve runs.`), `exits` (`0 suggested or none; 2 refused, no_index or index_unreadable.`) and example `clutch context suggest my-ticket`, plus one positional `stem`; `def _run_context_suggest(config, root, stem, *, fs, connect=duckdb.connect)` that validates, reads, calls `context.suggest`, prints and returns the exit code (`connect` is the test seam; `import duckdb` there); `handle_context` with no lock; a `"context": handle_context` entry in `handlers`.
- `clutch/docs/host-running.md`: one row `context suggest`, `Works while serve runs?` = `Yes`.
- `README.md`: one sentence in the "Run its verbs" paragraph naming `clutch context suggest <stem>`.
- `docs/how-clutch-works.md`: one row `context suggest <stem>` (lock `no`) in the section 2.1 table, and one paragraph appended at the end of section 14 with the two lists, the outcome table above, and the line format. Edit nothing else in the document.
- After the document edits run `uv run clutch meta refresh clutch/docs/host-running.md docs/how-clutch-works.md`; `uv run clutch meta check` must be clean.
- Three new test files, each starting with a `# clutch:meta` header and a NON-EMPTY one-line `# purpose:`: `# purpose: context suggest query over index tables` in `tests/unit/test_context_suggest.py`, `# purpose: context suggest verb outcomes and exit codes` in `tests/unit/test_context_suggest_verb.py`, `# purpose: clutch context suggest end to end through main` in `tests/integration/test_context_suggest_cli.py`; run `uv run clutch meta refresh` on them to generate the other keys.
Scope out: `clutch/index.py` and its tests (the unmerged `index-box-neighbors-query` fences them and adds `neighbors`; this ticket neither calls nor edits it, so either merge order works); `clutch/merge.py`; the Author prompt spec, its builder module and the authoring guide (the Author data block, `context-suggest-author-block`); embeddings and full-text search; `clutch/help.py` and `vscode-clutchwork/` (no extension surface); `clutch/tickets.py`; a `./dev.py` subcommand; flags. `tests/unit/test_host_running.py`, `tests/unit/test_main_help.py` and `tests/unit/test_main_verb_groups.py` read the parser and guide dynamically and pass without edit; none is fenced. `docs/how-clutch-works.md` is shared with other tickets; this one adds one row and one paragraph only.

## Scope fence
- clutch/context.py
- clutch/__main__.py
- clutch/docs/host-running.md
- README.md
- docs/how-clutch-works.md
- tests/unit/test_context_suggest.py
- tests/unit/test_context_suggest_verb.py
- tests/integration/test_context_suggest_cli.py

## Acceptance criteria
1. `tests/unit/test_context_suggest.py` builds an in-memory DuckDB with `files`, `chunks` and `touches` as `index.build` creates them and asserts the Goal's worked example exactly: `suggest` returns files `[("clutch/merge.py", "changed with clutch/index.py in 2 past tickets")]` and sections `[("clutch/index.py::build", "matches build, index")]`; a version that ranks by recency or counts rows instead of distinct tickets fails it. Check: `./dev.py test tests/unit/test_context_suggest.py`.
2. `tests/unit/test_context_suggest.py` asserts the filters: the ticket's own stem is excluded from past tickets; fenced paths, `tickets/` paths, paths missing from `files`, and paths already in Context are not co-changed candidates; `box:` and `tickets/` chunks and exact Context selectors are not section candidates; a chunk with 1 term is dropped and one with 2 is kept; a term found only in a selector and not in the text does not count; a Goal without backticks gives no sections. Check: `./dev.py test tests/unit/test_context_suggest.py`.
3. `tests/unit/test_context_suggest.py` asserts ordering and caps: 7 candidates give 5 lines, ordered by score descending then path (or selector) ascending, with a tie on score broken by path; the reason names the fence bullet with the most shared tickets and, on a tie, the first sorted bullet; more than 5 matched terms print only the first 5 ascending. Check: `./dev.py test tests/unit/test_context_suggest.py`.
4. `tests/unit/test_context_suggest_verb.py` calls `_run_context_suggest` with a fake `fs` and a fake `connect` and asserts every row of the outcome table: `suggested` exit 0 with stdout exactly `context suggest: suggested` then the `- <selector>  # <reason>` lines; `none` exit 0 with stdout `context suggest: none`; `refused` exit 2 for each of: stem `Bad_Stem`, stem `decisions`, missing ticket file, non-UTF-8 file, blank Goal, missing Scope fence; `no_index` when the database path does not exist, with stderr containing `run clutch index build`; `index_unreadable` when `connect` raises `duckdb.Error`, with stderr containing ` -- `; no refusal prints `Traceback`, and a verb that exits 1 anywhere fails it. It also calls `main(["context", "suggest", "demo"], cwd=tmp_path)` with a minimal valid `config.yaml` and `tickets/demo/ticket.md` under `tmp_path` and no index, and asserts exit 2 with `no_index` on stderr, so `handle_context` runs in a unit test. Check: `./dev.py test tests/unit/test_context_suggest_verb.py`.
5. `tests/unit/test_context_suggest_verb.py` asserts the `context` group parses `["context", "suggest", "x"]` with `context_verb == "suggest"`, refuses `["context", "suggest"]`, `["context", "suggest", "a", "b"]` and `["context"]` with SystemExit 2, that the group and `suggest` carry a description, `Reads:`, `Writes:`, `Lock:`, `Exit codes:` and an `Examples:` line `clutch context suggest my-ticket`, and that `format_help()` of the top parser lists `context suggest`. Check: `./dev.py test tests/unit/test_context_suggest_verb.py tests/unit/test_main_help.py`.
6. `tests/integration/test_context_suggest_cli.py` runs `main(["index", "build"], cwd=<git repo>)` with `clutch.index.default_creator` monkeypatched to a fake whose `load` and `create` return `[]`, on a repo with two committed tickets' worth of `clutch-ticket` trailer commits and one draft `tickets/demo/ticket.md`, then `main(["context", "suggest", "demo"], cwd=...)` and asserts exit 0, `context suggest: suggested` on stdout and the expected co-changed line; the same command before any build exits 2 with `no_index`; with the writer lock held by another `Lockfile` it still exits 0; and `<state_dir>/index.duckdb` has the same bytes before and after. Also asserts `clutch/docs/host-running.md` has exactly one `context suggest` row, `docs/how-clutch-works.md` exactly one `context suggest` row in 2.1, and `README.md` contains `clutch context suggest`. Check: `./dev.py test tests/integration/test_context_suggest_cli.py tests/unit/test_host_running.py`.

## Verification
```
./dev.py test tests/unit/test_context_suggest.py tests/unit/test_context_suggest_verb.py tests/integration/test_context_suggest_cli.py tests/unit/test_host_running.py tests/unit/test_main_help.py tests/unit/test_main_verb_groups.py tests/unit/test_index_verb.py
uv run clutch meta check
uv run ruff format --check .
```

## Definition of rejected
The branch is thrown away if any code opens a SQLite file, if `clutch/index.py` or any file outside the Scope fence is edited, if the verb writes any file, takes the writer lock, runs `INSTALL` or `LOAD`, or accepts a flag, if a refusal exits anything but 2 or prints a traceback, if the SQL is built by string formatting, if a new test goes into a hot test file, or if a document describing the verb is left stale.

## Time budget
- expected: 30m
- stuck: 60m
- reason: three boundaries, eight fenced files and six criteria, one small query module over three merged tables; the Author data block is split out so this stays within the budget.
