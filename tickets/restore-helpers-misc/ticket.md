---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- restore-helpers-loop
- shared-review-script

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_inbox.py
- tests/integration/test_author.py
- tests/integration/test_retro_box.py
- tests/integration/test_retro.py
- tests/integration/test_kill_signal_journal.py
- tests/integration/test_git.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in batches (`restore-io-tests-01` through `restore-io-tests-39`). Most skipped files import their scaffolding from a few large skipped files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is step 7 of 7 in the helper chain (`restore-helpers-cli`, `-drain`, `-stages`, `-daemon`, `-config`, `-loop`, `-misc`); each step depends on the one before it.

Six files remain: `test_inbox.py` (`arrival`, `raw_report`), `test_author.py` (the `_routes`, `_box`, `_run` family and `requisition_reply`, 5 importers), `test_retro_box.py` (`PROPOSAL`), `test_retro.py` (`rig`, `completed`, `merged`), `test_kill_signal_journal.py` (`Rig`, `decision`) and `test_git.py`, from which 34 files import `commit_lock` to build a real `Git`. `test_git.py` tests real git and is in `REAL_IO_TESTS`: it stays unskipped and keeps its own real-git helpers for its own tests.

When this ticket is done, `tests/misc_helpers.py` defines every name that another test file imports from `tests/integration/test_inbox.py`, `test_author.py`, `test_retro_box.py`, `test_retro.py`, `test_kill_signal_journal.py` and `test_git.py` (all under `tests/integration/`) (the names are listed under Scope in), and each of those 45 importers takes it from `tests.misc_helpers`. The helpers use the shared fakes, so a restored test file that needs them does not start a process or run git, and a later batch ticket (`restore-io-tests-01` onward) can turn a file back on without first fixing a helper that sits in a skipped file.

The helpers follow the rules in `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`, created by `shared-git-fake`; read it in the worktree), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a journal as `tests.fakes.FakeJournal` unless the helper's subject is journal persistence, and a disk write only under a `tmp_path` the caller passes in. A model-reply helper or config text reuses `tests/stage_replies.py` and `tests/config_fixture.py` (created by `shared-review-script` and `shared-serve-rig-config`, merged before `shared-fakes-guard`); a helper never copies either. The owner requires restored tests to be fast and to reuse shared fixtures: this module is the one place each helper below lives.

## Boundary contract
### Shared inbox, author, retro, kill and commit-lock test helpers
- disposition: create
- owner: tests/misc_helpers.py
- consumers: the 45 test files listed in `## Scope fence` that import from `tests/integration/test_inbox.py`, `test_author.py`, `test_retro_box.py`, `test_retro.py`, `test_kill_signal_journal.py` and `test_git.py` (all under `tests/integration/`), and the `restore-io-tests-NN` batch tickets that restore the skipped ones
- observable change: the names listed under Scope in move from `tests/integration/test_inbox.py`, `test_author.py`, `test_retro_box.py`, `test_retro.py`, `test_kill_signal_journal.py` and `test_git.py` (all under `tests/integration/`) into `tests/misc_helpers.py`, rewritten onto the shared fakes; every importer's import line changes to `tests.misc_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub (for example `test_cli.Clock` in `tests/integration/test_shared_fakes_adoption.py`) stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_misc_helpers.py` imports each moved name from `tests.misc_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_misc_helpers.py
- post-merge source of truth: tests/misc_helpers.py
- closest existing: `tests/fakes.py` (FakeClock, FakeExec, FakeFileSystem, FakeJournal, `turn`, `until`) and `tests/git_fake.py::GitFake` supply the fake seams but none of the scaffolding below; the hub definitions today do real git and processes, so a skipped file cannot reuse them
- earning reason: consolidation of evidenced duplicates and shared use: 45 files import these names from `tests/integration/test_inbox.py`, `test_author.py`, `test_retro_box.py`, `test_retro.py`, `test_kill_signal_journal.py` and `test_git.py` (all under `tests/integration/`), and the hub is skipped, so no importer can be restored until the names live in an unskipped module that follows the I/O rules

