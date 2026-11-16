---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Runs before
- roadmap-no-human-gates
- release-gates-as-commands
- roadmap-author
- roadmap-table-parser

## Context
- docs/roadmap.md
- docs/roadmap-driver-plan.md
- docs/journal-sql-refactor-plan.md
- docs/parallel-tickets-plan.md
- docs/training-data-plan.md
- clutch/runner.py::failure_terminal
- clutch/runner.py::reject_ticket
- clutch/status.py::reject_queue
- clutch/release.py
- dev.py::main

## On-demand
- docs/annotations-index-plan.md
- docs/gemini-graphics-refactor-plan.md
- docs/document-agent-plan.md
- docs/evidence-trail-plan.md
- docs/stage-panels-plan.md
- docs/upstream-issue-plan.md

## Goal / Why
Every roadmap ticket is authored from `docs/roadmap.md` and the plans under `docs/`, and the roadmap driver tickets (`roadmap-author`, `release-gates-as-commands`) will parse `docs/roadmap.md` by release name and row. At HEAD these documents state things that merged code and the journal contradict. Suggestion Box messages box-000471, 472, 473, 480, 481, 486, 492, 495, 496 and 497 report them; each was re-checked at HEAD for this ticket.

1. **Row 88 `superseded-settles` and section 5 decision 17 rest on a false premise.** They say a split's parent stays in the Reject queue until a person rejects it. In the code, a published Rework split never reaches the Reject queue. `clutch/runner.py::failure_terminal` journals the parent's terminal without `routed`, so `clutch/status.py::reject_queue` never holds it. In the same call it retires the parent through `clutch/runner.py::reject_ticket`, which stamps `state: rejected`, commits `clutch(<stem>): rejected`, and journals `reject_verdict kill` with `actor: operator` although no person acted. `tests/integration/test_ladder.py::test_split_dispatches_reviewed_rework` pins that order. The journal shows the same thing for the only three stems that ever got a `supersedes` signal (`chupa-ruff-config`, `split-test-serve`, `menu-mirrors-verb-admission`): each kill lands within half a second of the signal. So 3 of the 28 "operator" kills that `docs/roadmap-driver-plan.md` counts at `c2d1c2a7` were the engine's. The split parents a person did kill (`specs-in-package`, `vscode-help`, `vscode-help-registry`) were Rework splits that did not publish. Each got a diagnosis verdict `split` and no `supersedes` signal, and was routed to the Reject queue as a reject. A `superseded` state would have released none of them. The driver plan repeats the false premise in its summary, "Why this is viable", "Current state", Target design section 1, "Where each piece lives", its ticket table and its `Runs before` line. Row 93 depends on row 88, and row 88 orders itself before row 89.
2. **The release names lag the version by one minor.** Section 1 says "Versions follow `pyproject.toml` (`0.1.5` today)". `pyproject.toml` is in fact `0.3.0`, tagged `v0.3.0` at `c761b213` as the start of the phase the roadmap calls 0.2.0. `clutch release --minor` (merged in `release-verb`) bumps one minor, so at the next phase boundary it produces 0.4.0, the name the roadmap gives the parallel release. The journal plan's step "tag 0.3.0 with `clutch release --minor`" cannot happen. `release-gates-as-commands` keys gates by release name, so the names must equal the versions.
3. **The release tooling text is stale.** Row 3 says `publish` "keeps bumping only the patch", and the driver plan says nothing tags. `clutch release` exists now (`clutch/release.py::release`). Its plan text calls it the verb "behind `./dev.py release`", which does not exist, and says it journals a `release` signal, which it does not. `./dev.py publish` (`dev.py::main`) bumps the patch again before it uploads, so a tagged release never reaches PyPI (box-000480). Row 92 `release-publish` does not say that publishing must not bump.
4. **Merged tickets left statements stale.**
   - `redaction-harvest-seam` made `clutch/runner.py::harvest` scrub `harvest.json`, but roadmap 3.1 and 4.2 and the training plan still say harvest is unscrubbed.
   - `docs-truth-sweep-code-strings` fixed the `Dormant` docstrings, the `review` help and the `retro_check` vocabulary, but the roadmap and the parallel plan still assign those fixes to `docs-truth-sweep`.
   - Row 6 says drain roads should name `./dev.py` verbs, which `CLAUDE.md` section B forbids. It ends "Superseded by `dev-py-dev-tasks-only`", which it was not: `paved-roads-name-verbs` merged it. Section 3.1 calls the drain report "the one operator surface" that names argv, but `status.py`, `doctor.py` and `providers.py` did too.
   - `contention-authoring-rules` put the do-not-grow rule in `CLAUDE.md` section A and `AGENTS.md` `## Engine conduct`, naming seven files. The parallel plan says section B and five files, and roadmap 2.6 says the list is in no rule file.
5. **Section 8 does not link or strike the 12 merged rows of the current phase,** as section 9 requires.

After this change:
- These documents say what the code and the journal show.
- Each phase is named for the version `clutch release --minor` gives it when the phase starts: 0.3.0 now, then 0.4.0 (journal, conditional), 0.5.0 (parallel and graphics), 0.6.0 (training, panels, index) and 0.7.0 (document agent).
- The current phase's merged rows are linked and struck.

