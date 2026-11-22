---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- io-helpers-stages
- shared-git-fake-integration

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_daemon_composition.py
- tests/integration/test_mergequeue.py
- tests/integration/test_daemon_admission.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in batch tickets authored after this helper chain merges. Most skipped files import their scaffolding from a few large skipped files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is step 4 of 7 in the helper chain (`io-helpers-cli`, `-drain`, `-stages`, `-daemon`, `-config`, `-loop`, `-misc`); each step depends on the one before it.

Three large skipped files feed the serve, daemon and merge tests: `test_daemon_composition.py` (2148 lines; 25 importers of `CoreRig`, `LiveDrain` and the wiring assertions), `test_mergequeue.py` (1242 lines; 23 importers of `ctx`, `ready`, `commit`, `approve`) and `test_daemon_admission.py` (297 lines; 4 importers of `turn`, `tickets` and two assertions).

When this ticket is done, `tests/daemon_helpers.py` defines every name that another test file imports from `tests/integration/test_daemon_composition.py`, `tests/integration/test_mergequeue.py` and `tests/integration/test_daemon_admission.py` (the names are listed under Scope in), and each of those 38 importers takes it from `tests.daemon_helpers`. The helpers use the shared fakes, so a restored test file that needs them does not start a process or run git, and a later batch ticket can turn a file back on without first fixing a helper that sits in a skipped file.

The helpers follow the rules in `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`, created by `shared-git-fake`; read it in the worktree), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a journal as `tests.fakes.FakeJournal` unless the helper's subject is journal persistence, and a disk write only under a `tmp_path` the caller passes in. A model-reply helper or config text reuses `tests/stage_replies.py` and `tests/config_fixture.py` (created by `shared-review-script` and `shared-serve-rig-config`, merged before `shared-fakes-guard`); a helper never copies either. The owner requires restored tests to be fast and to reuse shared fixtures: this module is the one place each helper below lives.

## Boundary contract
### Shared daemon and merge-queue test helpers
- disposition: create
- owner: tests/daemon_helpers.py
- consumers: the 38 test files listed in `## Scope fence` that import from `tests/integration/test_daemon_composition.py`, `tests/integration/test_mergequeue.py` and `tests/integration/test_daemon_admission.py`, and the later batch tickets that restore the skipped ones
- observable change: the names listed under Scope in move from `tests/integration/test_daemon_composition.py`, `tests/integration/test_mergequeue.py` and `tests/integration/test_daemon_admission.py` into `tests/daemon_helpers.py`, rewritten onto the shared fakes; every importer's import line changes to `tests.daemon_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub (for example `test_cli.Clock` in `tests/integration/test_shared_fakes_adoption.py`) stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_daemon_helpers.py` imports each moved name from `tests.daemon_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_daemon_helpers.py
- post-merge source of truth: tests/daemon_helpers.py
- closest existing: `tests/fakes.py` (FakeClock, FakeExec, FakeFileSystem, FakeJournal, `turn`, `until`) and `tests/git_fake.py::GitFake` supply the fake seams but none of the scaffolding below; the hub definitions today do real git and processes, so a skipped file cannot reuse them
- earning reason: consolidation of evidenced duplicates and shared use: 38 files import these names from `tests/integration/test_daemon_composition.py`, `tests/integration/test_mergequeue.py` and `tests/integration/test_daemon_admission.py`, and the hub is skipped, so no importer can be restored until the names live in an unskipped module that follows the I/O rules

