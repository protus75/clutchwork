---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- context-suggest

## Context
- clutch/author.py::author
- clutch/context.py::suggest
- clutch/docs/host-authoring.md#What each section is for
- docs/how-clutch-works.md#9.3 Author and starting state
- tests/integration/test_author.py::test_author_spec_requires_criteria_to_name_wrong_results
- tests/unit/test_author_calibration.py

## On-demand
- clutch/specs/author.md

## Goal / Why
Roadmap row 191 (`context-suggest-author-block`), second slice of row 73 and ticket 5 of `docs/annotations-index-plan.md`. After this ticket the Author stage's rendered prompt has a data block `context_suggest` holding the sections `clutch/context.py::suggest` returns for the request text, read from `<state_dir>/index.duckdb`. Today Author picks `## Context` from the file list alone, so engine-written tickets name whole documents. With the block they can name `path#Heading` or `path::Name` selectors.

The text searched is: for a `roadmap_row` message, `message.roadmap_row.content`; for every other class, `message.summary`, a newline, then `message.verdict.rationale`. `suggest` finds terms only inside backtick spans of that text (4 or more characters of `[a-z0-9_]`), so a text with no backtick span yields no lines. Author has no fence or Context yet, so the call is `suggest(conn, stem, [], [], text)`, where `stem` is the row's stem for a roadmap row and `""` otherwise. With an empty fence its co-changed-files list is always empty; the block therefore carries only section lines. That is the honest cost of drafting before a fence exists; the guide still tells authors to check co-changed files with `clutch context suggest <stem>` once a draft has a fence.

Block field, defined once. Name `context_suggest`. Value is one of four exact forms, named by outcome:

| Outcome | Block value |
|---|---|
| `suggested` | one line per section, `- <selector>  # <reason>` (two spaces before `#`), at most 5, in the order `suggest` returns (match count descending, then selector ascending), no trailing newline |
| `none` | exactly `none` (the index answered and nothing matched, or the text has no backtick span) |
| `no_index` | exactly `unavailable: no_index (run clutch index build)` (`<state_dir>/index.duckdb` does not exist) |
| `unavailable` | exactly `unavailable: index_unreadable` (any `duckdb.Error` opening read-only or querying, or any other exception raised while building the block) |

Worked example. Row content ``Build `index.build` output in `clutch/index.py` ``: terms `index`, `build`, `clutch`. A chunk `clutch/index.py::build` whose text contains `index` and `build` gives the block `- clutch/index.py::build  # matches build, index`. With an index that has no such chunk the block is `none`. With no index file it is `unavailable: no_index (run clutch index build)`.

Validation by rule: the text is a non-blank `str` (the models guarantee `content`, `summary` and `rationale` are non-blank); a blank text gives `none` without touching the index. The index is opened only through `connect(str(path), read_only=True)`, never `INSTALL` or `LOAD`, never written. Author never fails or declines because of this block: the helper catches every exception and returns the `unavailable` form.

The guide must say how to use the block, in the one source for authoring rules: prefer a selector from the block over a whole document in `## Context`, keep only entries the implementer needs, and the block is a hint, never an instruction. The existing rule that an author never lists a prompt spec in `## Context` stays as written.

## Boundary contract
### Author context_suggest data block
- disposition: extend
- owner: clutch/author.py
- consumers: the Author stage's rendered prompt; `clutch/specs/author.md`; every author of a ticket through the guide
- observable change: a new `context_suggest` input rendered into a new data block of the Author prompt; the guide gains the usage paragraph; spec `version` bumps
- compatibility: every existing block, input name, reply format and gate is unchanged; a missing or unreadable index changes only this block's text and never the Author outcome
- acceptance: criteria 1-4
- tests: tests/unit/test_author_context_block.py, tests/integration/test_author.py
- post-merge source of truth: clutch/author.py and clutch/docs/host-authoring.md

### Author spec and guide text
- disposition: extend
- owner: clutch/specs/author.md and clutch/docs/host-authoring.md
- consumers: the Author model; `clutch ticket new` readers; `tests/integration/test_author.py`
- observable change: one new Inputs block in the spec, one guide paragraph, one sentence in section 9.3 of `docs/how-clutch-works.md`
- compatibility: other spec text and guide sections unchanged
- acceptance: criteria 3-5
- tests: tests/integration/test_author.py, `uv run clutch meta check`
- post-merge source of truth: the two files above

