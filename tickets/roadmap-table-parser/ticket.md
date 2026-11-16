---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Runs before
- roadmap-author

## Context
- clutch/status.py::SETTLED
- clutch/status.py::last_states
- clutch/runner.py::Refusal
- clutch/release.py
- tests/unit/test_release.py
- docs/roadmap.md#8. Master ticket table
- docs/roadmap.md#9. Keeping this document true
- docs/roadmap-driver-plan.md#3.

## Goal / Why
`docs/roadmap-driver-plan.md` section 3 (roadmap row 90) has the roadmap driver read the master ticket table in `docs/roadmap.md` (section 8) and find rows that have no linked stem and whose `Depends on` stems have all merged, in release order. It files those rows for authoring a few at a time, links each authored row, and strikes each merged one. A row whose content says it waits on a hand test is refused until an evidence file the row names exists under `tickets/<stem>/evidence/`. Nothing in clutch reads that table today, and `clutch/roadmap.py` does not exist (`docs/roadmap-driver-plan.md`, "Where each piece lives").

This ticket adds the pure half: a parser, the two text edits, and the row choice. It does no I/O, so `roadmap-author` (the `clutch roadmap author` verb, which depends on this ticket) and the later `clutch roadmap status` (roadmap row 91) share one reading of the table.

The table changes shape while it is used, so the parser must not depend on any of these:
- version numbers in the release headings (`roadmap-plan-corrections` renames them);
- section numbers;
- whether a row is linked as `tickets/<stem>/` (by a person, by `roadmap-plan-corrections`, or by this ticket's `link`);
- whether a row is struck with `~~` (a merged row, or a skipped one such as row 88 `superseded-settles`).

It must also read the content cells that hold a bare `|` inside a code span (rows 3 and 49 at HEAD). It must skip rows that are not tickets: `(re-measure)` has no backticked stem, and the conditional row `(56)` has no bare row number.

After this change, `clutch/roadmap.py` has:
1. `parse(text)`: every row of every master table, with its release group, fields, linked flag, and struck flag.
2. `link(text, row)` and `strike(text, row)`: line-local edits that the parser reads back as linked or struck.
3. `plan_path(owner, files)`: maps a row's Owner cell to its plan file.
4. `choose(rows, states=..., files=...)`: returns the rows to strike, the rows to link, the count of open rows, the ready rows in release order, and the rows that wait with a reason and a paved road. That includes the hand-test refusal.

## Scope in / Scope out
Scope in:
- New `clutch/roadmap.py` with module constants `ROADMAP = "docs/roadmap.md"` and `COLUMNS = ("#", "Stem", "Owner", "Kind", "P", "Depends on", "Runs before", "Content")`, plus:
  - A frozen dataclass `Row` with fields:
    - `number` (int) and `release` (the text of the nearest `### ` heading above the row's table, without the `### `);
    - `stem`, `owner`, `kind`, `priority`, `depends` (the Depends on cell as text), `runs_before` (tuple of backticked stems in that cell; prose is ignored), and `content`;
    - `linked` and `struck` (bools), and `line` (the row's 0-based line index in the text).

    Every text field has every `~~` removed and is trimmed.
  - `parse(text) -> list[Row]`, in document order:
    - A master table is a Markdown table whose header cells, trimmed, equal `COLUMNS` in order. Its rows run from the line after the `|---|` separator to the first line that does not start with `|`.
    - A row line is split on `|` after its leading and trailing pipe are dropped. The first seven cells are `#` through `Runs before`. Every remaining cell, joined back with `|`, is `Content`.
    - A row is a ticket row only when its `#` cell (with `~~` removed) is a bare integer and its Stem cell holds a backticked token, which may sit inside a Markdown link. The first such token is the stem. Other rows are skipped.
    - `linked` is true when any cell of the row contains `tickets/<stem>/`. `struck` is true when any raw cell, trimmed, both starts and ends with `~~`.
    - `parse` raises `clutch/runner.py::Refusal` in two cases. When the text has no master table, the paved road names the header to restore. When two ticket rows share a number or a stem, the message names the duplicate and the paved road says to make it unique.
  - `depends_on(row, rows) -> tuple[str, ...]`: splits the Depends on cell on commas. Each part is a backticked stem, `row N`, or `rows N-M` (inclusive). Row references resolve to the stems of those ticket rows. An empty cell gives `()`. Any other part, or a row number with no ticket row, raises `ValueError` naming the part.
  - `link(text, row) -> str`: in the row's line only, replaces the first `` `stem` `` in the Stem cell with `` [`stem`](../tickets/stem/) ``. An already linked row returns `text` unchanged.
  - `strike(text, row) -> str`: in the row's line only, wraps each nonempty cell's trimmed text in `~~` and leaves empty cells empty. `Content` is wrapped as one cell, even when it holds `|`. A cell already wrapped is left as is. Every other line is byte-identical.
  - `plan_path(owner, files) -> str | None`: takes the first whitespace-separated word of the Owner cell, lowercased. `roadmap` maps to `docs/roadmap.md`. Any other word maps to the one path in `files` of the form `docs/<name>-plan.md` whose `<name>-plan` hyphen-separated words include it. No match, or more than one, gives `None`.
  - A frozen dataclass `Wait(row, reason, road)` and a frozen dataclass `Choice(strike, link, open, ready, waits)` (tuples, except the `open` int).
  - `choose(rows, *, states, files) -> Choice`. `states` maps a stem to its last journal state, as `clutch/status.py::last_states` returns. `files` is the set of repo-relative paths present in the checkout. A row is done when its stem's state is in `clutch/status.py::SETTLED` or the row is struck. For each ticket row that is not struck:
    1. If its state is in `SETTLED`, it goes to `strike`.
    2. Otherwise, if it is linked, it counts as `open` unless its state is `rejected`.
    3. Otherwise, if `tickets/<stem>/ticket.md` is in `files`, it goes to `link` and counts as `open` unless its state is `rejected`.
    4. Otherwise, if its stem has any state, it waits: the stem is already in the journal; the paved road is to give the row a new stem.
    5. Otherwise it is a candidate. Its checks run in this order, and the first that applies decides:
       - an unreadable Depends on cell waits with the `ValueError` text;
       - a dependency that is not done leaves the row out of every list;
       - a kind other than `feature`, `chore`, or `bug`, or a priority other than `P0`-`P3`, waits;
       - `plan_path` returning `None` waits, with a paved road saying to start the Owner cell with `roadmap` or a word from exactly one `docs/*-plan.md` name;
       - the hand-test refusal waits (below);
       - otherwise the row is ready.
  - The hand-test refusal. A candidate's named evidence is every backticked token in `Content` that starts with `tickets/<stem>/evidence/`.
    - When it names any, the row waits until every named path is in `files`. The reason names each missing path, and the paved road says to run the hand test and save its capture at that path.
    - When it names none but `Content` contains `hand test` (any case), the row waits. The paved road says to name the capture in Content as `tickets/<stem>/evidence/<file>`.
    - When its kind is `bug` and no path in `files` starts with `tickets/<stem>/evidence/`, the row waits. The paved road says to save the observed failure there. Reason: Author validates a bug ticket against its evidence (`clutch/tickets.py::missing_evidence_findings`), so a bug row without evidence could only be declined.
  - `ready` is ordered by the index of the row's master table in the document, then priority `P0` to `P3`, then line.
- New tests: `tests/unit/test_roadmap_table.py`, which uses only in-memory strings and sets and reads no repo file, and `tests/integration/test_roadmap_table.py`, which reads the real `docs/roadmap.md`. `clutch/roadmap.py` is a new file under `test-gate.toml`'s `default = 90` unit floor. The unit file must cover it at or above 90 on its own, because this ticket adds no other code to the module.

Scope out:
- Any I/O in `clutch/roadmap.py`: reading `docs/roadmap.md`, listing files, reading the journal, filing Box messages, committing, and the `clutch roadmap author` verb all belong to `roadmap-author`.
- `clutch/box.py`'s `roadmap_row` message and the Author data blocks (`roadmap-row-message`).
- `clutch roadmap status` and release gate blocks (roadmap row 91, `release-gates-as-commands`).
- `docs/roadmap.md` itself, `docs/how-clutch-works.md`, and the host guides: this ticket adds no verb and no behavior a person runs.

## Scope fence
- clutch/roadmap.py
- tests/unit/test_roadmap_table.py
- tests/integration/test_roadmap_table.py

## Acceptance criteria
1. `tests/unit/test_roadmap_table.py::test_parse_reads_master_tables` parses a text with: a non-master table (`| Release | Theme |`) that is ignored; a `### Next` table; and a `### Later, last group` table. Expected results:
   - ticket rows come back in document order, each with its `release` (`Next` or `Later, last group`) and its number, stem, owner, kind, priority, `runs_before`, and content;
   - a Content cell holding `` `cmd --a|--b` `` comes back whole;
   - the rows `| (56) | `cond-row` | ...` and `| 35 | (re-measure) | ...` are absent;
   - a Runs before cell `every feature ticket below` gives `()`.

   Ruled out: a row from a non-master table, a Content cell cut at an inner `|`, a conditional row read as a ticket, and a release name tied to a version number.
2. `tests/unit/test_roadmap_table.py::test_parse_linked_and_struck` covers these rows:
   - linked through `` [`a-row`](../tickets/a-row/) ``;
   - linked through `(`tickets/b-row/`)` in Content;
   - struck in every cell (`~~1~~`, `` ~~`c-row`~~ ``, ...);
   - struck only in Content;
   - plain.

   Each comes back with the right `linked` and `struck` flags. The struck rows' number, stem, and content carry no `~~`. Ruled out: a struck row read as unstruck, or with `~~` left in its fields.
3. `tests/unit/test_roadmap_table.py::test_parse_refuses`: `parse` raises `Refusal` for a text with no master table, for two rows numbered `4`, and for two rows with stem `dup-row`, naming the duplicate. Ruled out: silently picking one duplicate, and returning `[]` for a missing table.
4. `tests/unit/test_roadmap_table.py::test_depends_on`:
   - `rows 2-3, `x-row`` resolves to the stems of rows 2 and 3, then `x-row`;
   - `row 2` resolves to row 2's stem;
   - an empty cell gives `()`;
   - `rows 7-8` with no row 7 raises `ValueError` naming `7`;
   - `after the hand test` raises `ValueError`.

   Ruled out: unknown row numbers or prose read as no dependency.
5. `tests/unit/test_roadmap_table.py::test_link_and_strike_edit_one_line`:
   - `link` on a plain row turns its Stem cell into `` [`a-row`](../tickets/a-row/) ``. `parse` then reports it linked, with fields unchanged, and every other line is byte-identical. `link` on a linked row returns the text unchanged.
   - `strike` on a row whose Content holds `` `cmd --a|--b` `` gives a line where `parse` reports the row struck, its content equal to the original, and its empty cells still empty. Every other line is byte-identical.

   Ruled out: an edit that touches another row, a strike that splits Content's code span, and a double link.
6. `tests/unit/test_roadmap_table.py::test_plan_path`, with files `docs/roadmap-driver-plan.md`, `docs/stage-panels-plan.md`, `docs/how-clutch-works.md`, and `docs/roadmap.md`:
   - `driver plan 3` gives `docs/roadmap-driver-plan.md`;
   - `panels plan 5` gives `docs/stage-panels-plan.md`;
   - `roadmap (decision 4)` gives `docs/roadmap.md`;
   - `works plan 1` gives `None`;
   - with a second file `docs/driver-extra-plan.md` added, `driver plan 3` gives `None`.

   Ruled out: matching a non-plan document, a substring match, and an ambiguous owner resolved to one plan.
7. `tests/unit/test_roadmap_table.py::test_choose_partitions_rows`, from one parsed text, a `states` map, and a `files` set:
   - a linked row with state `merged` and an unlinked row with state `already_satisfied` are in `strike`;
   - an unlinked row whose `tickets/<stem>/ticket.md` is in `files` is in `link`;
   - `open` counts the linked unmerged rows and the to-be-linked rows, but not a linked row whose state is `rejected`;
   - an unlinked row whose stem's state is `blocked` waits with a reason naming the journal;
   - a row depending on an unmerged stem is in no list;
   - a row depending through `row N` on a struck row is ready;
   - a row with kind `evidence` waits;
   - `ready` lists, in this order: the `Next` table's P1 row (which sits below its P2 row in the document), then that P2 row, then the `Later, last group` table's P0 row.

   Ruled out: authoring a merged, linked, journaled, or blocked row; counting a rejected row as open; and ordering across tables by priority alone.
8. `tests/unit/test_roadmap_table.py::test_choose_hand_test_refusal`:
   - A row whose Content says `after the hand test` and names `` `tickets/h-row/evidence/a0.txt` `` waits with that path in its reason while the path is absent from `files`, and is ready once it is present.
   - A row whose Content says `after its hand test` and names no evidence path waits, with a paved road containing `tickets/g-row/evidence/`.
   - A `bug` row waits until some `tickets/b-row/evidence/...` path is in `files`.
   - A row that names `` `tickets/n-row/evidence/x.txt` `` without saying `hand test` also waits for that file.

   Ruled out: a hand-test row filed before its evidence exists, a bug row filed with no evidence, and a refusal that names no paved road.
9. `tests/unit/test_roadmap_table.py::test_choose_waits_on_plan_and_depends`: a candidate whose Owner resolves to no plan waits with a paved road naming `docs/*-plan.md`, and a candidate whose Depends on cell is `see notes` waits with the `ValueError` text. Ruled out: either row ready.
10. `tests/integration/test_roadmap_table.py::test_real_roadmap_parses` reads the repo's `docs/roadmap.md`. `parse` returns without raising. Its result holds a row with number `90` and stem `roadmap-author`, with kind `feature` and priority `P1`. `choose(rows, states={}, files=set())` returns without raising. Ruled out: a parser that only reads its own fixtures and refuses the real table.
11. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes with `clutch/roadmap.py` at or above `test-gate.toml`'s `default = 90`.
12. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_table.py
./dev.py test tests/integration/test_roadmap_table.py
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- `clutch/roadmap.py` reads or writes a file, runs a process, or reads the journal;
- `parse` keys anything on a version number or section number in a heading;
- `choose` makes ready a row that is linked, struck, settled, already in the journal, waiting on an unmerged dependency, or waiting on a missing hand-test or bug evidence file;
- any edit changes a line other than the row's own;
- it adds a verb, a config field, or a Box message class;
- it edits `docs/roadmap.md`.

## Time budget
- expected: 75m
- stuck: 150m