## Scope in / Scope out
**Rename rule (all eleven fenced documents).** Every release name `0.2.0`, `0.3.0`, `0.4.0`, `0.5.0` or `0.6.0` that names a roadmap phase becomes the next minor (`0.2.0`->`0.3.0`, `0.3.0`->`0.4.0`, `0.4.0`->`0.5.0`, `0.5.0`->`0.6.0`, `0.6.0`->`0.7.0`). Each token shifts exactly once: rename in one pass, or from `0.6.0` down. No other version string changes: `0.1.5` and `0.0.40` in the roadmap Status, `0.50`, `0.85`, `0.0`, and schema versions such as `1.0` stay. Where an edit below gives new text, that text already carries the renamed tokens and is not shifted again. In the six `## On-demand` plans (annotations-index, gemini-graphics-refactor, document-agent, evidence-trail, stage-panels, upstream-issue) the rename is the only change.

**Struck-row format (roadmap section 8).** A struck row's Stem cell is its stem in backticks wrapped in `~~`, for example ``~~`release-verb`~~``. A merged row's Content cell starts with ``**Merged** (`tickets/<stem>/`).`` followed by one space and the existing content. Rows 1 and 2 replace their ``**Authored 2026-11-14, confirmed** (`tickets/<stem>/`).`` prefix with that one. An authored row that has not merged keeps a plain stem, and its Content cell starts with ``**Authored** (`tickets/<stem>/`).``, listing each ticket directory authored from the row, comma-separated, followed by one space and the content. Strike or link only the rows this ticket names; every other row stays as it is.

`docs/roadmap.md`:
1. Section 1: replace the paragraph that starts "Versions follow" with exactly:
   ``Versions follow `pyproject.toml` (`0.3.0` today). Each release below is a minor version, named for the version `clutch release --minor` gives it: a phase is bumped and tagged at its start, so tag `v0.3.0` (`c761b213`) opened 0.3.0. These names were once one minor lower (0.3.0 was `0.2.0`), and older commits, tickets, and Suggestion Box messages use the old names. Each phase takes the next minor when it starts, so if the conditional 0.4.0 window slides, the phases after 0.3.0 are renamed to the versions they start at. `clutch release --minor|--patch` (`release-verb`, merged) bumps, commits, and tags; `./dev.py publish` still bumps the patch again before it uploads, which `release-publish` (row 92) replaces with a publish that never bumps.``
   This is the only `0.2.0` left in the file.
2. Section 1 table: apply the rename rule to the release cells and to the references inside the rows. In the journal row's start cell, delete " and its slot is skipped", so the cell ends "if not, this release slides behind 0.6.0". A slot is never skipped, because each phase takes the next minor. Change nothing else in the table.
3. Section 1 "Independent of release", section 1.1, section 3.3, section 3.4, section 5 decisions 5, 7 and 8, section 6 decisions 1, 11, 12, 13 and 15, row 86, and every section 8 heading: rename only. The section 8 headings become `### 0.3.0`, `### 0.3.0, last group: the roadmap driver`, `### 0.4.0 (conditional)`, `### 0.5.0`, `### 0.6.0` and `### 0.7.0`.
4. Section 2.1 row 14: the Ticket cell becomes `` `docs-truth-sweep-code-strings` (done) ``.
5. Section 2.6: replace the last bullet with:
   ``- The do-not-grow rule is in `CLAUDE.md` section A and `AGENTS.md` `## Engine conduct` (`contention-authoring-rules`, done). It names seven files: the five measured at `80b76d5d` (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `serve_rig.py`), which took 53 commits in the 13 days to 2026-11-13, and `tests/integration/test_cli.py` and `tests/integration/test_watch.py`, added when the list was re-measured at `c761b213`.``
   Under it, the Tickets line becomes ``Tickets: `test-fakes-and-conftest`, `contention-authoring-rules` (done).``.
6. Section 3.1:
   - Paved-roads row: the Defect cell's opening clause, up to the first `;`, becomes `` Operator paved roads print `uv run python -m clutch drain|confirm|reject` and other argv instead of a verb, in the drain report and in `status.py`, `doctor.py`, and `providers.py` ``. The rest of the cell stays. The Ticket cell becomes `` `paved-roads-name-verbs` (done, `tickets/paved-roads-name-verbs/`) ``.
   - `harvest.json` row: the Ticket cell becomes `` `redaction-harvest-seam` (done) ``.
   - argparse row: the Ticket cell becomes `` `docs-truth-sweep-code-strings` (done) ``.
7. Section 4.1:
   - Row `452-453, 485-488`: the Truth cell ends ``code fix in `paved-roads-name-verbs` (done, `tickets/paved-roads-name-verbs/`)``.
   - Row `694`: the Truth cell becomes ``two outcome vocabularies; one (`clutch/retro.py::RetroCheckOutcome`) since `docs-truth-sweep-code-strings` (done)``.