## Scope in / Scope out
Scope in:
- Create `tests/misc_helpers.py` holding these moved names, each rewritten as described, keeping its signature unless a change is named: `PROPOSAL`, `Rig`, `_box`, `_events`, `_failure`, `_routes`, `_run`, `arrival`, `block`, `bug_reply`, `commit_lock`, `completed`, `decision`, `merged`, `raw_report`, `requisition_reply`, `rig`.
  - From `test_inbox.py`: `raw_report`, `arrival` (writes an arrival file under `tmp_path`). From `test_author.py`: `block`, `_run`, `_routes`, `_box`, `_events`, `_failure`, `bug_reply`, `requisition_reply` (a model-reply shape: the module re-exports `tests/stage_replies.py`'s, no copy). From `test_retro_box.py`: `PROPOSAL`. From `test_retro.py`: `rig`, `completed`, `merged`. From `test_kill_signal_journal.py`: `Rig` (it builds `LocalFileSystem`; `FakeFileSystem`) and `decision`.
  - `test_git.py::commit_lock` is the only name any file imports from it (34 importers, plus `tests/harness/host_loop.py`). It builds a real `CommitLock` over a real state directory. The module defines `commit_lock(state_dir)` returning a lock built over `tests.fakes.FakeFileSystem` and `FakeClock` (a plain `asyncio` lock if `CommitLock` has no fake-backed form) that needs no disk; the importers take it from `tests.misc_helpers`, while `test_git.py` keeps its own real `commit_lock` for its own real-git tests and does not import the new one.
  - The brief behind this chain also expected `read_capture` and `list_captures` to be imported from `test_git.py`; they are defined in `tests/spool_captures.py`, imported from there by `tests/integration/test_stages.py` and `tests/integration/test_mergequeue.py`. This ticket adds `read_capture`/`list_captures` equivalents over `FakeFileSystem` to `tests/misc_helpers.py` and edits those two hubs' import lines (`from tests.spool_captures import ...` becomes `from tests.misc_helpers import ...`) so a restored file reads captures through the fake; `tests/spool_captures.py` itself stays unchanged for its other users.
- In every importer listed in `## Scope fence`, change only the import line (and an in-function import line) from `tests.integration.<hub>` to `tests.misc_helpers` for the moved names; a line that imports a name this ticket does not move is kept and any name it still imports from another hub stays. A `tests.integration` module import (`from tests.integration import <hub>`) is not an importer of a name and stays.
- Each hub file (`tests/integration/test_inbox.py`, `tests/integration/test_author.py`, `tests/integration/test_retro_box.py`, `tests/integration/test_retro.py`, `tests/integration/test_kill_signal_journal.py`, `tests/integration/test_git.py`) deletes its definition of every moved name and imports the name back from `tests.misc_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line, and every name it defines that no other file imports). Its own tests keep working through the name it imports back; the hub module keeps each moved name as a module attribute.
- Earlier helper modules (`tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py`) change only where one of them imports a name this ticket moves.
- Create `tests/unit/test_misc_helpers.py`: one test per moved name that calls it with `tmp_path` and the shared fakes and asserts what it returns or writes, plus one test that every name above is importable from `tests.misc_helpers` and that the module source names no `subprocess` or `SubprocessExec` import.
- Importers of `commit_lock` are 34 files under `tests/integration` plus `tests/harness/host_loop.py` (its line 29); `## Scope fence` lists all of them, and each that is a hub of an earlier step (`test_cli.py`, `test_drain.py`, `test_stages.py`, `test_mergequeue.py`, `serve_rig.py` and others) also has its own earlier-moved helpers importing it, so `tests/*_helpers.py` modules that call `commit_lock` change their import to `tests.misc_helpers` or drop it where `GitFake` made it unnecessary.
- `tests/integration/test_git.py` stays in `REAL_IO_TESTS` and unskipped; its own tests do not change.

Scope out:
- Restoring any skipped test file (the `restore-io-tests-NN` tickets): a hub file stays skipped and its tests are unchanged.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior.
- Defining a `Fake*` or stand-in class in `tests/misc_helpers.py`: use the shared fakes. Any test in `test_git.py`; `tests/spool_captures.py`.
- Skipped importers may still break semantically; their batch ticket fixes that.

## Scope fence
- tests/misc_helpers.py
- tests/unit/test_misc_helpers.py
- tests/integration/test_inbox.py
- tests/integration/test_author.py
- tests/integration/test_retro_box.py
- tests/integration/test_retro.py
- tests/integration/test_kill_signal_journal.py
- tests/integration/test_git.py
- tests/harness/daemon_soak.py
- tests/harness/host_loop.py
- tests/harness/reliability_battery.py
- tests/harness/shakeout/bench.py
- tests/harness/shakeout/run.py
- tests/integration/test_box.py
- tests/integration/test_checkpoint.py
- tests/integration/test_cli.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_soak.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/test_drain.py
- tests/integration/test_fixture_host.py
- tests/integration/test_gates.py
- tests/integration/test_git_tree_id.py
- tests/integration/test_heartbeat.py
- tests/integration/test_hostfiles.py
- tests/integration/test_hot_paths_snapshot.py
- tests/integration/test_image_candidates_select.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_lint_verb.py
- tests/integration/test_lockfile.py
- tests/integration/test_menu_verb_parity.py
- tests/integration/test_merge.py
- tests/integration/test_mergequeue.py
- tests/integration/test_paved_roads.py
- tests/integration/test_reconcile.py
- tests/integration/test_reject_queue.py
- tests/integration/test_requisition.py
- tests/integration/test_requisition_identity_record.py
- tests/integration/test_roadmap_author.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_scorecard.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_stages.py
- tests/integration/test_stale_running.py
- tests/integration/test_status.py
- tests/integration/test_ticket_write_serialization.py
- tests/integration/test_tickets.py
- tests/integration/test_triage.py
- tests/integration/test_watch.py
- tests/regress_status_optional_locks.py
- tests/cli_helpers.py
- tests/drain_helpers.py
- tests/stages_helpers.py
- tests/daemon_helpers.py
- tests/config_helpers.py
- tests/loop_helpers.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_misc_helpers.py` passes, and `tests/unit/test_misc_helpers.py` checks that `commit_lock(tmp_path / "state")` creates no file under `tmp_path`, that `read_capture` returns the bytes a `write_capture` equivalent stored in the `FakeFileSystem`, and that `arrival(...)` writes only under the `tmp_path` it is given.
2. `grep -rnE "from tests\.integration\.(test_inbox|test_author|test_retro_box|test_retro|test_kill_signal_journal|test_git) import" tests --include=*.py` prints nothing: every importer takes the moved names from `tests.misc_helpers`, and a leftover line names the importer that was missed.
3. `grep -nE "^(async def|def|class) (arrival|raw_report|_box|_events|_failure|_routes|_run|block|bug_reply|requisition_reply|PROPOSAL|completed|merged|rig|Rig|decision)\b|^(arrival|raw_report|_box|_events|_failure|_routes|_run|block|bug_reply|requisition_reply|PROPOSAL|completed|merged|rig|Rig|decision) =" tests/integration/test_inbox.py tests/integration/test_author.py tests/integration/test_retro_box.py tests/integration/test_retro.py tests/integration/test_kill_signal_journal.py tests/integration/test_git.py` prints nothing: the hub files no longer define a moved name.
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/misc_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the same number of passed and skipped tests as on the base commit, both recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object).

## Verification
```
./dev.py test tests/unit/test_misc_helpers.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test that runs today fails or is skipped, or a skipped test becomes unskipped.
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/misc_helpers.py` defines a new `Fake*` or copied reply or config helper.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 30m
- stuck: 60m
- reason: 45 import lines and the hub definitions move in one change because a name must resolve in every importer at once; splitting by importer leaves a name defined in two places, and the files share one module so they stay together
