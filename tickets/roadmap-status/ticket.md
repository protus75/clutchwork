---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- roadmap-table-parser
- roadmap-author
- roadmap-merged-query
- release-gates-as-commands

## Context
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/status.py::SETTLED
- clutch/status.py::last_states
- clutch/journal.py::Event
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
`docs/roadmap-driver-plan.md` section 4 (roadmap row 91) asks for a read-only `clutch roadmap status`. Per release, it shows how far the work has come, the gate's last result, and the rows the driver will author next. The driver plan says the extension draws it later. Today the only view of the roadmap is reading `docs/roadmap.md` against `clutch status` by hand. Neither says which rows are ready, which wait and why, or whether a release's gate last passed. Once the driver runs unattended (`driver-loop`, row 93), this verb is how anyone sees what it will do next and why a release has not shipped.

This is the third part of the row's split. `release-gates-as-commands` journals each gate run as a `roadmap_gate` signal (`{"signal": "roadmap_gate", "release", "passed", "failed"}`). `roadmap-table-parser`'s `choose` already sorts every row into strike, link, ready, and waiting, and counts open rows. `roadmap-merged-query`'s `release_name` turns a heading into its release. This ticket only projects those.

After this change `uv run clutch roadmap status` prints, without writing anything or taking a lock:
1. one line per release in document order: `release <R>: <m> merged, <a> authored, <r> ready, <b> blocked; gate <last result>`;
2. `next: <stems>`, the ready rows in the order the driver files them;
3. one `waits:` line per row `choose` holds back, with its reason and paved road.

