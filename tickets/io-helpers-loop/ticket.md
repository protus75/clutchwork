---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- io-helpers-config
- shared-git-fake-integration
- shared-review-script
- shared-serve-rig-config

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_scheduler.py
- tests/integration/test_triage.py
- tests/integration/test_terminal.py
- tests/integration/test_restart_timers.py
- tests/integration/serve_rig.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in batch tickets authored after this helper chain merges. Most skipped files import their scaffolding from a few large skipped files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is step 6 of 7 in the helper chain (`io-helpers-cli`, `-drain`, `-stages`, `-daemon`, `-config`, `-loop`, `-misc`); each step depends on the one before it.

Five files hold the serve-loop rigs: `test_scheduler.py` (`Rig`, `Time`, `text`, 16 importers), `test_triage.py` (`root_with_box`, the reply builders, 14 importers), `test_terminal.py` (`repo`, `author`, `diagnosis_reply`, 11 importers), `test_restart_timers.py` (`repository`, `orphan`, `held`, 5 importers) and `tests/integration/serve_rig.py` (25 importers; its `graph`, `admission_graph`, `enable_upgrade` and `notify_command` run real git, a real filesystem or a real process).

When this ticket is done, `tests/loop_helpers.py` defines every name that another test file imports from `tests/integration/test_scheduler.py`, `test_triage.py`, `test_terminal.py`, `test_restart_timers.py` and `serve_rig.py` (all under `tests/integration/`) (the names are listed under Scope in), and each of those 46 importers takes it from `tests.loop_helpers`. The helpers use the shared fakes, so a restored test file that needs them does not start a process or run git, and a later batch ticket can turn a file back on without first fixing a helper that sits in a skipped file.

The helpers follow the rules in `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`, created by `shared-git-fake`; read it in the worktree), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a journal as `tests.fakes.FakeJournal` unless the helper's subject is journal persistence, and a disk write only under a `tmp_path` the caller passes in. A model-reply helper or config text reuses `tests/stage_replies.py` and `tests/config_fixture.py` (created by `shared-review-script` and `shared-serve-rig-config`, merged before `shared-fakes-guard`); a helper never copies either. The owner requires restored tests to be fast and to reuse shared fixtures: this module is the one place each helper below lives.

## Boundary contract
### Shared serve-loop and triage test helpers
- disposition: create
- owner: tests/loop_helpers.py
- consumers: the 46 test files listed in `## Scope fence` that import from `tests/integration/test_scheduler.py`, `test_triage.py`, `test_terminal.py`, `test_restart_timers.py` and `serve_rig.py` (all under `tests/integration/`), and the later batch tickets that restore the skipped ones
- observable change: the names listed under Scope in move from `tests/integration/test_scheduler.py`, `test_triage.py`, `test_terminal.py`, `test_restart_timers.py` and `serve_rig.py` (all under `tests/integration/`) into `tests/loop_helpers.py`, rewritten onto the shared fakes; every importer's import line changes to `tests.loop_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub (for example `test_cli.Clock` in `tests/integration/test_shared_fakes_adoption.py`) stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_loop_helpers.py` imports each moved name from `tests.loop_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_loop_helpers.py
- post-merge source of truth: tests/loop_helpers.py
- closest existing: `tests/fakes.py` (FakeClock, FakeExec, FakeFileSystem, FakeJournal, `turn`, `until`) and `tests/git_fake.py::GitFake` supply the fake seams but none of the scaffolding below; the hub definitions today do real git and processes, so a skipped file cannot reuse them
- earning reason: consolidation of evidenced duplicates and shared use: 46 files import these names from `tests/integration/test_scheduler.py`, `test_triage.py`, `test_terminal.py`, `test_restart_timers.py` and `serve_rig.py` (all under `tests/integration/`), and the hub is skipped, so no importer can be restored until the names live in an unskipped module that follows the I/O rules

