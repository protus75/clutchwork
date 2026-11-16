---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- roadmap-row-message
- roadmap-table-parser

## Context
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/__main__.py::_preflighted_llm
- clutch/triage.py::triage_pass
- clutch/triage.py::_settle_pass
- clutch/box.py::Box
- clutch/box.py::Verdict
- clutch/box.py::Resolution
- clutch/box.py::RereportJournal
- clutch/status.py::last_states
- clutch/git.py::Git.commit
- clutch/git.py::Git.status_porcelain
- clutch/release.py
- clutch/runner.py::Refusal
- tests/unit/test_release.py::test_main_release_locks_calls_and_prints
- tests/unit/test_retro_recurrence.py::MemoryJournal
- tests/integration/test_author.py::_run
- tests/integration/test_author.py::_routes
- tests/integration/test_triage.py::author_reply
- tests/integration/test_drain.py::make_root
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1
- docs/roadmap-driver-plan.md#3.

## Goal / Why
`docs/roadmap-driver-plan.md` section 3 (roadmap row 90) defines `clutch roadmap author [--ahead N]`. It reads the master ticket table in `docs/roadmap.md`, files one `roadmap_row` Suggestion Box message per row whose dependencies have merged, in release order, until `N` rows (default 2) are open, and has the Author stage write each ticket. It links the authored row as a ticket-plane commit `clutch(roadmap): author <stem>` and strikes the row once its ticket merges, so the roadmap stays true without a person editing it. Open decision 3 is taken as proposed: row linking is a ticket-plane commit, not a journal-only record. `--ahead` keeps the driver from authoring rows against source that earlier rows will still change. The `driver-loop` ticket (roadmap row 93) calls this pass at serve's idle point; this ticket makes it a verb.

Today nothing files a roadmap row, and every row link or strike in `docs/roadmap.md` is a hand edit. This ticket joins two dependencies:
- `roadmap-table-parser`: `clutch/roadmap.py`'s `parse`, `link`, `strike`, `plan_path`, `depends_on`, and `choose`, including the hand-test refusal;
- `roadmap-row-message`: the `roadmap_row` class, its `RoadmapRow` payload, and Author's handling of it.

A roadmap message reaches Author through triage's existing recorded-`author`-verdict path (`clutch/triage.py::_settle_pass`). It is filed with an `author` verdict stamped with the current triage spec version, then settled with `triage_pass` over exactly those ids. So no triage model judges a row the roadmap already approved, and crash handling stays triage's: a message whose Author run did not settle is declined on the next pass.