## Scope in / Scope out
Scope in:
- Create `tests/daemon_helpers.py` holding these moved names, each rewritten as described, keeping its signature unless a change is named: `CoreRig`, `LiveDrain`, `admission`, `admission_control`, `approve`, `assert_core_wiring`, `assert_idle`, `assert_reachable`, `assert_startup_pause_wiring`, `capture_pipeline_queue`, `commit`, `conflict`, `ctx`, `facts`, `host`, `import_closure`, `production_writer`, `ready`, `scripted`, `sources`, `tickets`, `turn`, `without_core_import`.
  - From `test_daemon_composition.py`: `CoreRig` (68-line rig that writes config and files and runs the daemon core with fakes; its writes stay under a passed `tmp_path`), `LiveDrain` (113 lines; today it builds `SubprocessExec` and `LocalFileSystem` and a real drain: it becomes `FakeExec` and `FakeFileSystem` based), `assert_core_wiring`, `assert_startup_pause_wiring`, `capture_pipeline_queue`, `production_writer` (today it uses real git), `sources`, `without_core_import`.
  - From `test_mergequeue.py`: the `ctx` fixture (builds a repo, `Git(SubprocessExec())`, `LocalFileSystem`; becomes `GitFake` + `FakeExec` + `FakeFileSystem`/`tmp_path`), `commit`, `approve`, `ready`, `conflict` (each runs git; become calls on `ctx.git`'s `GitFake`), `admission`, `admission_control`, `facts`, `host`, `scripted`, `import_closure`.
  - From `test_daemon_admission.py`: `tickets` (fixture writing two tickets under `tmp_path`), `turn` (the same as `tests.fakes.turn`: the module re-exports the shared function and does not define a second one), `assert_idle`, `assert_reachable`.
  - `sources()` reads every `clutch/**/*.py` through a `Path(__file__)` anchor (now `parents[1]` of `tests/daemon_helpers.py`); it stays a read-only repo read. `import_closure(sources)` and `without_core_import(material)` are pure functions of a dict of module sources.
  - The module imports `CONFIG`, `ENV`, `SECRET`, `SPECS`, `STEM`, `TICKET`, `adopt_conduct` from `tests.stages_helpers` and `CONFIG`/`ENV` pieces from `tests.cli_helpers`; `ctx` no longer imports `commit_lock`.
- In every importer listed in `## Scope fence`, change only the import line (also an import line inside a function) so each moved name comes from `tests.daemon_helpers`. Every name any file imports from these hubs is moved, except where Scope in says otherwise, so no importer keeps an import from a hub. Names an importer takes from other hubs stay as they are. A module import (`from tests.integration import <hub>`) is not an import of a name and stays.
- Each hub file (`tests/integration/test_daemon_composition.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_daemon_admission.py`) deletes its definition of every moved name it defines and imports the name back from `tests.daemon_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line, and every name it defines that no other file imports). Its own tests keep working through the name it imports back; the hub module keeps each moved name as a module attribute.
- Earlier helper modules (`tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`) change only where one of them imports a name this ticket moves.
- Create `tests/unit/test_daemon_helpers.py`: one test per moved name that runs without reading a repo file, calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name above is importable from `tests.daemon_helpers`. `sources()` reads the repo, so its test, and the one that feeds its output to `import_closure` and `without_core_import`, is the new `tests/integration/test_daemon_helpers_sources.py` (it reads repo files only through a `Path(__file__)` anchor and writes nothing); the unit test gives `import_closure` and `without_core_import` a hand-built dict of module sources instead.
- `test_mergequeue.import_closure` and `test_scheduler.import_closure` are different functions with the same name; this ticket moves the mergequeue one as `import_closure`, and `io-helpers-loop` moves the scheduler one under its own distinct name (`scheduler_import_closure`, aliased back at the two importers).
- `tests/integration/test_daemon_composition.py` imports from `tests/integration/test_providers.py`, `tests/integration/test_scheduler.py`, `tests/integration/serve_rig.py` and others that later steps move; those lines stay untouched here.

- Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.
Scope out:
- Restoring any skipped test file (later batch tickets): a hub file stays skipped and its tests are unchanged.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior.
- Defining in `tests/daemon_helpers.py` a class that duplicates `tests/fakes.py` or `tests/git_fake.py`: use the shared fakes. A thin subclass is not needed by any moved name. Names that no other file imports stay in their hub (for example the many tests in `test_daemon_composition.py` that use `CoreRig`).
- Skipped importers may still break semantically; their batch ticket fixes that.

## Scope fence
- tests/daemon_helpers.py
- tests/unit/test_daemon_helpers.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_mergequeue.py
- tests/integration/test_daemon_admission.py
- tests/integration/test_bug_gate.py
- tests/integration/test_caps.py
- tests/integration/test_checkpoint.py
- tests/integration/test_conflict_rerun_swap.py
- tests/integration/test_control.py
- tests/integration/test_control_cli.py
- tests/integration/test_daemon_config.py
- tests/integration/test_daemon_core_queue_seams.py
- tests/integration/test_daemon_pause.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_drain.py
- tests/integration/test_evidence_envelope.py
- tests/integration/test_flake.py
- tests/integration/test_heartbeat.py
- tests/integration/test_host_mechanical.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_merge.py
- tests/integration/test_merge_admission_owner.py
- tests/integration/test_merge_config_local.py
- tests/integration/test_merge_model_resolve.py
- tests/integration/test_mergequeue_tree_moved.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_reject_reason_both_paths.py
- tests/integration/test_requisition_identity_record.py
- tests/integration/test_restart_timers.py
- tests/integration/test_rework.py
- tests/integration/test_rework_failure_terminal_findings.py
- tests/integration/test_rework_supervise.py
- tests/integration/test_scheduler.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_storm_hold.py
- tests/integration/test_storm_notification_activation.py
- tests/integration/test_storm_producer.py
- tests/integration/test_ticket_write_serialization.py
- tests/integration/test_watchdog.py
- tests/integration/test_watchdog_activation.py
- tests/cli_helpers.py
- tests/drain_helpers.py
- tests/stages_helpers.py
- tests/integration/test_daemon_helpers_sources.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_daemon_helpers.py` passes, and `tests/unit/test_daemon_helpers.py` and `tests/integration/test_daemon_helpers_sources.py` pass; the unit test checks that a `CoreRig` built over `tmp_path` writes its files only under `tmp_path`, that the `ctx` fixture's `StageContext.git` is the `GitFake` (its `fake.calls` records `init`, `add` and `commit`) with no `.git` directory, and that `daemon_helpers.turn is fakes.turn`.
2. `grep -rnE "from tests\.integration\.(test_daemon_composition|test_mergequeue|test_daemon_admission) import" tests --include=*.py` prints nothing: every name any file imports from these hubs is moved, so a leftover line names the importer that was missed.
3. `grep -nE "^(async def|def|class) (CoreRig|LiveDrain|assert_core_wiring|assert_startup_pause_wiring|capture_pipeline_queue|production_writer|sources|without_core_import|admission|admission_control|approve|commit|conflict|ctx|facts|host|import_closure|ready|scripted|assert_idle|assert_reachable|tickets|turn)\b|^(CoreRig|LiveDrain|assert_core_wiring|assert_startup_pause_wiring|capture_pipeline_queue|production_writer|sources|without_core_import|admission|admission_control|approve|commit|conflict|ctx|facts|host|import_closure|ready|scripted|assert_idle|assert_reachable|tickets|turn) =" tests/integration/test_daemon_composition.py tests/integration/test_mergequeue.py tests/integration/test_daemon_admission.py` prints nothing: the hub files no longer define a moved name.
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/daemon_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the same number of skipped tests as on the base commit and a passed count that exceeds the base by exactly the tests in the new `tests/integration/test_daemon_helpers_sources.py`, both recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object).

## Verification
```
./dev.py test tests/unit/test_daemon_helpers.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test that runs today fails or is skipped, or a skipped test becomes unskipped.
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/daemon_helpers.py` defines a class that duplicates a shared fake or a copied reply or config helper.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 30m
- stuck: 60m
- reason: 38 import lines and the hub definitions move in one change because a name must resolve in every importer at once; splitting by importer leaves a name defined in two places, and the files share one module so they stay together