8. Section 4.2:
   - `clutch/redact.py:7-9` row: the Truth cell becomes ``fixed by `redaction-harvest-seam` (done): `clutch/runner.py::harvest` scrubs `harvest.json` at the write, and the checklist names every writer``.
   - `Dormant` row: the Truth cell gains ``; both docstrings fixed by `docs-truth-sweep-code-strings` (done)`` at its end.
9. Section 5:
   - Decision 11 starts ``11. **The mergequeue docstring** was fixed by `docs-truth-sweep-code-strings` (done), not by a parallel-plan ticket;``. The rest stays, renamed ("the two 0.3.0 chores").
   - Decision 17 keeps its number. Its existing text is wrapped in `~~`, and these sentences follow it:
     ``Struck: the premise is false. A published Rework split never reaches the Reject queue: `clutch/runner.py::failure_terminal` journals the parent's terminal without `routed` and retires it through `reject_ticket` in the same second (box-000471). The split parents a person killed were Rework splits that did not publish, and they carry no `supersedes` signal (box-000473).``
10. Section 6 decision 4 becomes:
    ``4. **Split the do-not-grow test files.** Decided: the do-not-grow rule lands in 0.3.0 (`contention-authoring-rules`, done; it names seven files, the five measured at `80b76d5d` plus `tests/integration/test_cli.py` and `tests/integration/test_watch.py` measured at `c761b213`); splitting is chore tickets, one per file, during the 0.4.0 window if it runs, else in 0.5.0 before parallel runs start.``
11. Section 8 rows. Apply the struck-row format to these rows:
    - Rows 1 (`provider-capture-overwrite`), 2 (`provider-failure-single-mapper`), 3 (`release-verb`), 4 (`docs-truth-sweep`), 5 (`conduct-files-parity`), 6 (`paved-roads-name-verbs`), 7 (`dev-surface-completeness`), 9 (`unit-criteria-disk-snag`), 10 (`fence-closure-registries`), 11 (`watch-surface-tier-truth`), 12 (`redaction-harvest-seam`) and 13 (`contention-authoring-rules`): struck stem and the Merged prefix. Each one's journal state at HEAD is `merged`.
    - Row 3: the Content after the prefix is `` `clutch release --minor|--patch`: bumps `pyproject.toml`, commits, tags `v<version>`. `` It drops "`publish` keeps bumping only the patch. Needed to tag 0.2.0.".
    - Row 4: right after the prefix, insert ``Split in two: `docs-truth-sweep` (documents) and `docs-truth-sweep-code-strings` (code strings; `tickets/docs-truth-sweep-code-strings/`).``.
    - Row 6: the Content after the prefix is ``Operator roads in `clutch/drain.py`, `clutch/status.py`, `clutch/doctor.py`, and `clutch/providers.py` name `clutch` verbs instead of `uv run python -m clutch` argv; the unknown-box-id refusal in `clutch/status.py` carries a road; a failed retro's `error_code` keeps the stage outcome; five `BoxError` sites name a repair.``
    - Row 8 (`host-prompts-no-dev-py`): struck stem. Its Content starts ``**Not authored: already done at `73a41696`.**`` followed by the existing content. At HEAD, `grep -rln dev.py clutch/specs/ask/ clutch/docs/` finds nothing.
    - Row 88 (`superseded-settles`): struck stem and an empty Runs before cell. Its Content becomes:
      ``**Struck: premise false.** A published Rework split never reaches the Reject queue: `clutch/runner.py::failure_terminal` retires the parent through `reject_ticket` in the same second, so a `superseded` state would release nothing (box-000471, box-000472). The split parents a person killed by hand (`specs-in-package`, `vscode-help`, `vscode-help-registry`) were Rework splits that did not publish; they carry no `supersedes` signal (box-000473).``
    - Row 90 (`roadmap-author`), not struck: its Content starts ``**Authored** (`tickets/roadmap-row-message/`).`` followed by the existing content.
    - Row 92 (`release-publish`), not struck: its Content becomes:
      ``**Authored** (`tickets/release-publish/`). Publishing never bumps the version: `clutch publish` (PyPI, token env name in config) uploads the `pyproject.toml` version only when its `v<version>` tag is on HEAD, and refuses otherwise (box-000480; `./dev.py publish` bumps the patch first today, so a tagged release never reaches PyPI). `clutch release` (merged in `release-verb`) gains the `release` journal signal. `./dev.py vscode-publish` (Marketplace); publish only on `release.publish: true`, else a park for `confirm`.``
    - Row 93 (`driver-loop`): the Depends on cell becomes `rows 89-92`.
    - Row 35: "at the 0.2.0 tag" becomes "at the end of 0.3.0".