After this change, `uv run clutch roadmap author [--ahead N]`:
1. takes the writer lock as `triage` does;
2. refuses (exit 2) when `docs/roadmap.md` has uncommitted changes, because its commits would carry them;
3. strikes each settled row and links each row whose ticket already exists, one commit per row;
4. files `roadmap_row` messages for ready rows in `choose` order until open rows plus filed messages reach `N`, and has Author settle them;
5. links each row whose message resolved to a ticket;
6. reports declined, still-pending, and waiting rows with their paved roads;
7. prints how many rows are open.

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py`: add `async def author_ahead(checkout, ahead, author_messages) -> list[str]`. `author_messages` is an async callable that takes a list of Box ids and settles them. The function returns the output lines and runs these steps in order:
  1. `checkout.git.status_porcelain(checkout.repo, "--", ROADMAP)`. Nonempty output raises `Refusal` naming `docs/roadmap.md`, with paved road "commit or restore docs/roadmap.md, then run `clutch roadmap author` again". A missing `docs/roadmap.md` raises `Refusal` whose paved road names the master ticket table. Either refusal happens before any write, commit, or Box message.
  2. Read the text, then `rows = parse(text)`. `files` is the NUL-split output of `checkout.git._run(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")`. `states` is `last_states(checkout.journal.read())`. `choice = choose(rows, states=states, files=files)`.
  3. Each row in `choice.strike`: apply `strike`, write through `checkout.fs.write`, commit with `checkout.git.commit(repo, "clutch(roadmap): strike <stem>", only=[ROADMAP])`, and output `roadmap: struck row <n> <stem>`. Each row in `choice.link` is handled the same way, with `link`, `clutch(roadmap): link <stem>`, and `roadmap: linked row <n> <stem>`. The text is edited cumulatively; each edit uses the row's own line.
  4. `open = choice.open`. Use `Box(checkout.config.state_dir / BOX_DIR, checkout.fs, rereport=RereportJournal(checkout.journal))`. Walk `choice.ready` while `open` plus the number of filed messages is below `ahead`. For each row, `box.enqueue(message_class="roadmap_row", origin="roadmap/<stem>", summary="Roadmap row <n> `<stem>`: <content>", roadmap_row=RoadmapRow(...))`. The `RoadmapRow` copies the row's fields, uses `list(depends_on(row, rows))` for `depends` and `list(row.runs_before)` for `runs_before` (`RoadmapRow` is strict, so tuples are refused), and takes `plan` from `plan_path(row.owner, files)`. Then read the message back:
     - Resolved `declined`: output `roadmap: row <n> <stem> declined -> <record> -- reword the row's Content in docs/roadmap.md to file it again`, and continue without counting it. This is how an earlier pass's decline stays settled.
     - Pending without a verdict: record `Verdict(verdict="author", produced_by_spec_version=load_spec((SPECS_DIR / "triage.md").read_text()).meta.version, rationale="Roadmap row <n> is planned work in docs/roadmap.md")`, with `SPECS_DIR` (from `clutch/runner.py`) and `load_spec` (from `clutch/specs`) imported into `clutch/roadmap.py`'s namespace so a unit test can replace both. Then, and also when it is pending with a verdict, count it as filed.
  5. When at least one message was filed, await `author_messages(ids)` once with all of them. When none was filed, `author_messages` is never called, so no provider is preflighted.
  6. For each filed message, read it back from the Box:
     - Resolved `ticket`: apply `link`, write, commit `clutch(roadmap): author <stem>`, output `roadmap: authored row <n> <stem>`, and increment `open`.
     - Resolved `declined`: output the declined line from step 4.
     - Still pending: output `roadmap: row <n> <stem> pending -- run clutch roadmap author again`.
  7. Output `roadmap: row <n> <stem> waits: <reason> -- <road>` for each `choice.waits` entry, then `roadmap: <open> of <ahead> rows open` last.

  Every commit names only `docs/roadmap.md`. Git runs through `Git`. Writes go through `checkout.fs`. The roadmap is read with `Path.read_text` as `clutch/author.py` reads the authoring guide.
- `clutch/__main__.py`:
  - In `_parser`: a `roadmap` subcommand with a required sub-subcommand `author`, which takes `--ahead` (`type=int`, default 2).
  - In `main`: the `roadmap` branch refuses (exit 2) when `--ahead` is below 1, before taking the lock. Otherwise it follows the `triage` branch:
    1. `Lockfile(config.state_dir, verb="roadmap", ...)` and `runner.reap(checkout)`, with a provider session from `build_control(checkout).providers` closed in a `finally`;
    2. it calls `clutch.roadmap.author_ahead(checkout, args.ahead, author_messages)`, looked up on the module at call time so a unit test can replace it. `author_messages(ids)` runs `_preflighted_llm(checkout, session)`, then `triage.triage_pass(checkout, llm, frozenset(ids))`;
    3. it prints the returned lines, one per line, releases the lock in a `finally`, and returns 0.

    `Refusal`, `LockHeld`, and `ProviderSetupError` already map to exit 2 through `main`'s handler. Nothing is added to it.
- `clutch/docs/host-running.md`: add a `| `roadmap` | No | ... |` verb-table row describing `roadmap author [--ahead N]`. Add `roadmap` to the "Stop serve before ..." sentence's list of verbs that take the writer lock. `tests/unit/test_host_running.py` requires the row and is not edited.
- `docs/how-clutch-works.md` section 2.1: add a `roadmap author [--ahead N]` row to the verb table (Lock: yes). It describes the steps above: the dirty refusal, strike and link commits, filing until `N` rows are open in release order, settlement through triage's recorded-verdict path with no triage model call, the `clutch(roadmap): author <stem>` link commit, and the hand-test and bug-evidence waits. Nothing else in the file changes.
- New tests: `tests/unit/test_roadmap_author.py` and `tests/integration/test_roadmap_author.py`. The unit file uses fakes (a fake `Git` with async `status_porcelain`, `_run`, and `commit`; `MemoryJournal`; a `Box` and repo under `tmp_path` with `LocalFileSystem`; `clutch.roadmap.SPECS_DIR` monkeypatched to a `tmp_path` directory holding a placeholder `triage.md`, and `clutch.roadmap.load_spec` monkeypatched to report version `9.9`, so the repo's `clutch/specs/triage.md` is never read). It reads no repo file, and together with `roadmap-table-parser`'s unit tests it keeps `clutch/roadmap.py` at or above 90. It also drives `main`'s new branch, because `clutch/__main__.py` has a unit floor of 13.

Scope out:
- `parse`, `choose`, `link`, `strike`, `plan_path`, and `depends_on` are `roadmap-table-parser`'s. This ticket only calls them.
- The `roadmap_row` message, the Author data blocks, and the Author gate (`roadmap-row-message`).
- `clutch roadmap status`, gate blocks (row 91), and calling `author_ahead` from serve or drain (row 93 `driver-loop`).
- `docs/roadmap.md`: the implementing agent does not edit it. The verb edits it at run time.
- `clutch/help.py`, `clutch/observe.py`, and `vscode-clutchwork/`: `roadmap` is not an extension surface.
- `README.md`, `CLAUDE.md`, `AGENTS.md`, `clutch/hostfiles.py`, and `clutch/specs/`.

## Scope fence
- clutch/roadmap.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_roadmap_author.py
- tests/integration/test_roadmap_author.py

## Acceptance criteria
1. `tests/unit/test_roadmap_author.py::test_dirty_or_missing_roadmap_refuses`:
   - with `status_porcelain` answering ` M docs/roadmap.md`, `author_ahead` raises `Refusal` naming `docs/roadmap.md`;
   - with an empty `status_porcelain` and a `tmp_path` repo that has no `docs/roadmap.md`, `author_ahead` raises `Refusal` whose text contains `master ticket table`.

   In both cases no commit is recorded, no file exists under the Box directory, and `author_messages` is not called. Ruled out: committing a person's roadmap edits along with the driver's, and a missing roadmap that crashes or writes before refusing.
2. `tests/unit/test_roadmap_author.py::test_files_until_ahead_and_links`. The roadmap holds one linked open row `a-row`, and ready rows `b-row` and `c-row` with plan `docs/sample-plan.md` in `files`. `author_ahead(..., ahead=2, ...)` runs with an `author_messages` fake that resolves each id to `ticket` -> its stem.
   - It files exactly one message, for `b-row`. Its `roadmap_row` equals row `b-row`'s number, release, stem, owner, kind, priority, content, and plan, and its verdict is `author` with `produced_by_spec_version` `9.9`.
   - `author_messages` is called once, with that id.
   - The commits are exactly one: `clutch(roadmap): author b-row`, with `only=["docs/roadmap.md"]`.
   - The written roadmap's `b-row` line contains `tickets/b-row/`, and `c-row`'s line is unchanged.
   - The last output line is `roadmap: 2 of 2 rows open`.

   Ruled out: filing past `--ahead`, a triage verdict left unrecorded, a link before the ticket exists, and a commit naming other paths.
3. `tests/unit/test_roadmap_author.py::test_declined_row_is_skipped`: when `b-row`'s message was already resolved `declined` in an earlier pass, a pass with `ahead=2` outputs `roadmap: row 2 b-row declined -> <record> -- ...`, files `c-row`, and links `c-row` only. Ruled out: re-authoring a declined row, and a declined row holding the slot.
4. `tests/unit/test_roadmap_author.py::test_full_window_calls_no_model`: with two linked open rows and `ahead=2`, `author_ahead` files no message and never calls `author_messages`. Its last line is `roadmap: 2 of 2 rows open`. Ruled out: a provider preflight or Author call when nothing is due.
5. `tests/unit/test_roadmap_author.py::test_strikes_and_links_existing`. Given a linked row whose state is `merged`, and an unlinked row whose `tickets/y-row/ticket.md` is in `files`, `author_ahead` makes two commits:
   - `clutch(roadmap): strike x-row`: after it, the written roadmap's `x-row` line parses as struck;
   - `clutch(roadmap): link y-row`: after it, the `y-row` line parses as linked and the `x-row` line still parses as struck.

   Both commits pass `only=["docs/roadmap.md"]`. The output holds `roadmap: struck row <n> x-row` and `roadmap: linked row <n> y-row`. Ruled out: a merged row left unstruck, a later edit that undoes an earlier one, and an authored row left unlinked or re-filed.
6. `tests/unit/test_roadmap_author.py::test_unsettled_and_waiting_rows_are_reported`:
   - when `author_messages` leaves the message pending, `author_ahead` outputs `roadmap: row <n> <stem> pending -- run clutch roadmap author again` and makes no link commit;
   - a second `author_ahead` pass over that pending message, whose verdict the first pass recorded, calls `author_messages` again with the same id. The Box still holds exactly one message for the row, with the verdict recorded earlier. When the fake resolves it `declined`, the pass outputs `roadmap: row <n> <stem> declined -> <record> -- ...` and makes no link commit;
   - a hand-test row with no evidence outputs a `waits:` line carrying `choose`'s reason and paved road.

   Ruled out: linking a row whose ticket was never written, dropping a pending message that already has a verdict, filing a second message for the row, linking a row whose message was declined in this pass, and a silent wait.
7. `tests/unit/test_roadmap_author.py::test_main_roadmap_author`, faked as `tests/unit/test_release.py::test_main_release_locks_calls_and_prints` does, with `runner.reap` and `build_control` also faked:
   - `main(["roadmap", "author", "--ahead", "3"], ...)` with a fake `author_ahead` that records `ahead` and awaits `author_messages(["box-1"])`, `cli._preflighted_llm` faked to return a sentinel llm, and `cli.triage.triage_pass` faked to record its arguments: it records the lock verb `roadmap`; records acquire, then `author_ahead` with `ahead=3`, then `triage_pass` with the sentinel llm and `frozenset({"box-1"})`, then the faked session's `close`, then release, in that order; prints the fake's lines; and returns 0;
   - a fake raising `Refusal` returns 2, prints a `clutch roadmap:` line to stderr, and still releases the lock;
   - `--ahead 0` returns 2 without acquiring the lock;
   - `_parser().parse_args(["roadmap"])` raises `SystemExit`, and `["roadmap", "author"]` parses with `ahead == 2`.

   Ruled out: running without the lock, a lock left held, a provider session left open, settling messages other than the filed ids or with an unpreflighted llm, and a zero window.
8. `tests/integration/test_roadmap_author.py::test_roadmap_author_end_to_end`. Setup:
   - a repo from `tests/integration/test_drain.py::make_root` with `tests/integration/test_author.py::_routes`, `engine_plane_safety_inventory: [config.yaml]`, and one `NO_GO` `review_baseline` signal with the current `baseline_identity`;
   - a committed `docs/sample-plan.md` and a committed `docs/roadmap.md` whose master table (under `### Next`) holds row 1 `first-row` and row 2 `second-row`, both `feature` and `P2` with owner `sample plan 1`, where row 2 depends on `first-row`.

   Three runs of `main(["roadmap", "author", "--ahead", "1"], ...)`:
   - First run, with a FakeLLM holding `tests/integration/test_triage.py::author_reply("first-row")` and an approving requisition review: it returns 0 and prints `roadmap: authored row 1 first-row` and `roadmap: 1 of 1 rows open`. The last two commit subjects are `clutch(first-row): ticket` then `clutch(roadmap): author first-row`, and the second lists only `docs/roadmap.md`. Row 1's line contains `tickets/first-row/`. `tickets/first-row/ticket.md` has `state: confirmed`. No request has surface `triage`.
   - Second run, with an empty FakeLLM: it returns 0, makes no request and no commit, and prints `roadmap: 1 of 1 rows open`.
   - Third run, after the test journals a `state_transition` to `merged` for `first-row` and uses a FakeLLM for `second-row`: it commits `clutch(roadmap): strike first-row` before `clutch(second-row): ticket` and `clutch(roadmap): author second-row`. Afterwards `docs/roadmap.md`'s `first-row` line parses as struck and its `second-row` line contains `tickets/second-row/`.

   Ruled out: a draft under NO_GO, a triage model call, a second authoring inside the window, and a merged row left unstruck.
9. `tests/integration/test_roadmap_author.py::test_roadmap_author_refusals_change_nothing` runs three cases in repos built as in criterion 8: `docs/roadmap.md` modified, the writer lock held by the test, and `--ahead 0`. Each returns 2, with stderr starting `clutch roadmap:`. In all three, HEAD, the bytes of `docs/roadmap.md`, and the Box directory are unchanged, and no FakeLLM request is made. Ruled out: a refusal reached after a write.
10. `./dev.py test tests/unit/test_host_running.py` exits 0 with the `roadmap` row, and the docs command in `## Verification` exits 0: `docs/how-clutch-works.md` section 2.1 has a row starting `| `roadmap author`, and host-running's "Stop serve before" sentence names `roadmap`.
11. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes, with `clutch/roadmap.py` at or above 90 and `clutch/__main__.py` at or above 13.
12. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_author.py tests/unit/test_host_running.py
./dev.py test tests/integration/test_roadmap_author.py
uv run python -c "import pathlib; q = chr(96); t = pathlib.Path('docs/how-clutch-works.md').read_text(); verbs = t.split('### 2.1 Verbs')[1].split('### 2.2')[0]; assert '| ' + q + 'roadmap author' in verbs; h = pathlib.Path('clutch/docs/host-running.md').read_text(); stop = next(line for line in h.splitlines() if line.startswith('Stop serve before')); assert q + 'roadmap' + q in stop"
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- a roadmap row reaches a triage model call;
- a commit by the verb names any path but `docs/roadmap.md`, or the verb commits while `docs/roadmap.md` is dirty;
- it files more messages than `--ahead` allows;
- it files a row `choose` did not make ready;
- it links a row whose message did not resolve to a ticket;
- it pushes or publishes;
- it calls `author_ahead` from serve or drain;
- it edits `docs/roadmap.md` in the diff;
- it adds a `clutch/help.py` entry, an extension menu item, or a config field.

## Time budget
- expected: 90m
- stuck: 180m