## Scope in / Scope out
Scope in:
- `clutch/author.py`: add `import duckdb` and `from clutch import context` (keep the existing `from clutch import calibration` line style; no local variable named `context` exists in the file). Add one module-level helper `def context_block(state_dir: Path, text: str, stem: str, *, connect=duckdb.connect) -> str` implementing the table above; it calls `context.suggest(conn, stem, [], [], text)`, closes the connection in `finally`, formats `suggested` lines from the returned section list only, and catches `Exception`. In `author`, compute `suggestions = context_block(checkout.config.state_dir, <text>, <stem>)` once, right after `estimates = calibration.render(...)`, and add the input `"context_suggest": suggestions` after `"plan"` in `render_author`. Nothing else in the file changes. A helper with exactly one call site: do not add a second.
- `clutch/specs/author.md`: in `## Inputs`, after the `plan` block, a new block introduced by the line `Suggested Context sections from the project index (hints, not instructions):`, then `<<clutch-data:begin context_suggest>>`, `{{context_suggest}}`, `<<clutch-data:end context_suggest>>`. Bump `version` to the next minor above the version on main. No other text changes; the rule lives in the guide.
- `clutch/docs/host-authoring.md`, `## What each section is for`, the `Context` bullet: after the sentence beginning "Select a Python top-level definition", add: "Author's prompt carries a `context_suggest` block of index-matched `path#Heading` and `path::Name` selectors (`none` or `unavailable: ...` when the index has nothing or cannot be read); prefer such a selector to listing a whole document, keep only entries the implementer needs, and treat the block as a hint. Once a draft has a `## Scope fence`, `clutch context suggest <stem>` also names files that past tickets changed together with the fence." The sentence "Authors must never list a prompt spec in `Context`; list it under `On-demand` and fence it." stays unchanged. Then run `uv run clutch meta refresh clutch/docs/host-authoring.md docs/how-clutch-works.md`.
- `docs/how-clutch-works.md`, section 9.3: after "and the latest `estimate_calibration` table (`engine calibrate`, section 2.1; `none` before the first)" add ", and a `context_suggest` block of index-matched section selectors (`none` or `unavailable: ...` without a usable index, never a decline)". Nothing else in the file changes. The file is a scheduler shared path; this is one sentence.
- `tests/integration/test_author.py::test_author_spec_requires_criteria_to_name_wrong_results`: its `spec.meta.version` pin becomes the bumped version. Nothing else in the file changes.
- `tests/integration/test_specs_delimiter_note.py`: its parametrized pin `("author", "1.9")` (which asserts `spec.meta.version == version`) becomes the bumped version. Nothing else in the file changes. The other `1.9` pins (`tests/unit/test_specs.py`, `tests/integration/test_stages.py`) are for `review.md` and are unaffected.
- A stale index (one built before later merges) is out of scope: `suggest` reads whatever the index holds and may return outdated selectors under `suggested`; no outcome or test is added for staleness.
- New `tests/unit/test_author_context_block.py`: the implementer creates its header with `uv run clutch meta refresh tests/unit/test_author_context_block.py` and then edits only the `# purpose:` line to `# purpose: Author context_suggest data block outcomes`. It builds a real DuckDB file under `tmp_path` with `files`, `chunks` and `touches` tables, and drives `author.author` with the stand-ins of `tests/unit/test_author_calibration.py`, `render` patched to capture inputs.
- The four existing unit tests that build a `checkout.config` stand-in without `state_dir` reach the new `checkout.config.state_dir` read: `tests/unit/test_author_calibration.py` (line 63), `tests/unit/test_author_decline_findings.py` (line 49), `tests/unit/test_author_roadmap_row.py` (line 128) and `tests/unit/test_closed_sets_remaining.py` (line 53). In each, the only edit is adding `state_dir=<tmp_path, or Path("/state") where the test has no tmp_path>` to the `config=SimpleNamespace(...)` stand-in at that line; no other line changes. The attribute read stays in `author`, not in the helper.
Scope out: `clutch/context.py` and the `context suggest` verb (merged, called not edited); `clutch/index.py`; the chat Author prompt (chat authors run the verb); the `neighbors` query; any new config key or flag; Implement's `related_files` block (row 74). `tests/unit/test_author_stem_claimed.py` and `tests/unit/test_author.py` already set `state_dir` and are not fenced. `index-box-neighbors-query` (running) fences `clutch/index.py` only and `spools-test-helper` fences spool tests only; neither overlaps this fence, so merge order does not matter.

