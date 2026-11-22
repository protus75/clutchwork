---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- io-helpers-loop
- shared-git-fake-integration
- shared-review-script

## Runs before
- shared-git-fake

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

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in batch tickets authored after this helper chain merges. Most skipped files import their scaffolding from a few large skipped files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is step 7 of 7 in the helper chain (`io-helpers-cli`, `-drain`, `-stages`, `-daemon`, `-config`, `-loop`, `-misc`); each step depends on the one before it.

Six files remain: `test_inbox.py` (`arrival`, `raw_report`), `test_author.py` (the `_routes`, `_box`, `_run` family and `requisition_reply`, 5 importers), `test_retro_box.py` (`PROPOSAL`), `test_retro.py` (`rig`, `completed`, `merged`), `test_kill_signal_journal.py` (`Rig`, `decision`) and `test_git.py`, from which 35 files import `commit_lock` to build a real `Git`. `test_git.py` tests real git and is in `REAL_IO_TESTS`: it stays unskipped and keeps its own real-git helpers for its own tests.

When this ticket is done, `tests/misc_helpers.py` defines every name that another test file imports from `tests/integration/test_inbox.py`, `test_author.py`, `test_retro_box.py`, `test_retro.py`, `test_kill_signal_journal.py` and `test_git.py` (all under `tests/integration/`) (the names are listed under Scope in), and each of those 37 importers takes it from `tests.misc_helpers`. The helpers use the shared fakes, so a restored test file that needs them does not start a process or run git, and a later batch ticket can turn a file back on without first fixing a helper that sits in a skipped file.

The helpers follow the rules in `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`, created by `shared-git-fake`; read it in the worktree), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a journal as `tests.fakes.FakeJournal` unless the helper's subject is journal persistence, and a disk write only under a `tmp_path` the caller passes in. A model-reply helper or config text reuses `tests/stage_replies.py` and `tests/config_fixture.py` (created by `shared-review-script` and `shared-serve-rig-config`, merged before `shared-fakes-guard`); a helper never copies either. The owner requires restored tests to be fast and to reuse shared fixtures: this module is the one place each helper below lives.

## Boundary contract
### Shared inbox, author, retro, kill and commit-lock test helpers
- disposition: create
- owner: tests/misc_helpers.py
- consumers: the 37 test files listed in `## Scope fence` that import from `tests/integration/test_inbox.py`, `test_author.py`, `test_retro_box.py`, `test_retro.py`, `test_kill_signal_journal.py` and `test_git.py` (all under `tests/integration/`), and the later batch tickets that restore the skipped ones
- observable change: the names listed under Scope in move from `tests/integration/test_inbox.py`, `test_author.py`, `test_retro_box.py`, `test_retro.py`, `test_kill_signal_journal.py` and `test_git.py` (all under `tests/integration/`) into `tests/misc_helpers.py`, rewritten onto the shared fakes; every importer's import line changes to `tests.misc_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub (for example `test_cli.Clock` in `tests/integration/test_shared_fakes_adoption.py`) stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_misc_helpers.py` imports each moved name from `tests.misc_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_misc_helpers.py
- post-merge source of truth: tests/misc_helpers.py
- closest existing: `tests/fakes.py` (FakeClock, FakeExec, FakeFileSystem, FakeJournal, `turn`, `until`) and `tests/git_fake.py::GitFake` supply the fake seams but none of the scaffolding below; the hub definitions today do real git and processes, so a skipped file cannot reuse them
- earning reason: consolidation of evidenced duplicates and shared use: 37 files import these names from `tests/integration/test_inbox.py`, `test_author.py`, `test_retro_box.py`, `test_retro.py`, `test_kill_signal_journal.py` and `test_git.py` (all under `tests/integration/`), and the hub is skipped, so no importer can be restored until the names live in an unskipped module that follows the I/O rules