It exits 0.

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py`: `async def status(checkout) -> list[str]`:
  1. Read `checkout.repo / ROADMAP`. A missing file raises `clutch/runner.py::Refusal` naming `docs/roadmap.md`. Then `rows = parse(text)`. `files` is the NUL-split output of `checkout.git._run(checkout.repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")`, the same listing `author_ahead` uses. `events = checkout.journal.read()`, `states = last_states(events)`, and `choice = choose(rows, states=states, files=files)`.
  2. Each row belongs to `release_name(row.release)`, and the releases appear in first-seen document order. Each row is counted in exactly one bucket:
     - **merged**: the row is struck, or its state is in `clutch/status.py::SETTLED`;
     - **authored**: otherwise, the row is linked or `tickets/<stem>/ticket.md` is in `files`, and its state is not `rejected` (the rows `choose` counts in `open`);
     - **ready**: otherwise, the row is in `choice.ready`;
     - **blocked**: every other row (waiting, a dependency not done, or `rejected`).

     The label is `ready`, not `open`, because `choose` and `roadmap author`'s output (`roadmap: <n> of <ahead> rows open`) already use "open" for authored rows that have not merged.
  3. A release's gate result comes from the last `roadmap_gate` signal in `events` whose `release` is that release: `gate passed <ts>`, `gate failed <ts>: <failed>`, or `gate not run` when there is none. A signal for a name that has no row adds no line.
  4. The lines are, in order:
     - one release line per release;
     - `next: ` followed by the stems of `choice.ready` joined with `, `, or `next: none`;
     - `waits: row <number> <stem>: <reason> -- <road>` for each `choice.waits` entry, in its order.
  5. It appends nothing to the journal, writes no file, and runs no git command but the listing.
- `clutch/__main__.py`:
  - `_parser`: the `roadmap` subcommand's sub-subcommands gain `status`, with no arguments.
  - `main`: a `roadmap status` invocation calls `clutch.roadmap.status` (looked up on the module at call time) without taking the writer lock, prints the lines, and returns 0. `Refusal` already maps to exit 2.
- `clutch/docs/host-running.md`: the `roadmap` verb-table row gains one sentence: `roadmap status` prints, per release, the rows merged, authored, ready, and blocked and the last gate result, then the next rows to author and the waiting rows. It writes nothing and works while serve runs.
- `docs/how-clutch-works.md` section 2.1: add a row `roadmap status` (Lock: no) with the four buckets, the gate result, `next:` and `waits:`, and "Read-only". Nothing else in the file changes.
- New tests in two new files: `tests/unit/test_roadmap_status.py` (fakes only: `MemoryJournal` from `tests/unit/test_retro_recurrence.py` or `clutch/journal.py::Event` values, a fake git with async `_run`, roadmap text under `tmp_path`; it runs every new line of `clutch/roadmap.py` and the new `main` branch, which have unit floors of 90 and 13) and `tests/integration/test_roadmap_status.py` (real git and a real `Journal`).

Scope out:
- Running a gate, journaling anything, linking or striking rows, filing messages: `roadmap gate` and `roadmap author` do those.
- `parse`, `choose`, `release_name`, `run_gate`, `merged`, and `author_ahead`: called, not changed.
- A JSON form, a snapshot field, or an extension view of the status: the driver plan leaves the extension for later, and no reader exists yet.
- A count of rows blocked on a missing provider credential: no row or code records one at HEAD.
- `docs/roadmap.md`, the plan documents, `clutch/help.py`, `clutch/observe.py`, `vscode-clutchwork/`, `README.md`, `CLAUDE.md`, and `AGENTS.md`.

## Scope fence
- clutch/roadmap.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_roadmap_status.py
- tests/integration/test_roadmap_status.py

## Acceptance criteria
1. `tests/unit/test_roadmap_status.py::test_status_buckets` writes a roadmap under `tmp_path` with these master tables:
   - `### 1.0.0`: row 1 `m-one`, linked, state `merged`; row 2 `s-two`, struck, no state; row 3 `a-three`, linked, state `running`; row 4 `t-four`, unlinked, with `tickets/t-four/ticket.md` in the faked listing; row 5 `x-five`, linked, state `rejected`; row 6 `r-six`, no dependency, no state; row 7 `d-seven`, depends on `` `a-three` ``.
   - `### 1.0.0, last group`: row 8 `h-eight`, whose Content names `` `tickets/h-eight/evidence/a0.txt` ``, which is absent from the listing.
   - `### 2.0.0`: row 9 `n-nine`, P0, no state.

   Every row has a valid kind, priority, and an Owner of `roadmap`, and the faked listing also holds `docs/roadmap.md`. `status(checkout)` returns exactly:
   - `release 1.0.0: 2 merged, 2 authored, 1 ready, 3 blocked; gate not run`
   - `release 2.0.0: 0 merged, 0 authored, 1 ready, 0 blocked; gate not run`
   - `next: r-six, n-nine`
   - one `waits: row 8 h-eight: ` line that contains `tickets/h-eight/evidence/a0.txt` and ` -- `.

   The test also asserts that the authored counts sum to `choose(...).open` for the same inputs. Ruled out: the last-group heading read as its own release, a struck or `already_satisfied` row read as unmerged, a `rejected` row read as authored, a waiting row read as ready, and a `next:` order other than `choose`'s.
2. `tests/unit/test_roadmap_status.py::test_status_gate_results` uses the same roadmap. The journal holds these `roadmap_gate` signals, built as `clutch/journal.py::Event` values with distinct `ts`:
   - `1.0.0` failed at `ts1` with `failed: "./dev.py test"`, then `1.0.0` passed at `ts2`;
   - `2.0.0` failed at `ts3` with `failed: "uv run clutch roadmap merged --release 2.0.0"`;
   - one for release `9.9.9`.

   The release lines end `; gate passed <ts2>` and `; gate failed <ts3>: uv run clutch roadmap merged --release 2.0.0`, and no line names `9.9.9`. Ruled out: an older result shown, a result shown under the wrong release, and a line for a release with no rows.
3. `tests/unit/test_roadmap_status.py::test_status_is_read_only`: with a journal fake whose `append` fails the test, `status` returns. The fake git records exactly one call, `_run(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")`. The roadmap file's bytes are unchanged. With no `docs/roadmap.md`, `status` raises `Refusal` naming `docs/roadmap.md`, and the git fake records no call. Ruled out: any journal or file write, and a missing roadmap read as an empty status.
4. `tests/unit/test_roadmap_status.py::test_main_roadmap_status` fakes `load_config` and `child_env` as `tests/unit/test_release.py::test_main_release_locks_calls_and_prints` does, and replaces `cli.Lockfile` with a class whose constructor fails the test.
   - A `clutch.roadmap.status` fake returning `["a", "b"]` makes `main(["roadmap", "status"], ...)` print exactly `a\nb\n` and return 0.
   - A fake raising `Refusal("missing", "restore it")` makes it return 2 and print `clutch roadmap: missing -- restore it` to stderr.
   - `_parser().parse_args(["roadmap", "status", "extra"])` raises `SystemExit`.

   Ruled out: taking the writer lock, and an argument the verb does not use.
5. `tests/integration/test_roadmap_status.py::test_roadmap_status_end_to_end` builds a real git repo under `tmp_path` (as `tests/integration/test_release.py::repository` does) with `config.yaml` and a committed `docs/roadmap.md`. Its `### 1.0.0` master table holds row 1 `done-row` and row 2 `next-row`, and it has a gate block running `<sys.executable> -c pass`. A real `Journal` holds a `merged` transition for `done-row`.
   - `main(["roadmap", "status"], ...)` returns 0 and prints `release 1.0.0: 1 merged, 0 authored, 1 ready, 0 blocked; gate not run` and `next: next-row`. HEAD, `git status --porcelain`, and the journal segment bytes are the same before and after.
   - After `main(["roadmap", "gate", "1.0.0"], ...)` returns 0, a second `main(["roadmap", "status"], ...)` prints a release line ending `; gate passed ` followed by the journaled signal's `ts`.

   Ruled out: a status that never sees the gate result written through the real journal, and a status run that writes anything.
6. `./dev.py test tests/unit/test_host_running.py` exits 0, and the docs command in `## Verification` exits 0: `docs/how-clutch-works.md` section 2.1 has a row starting `` | `roadmap status ``, and the `roadmap` row of `clutch/docs/host-running.md` names `roadmap status`.
7. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes, with `clutch/roadmap.py` at or above `test-gate.toml`'s `default = 90` and `clutch/__main__.py` at or above its `13` floor.
8. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_status.py tests/unit/test_host_running.py
./dev.py test tests/integration/test_roadmap_status.py
uv run python -c "import pathlib; q = chr(96); t = pathlib.Path('docs/how-clutch-works.md').read_text(); verbs = t.split('### 2.1 Verbs')[1].split('### 2.2')[0]; assert '| ' + q + 'roadmap status' in verbs; h = pathlib.Path('clutch/docs/host-running.md').read_text(); row = next(line for line in h.splitlines() if line.startswith('| ' + q + 'roadmap' + q + ' |')); assert 'roadmap status' in row"
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- `roadmap status` takes the writer lock, appends to the journal, writes a file, runs a gate, or runs any git command but the one listing;
- a row lands in more than one bucket, or the buckets disagree with `choose`;
- it restates `choose`'s readiness rules instead of calling `choose`;
- it labels ready rows "open";
- it adds a JSON flag, a snapshot field, a `clutch/help.py` entry, an extension menu item, or a config field;
- it changes `parse`, `choose`, `release_name`, `run_gate`, `merged`, or `author_ahead`;
- it edits `docs/roadmap.md`.

## Time budget
- expected: 60m
- stuck: 150m
