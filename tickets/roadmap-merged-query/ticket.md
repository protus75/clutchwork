---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- roadmap-table-parser
- roadmap-author

## Context
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/status.py::SETTLED
- clutch/status.py::last_states
- clutch/tickets.py::INTAKE_SIGNAL
- clutch/tickets.py::Frontmatter
- clutch/tickets.py::stem_findings
- clutch/git.py::Git.rev_parse
- clutch/runner.py::Refusal
- tests/unit/test_release.py::test_main_release_locks_calls_and_prints
- tests/unit/test_retro_recurrence.py::MemoryJournal
- tests/integration/test_release.py::repository
- tests/integration/test_cli.py::ENV
- tests/integration/test_cli.py::CONFIG
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1
- docs/roadmap-driver-plan.md#4.

## Goal / Why
The owner decided on 2026-11-16 that no release gate is a person's judgment: every gate in `docs/roadmap.md` is one or more argv commands that exit 0 when the release may ship (`docs/roadmap.md` section 6, the "No human in the loop" decision; roadmap row 91 `release-gates-as-commands`). The ship gates in roadmap section 1 are mostly facts about merged tickets: "every P0 and P1 row merged", "`docs-truth-sweep` merged", "the driver has authored and run at least three roadmap rows on this repo with no operator verdict". No clutch verb can answer any of those with an exit code. `clutch status` prints the journal projection and always exits 0, and nothing counts the tickets merged since a release's tag.

A phase is tagged at its start (`docs/roadmap.md` section 1, as `roadmap-plan-corrections` rewrites it: tag `v0.3.0` opened 0.3.0), and every ticket merge on main is a first-parent commit carrying a `clutch-ticket: <stem>` trailer (for example `git log --first-parent --format='%(trailers:key=clutch-ticket,valueonly)' v0.3.0..HEAD` lists the 11 stems merged in the current phase at HEAD `865f648f`). Author records where each ticket came from in its `ticket_intake` signal (`source: box:<class>`), and `roadmap-row-message` makes a roadmap row's ticket `source: box:roadmap_row`.