## Scope in / Scope out
Scope in:
- Create `tests/misc_helpers.py` holding these moved names, each rewritten as described, keeping its signature unless a change is named: `PROPOSAL`, `Rig`, `_box`, `_events`, `_failure`, `_routes`, `_run`, `arrival`, `block`, `bug_reply`, `commit_lock`, `completed`, `decision`, `merged`, `raw_report`, `requisition_reply`, `rig`.
  - From `test_inbox.py`: `raw_report`, `arrival` (writes an arrival file under `tmp_path`). From `test_author.py`: `block`, `_run`, `_routes`, `_box`, `_events`, `_failure`, `bug_reply`, `requisition_reply` (a model-reply shape: the module re-exports `tests/stage_replies.py`'s, no copy). From `test_retro_box.py`: `PROPOSAL`. From `test_retro.py`: `rig`, `completed`, `merged`. From `test_kill_signal_journal.py`: `Rig` (it builds `LocalFileSystem`; `FakeFileSystem`) and `decision`.
  - `commit_lock(state_dir)`: `test_git.py::commit_lock` is the only name any file imports from `test_git.py`. It builds a real `CommitLock` (`clutch/lockfile.py`: `os.open` and `flock` on `state_dir/commit.lock`). The new `commit_lock(state_dir)` returns `asyncio.Lock()` and touches no disk; `tests/git_fake.py::GitFake` holds its own `asyncio.Lock` for `_commit_lock`, so a restored test that still builds a `Git` passes this lock and never opens a file. When `Git` reads an attribute only `CommitLock` has (such as `path`), the run stops as a premise failure naming it. Importers that need a real lock keep importing `commit_lock` from `test_git.py` unchanged: `tests/integration/test_git_tree_id.py` and `tests/integration/test_lockfile.py` (both in `REAL_IO_TESTS`), `tests/regress_status_optional_locks.py` and the real harnesses under `tests/harness/`. Every other importer (the skipped integration files) takes `commit_lock` from `tests.misc_helpers`.
- In every importer listed in `## Scope fence`, change only the import line (also an import line inside a function) so each moved name comes from `tests.misc_helpers`. Every name any file imports from these hubs is moved, except where Scope in says otherwise, so no importer keeps an import from a hub. Names an importer takes from other hubs stay as they are. A module import (`from tests.integration import <hub>`) is not an import of a name and stays.
- Each hub file (`tests/integration/test_inbox.py`, `tests/integration/test_author.py`, `tests/integration/test_retro_box.py`, `tests/integration/test_retro.py`, `tests/integration/test_kill_signal_journal.py`) deletes its definition of every moved name it defines and imports the name back from `tests.misc_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line, and every name it defines that no other file imports). Its own tests keep working through the name it imports back; the hub module keeps each moved name as a module attribute.
- Earlier helper modules (`tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py`) change only where one of them imports a name this ticket moves.
- Create `tests/unit/test_misc_helpers.py`: one test per moved name that runs without reading a repo file, calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name above is importable from `tests.misc_helpers`. 
- `commit_lock` has 35 importers; 8 are real-I/O users kept on the real one (named above), the other 27 are fenced here, and the earlier helper modules (`tests/*_helpers.py`) that import it change to `tests.misc_helpers` or drop it where `GitFake` made it unnecessary.
- `tests/integration/test_git.py` stays in `REAL_IO_TESTS` and unskipped and is not edited here.

Scope out:
- Restoring any skipped test file (later batch tickets): a hub file stays skipped and its tests are unchanged.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior.
- Defining in `tests/misc_helpers.py` a class that duplicates `tests/fakes.py` or `tests/git_fake.py`: use the shared fakes. A thin subclass is not needed by any moved name. `tests/integration/test_git.py` (not edited; it keeps its real `commit_lock` and every test) and `tests/spool_captures.py`: `read_capture`, `list_captures` and `write_capture` live there, not in `test_git.py`, and already take an `fs=` argument, so a restored test passes a `FakeFileSystem` and nothing is added here.
- Skipped importers may still break semantically; their batch ticket fixes that.

## Scope fence
- tests/misc_helpers.py
- tests/unit/test_misc_helpers.py
- tests/integration/test_inbox.py
- tests/integration/test_author.py
- tests/integration/test_retro_box.py
- tests/integration/test_retro.py
- tests/integration/test_kill_signal_journal.py
- tests/integration/test_box.py
- tests/integration/test_checkpoint.py
- tests/integration/test_cli.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_soak.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/test_drain.py
- tests/integration/test_fixture_host.py
- tests/integration/test_gates.py
- tests/integration/test_heartbeat.py
- tests/integration/test_hostfiles.py
- tests/integration/test_hot_paths_snapshot.py
- tests/integration/test_image_candidates_select.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_lint_verb.py
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
- tests/cli_helpers.py
- tests/drain_helpers.py
- tests/stages_helpers.py
- tests/daemon_helpers.py
- tests/config_helpers.py
- tests/loop_helpers.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_misc_helpers.py` passes, and `tests/unit/test_misc_helpers.py` checks that `commit_lock(tmp_path / "state")` returns an `asyncio.Lock` and creates nothing under `tmp_path` (a real `CommitLock` creates `state/commit.lock` on entry), and that `arrival(...)` writes only under the `tmp_path` it is given.
2. `grep -rnE "from tests\.integration\.(test_inbox|test_author|test_retro_box|test_retro|test_kill_signal_journal) import" tests --include=*.py` prints nothing, and `grep -rlE "from tests\.integration\.test_git import" tests --include=*.py` lists only `tests/integration/test_git_tree_id.py`, `tests/integration/test_lockfile.py`, `tests/regress_status_optional_locks.py` and files under `tests/harness/` (the real-I/O users, which keep the real `commit_lock`).
3. `grep -nE "^(async def|def|class) (arrival|raw_report|_box|_events|_failure|_routes|_run|block|bug_reply|requisition_reply|PROPOSAL|completed|merged|rig|Rig|decision)\b|^(arrival|raw_report|_box|_events|_failure|_routes|_run|block|bug_reply|requisition_reply|PROPOSAL|completed|merged|rig|Rig|decision) =" tests/integration/test_inbox.py tests/integration/test_author.py tests/integration/test_retro_box.py tests/integration/test_retro.py tests/integration/test_kill_signal_journal.py` prints nothing: the hub files no longer define a moved name.
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
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/misc_helpers.py` defines a class that duplicates a shared fake or a copied reply or config helper.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 30m
- stuck: 60m
- reason: 37 import lines and the hub definitions move in one change because a name must resolve in every importer at once; splitting by importer leaves a name defined in two places, and the files share one module so they stay together