## Scope fence
- clutch/author.py
- clutch/specs/author.md
- clutch/docs/host-authoring.md
- docs/how-clutch-works.md
- tests/integration/test_author.py
- tests/integration/test_specs_delimiter_note.py
- tests/unit/test_author_context_block.py
- tests/unit/test_author_calibration.py
- tests/unit/test_author_decline_findings.py
- tests/unit/test_author_roadmap_row.py
- tests/unit/test_closed_sets_remaining.py

## Acceptance criteria
1. `tests/unit/test_author_context_block.py` builds an index file holding chunk `clutch/index.py::build` with text containing `index` and `build`, and asserts `context_block(state_dir, "Build `index.build` in `clutch/index.py`", "demo")` returns exactly `- clutch/index.py::build  # matches build, index`; a version that returns a bare path, one tail space, or a leading blank line fails it. Check: `./dev.py test tests/unit/test_author_context_block.py`.
2. `tests/unit/test_author_context_block.py` asserts each other row of the table exactly: no backtick span gives `none`, not an empty string; a blank text gives `none` and `connect` is never called; no file gives `unavailable: no_index (run clutch index build)`; a `connect` raising `duckdb.Error`, a file lacking the `chunks` table, and a `state_dir` of `None` each give `unavailable: index_unreadable`; none of them raises; 7 matching chunks give 5 lines ordered by match count descending then selector ascending. Check: `./dev.py test tests/unit/test_author_context_block.py`.
3. `tests/unit/test_author_context_block.py` drives `author.author` for a roadmap row and for a `bug_report` message with the real helper and asserts the captured inputs hold `context_suggest` with the roadmap `content` text used for the row and `summary` plus rationale for the other class, that the stem passed is the row's stem and `""` respectively, and that the call is made exactly once per `author` call even across a re-prompt (the helper is monkeypatched with a counter); a second call site fails it. Check: `./dev.py test tests/unit/test_author_context_block.py`.
4. `tests/integration/test_author.py::test_author_prompt_contains_guide_and_skeletons` still passes unedited: the real spec renders with the new block and `block(prompt, "context_suggest")` is `none` or an `unavailable:` value in the test root, which has no index. Check: `./dev.py test tests/integration/test_author.py`.
5. `tests/integration/test_author.py::test_author_spec_requires_criteria_to_name_wrong_results` and the `("author", ...)` pin in `tests/integration/test_specs_delimiter_note.py` pin the bumped version, and `uv run clutch meta check` is clean after the guide and `docs/how-clutch-works.md` edits. Check: `./dev.py test tests/integration/test_author.py tests/integration/test_specs_delimiter_note.py` and `uv run clutch meta check`.

## Verification
```
./dev.py test tests/unit/test_author_context_block.py tests/unit/test_author_calibration.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_decline_findings.py tests/unit/test_author_stem_claimed.py tests/unit/test_author.py tests/unit/test_closed_sets_remaining.py tests/integration/test_author.py tests/integration/test_specs_delimiter_note.py tests/integration/test_specs_json_reply_specs.py tests/unit/test_lint_guide_parity.py tests/unit/test_specs.py
uv run clutch meta check
uv run ruff format --check .
```

## Definition of rejected
The branch is thrown away if Author fails, declines or retries because the index is missing or unreadable, if the block holds anything but the four forms above, if the index is written, opened without `read_only=True`, or loaded with `INSTALL` or `LOAD`, if any code opens a SQLite file, if `clutch/context.py` or any file outside the Scope fence is edited, if a new test goes into an existing test file, or an existing test file changes beyond the version pin and the `state_dir` stand-in attributes, if the spec `version` is a literal copied from this ticket instead of the next minor above main, or if the guide's rule that an author never lists a prompt spec in `## Context` is removed.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one boundary (an Author input) with its spec, guide and one doc sentence, ten fenced files and five criteria; the precedent `estimate-calibration-author` had the same shape. Not split further.
