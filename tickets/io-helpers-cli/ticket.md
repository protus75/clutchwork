---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- disk-io-skip-per-file
- shared-git-fake-integration
- shared-fakes-guard

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_cli.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in batch tickets authored after this helper chain merges. Most skipped files import their scaffolding from a few large skipped files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is step 1 of 7 in the helper chain (`io-helpers-cli`, `-drain`, `-stages`, `-daemon`, `-config`, `-loop`, `-misc`); each step depends on the one before it.

`tests/integration/test_cli.py` (730 lines) is the most imported of them: 94 files take `ENV`, `root`, `ticket`, `write`, `git_out` and the rest from it, and it builds each `root` by running real `git init`, `add` and `commit` in a subprocess.

When this ticket is done, `tests/cli_helpers.py` defines every name that another test file imports from `tests/integration/test_cli.py` (the names are listed under Scope in), and each of those 94 importers takes it from `tests.cli_helpers`. The helpers use the shared fakes, so a restored test file that needs them does not start a process or run git, and a later batch ticket can turn a file back on without first fixing a helper that sits in a skipped file.

The helpers follow the rules in `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`, created by `shared-git-fake`; read it in the worktree), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a journal as `tests.fakes.FakeJournal` unless the helper's subject is journal persistence, and a disk write only under a `tmp_path` the caller passes in. A model-reply helper or config text reuses `tests/stage_replies.py` and `tests/config_fixture.py` (created by `shared-review-script` and `shared-serve-rig-config`, merged before `shared-fakes-guard`); a helper never copies either. The owner requires restored tests to be fast and to reuse shared fixtures: this module is the one place each helper below lives.

## Boundary contract
### Shared CLI test helpers
- disposition: create
- owner: tests/cli_helpers.py
- consumers: the 94 test files listed in `## Scope fence` that import from `tests/integration/test_cli.py`, and the later batch tickets that restore the skipped ones
- observable change: the names listed under Scope in move from `tests/integration/test_cli.py` into `tests/cli_helpers.py`, rewritten onto the shared fakes; every importer's import line changes to `tests.cli_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub (for example `test_cli.Clock` in `tests/integration/test_shared_fakes_adoption.py`) stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_cli_helpers.py` imports each moved name from `tests.cli_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_cli_helpers.py
- post-merge source of truth: tests/cli_helpers.py
- closest existing: `tests/fakes.py` (FakeClock, FakeExec, FakeFileSystem, FakeJournal, `turn`, `until`) and `tests/git_fake.py::GitFake` supply the fake seams but none of the scaffolding below; the hub definitions today do real git and processes, so a skipped file cannot reuse them
- earning reason: consolidation of evidenced duplicates and shared use: 94 files import these names from `tests/integration/test_cli.py`, and the hub is skipped, so no importer can be restored until the names live in an unskipped module that follows the I/O rules

## Scope in / Scope out
Scope in:
- Create `tests/cli_helpers.py` holding these moved names, each rewritten as described, keeping its signature unless a change is named: `CONFIG`, `Clock`, `ENV`, `PLAN`, `Stages`, `TICKET`, `cli`, `core_config`, `git_fake`, `git_out`, `journal`, `root`, `ticket`, `with_retro_driver`, `write`.
  - Constants moved verbatim: `ENV`, `PLAN`, `TICKET`, and `ticket(depends)`. `CONFIG` is the text `tests/config_fixture.py::build_config()` returns with no arguments (byte-identical to the literal in the hub today), never a copy. `Clock` is `tests.fakes.FakeClock`, imported into the module under the name `Clock`. `with_retro_driver(checkout, dispatch)` and `write(root, stem, text)` move unchanged (`write` writes only under the `root` it is given).
  - `Stages` (the scripted stage-dispatch seam) moves with the same behavior; its lock probe writes a lockfile under `checkout.config.state_dir`, which lies under the `tmp_path` repo.
  - `git_fake(root) -> GitFake` (one new name, defined here and reused by every later helper module): keeps one `GitFake` per `root` path in a module-level dict, creating it on first use. `tests/git_fake.py::GitFake` (merged by `shared-git-fake`; read it in the worktree) takes `GitFake(**overrides)` keyed by `Git` member name, answers a member with no override from its return annotation, and appends each call to `fake.calls` as `(name, args, kwargs)`.
  - `root` (pytest fixture): creates the same files under `tmp_path / "repo"` (`clutch/thing.py`, the plan file, `config.yaml`, `.gitignore`, the routed conduct files and the agent-rules file the fixture renders) but does not run `git init`, `add` or `commit`; it returns the path after creating `git_fake(path)`.
  - `git_out(root, *args)` stops running `git`: it appends `("git_out", args, {})` to `git_fake(root).calls` and returns `""`. A batch ticket whose test asserted real git output asserts on `fake.calls` or on an override of the `Git` member that answers it, and keeps the behavior the test checks.
  - `journal(root)` returns a `tests.fakes.FakeJournal` when it supplies every method the importers call on it (`read`, `append`); if one is missing the run stops as a premise failure naming the method.
  - `cli(root, *argv, stages=None)` keeps calling `clutch.__main__.main` in process with `env=ENV`, `clock=Clock()` and `pipeline=stages or Stages()`.
  - `core_config(root, routes)` moves unchanged (it writes `config.yaml` under the given `root`).