This ticket adds the one read-only query the gate blocks need (`release-gates-as-commands` writes the blocks and their runner; this is the split's first part). After this change, `uv run clutch roadmap merged [STEM ...] [--release NAME [--priority P ...]] [--since TAG --at-least N [--source SOURCE] [--unattended]]`:
1. checks that every named STEM is settled in the journal (`merged` or `already_satisfied`);
2. with `--release NAME`, checks that every master-table row of that release (filtered by `--priority`) is struck or settled, where a row split into several tickets settles only when its own stem and every stem in its `**Authored**` list have settled (the rule `roadmap-table-parser`'s `choose` strikes by);
3. with `--since TAG --at-least N`, counts the distinct stems merged on main after tag TAG (first-parent `clutch-ticket:` trailers in `TAG..HEAD`), keeping only those whose latest `ticket_intake` source is SOURCE when `--source` is given and those with no person's verdict when `--unattended` is given, and checks the count is at least N;
4. prints one line per unmet condition, or `roadmap merged: ok` when all hold, and exits 0 when all hold, 1 otherwise, 2 on a refusal.

It writes nothing and takes no lock, so a gate can run it while serve runs.

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py` (created by `roadmap-table-parser`, extended by `roadmap-author`):
  - A pure function `release_name(heading: str) -> str`: the heading text up to the first space or comma. `"0.3.0, last group: the roadmap driver"` gives `0.3.0`; `"0.4.0 (conditional)"` gives `0.4.0`; `"Next"` gives `Next`. A `Row.release` is a heading text, so `release_name(row.release)` is the row's release. No version number is parsed or compared.
  - `async def merged(checkout, stems, *, release=None, priorities=(), since=None, at_least=None, source=None, unattended=False) -> tuple[bool, list[str]]`. Before reading anything it raises `clutch/runner.py::Refusal` (each with a paved road naming the flag to add or drop) when: no condition is given (no stems, no `release`, no `at_least`); `priorities` without `release`; `since` without `at_least` or `at_least` without `since`; `source` or `unattended` without `at_least`; `at_least` below 1; or a stem has `clutch/tickets.py::stem_findings`. Then, with `states = last_states(checkout.journal.read())`:
    - each stem whose state is not in `clutch/status.py::SETTLED` adds `roadmap merged: <stem> is <state>`, or `roadmap merged: <stem> is not in the journal` when it has none. A named stem is a ticket, checked by its own journal state, not read as a roadmap row;
    - with `release`: `rows = parse(text)` over the text of `checkout.repo / ROADMAP` (a missing file raises `Refusal` whose road names `docs/roadmap.md`), and `choice = choose(rows, states=states, files=frozenset())`. `files` is empty because `choose`'s strike step reads only `states`; the query lists no files. The release's rows are those with `release_name(row.release) == release` and, when `priorities` is nonempty, `row.priority in priorities`. No row with that release name raises `Refusal` naming it, with the road "name a release heading of docs/roadmap.md section 8". A row is settled only when `row.struck` is true or the row is in `choice.strike`, so a split row settles only when its own stem and every stem in its `**Authored**` list have settled. `merged` does not read the `**Authored**` prefix itself. Each release row that is not settled adds one line:
      - `roadmap merged: release <release> row <number> <stem> is <state>` (or `is not in the journal`) when its own stem's state is not in `SETTLED`;
      - otherwise `roadmap merged: release <release> row <number> <stem> has a split ticket that has not settled`;
    - with `since`: `checkout.git.rev_parse(checkout.repo, f"refs/tags/{since}")`; a `GitError` raises `Refusal` naming the tag, with the road "a phase's tag is made at its start by `clutch release --minor`". Then `checkout.git._run(checkout.repo, "log", "--first-parent", "--format=%(trailers:key=clutch-ticket,valueonly)", f"refs/tags/{since}..HEAD")`; its non-blank lines, stripped and de-duplicated, are the merged stems. With `source`, keep a stem only when its last `ticket_intake` signal (`clutch/tickets.py::INTAKE_SIGNAL`) has that `source`. With `unattended`, drop a stem whose journal holds a `draft_confirmed` signal or a `reject_verdict` signal with `actor: operator` (a `machine` or `supervisor` keep does not drop it). Fewer than `at_least` stems adds `roadmap merged: <count> of <at_least> tickets merged since <since> match`.
    - No unmet condition gives `(True, ["roadmap merged: ok"])`; otherwise `(False, lines)` with the lines in the order above.

    It appends nothing to the journal and runs no git command but the two above.
- `clutch/__main__.py`:
  - `_parser`: the `roadmap` subcommand's sub-subcommands gain `merged`, with positional `stems` (`nargs="*"`), `--release`, `--priority` (`nargs="+"`, choices read from `clutch/tickets.py::Frontmatter`'s `priority` annotation with `typing.get_args`, not a restated literal), `--since`, `--at-least` (`type=int`), `--source`, and `--unattended` (`store_true`).
  - `main`: a `roadmap merged` invocation calls `clutch.roadmap.merged` (looked up on the module at call time, as `main` does for `clutch.release.release`) before any lock is taken, prints the lines, and returns 0 for `True`, 1 for `False`. Only `roadmap author` takes the writer lock. `Refusal` already maps to exit 2 through `main`'s handler; nothing is added to it.
- `clutch/docs/host-running.md`: the `roadmap` verb-table row gains one sentence: `roadmap merged` checks named stems, a release's rows, or a count of tickets merged since a tag, exits 0 when they hold and 1 otherwise, writes nothing, and works while serve runs.
- `docs/how-clutch-works.md` section 2.1: add a row `roadmap merged [stem ...] [--release R [--priority P ...]] [--since TAG --at-least N [--source S] [--unattended]]` (Lock: no) describing steps 1-4 of the Goal. Nothing else in the file changes.
- New tests in two new files: `tests/unit/test_roadmap_merged.py` (fakes only: `MemoryJournal` from `tests/unit/test_retro_recurrence.py`, a fake git with async `rev_parse` and `_run`, roadmap text written under `tmp_path`; it runs every new line of `clutch/roadmap.py` and the new `main` branch, because `clutch/roadmap.py` is under the `default = 90` unit floor and `clutch/__main__.py` has a floor of 13) and `tests/integration/test_roadmap_merged.py` (real git and a real `Journal` under `tmp_path`).

Scope out:
- The gate blocks in `docs/roadmap.md`, their runner, and the `roadmap gate` verb (`release-gates-as-commands`); `clutch roadmap status` (`roadmap-status`).
- `parse`, `choose`, `link`, `strike`, and `author_ahead` in `clutch/roadmap.py`: this ticket calls `parse` and `choose` and changes none of them. Reading a split row's `**Authored**` list again inside `merged` was rejected: it would restate `choose`'s strike rule, and the two copies could drift.
- `clutch/git.py`: the two git calls go through the existing `Git.rev_parse` and `Git._run`, as `roadmap-author` already calls `Git._run`.
- Filters this ticket has no gate line for: ticket kind, an upper bound, a journal-signal filter, or a release-membership filter on the count. Writing no flag that no gate uses is the minimum; the simpler alternative of a hand-built `uv run python -c` journal fold per gate line was rejected because `CLAUDE.md` section A asks for verbs, not command lines.
- `clutch/help.py`, `clutch/observe.py`, and `vscode-clutchwork/`: `roadmap` is not an extension surface.
- `docs/roadmap.md`, `README.md`, `CLAUDE.md`, `AGENTS.md`, and the plan documents.

## Scope fence
- clutch/roadmap.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_roadmap_merged.py
- tests/integration/test_roadmap_merged.py

## Acceptance criteria
1. `tests/unit/test_roadmap_merged.py::test_release_name` asserts `release_name("0.3.0") == "0.3.0"`, `release_name("0.3.0, last group: the roadmap driver") == "0.3.0"`, `release_name("0.4.0 (conditional)") == "0.4.0"`, and `release_name("Next") == "Next"`. Ruled out: a name that keeps `, last group...` or `(conditional)`, which would split one release into two.
2. `tests/unit/test_roadmap_merged.py::test_named_stems` journals `merged` for `a-row`, `already_satisfied` for `b-row`, and `gate_failed` for `c-row`. `merged(checkout, ["a-row", "b-row"])` returns `(True, ["roadmap merged: ok"])`. `merged(checkout, ["a-row", "c-row", "d-row"])` returns `False` with exactly the lines `roadmap merged: c-row is gate_failed` and `roadmap merged: d-row is not in the journal`. Ruled out: `already_satisfied` treated as unmerged, and an unknown stem treated as merged.
3. `tests/unit/test_roadmap_merged.py::test_release_rows` writes a roadmap under `tmp_path` whose master tables are `### 1.0.0` (row 1 `p-one` P1 with state `merged`, row 2 `p-two` P2 with no state, row 3 `p-three` P1 struck in every cell with no state), `### 1.0.0, last group` (row 4 `p-four` P1 with state `merged`), and `### 2.0.0` (row 5 `p-five` P0 with state `running`). Then:
   - `release="1.0.0", priorities=("P0", "P1")` returns `(True, ["roadmap merged: ok"])`;
   - `release="1.0.0"` returns `False` with the one line `roadmap merged: release 1.0.0 row 2 p-two is not in the journal`;
   - `release="2.0.0"` returns `False` with the line `roadmap merged: release 2.0.0 row 5 p-five is running`;
   - `release="9.9.9"` raises `Refusal` naming `9.9.9`.

   Ruled out: another release's row counted, the last-group heading read as a separate release, a struck row reported as open, and the priority filter ignored.
4. `tests/unit/test_roadmap_merged.py::test_release_split_row` writes a roadmap under `tmp_path` whose one master table, `### 1.0.0`, holds row 1 `s-row` P1, unstruck, whose Content starts ``**Authored** (`tickets/s-row/`, `tickets/s-two/`).``. The journal holds `merged` for `s-row` and `running` for `s-two`.
   - `merged(checkout, [], release="1.0.0")` returns `False` with exactly the one line `roadmap merged: release 1.0.0 row 1 s-row has a split ticket that has not settled`.
   - After the test journals `merged` for `s-two`, the same call returns `(True, ["roadmap merged: ok"])`.

   Ruled out: a split row settled by its own stem alone while a stem in its `**Authored**` list is unmerged, and a split row left unsettled once every listed stem has merged.
5. `tests/unit/test_roadmap_merged.py::test_count_since_tag` fakes `rev_parse` to succeed for `refs/tags/v1.0.0` and `_run` to answer the log with `a-row\n\nb-row\n\nb-row\n\nc-row\n\n`. The journal holds `ticket_intake` signals with source `box:roadmap_row` for `a-row` and `b-row` and `human` for `c-row`, and a `draft_confirmed` signal for `a-row`. Then:
   - `since="v1.0.0", at_least=3` returns `(True, ["roadmap merged: ok"])`, and the recorded `_run` argv contains `--first-parent` and ends with `refs/tags/v1.0.0..HEAD`;
   - `at_least=4` returns `False` with the line `roadmap merged: 3 of 4 tickets merged since v1.0.0 match`;
   - `source="box:roadmap_row", at_least=2` returns `True`;
   - `source="box:roadmap_row", unattended=True, at_least=2` returns `False` with `1 of 2`;
   - after the test journals `reject_verdict` with `actor: machine` for `c-row`, `unattended=True, at_least=2` returns `True`; after it journals one with `actor: operator` for `b-row`, the same call returns `False`.

   Ruled out: a stem counted twice, the source or person-verdict filter ignored, and a machine keep counted as a person's verdict.
6. `tests/unit/test_roadmap_merged.py::test_missing_tag_refuses`: `rev_parse` raising `GitError` makes `merged(checkout, [], since="v9.9.9", at_least=1)` raise `Refusal` naming `v9.9.9` and `clutch release`, and `_run` is never called. Ruled out: a log over a missing tag read as zero merges.
7. `tests/unit/test_roadmap_merged.py::test_argument_refusals` asserts that each of these raises `Refusal` before any journal read or git call (the fakes record none): no condition; `priorities=("P1",)` without `release`; `since` without `at_least`; `at_least` without `since`; `source` without `at_least`; `unattended=True` without `at_least`; `at_least=0`; and the stem `Bad Stem`. Ruled out: a check with no condition passing as `ok`, and a filter silently ignored.
8. `tests/unit/test_roadmap_merged.py::test_main_roadmap_merged` fakes `load_config` and `child_env` as `tests/unit/test_release.py::test_main_release_locks_calls_and_prints` does, replaces `cli.Lockfile` with a class whose constructor fails the test, and replaces `clutch.roadmap.merged` with a recording fake:
   - `main(["roadmap", "merged", "a-row", "--since", "v1.0.0", "--at-least", "2", "--source", "box:roadmap_row", "--unattended"], ...)` passes those values to the fake; a fake returning `(True, ["roadmap merged: ok"])` makes `main` print `roadmap merged: ok` and return 0, and one returning `(False, ["x"])` makes it print `x` and return 1;
   - a fake raising `Refusal("blocked", "repair")` makes `main` return 2 and print `clutch roadmap: blocked -- repair` to stderr;
   - `_parser().parse_args(["roadmap", "merged", "--release", "1.0.0", "--priority", "P4"])` raises `SystemExit`.

   Ruled out: taking the writer lock for a read-only query, and an exit code that does not follow the result.
9. `tests/integration/test_roadmap_merged.py::test_roadmap_merged_end_to_end` builds a real git repo under `tmp_path` (as `tests/integration/test_release.py::repository` does) with `config.yaml` and a committed `docs/roadmap.md` whose `### 1.0.0` master table holds rows `a-row` and `b-row`. It tags the commit `v1.0.0` with `Git.tag`, then commits twice with messages ending in the trailers `clutch-ticket: a-row` and `clutch-ticket: b-row`, and once with no trailer. A real `Journal` in the state dir holds `merged` transitions for both stems. Then:
   - `main(["roadmap", "merged", "a-row", "b-row"])` and `main(["roadmap", "merged", "--release", "1.0.0"])` each return 0 and print `roadmap merged: ok`;
   - `main(["roadmap", "merged", "--since", "v1.0.0", "--at-least", "2"])` returns 0, and with `--at-least 3` returns 1 and prints `roadmap merged: 2 of 3 tickets merged since v1.0.0 match`;
   - `main(["roadmap", "merged", "--since", "v9.9.9", "--at-least", "1"])` returns 2 with stderr starting `clutch roadmap:`;
   - across all runs HEAD, the tag list, and the journal segment bytes are unchanged.

   Ruled out: counting the untrailered commit, and any write by the query.
10. `./dev.py test tests/unit/test_host_running.py` exits 0, and the docs command in `## Verification` exits 0: `docs/how-clutch-works.md` section 2.1 has a row starting `` | `roadmap merged ``, and the `roadmap` row of `clutch/docs/host-running.md` names `roadmap merged`.
11. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes, with `clutch/roadmap.py` at or above `test-gate.toml`'s `default = 90` and `clutch/__main__.py` at or above its `13` floor.
12. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_merged.py tests/unit/test_host_running.py
./dev.py test tests/integration/test_roadmap_merged.py
uv run python -c "import pathlib; q = chr(96); t = pathlib.Path('docs/how-clutch-works.md').read_text(); verbs = t.split('### 2.1 Verbs')[1].split('### 2.2')[0]; assert '| ' + q + 'roadmap merged' in verbs; h = pathlib.Path('clutch/docs/host-running.md').read_text(); row = next(line for line in h.splitlines() if line.startswith('| ' + q + 'roadmap' + q + ' |')); assert 'roadmap merged' in row"
./dev.py test
```

## Definition of rejected
The branch is rejected if `roadmap merged` takes the writer lock, appends to the journal, or runs a git command that writes; if it parses or compares a version number; if it counts a commit without a `clutch-ticket:` trailer or off the first-parent line; if any flag is silently ignored instead of refused; if it adds a filter or bound that no gate line uses (ticket kind, `--at-most`, a signal filter); if it changes `parse`, `choose`, `link`, `strike`, or `author_ahead`; if it decides whether a release row is settled by anything but the row's `struck` flag and membership in `choose`'s `strike` (for example its own stem's state alone, or its own reading of the `**Authored**` prefix); or if it adds a `clutch/help.py` entry, an extension menu item, or a config field.

## Time budget
- expected: 75m
- stuck: 150m