## Scope in / Scope out
Scope in:
- Create `tests/loop_helpers.py` holding these moved names, each rewritten as described, keeping its signature unless a change is named: `Rig`, `Time`, `admission_config`, `admission_graph`, `author`, `author_reply`, `clock`, `diagnosis_reply`, `enable_upgrade`, `enqueue`, `escape_report`, `escape_rig`, `graph`, `held`, `notify_command`, `orphan`, `reply`, `repo`, `repository`, `requisition_reply`, `root_with_box`, `run`, `scheduler_import_closure`, `text`, `transitions`, `turn`.
  - From `test_scheduler.py`: `Time`, `Rig` (writes config and files under `tmp_path`), `text`, and `turn` (re-exported from `tests.fakes`, no second definition); its `import_closure` moves as `scheduler_import_closure` (the mergequeue function of the same name moved in `io-helpers-daemon`), and the two importers `test_daemon_composition.py` and `test_serve_lifecycle.py` import it as `scheduler_import_closure as import_closure` where they also import the other.
  - From `test_triage.py`: `root_with_box`, `enqueue`, `reply`, `author_reply`, `requisition_reply` (the model-reply shapes come from `tests/stage_replies.py`; no copy), `run`, `escape_rig` (runs git; becomes `GitFake`) and `escape_report`.
  - From `test_terminal.py`: `clock`, `author`, `diagnosis_reply`, `transitions`, and the `repo` fixture (real git today; `GitFake`). `ENV`, `STEM` and `implement_reply` are re-exports of names already in `tests.stages_helpers`; the importers of those three from the hub (`test_caps.py` for `ENV` and `STEM`, `test_reject_queue.py` for `implement_reply`) import them from `tests.stages_helpers` instead.
  - From `test_restart_timers.py`: `repository` (39 lines: it wires a real `SubprocessExec`, `LocalFileSystem` and git into `CoreRig`; it becomes `GitFake`, `FakeExec` and `FakeFileSystem`), `orphan`, `held`.
  - From `tests/integration/serve_rig.py`, only the five names that run real git, a process or `LocalFileSystem` move: `graph` (uses `LocalFileSystem().publish`), `admission_graph` (79 lines, `SubprocessExec` and git), `enable_upgrade` (git and files), `notify_command` (writes a script and uses `sys.executable`; it returns an in-process command run through `FakeExec`) and `admission_config` (edits `config.yaml` under the given root). `serve_rig.py` keeps its path and every other name it exports (`until`, `write`, `script`, `terminals`, `request`, `trip`, `finish`, `activated_graph`, `active_graph`, `admission_ticket`, `start_admission`, `deliveries`, `notify_completions`, `escalation_batch`, `UpgradeChild`, `HeldLLM`, `retro_scenario`) and imports the five moved names back from `tests.loop_helpers`, so `tests.loop_helpers` never imports `serve_rig` (no cycle). The five moved functions call none of the stay-behind names.