`docs/roadmap-driver-plan.md`:
1. Summary: delete the sentence "When a split lands, the parent settles by itself."
2. Roadmap: ``Release 0.3.0, as its last group (`docs/roadmap.md` rows 89-93), after the truth-and-hygiene rows, because the driver is what runs 0.4.0 onward.`` The rest of the paragraph stays.
3. "Why this is viable", first bullet: "28 kills" becomes ``28 kills (3 of them the engine's own split retirements, which `clutch/runner.py::reject_ticket` journals as `actor: operator`; box-000471)``.
4. "Why this is viable", third bullet, replaced by:
   ``- The kills the owner remembers as necessary were split parents, and the journal shows two kinds. The three stems whose split published (`chupa-ruff-config`, `split-test-serve`, `menu-mirrors-verb-admission`) were retired by the engine, not by a person: `clutch/runner.py::failure_terminal` journals the parent's terminal without `routed`, so `clutch/status.py::reject_queue` never holds it, and retires it through `reject_ticket` within half a second of the `supersedes` signal (box-000471). The parents a person killed (`specs-in-package`, `vscode-help`, `vscode-help-registry`) were Rework splits that did not publish: the diagnosis said `split`, Rework failed, and the parent was routed to the Reject queue with no `supersedes` signal (box-000473). A Rework split that publishes, or the supervisor's reviewed retry (section 2), is what would have released them.``
5. "Current state", the bullet "**A split's parent lingers.**", replaced by:
   ``- **A published split retires its parent.** `record_supersedes` journals the map (`clutch/rework.py::record_supersedes`); dispatch skips superseded stems and dependents wait on the successors. `clutch/runner.py::failure_terminal` journals the parent's terminal without `routed`, so `clutch/status.py::reject_queue` never holds it, then retires it through `clutch/runner.py::reject_ticket`: `state: rejected`, a `clutch(<stem>): rejected` commit, and a `reject_verdict kill` journaled with `actor: operator` although no person acted (box-000471). `tests/integration/test_ladder.py::test_split_dispatches_reviewed_rework` pins that order. A Rework split that does not publish turns the verdict into `reject`, and the parent is routed to the Reject queue like any other reject.``
6. "Current state", the bullet "**Release tooling is partial and manual.**", replaced by:
   ``- **Release tooling is half built.** `clutch release --minor|--patch` (`clutch/release.py::release`, merged in `release-verb`) bumps the version with `uv version`, commits `pyproject.toml` and `uv.lock` as `release: <version>`, and tags `v<version>` at that commit; it journals nothing. `./dev.py publish` bumps the patch version again before it uploads to PyPI with `UV_PUBLISH_TOKEN` (`dev.py::main`), so the tagged version is never the one uploaded (box-000480). `./dev.py vscode-package` builds a `.vsix` and prints the Marketplace upload page for a hand upload.``
7. Target design section 1: the heading becomes ``### 1. ~~Superseded is settled (`superseded-settles`)~~``. Its two bullets are replaced by one paragraph:
   ``Struck: the premise is false (see Current state). A published split already retires its parent, which never enters the Reject queue, and the split parents a person killed carry no `supersedes` signal, so a `superseded` state would release none of them (box-000471, box-000473).``
   Sections 2-7 keep their numbers.
8. Target design section 5:
   - The first bullet becomes ``- `clutch release --minor|--patch` exists (`release-verb`; see Current state). This ticket adds its `release` journal signal. Hosts use the same verb for their own versions.``
   - The second bullet starts ``- `clutch publish`: never bumps the version. It uploads the version in `pyproject.toml` only when its `v<version>` tag is on HEAD, and refuses otherwise (box-000480). It builds and uploads to PyPI`` and continues with the existing text from "through the exec seam".
   - The Authorization bullet stays.
9. "Where each piece lives":
   - Delete the `superseded` state row.
   - The release row becomes ``| `publish`, `release` config, `release` signal | `clutch/__main__.py`, `clutch/release.py`, `clutch/config.py`; `dev.py` (`vscode-publish`) |``.
10. Ticket breakdown:
    - "Release 0.2.0, last group." is renamed.
    - Row 1 becomes ``| 1 | ~~`superseded-settles`~~ | bug | P1 | | Struck: premise false (Target design section 1). |``.
    - Row 5's Content starts ``Section 5: the `release` signal, `clutch publish`,`` (it drops `clutch release`).
    - Row 6's Depends on becomes `2, 3, 4, 5`.
    - In the `Runs before` line, delete "Ticket 1 before 2 (the supervisor must not supervise a superseded parent)."
11. Risks: "before 0.2.0's dedup" is renamed.

`docs/journal-sql-refactor-plan.md`:
1. Roadmap: ``Release 0.4.0, conditional``. The sentence about the release verb becomes ``The release verb this plan's step (a) asked for is the roadmap's row 3 (`release-verb`), merged in 0.3.0.``. "slides behind 0.6.0" and "(`docs/annotations-index-plan.md`, 0.6.0)" are renamed.
2. Release protocol:
   - Step 1 starts "**Checkpoint.** At the end of 0.3.0, re-measure". The rest stays.
   - Step 2 starts ``**Refactor window.** `clutch release --minor` opens it with tag `v0.4.0`.`` The rest stays, renamed ("until 0.4.0 ships", "scheduled in 0.4.0").
   - Step 3 becomes ``**Release.** When the refactor is complete and its surfaced bugs are fixed, the window closes, and `clutch release --minor` opens 0.5.0 with tag `v0.5.0`.``
3. Problem: "the re-measurement at the 0.2.0 tag" becomes "the re-measurement at the end of 0.3.0", and "the 0.2.0 ticket" becomes "the 0.3.0 ticket".
4. Ticket table row 0: "at the 0.2.0 tag" becomes "at the end of 0.3.0".
5. "(0.4.0), so they run in sequence" and Open decision 9's "0.3.0 is a minor version" are renamed.

`docs/parallel-tickets-plan.md`:
1. Roadmap: rename only.
2. Current state, merge-queue bullet: delete its last sentence, which starts "The module docstring still says".
3. Section 7:
   - "Rules for this repo only (`CLAUDE.md` and `AGENTS.md`, outside the managed block):" becomes ``Rules for this repo only (`CLAUDE.md` section A and `AGENTS.md` `## Engine conduct`, outside the managed block):``.
   - In its bullet, "No new tests go into these files:" becomes "No new test, fixture, or helper goes into these files:". The list becomes the seven merged paths, in this order: `tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`.
   - The parenthesis starts ``(Measured: the five measured at `80b76d5d` (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `serve_rig.py`) took 53 commits in the 13 days to 2026-11-13; at `c761b213` `test_cli.py` is imported by 60 test modules and `test_watch.py` is in 38 ticket fences, so `contention-authoring-rules` added both;``. It continues with the existing "37 test modules double as fixture libraries ..." text.
4. "Where each rule lives": the do-not-grow row becomes ``| Do-not-grow list of this repo's large test files | `CLAUDE.md` section A and `AGENTS.md` `## Engine conduct`, outside the managed block |``.
5. Ticket row 2: "both 0.3.0 chores" is renamed. Its last sentence becomes ``The docstring fix that was here merged as `docs-truth-sweep-code-strings`.``
6. Open decision 4: ``section 7's do-not-grow rule lands in 0.3.0 (`contention-authoring-rules`, merged); splitting `test_daemon_composition.py` and the other six is one chore ticket per file during the 0.4.0 window if it runs, else in 0.5.0 before parallel runs start.`` The rest stays.

`docs/training-data-plan.md`:
1. Gap 4: replace its last sentence, which starts "`harvest.json` is written without the redactor", with `` `harvest.json` gets the same configured-secret redaction at its write (`clutch/runner.py::harvest`, since `redaction-harvest-seam`). ``
2. Risks: delete the bullet that starts "**Unscrubbed harvest today.**".
3. Everything else: rename only.

Scope out:
- Gates, cadences, operator actions, hand tests, calibration and GO baselines; `roadmap-no-human-gates` owns them. This includes the "Gate to start" and "Gate to ship" conditions, `gate: operator`, "a week", the publish park for `confirm`, roadmap section 8 "Operator actions (not tickets)", driver plan sections 4, 6 and 7, and the journal plan's "the owner declares" step. Release tokens inside them are renamed and nothing else changes, except these edits Scope in names: the clause deleted in `docs/roadmap.md` item 2; roadmap row 35's "at the end of 0.3.0"; the journal plan's Release protocol steps 1-3, its Problem sentence on the re-measurement, and its ticket-table row 0.
- Audit rows in roadmap sections 2-4 that Scope in does not name, the Status sections, and "Facts the ordering rests on". These are the audit snapshot at `80b76d5d`, which section 9 re-runs before each release.
- Section 9's text. Plan ticket tables, except the driver plan's rows 1, 5 and 6, the parallel plan's row 2, and the journal plan's row 0. Plan Status lines.
- `docs/how-clutch-works.md`, `README.md`, `CLAUDE.md`, `AGENTS.md`, and all code, specs and tests. No test or code reads a fenced document: a grep for the eleven file names over `tests/`, `clutch/`, `vscode-clutchwork/` and `dev.py` finds nothing. So no test is fenced or added.
- Fixing `reject_ticket`'s `actor: operator` on an engine retirement (box-000471 stays in the Box), and changing `./dev.py publish` (row 92's ticket does that).

## Scope fence
- docs/roadmap.md
- docs/roadmap-driver-plan.md
- docs/journal-sql-refactor-plan.md
- docs/parallel-tickets-plan.md
- docs/training-data-plan.md
- docs/annotations-index-plan.md
- docs/gemini-graphics-refactor-plan.md
- docs/document-agent-plan.md
- docs/evidence-trail-plan.md
- docs/stage-panels-plan.md
- docs/upstream-issue-plan.md

## Acceptance criteria
1. The first `## Verification` command exits 0. It checks that the section 1 table's release cells are exactly `0.3.0` to `0.7.0`, in order, and that the section 8 version headings are exactly `0.3.0`, `0.3.0`, `0.4.0`, `0.5.0`, `0.6.0`, `0.7.0`. It checks that `0.1.5 today` and `its slot is skipped` are gone. It checks that `0.2.0` occurs exactly once, in the "one minor lower" sentence, and that section 1 names `v0.3.0`, `c761b213`, `clutch release --minor` and "at its start". It also finds the renamed phrases in sections 1, 1.1, 3.3, 3.4, 5, 6 and rows 35 and 86. Ruled out: HEAD's names, a token shifted twice (`0.2.0` to `0.4.0`), and a token left unrenamed.
2. The second `## Verification` command exits 0. It checks that rows 1-7 and 9-13 have exactly the struck stem and start with ``**Merged** (`tickets/<stem>/`).``, and that row 4 links `tickets/docs-truth-sweep-code-strings/`. It checks that no `Authored 2026-11-14` prefix is left, that row 8 is struck with `73a41696`, and that row 88 is struck with an empty Runs before cell and cites box-000471 and box-000473. It checks that rows 90 and 92 keep plain stems and start with ``**Authored** (`tickets/roadmap-row-message/`).`` and ``**Authored** (`tickets/release-publish/`).``, that row 93 depends on `rows 89-92`, and that no other row is struck. It also checks that row 3 drops the patch-bump sentence, that row 6 has no `dev.py` and no "Superseded by", and that row 92 says publishing never bumps and names `v<version>`, `on HEAD` and box-000480. Ruled out: HEAD's unlinked rows, a struck unmerged row, an authored row struck or left unlinked, and row 88 still ordered before `supervisor-rework`.
3. The third `## Verification` command exits 0. It checks the audit and decision fixes: section 2.6 names section A, both added test files and `contention-authoring-rules` (done), and no longer says "in no rule file". Section 2.1 row 14 and the 3.1 argparse row name `docs-truth-sweep-code-strings` (done). The 3.1 paved-roads row names `doctor.py`, `providers.py` and the ticket path, and drops "the one operator surface". The 3.1 harvest row says `redaction-harvest-seam` (done). Section 4.1 rows 452-453 and 694 and the 4.2 redact and `Dormant` rows point at the merged tickets, and "harvest is unscrubbed" is gone. Decision 11 names `docs-truth-sweep-code-strings`. Decision 17 starts struck and cites box-000471 and box-000473. Section 6 decision 4 names `test_cli.py` and `test_watch.py` and drops "five large". Ruled out: each of HEAD's stale statements.
4. The fourth `## Verification` command exits 0. In `docs/roadmap-driver-plan.md`, `0.2.0` is gone and the renamed phrases and `rows 89-93` are present. Section 1 and ticket row 1 are struck, and `driver-loop` depends on `2, 3, 4, 5`. The split-parent facts cite `reject_ticket`, `test_split_dispatches_reviewed_rework`, `specs-in-package`, box-000471 and box-000473. The release text names `clutch/release.py::release`, "never bumps the version", "on HEAD" and box-000480. None of these remain: "parent settles by itself", "neither settles the parent", "lingers", "until a person rejects it", "Ticket 1 before 2", the `superseded` Where row, `./dev.py release`, "nothing tags", "new `clutch/release.py`", or `clutch release` in ticket row 5. Ruled out: HEAD's driver plan.
5. The fifth `## Verification` command exits 0. In `docs/journal-sql-refactor-plan.md`, `0.2.0` and `tag 0.3.0` are gone. The Release protocol says "At the end of 0.3.0", `v0.4.0`, "until 0.4.0 ships", "scheduled in 0.4.0", "opens 0.5.0" and `v0.5.0`. The file has the renamed Roadmap, Problem, row 0, sequence and Open decision 9 phrases. Ruled out: HEAD's "tag 0.3.0 with `clutch release --minor`", and a protocol that tags at the end of a phase instead of its start.
6. The sixth `## Verification` command exits 0. `docs/parallel-tickets-plan.md` has the release counts `{0.3.0: 4, 0.4.0: 2, 0.5.0: 2}`. It has no `Dormant` and no "the other four". It has "the other six" and `docs-truth-sweep-code-strings`. Its section 7 names all seven do-not-grow paths, and its do-not-grow rule-location row says section A and `Engine conduct`, not section B. `docs/training-data-plan.md` has the counts `{0.3.0: 2, 0.5.0: 1, 0.6.0: 4}`. It no longer contains "written without the redactor" or "Unscrubbed harvest", and it names `clutch/runner.py::harvest`. Ruled out: HEAD's five-file list and section B, the stale harvest statements, and a missed or doubled rename.
7. The seventh `## Verification` command exits 0. Each of the six rename-only plans has exactly its renamed release-token counts. Ruled out: HEAD's counts, which carry `0.2.0`, and any token shifted twice or skipped.

## Verification
```
uv run python -c "import re, pathlib; t = pathlib.Path('docs/roadmap.md').read_text(); s1 = t.split('## 1. Release plan', 1)[1].split('### 1.1 ', 1)[0]; assert re.findall(r'^\| \*\*(0\.\d\.0)\*\* \|', s1, re.M) == ['0.3.0', '0.4.0', '0.5.0', '0.6.0', '0.7.0']; assert re.findall(r'^### (0\.\d\.0)', t, re.M) == ['0.3.0', '0.3.0', '0.4.0', '0.5.0', '0.6.0', '0.7.0']; assert '0.1.5 today' not in t and 'its slot is skipped' not in t; hits = [l for l in t.splitlines() if '0.2.0' in l]; assert len(hits) == 1 and hits[0].count('0.2.0') == 1 and 'one minor lower' in hits[0]; assert all(p in s1 for p in ('v0.3.0', 'c761b213', 'clutch release --minor', 'at its start', 'slides behind 0.6.0', '0.3.0 dedup tickets merged', 'land in 0.3.0 because')); assert all(p in t for p in ('The evidence store (0.3.0)', 'Export and eval (0.6.0)', '0.4.0 is conditional on it', '| 0.5.0, declared in', 'scheduled in 0.3.0.', 'Order in 0.3.0 and 0.5.0', 'Journal window.** 0.4.0 runs only', '(0.3.0) widens the reviewer prompt', 'mechanical checker in 0.4.0.', 'during the 0.4.0 window if it runs, else in 0.5.0', 'at the end of 0.3.0;', '0.7.0' + chr(39) + 's ship gate'))"
uv run python -c "import re, pathlib; t = pathlib.Path('docs/roadmap.md').read_text(); B = chr(96); s = t.split('## 8. Master ticket table', 1)[1].split('## 9. ', 1)[0]; rows = {int(p[1]): p for l in s.splitlines() if re.match(r'^\| \d+ \|', l) for p in [l.split('|')]}; body = lambda n: '|'.join(rows[n][8:]); merged = {1: 'provider-capture-overwrite', 2: 'provider-failure-single-mapper', 3: 'release-verb', 4: 'docs-truth-sweep', 5: 'conduct-files-parity', 6: 'paved-roads-name-verbs', 7: 'dev-surface-completeness', 9: 'unit-criteria-disk-snag', 10: 'fence-closure-registries', 11: 'watch-surface-tier-truth', 12: 'redaction-harvest-seam', 13: 'contention-authoring-rules'}; bad = [n for n, m in merged.items() if rows[n][2].strip() != '~~' + B + m + B + '~~' or not body(n).strip().startswith('**Merged** (' + B + 'tickets/' + m + '/' + B + ').')]; assert not bad, bad; assert 'tickets/docs-truth-sweep-code-strings/' in body(4); assert 'Authored 2026-11-14' not in s; assert rows[8][2].strip() == '~~' + B + 'host-prompts-no-dev-py' + B + '~~' and '73a41696' in body(8); assert rows[88][2].strip() == '~~' + B + 'superseded-settles' + B + '~~' and rows[88][7].strip() == '' and 'box-000471' in body(88) and 'box-000473' in body(88); assert rows[93][6].strip() == 'rows 89-92'; authored = {90: ['roadmap-row-message'], 92: ['release-publish']}; assert all(rows[n][2].strip() == B + rows[n][2].strip().strip(B) + B and body(n).strip().startswith('**Authored** (' + ', '.join(B + 'tickets/' + m + '/' + B for m in v) + ').') for n, v in authored.items()); assert not [n for n in rows if n not in merged and n not in (8, 88) and rows[n][2].strip().startswith('~~')]; assert 'keeps bumping only the patch' not in body(3) and 'Needed to tag' not in body(3); assert 'Superseded by' not in body(6) and 'dev.py' not in body(6); assert all(p in body(92) for p in ('never bumps the version', 'v<version>', 'on HEAD', 'box-000480'))"
uv run python -c "import pathlib; t = pathlib.Path('docs/roadmap.md').read_text(); sec = lambda a, b: t.split(a, 1)[1].split(b, 1)[0]; line = lambda s, p: next(l for l in s.splitlines() if p in l); s26 = sec('### 2.6 ', '## 3. '); assert 'in no rule file' not in s26 and all(p in s26 for p in ('section A', 'tests/integration/test_cli.py', 'tests/integration/test_watch.py', 'contention-authoring-rules' + chr(96) + ' (done)')); assert 'docs-truth-sweep-code-strings' + chr(96) + ' (done)' in line(sec('### 2.1 ', '### 2.2 '), '| 14 |'); s31 = sec('### 3.1 ', '### 3.2 '); assert 'the one operator surface' not in s31; assert all(p in line(s31, 'paved roads print') for p in ('doctor.py', 'providers.py', 'tickets/paved-roads-name-verbs/')); assert 'redaction-harvest-seam' + chr(96) + ' (done)' in line(s31, 'harvest.json'); assert 'docs-truth-sweep-code-strings' + chr(96) + ' (done)' in line(s31, 'argparse'); s41 = sec('### 4.1 ', '### 4.2 '); assert 'tickets/paved-roads-name-verbs/' in line(s41, '| 452-453'); assert 'docs-truth-sweep-code-strings' in line(s41, '| 694 |'); s42 = sec('### 4.2 ', '### 4.3 '); assert 'harvest is unscrubbed' not in s42 and 'redaction-harvest-seam' in line(s42, 'redact.py:7-9'); assert 'docs-truth-sweep-code-strings' in line(s42, 'Dormant'); s5 = sec('## 5. ', '## 6. '); assert 'docs-truth-sweep-code-strings' in line(s5, '11. **The mergequeue docstring**'); d17 = line(s5, '17. '); assert d17.startswith('17. ~~**Superseded is settled.**') and 'box-000471' in d17 and 'box-000473' in d17; d4 = line(sec('## 6. ', '## 7. '), '4. **Split the'); assert 'five large' not in d4 and 'test_cli.py' in d4 and 'test_watch.py' in d4"
uv run python -c "import pathlib; t = pathlib.Path('docs/roadmap-driver-plan.md').read_text(); B = chr(96); assert '0.2.0' not in t; assert all(p in t for p in ('Release 0.3.0, as its last group', 'rows 89-93', 'runs 0.4.0 onward', 'Release 0.3.0, last group.', 'before 0.3.0' + chr(39) + 's dedup', 'box-000471', 'box-000473', 'reject_ticket', 'test_split_dispatches_reviewed_rework', 'specs-in-package', '### 1. ~~Superseded is settled', '| 1 | ~~' + B + 'superseded-settles' + B + '~~ |', '| 6 | ' + B + 'driver-loop' + B + ' | feature | P1 | 2, 3, 4, 5 |', 'clutch/release.py::release', 'never bumps the version', 'on HEAD', 'box-000480')); assert not any(p in t for p in ('parent settles by itself', 'neither settles the parent', 'lingers', 'until a person rejects it', 'Ticket 1 before 2', 'projection, verdict refusal', './dev.py release', 'nothing tags', 'new ' + B + 'clutch/release.py' + B, 'Section 5: ' + B + 'clutch release' + B))"
uv run python -c "import pathlib; t = pathlib.Path('docs/journal-sql-refactor-plan.md').read_text(); assert '0.2.0' not in t and 'tag 0.3.0' not in t; s = t.split('## Release protocol', 1)[1].split('## Problem', 1)[0]; assert all(p in s for p in ('At the end of 0.3.0', 'v0.4.0', 'until 0.4.0 ships', 'scheduled in 0.4.0', 'opens 0.5.0', 'v0.5.0', 'clutch release --minor')); assert all(p in t for p in ('Release 0.4.0, conditional', 'merged in 0.3.0', 'slides behind 0.6.0', '0.6.0) adds the dependency first', 'the re-measurement at the end of 0.3.0', 'the 0.3.0 ticket', 'at the end of 0.3.0; attach', '(0.5.0), so they run in sequence', '**Release version.** 0.4.0 is a minor version'))"
uv run python -c "import re, pathlib, collections; count = lambda f: dict(collections.Counter(re.findall(r'(?<![\d.])0\.\d\.0(?![\d])', pathlib.Path('docs', f).read_text()))); p = pathlib.Path('docs/parallel-tickets-plan.md').read_text(); assert count('parallel-tickets-plan.md') == {'0.3.0': 4, '0.4.0': 2, '0.5.0': 2}, count('parallel-tickets-plan.md'); assert 'Dormant' not in p and 'the other four' not in p and 'the other six' in p and 'docs-truth-sweep-code-strings' in p; s7 = p.split('### 7. ', 1)[1].split('### 8. ', 1)[0]; assert all('tests/integration/' + f in s7 for f in ('test_daemon_composition.py', 'test_drain.py', 'test_mergequeue.py', 'test_stages.py', 'test_cli.py', 'test_watch.py', 'serve_rig.py')); row = next(l for l in p.splitlines() if l.startswith('| Do-not-grow list')); assert 'section A' in row and 'Engine conduct' in row and 'section B' not in row; t = pathlib.Path('docs/training-data-plan.md').read_text(); assert count('training-data-plan.md') == {'0.3.0': 2, '0.5.0': 1, '0.6.0': 4}, count('training-data-plan.md'); assert 'written without the redactor' not in t and 'Unscrubbed harvest' not in t and 'clutch/runner.py::harvest' in t"
uv run python -c "import re, pathlib, collections; count = lambda f: dict(collections.Counter(re.findall(r'(?<![\d.])0\.\d\.0(?![\d])', pathlib.Path('docs', f).read_text()))); want = {'annotations-index-plan.md': {'0.3.0': 1, '0.4.0': 1, '0.6.0': 7}, 'gemini-graphics-refactor-plan.md': {'0.3.0': 3, '0.5.0': 11, '0.6.0': 1}, 'document-agent-plan.md': {'0.3.0': 1, '0.5.0': 1, '0.6.0': 2, '0.7.0': 2}, 'evidence-trail-plan.md': {'0.3.0': 7, '0.6.0': 5, '0.7.0': 1}, 'stage-panels-plan.md': {'0.3.0': 1, '0.5.0': 1, '0.6.0': 6, '0.7.0': 4}, 'upstream-issue-plan.md': {'0.3.0': 2, '0.5.0': 1}}; bad = {f: count(f) for f in want if count(f) != want[f]}; assert not bad, bad"
```

## Definition of rejected
The branch is rejected if it:
- changes any file outside the fence, or any code, spec, test, `CLAUDE.md` or `AGENTS.md`;
- changes a gate, cadence, operator action, hand test or calibration text beyond renaming a release token inside it, except the edits Scope out bullet 1 lists;
- shifts a release token twice, leaves one unrenamed, or changes a version string that does not name a phase;
- strikes or links a row Scope in does not name, or deletes a roadmap section 8 row, a numbered decision or a plan section instead of striking it (the driver plan's "Where each piece lives" `superseded` row is the one table row Scope in deletes);
- renumbers roadmap rows, decisions, or the driver plan's sections;
- edits an audit row, Status section or plan ticket table that Scope in does not name;
- states a behavior that the cited code or journal does not have.

## Time budget
- expected: 60m
- stuck: 150m