- In every importer listed in `## Scope fence`, change only the import line (also an import line inside a function) so each moved name comes from `tests.cli_helpers`. Every name any file imports from these hubs is moved, except where Scope in says otherwise, so no importer keeps an import from a hub. Names an importer takes from other hubs stay as they are. A module import (`from tests.integration import <hub>`) is not an import of a name and stays.
- Each hub file (`tests/integration/test_cli.py`) deletes its definition of every moved name it defines and imports the name back from `tests.cli_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line, and every name it defines that no other file imports). Its own tests keep working through the name it imports back; the hub module keeps each moved name as a module attribute.
- Earlier helper modules (none yet; this is the first of the chain) change only where one of them imports a name this ticket moves.
- Create `tests/unit/test_cli_helpers.py`: one test per moved name that runs without reading a repo file, calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name above is importable from `tests.cli_helpers`. 
- `commit_lock` and `adopt_conduct`, which `root` uses today, are imported by the hub from `tests/integration/test_git.py` and `tests/integration/test_stages.py` and move in later steps (`io-helpers-stages`, `io-helpers-misc`); `root` needs no commit lock once git is a `GitFake`, and it imports `adopt_conduct` from `tests.integration.test_stages` until `io-helpers-stages` moves it (that ticket then edits the import).
- `clutch.__main__.main` builds its own `SubprocessExec` and `Git` (see `clutch/__main__.py`, where `SubprocessExec()` is constructed in each verb branch) and has no parameter for either, so a helper that calls `main` replaces those two names on the `clutch.__main__` module with the shared `FakeExec` and `GitFake` for the duration of the call (a patch inside the helper, never a change under `clutch/`). When a verb a helper drives still reaches a real process after that, the run stops as a premise failure naming the verb and the construction site.
- `tests/unit/test_main_evidence_captures.py`, `tests/regress_drain_park_findings.py`, `tests/regress_stale_running.py`, `tests/regress_drain_detach.py`, `tests/regress_drain_signals.py`, `tests/regress_lint_worktree_journal.py` and `tests/regress_suggest_lands_in_box.py` run today and import from the hub (some inside a function); they stay green. `tests/integration/test_shared_fakes_adoption.py` asserts `test_cli.Clock is fakes.FakeClock`, so the hub keeps a module attribute `Clock`.

Scope out:
- Restoring any skipped test file (later batch tickets): a hub file stays skipped and its tests are unchanged.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior.
- Defining in `tests/cli_helpers.py` a class that duplicates `tests/fakes.py` or `tests/git_fake.py`: use the shared fakes. A thin subclass is not needed by any moved name. Rewriting any test body in a hub or importer.
- Skipped importers may still break semantically; their batch ticket fixes that.

## Scope fence
- tests/cli_helpers.py
- tests/unit/test_cli_helpers.py
- tests/integration/test_cli.py
- tests/integration/serve_rig.py
- tests/integration/test_ask.py
- tests/integration/test_author.py
- tests/integration/test_box_triage_inbox.py
- tests/integration/test_caps.py
- tests/integration/test_checkpoint.py
- tests/integration/test_context_suggest_cli.py
- tests/integration/test_control.py
- tests/integration/test_control_cli.py
- tests/integration/test_daemon_admission.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_config.py
- tests/integration/test_daemon_pause.py
- tests/integration/test_daemon_soak.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_doctor.py
- tests/integration/test_drain.py
- tests/integration/test_drain_admissions.py
- tests/integration/test_drain_detach.py
- tests/integration/test_drain_signals.py
- tests/integration/test_drain_upgrade.py
- tests/integration/test_evidence_captures_verb.py
- tests/integration/test_evidence_verbs.py
- tests/integration/test_flake.py
- tests/integration/test_heartbeat.py
- tests/integration/test_hostfiles.py
- tests/integration/test_hot_paths_snapshot.py
- tests/integration/test_inbox.py
- tests/integration/test_index_cli.py
- tests/integration/test_intake_keeps_draft.py
- tests/integration/test_intake_scope.py
- tests/integration/test_issue_verb.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_signal_journal.py
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_lint_verb.py
- tests/integration/test_main_verb_groups.py
- tests/integration/test_menu_verb_parity.py
- tests/integration/test_merge.py
- tests/integration/test_meta_refresh_commit_lock.py
- tests/integration/test_paved_roads.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_providers.py
- tests/integration/test_reconcile.py
- tests/integration/test_reject_queue.py
- tests/integration/test_release.py
- tests/integration/test_release_publish.py
- tests/integration/test_requisition_gate.py
- tests/integration/test_requisition_identity_record.py
- tests/integration/test_restart_timers.py
- tests/integration/test_review_command.py
- tests/integration/test_roadmap_author.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_roadmap_gate.py
- tests/integration/test_roadmap_merged.py
- tests/integration/test_roadmap_named_stem.py
- tests/integration/test_roadmap_refile.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_roadmap_ship.py
- tests/integration/test_roadmap_start_gates.py
- tests/integration/test_roadmap_status.py
- tests/integration/test_route_kinds_judge_lint.py
- tests/integration/test_scheduler.py
- tests/integration/test_serve_admission.py
- tests/integration/test_serve_confirm_during_check.py
- tests/integration/test_serve_dispatch.py
- tests/integration/test_serve_driver.py
- tests/integration/test_serve_driver_overlap.py
- tests/integration/test_serve_kill.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_serve_merge_overlap.py
- tests/integration/test_serve_notify.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/test_serve_scan_head.py
- tests/integration/test_serve_scan_watch_overlap.py
- tests/integration/test_serve_upgrade.py
- tests/integration/test_shared_fakes_adoption.py
- tests/integration/test_stale_running.py
- tests/integration/test_stats.py
- tests/integration/test_status.py
- tests/integration/test_storm_hold.py
- tests/integration/test_storm_notification_activation.py
- tests/integration/test_triage.py
- tests/integration/test_watch.py
- tests/integration/test_watchdog_activation.py
- tests/regress_drain_detach.py
- tests/regress_drain_park_findings.py
- tests/regress_drain_signals.py
- tests/regress_lint_worktree_journal.py
- tests/regress_stale_running.py
- tests/regress_suggest_lands_in_box.py
- tests/unit/test_main_evidence_captures.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_cli_helpers.py` passes, and `tests/unit/test_cli_helpers.py` checks that the `root` fixture leaves no `.git` directory under `tmp_path` and that after `git_out(root, "status")` the list `git_fake(root).calls` ends with `("git_out", ("status",), {})`, so a version that runs real git fails the first check.
2. `grep -rnE "from tests\.integration\.(test_cli) import" tests --include=*.py` prints nothing: every name any file imports from these hubs is moved, so a leftover line names the importer that was missed.
3. `grep -nE "^(async def|def|class) (CONFIG|ENV|PLAN|TICKET|Stages|cli|core_config|git_out|journal|root|ticket|with_retro_driver|write)\b|^(CONFIG|ENV|PLAN|TICKET|Stages|cli|core_config|git_out|journal|root|ticket|with_retro_driver|write) =" tests/integration/test_cli.py` prints nothing: the hub files no longer define a moved name.
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/cli_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the same number of passed and skipped tests as on the base commit, both recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object).

## Verification
```
./dev.py test tests/unit/test_cli_helpers.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test that runs today fails or is skipped, or a skipped test becomes unskipped.
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/cli_helpers.py` defines a class that duplicates a shared fake or a copied reply or config helper.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 30m
- stuck: 60m
- reason: 94 import lines and the hub definitions move in one change because a name must resolve in every importer at once; splitting by importer leaves a name defined in two places, and the files share one module so they stay together