- In every importer listed in `## Scope fence`, change only the import line (also an import line inside a function) so each moved name comes from `tests.loop_helpers`. Every name any file imports from these hubs is moved, except where Scope in says otherwise, so no importer keeps an import from a hub. Names an importer takes from other hubs stay as they are. A module import (`from tests.integration import <hub>`) is not an import of a name and stays.
- Each hub file (`tests/integration/test_scheduler.py`, `tests/integration/test_triage.py`, `tests/integration/test_terminal.py`, `tests/integration/test_restart_timers.py`, `tests/integration/serve_rig.py`) deletes its definition of every moved name it defines and imports the name back from `tests.loop_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line, and every name it defines that no other file imports). Its own tests keep working through the name it imports back; the hub module keeps each moved name as a module attribute.
- Earlier helper modules (`tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`) change only where one of them imports a name this ticket moves.
- Create `tests/unit/test_loop_helpers.py`: one test per moved name, each running without reading a repo file and calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name above is importable from `tests.loop_helpers`. `scheduler_import_closure(sources)` takes a mapping of module name to source text and reads no file (`tests/integration/test_scheduler.py::import_closure`); its unit test passes a hand-built in-memory mapping (for example `{"clutch.__main__": "from clutch import a", "clutch": "", "clutch.a": ""}`) and asserts the reached set, never the real package sources. 
- `tests/integration/test_serve_rig_fakes.py` runs today and asserts `serve_rig.turn is fakes.turn` and that the source of `serve_rig.until` contains `fakes.until`; `until` therefore stays defined in `serve_rig.py` and the file stays green. Only the five `serve_rig.py` names under Scope in move; `retro_scenario` and the other `serve_rig.py` names stay (they use `until`, `request` and `admission_ticket`, which stay too, and write only config text under `tmp_path`), and their importers are not edited.
- `serve_rig.py` imports from `test_scheduler.py` (`text`), `test_triage.py` (`reply`), `test_restart_timers.py` (`repository`), `test_stages.py`, `test_cli.py` and `test_drain.py`; those lines change to the helper modules (it is a hub here and an importer).
- `tests/regress_serve_reoffer_dispatch.py` imports `Rig` from `test_scheduler.py` and stays green.

Scope out:
- Restoring any skipped test file (later batch tickets): a hub file stays skipped and its tests are unchanged.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior.
- Defining in `tests/loop_helpers.py` a class that duplicates `tests/fakes.py` or `tests/git_fake.py`: use the shared fakes. A thin subclass is not needed by any moved name. Names in `serve_rig.py` that do no git, process or disk work stay in `serve_rig.py`.
- Skipped importers may still break semantically; their batch ticket fixes that.

## Scope fence
- tests/loop_helpers.py
- tests/unit/test_loop_helpers.py
- tests/integration/test_scheduler.py
- tests/integration/test_triage.py
- tests/integration/test_terminal.py
- tests/integration/test_restart_timers.py
- tests/integration/serve_rig.py
- tests/integration/test_audit.py
- tests/integration/test_author.py
- tests/integration/test_box.py
- tests/integration/test_box_triage_inbox.py
- tests/integration/test_caps.py
- tests/integration/test_checkpoint.py
- tests/integration/test_cli.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_diagnose.py
- tests/integration/test_drain.py
- tests/integration/test_drain_reentry.py
- tests/integration/test_harvest.py
- tests/integration/test_harvest_cost_source.py
- tests/integration/test_harvest_orphans.py
- tests/integration/test_hostfiles.py
- tests/integration/test_inbox.py
- tests/integration/test_ladder.py
- tests/integration/test_merge.py
- tests/integration/test_notify.py
- tests/integration/test_open_tickets_closed.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_reject_queue.py
- tests/integration/test_requisition_identity_record.py
- tests/integration/test_retro.py
- tests/integration/test_retro_box.py
- tests/integration/test_roadmap_author.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_second_problems.py
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
- tests/integration/test_serve_rig_fakes.py
- tests/integration/test_serve_upgrade.py
- tests/integration/test_ticket_write_serialization.py
- tests/integration/test_watchdog.py
- tests/integration/test_watchdog_activation.py
- tests/regress_serve_reoffer_dispatch.py
- tests/cli_helpers.py
- tests/drain_helpers.py
- tests/stages_helpers.py
- tests/daemon_helpers.py
- tests/config_helpers.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_loop_helpers.py` passes, and `tests/unit/test_loop_helpers.py` checks that `Rig` built over `tmp_path` writes only under `tmp_path`, that `repository(...)` returns a rig whose `checkout.git` is a `GitFake` (its `fake.calls` records the `add` and `commit`) and leaves no `.git` directory, and that `serve_rig.until` and `serve_rig.turn` still resolve (`serve_rig.turn is tests.fakes.turn`).
2. `grep -rnE "from tests\.integration\.(test_scheduler|test_triage|test_terminal|test_restart_timers) import" tests --include=*.py` prints nothing, and `grep -rPzl "from tests\.integration\.serve_rig import (?:\([^)]*|[^\n(]*)\b(?:graph|admission_graph|admission_config|notify_command|enable_upgrade)\b" tests --include=*.py` lists no file (note `activated_graph` and `active_graph` stay in `serve_rig.py`; `\bgraph\b` does not match them).
3. `grep -nE "^(async def|def|class) (Rig|Time|text|author_reply|enqueue|escape_report|escape_rig|reply|requisition_reply|root_with_box|run|author|clock|diagnosis_reply|repo|transitions|held|orphan|repository|import_closure|graph|admission_graph|admission_config|notify_command|enable_upgrade)\b|^(Rig|Time|text|author_reply|enqueue|escape_report|escape_rig|reply|requisition_reply|root_with_box|run|author|clock|diagnosis_reply|repo|transitions|held|orphan|repository|import_closure|graph|admission_graph|admission_config|notify_command|enable_upgrade) =" tests/integration/test_scheduler.py tests/integration/test_triage.py tests/integration/test_terminal.py tests/integration/test_restart_timers.py tests/integration/serve_rig.py` prints nothing: the hub files no longer define a moved name.
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/loop_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the same number of passed and skipped tests as on the base commit, both recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object).

## Verification
```
./dev.py test tests/unit/test_loop_helpers.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test that runs today fails or is skipped, or a skipped test becomes unskipped.
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/loop_helpers.py` defines a class that duplicates a shared fake or a copied reply or config helper.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 30m
- stuck: 60m
- reason: 46 import lines and the hub definitions move in one change because a name must resolve in every importer at once; splitting by importer leaves a name defined in two places, and the files share one module so they stay together
