---
state: rejected
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- shared-review-script

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/integration/test_drain_admissions.py
- tests/integration/test_drain_containment.py
- tests/integration/test_drain_detach.py
- tests/integration/test_drain_reentry.py
- tests/integration/test_drain_signals.py
- tests/integration/test_drain_upgrade.py
- tests/integration/test_echo_stage.py

## On-demand
- tests/integration/test_driver.py

## Goal / Why
`integration-disk-io-skip` turned off 8 integration test files in this batch (1267 lines in all) because they write disk, start processes or run git. `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that does. When this ticket is done each file below runs again: its `pytestmark = pytest.mark.disk_io_skip` line is gone and its tests pass under the rules in the host authoring guide's `Unit and integration tests` section (listed in Context), driven by the shared fakes in `tests/fakes.py` and `tests/git_fake.py::GitFake` and by the shared helper modules the chain behind `restore-helpers-misc` created. Owner requirements: every restored test is fast (no restored test over 1.0 s) and reuses shared fixtures and fakes; no per-file fake class or helper copy.

The importers `test_kill_executor_abort.py`, `test_kill_worker_stop.py` and `test_kill_failure_suppression.py` import from `tests.integration.test_driver`, and `test_shared_fakes_adoption.py` imports the module `test_driver` from `tests.integration` (only the name `test_driver`, which now comes from `tests.unit`); only those import lines change.

## Boundary contract
none
- reason: tests encoding an existing contract; no production code, CLI, document or journal behavior changes.

## Scope in / Scope out
Scope in:
Every file in the batch is handled the same way (the per-file list below gives each file's current touches and final path):
- Delete the line `pytestmark = pytest.mark.disk_io_skip` (`disk-io-skip-per-file` added it).
- Git: `tests/git_fake.py::GitFake` (read it in the worktree; overrides by member name, defaults from return annotations, `fake.calls`). Processes: in-process `clutch.__main__.main([...])` or `tests/fakes.py::FakeExec`. Journal: `FakeJournal` unless the test's subject is journal persistence. Time: `FakeClock` plus `tests.fakes.until`/`turn`, never `sleep` or `asyncio.sleep` polling. A config in a test that only reads it: `clutch.config.load_config_text` instead of writing `config.yaml`. Code taking the `clutch.seams.FileSystem` seam gets `FakeFileSystem`.
- Names the file imports from the old hubs now come from the shared modules the helper tickets created (`tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py`, `tests/misc_helpers.py`, `tests/stage_replies.py`, `tests/config_fixture.py`). Read each in the worktree and grep it for the name before writing the import; never define a new `Fake*` or stand-in class, and never copy a helper. If a shared fake lacks a behavior a test needs, stop as a premise failure that names the missing behavior and the test; never edit a shared module.
- Placement by the rules in the host authoring guide's `Unit and integration tests` section (listed in Context): tests that still write real files (only under `tmp_path`) go to `tests/unit/` under the file's name (or `test_<name>_flow.py` when that name already exists in `tests/unit`); tests that read repo files (anchored on `Path(__file__)`) and write nothing stay in `tests/integration/`. A file with both kinds is split by whole test function into one file per place, each keeping the original name; a single test that needs both a repo read and a real write is not split, and the run stops as a premise failure naming that test. The final path of each file is in the list below.
- The helper fixtures and builders these files use (`root`, `repo`, `make_root`, `CoreRig`, `activated_graph`, `Stages`, `Script`) are rewritten by the helper tickets to run no git, start no process and write only under the `tmp_path` they are given; read each in the worktree before relying on it, and if one still runs git or starts a process, stop as a premise failure naming the helper and the test.
- Keep every test function and parametrization and the behavior each asserts; delete, skip or weaken none. A test with `@pytest.mark.asyncio` stays async. Update the import line in every other file that imports a name from a file this ticket moves (named in the list); only the import line changes there.
- Real-I/O subjects: a test whose subject is a real I/O function itself (a real process, real signals, node) goes verbatim into the file named for it below, and that file name is added as one new entry to `REAL_IO_TESTS` in `tests/integration/conftest.py` (that tuple entry is the only edit there). Those tests are exempt from the 1.0 s bound; run.md records their durations.

Per-file list (current touches, fakes, final path):
- `tests/integration/test_drain_admissions.py` (150 lines) -> `tests/unit/test_drain_admissions.py`. Three asyncio tests that run `drain(checkout, Dispatch(), reexec=NoChild())` on a `root` checkout, call `entry.main(['ticket','confirm'|'reject', ...], ...)` through `asyncio.to_thread`, write control requests with `publish_request` and poll with a local `until` using `asyncio.sleep(0.02)`. Replace the local `until` with `tests.fakes.until(predicate, clock, step)` and `turn`; the run still writes tickets, control files and the journal under `tmp_path`, so the file moves to unit. `commit_ticket`/`confirmed`/`pause_checkout`/`root` from `tests/drain_helpers.py`, `NoChild` likewise.
- `tests/integration/test_drain_containment.py` (65 lines) -> `tests/unit/test_drain_containment_flow.py`. `drain(root, Boom())` on `make_root(tmp_path, caps)` with `Script` hooks; writes the checkout under `tmp_path`. `tests/unit/test_drain_containment.py` already exists, so this file lands as `tests/unit/test_drain_containment_flow.py`.
- `tests/integration/test_drain_detach.py` (44 lines) -> `tests/unit/test_drain_detach.py` and `tests/integration/test_spawn_detached_real.py`. `test_detach_spawns_a_foreground_drain_and_returns` and `test_detach_forwards_config` call `main([... '--detach'], spawn=Mock(...))` on `make_root(tmp_path)`: they move to unit. `test_spawn_detached_runs_in_its_own_session_and_appends` starts a real child with `spawn_detached` and `os.waitpid`: its subject is a real process function, so it moves verbatim to the new file `tests/integration/test_spawn_detached_real.py`, which is added to `REAL_IO_TESTS`.
- `tests/integration/test_drain_reentry.py` (126 lines) -> `tests/unit/test_drain_reentry.py`. Four tests drive `main(['engine','drain'], pipeline=runner.bind(c, FakeLLM(script)), reexec=NoChild())` on the `repo` fixture with real `git(repo, ...)` commits and `Box(... LocalFileSystem())` reads. Git to `GitFake` through the helper `repo`; replies from `tests/stage_replies.py`; `NoChild`, `drain`, `implements`, `ticket_block`, `between_criteria_and_next_section` stay defined by `tests/drain_helpers.py` (moved there by `restore-helpers-drain`): this file imports them. Moves to unit (writes ticket and state files under `tmp_path`).
- `tests/integration/test_drain_signals.py` (46 lines) -> `tests/unit/test_drain_signals.py`. One test: `cli.main(['engine','drain'])` with `_engine_signals` patched and `Blocking(FakeLLM)`; reads `engine.log` and the journal under the `root` checkout. Moves to unit.
- `tests/integration/test_drain_upgrade.py` (305 lines) -> `tests/unit/test_drain_upgrade.py` and `tests/integration/test_exec_seam_inherited_stdio.py`. Its local `Script` makes real squash commits (`git_out add/commit/rev-parse`) and `Child.replace` runs the child drain through `asyncio.to_thread(main, ...)` on a `make_root(tmp_path)` checkout; `order` monkeypatches `Lockfile.release`, `Journal.close` and `Journal.append`; git calls move to `GitFake`. The local `Script` and `Child` classes are test-specific (they already exist in this file) and stay. `test_unbounded_run_streams_through_inherited_stdio` runs `SubprocessExec().run(...)` for real: its subject is the real exec seam, so it moves verbatim to the new file `tests/integration/test_exec_seam_inherited_stdio.py`, added to `REAL_IO_TESTS`. `test_a_closed_journal_handle_refuses_writes` uses the real `Journal` (its subject) under `tmp_path` and moves with the rest to unit.
- `tests/integration/test_driver.py` (408 lines) -> `tests/unit/test_driver.py`. Builds a `Driver` with `Journal(state_dir)` and real `engine.log` under `tmp_path`, `write_text` of `config.yaml`, `list_captures`/`read_capture` from `tests/spool_captures.py` on the real state dir; its `FakeClock` is already `tests.fakes.FakeClock`. Replace the `Journal` with `FakeJournal` where the test does not assert on journal files; keep real `engine.log`/capture reads (the subject), so it moves to unit. Its names `ECHO`, `Stub`, `build`, `echo_json`, `log_events` are imported by `test_kill_executor_abort.py`, `test_kill_worker_stop.py` and `test_kill_failure_suppression.py`.
- `tests/integration/test_echo_stage.py` (123 lines) -> `tests/unit/test_echo_stage.py`. Two tests: `Driver` over `Journal(state_dir)`, `write_text` of `config.yaml`, real `engine.log` and `read_capture` under `tmp_path`; moves to unit with `FakeJournal` where the journal is not asserted.

Importers whose import line changes because a file moved: `tests/integration/test_kill_executor_abort.py`, `tests/integration/test_kill_worker_stop.py`, `tests/integration/test_kill_failure_suppression.py`, `tests/integration/test_shared_fakes_adoption.py`.

New files this ticket creates: `tests/integration/test_spawn_detached_real.py`, `tests/integration/test_exec_seam_inherited_stdio.py`.

Real-I/O entries added to `REAL_IO_TESTS`: `test_spawn_detached_real.py`, `test_exec_seam_inherited_stdio.py`.

Scope out:
- Any shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/*_helpers.py`, `tests/stage_replies.py`, `tests/config_fixture.py`) and any production file under `clutch/`.
- Files of other batches: `restore-io-tests-NN` tickets restore the other skipped files; a name imported from a file of another batch is imported from where that file lives when this ticket runs (grep for it).

## Scope fence
- tests/integration/test_drain_admissions.py
- tests/integration/test_drain_containment.py
- tests/integration/test_drain_detach.py
- tests/integration/test_drain_reentry.py
- tests/integration/test_drain_signals.py
- tests/integration/test_drain_upgrade.py
- tests/integration/test_driver.py
- tests/integration/test_echo_stage.py
- tests/unit/test_drain_admissions.py
- tests/unit/test_drain_containment_flow.py
- tests/unit/test_drain_detach.py
- tests/integration/test_spawn_detached_real.py
- tests/unit/test_drain_reentry.py
- tests/unit/test_drain_signals.py
- tests/unit/test_drain_upgrade.py
- tests/integration/test_exec_seam_inherited_stdio.py
- tests/unit/test_driver.py
- tests/unit/test_echo_stage.py
- tests/integration/test_kill_executor_abort.py
- tests/integration/test_kill_worker_stop.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_shared_fakes_adoption.py
- tests/integration/conftest.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_drain_admissions.py tests/unit/test_drain_containment_flow.py tests/unit/test_drain_detach.py tests/integration/test_spawn_detached_real.py tests/unit/test_drain_reentry.py tests/unit/test_drain_signals.py tests/unit/test_drain_upgrade.py tests/integration/test_exec_seam_inherited_stdio.py tests/unit/test_driver.py tests/unit/test_echo_stage.py` lists no file (it exits 1), so none of the batch's restored files still carries the marker.
2. `./dev.py test tests/unit/test_drain_admissions.py tests/unit/test_drain_containment_flow.py tests/unit/test_drain_detach.py tests/integration/test_spawn_detached_real.py tests/unit/test_drain_reentry.py tests/unit/test_drain_signals.py tests/unit/test_drain_upgrade.py tests/integration/test_exec_seam_inherited_stdio.py tests/unit/test_driver.py tests/unit/test_echo_stage.py --durations=0` passes, and its durations table shows no restored test over 1.0 s except the tests in the real-I/O files named in Scope in; the table is pasted into `run.md`.
3. `./dev.py test tests/unit/test_drain_admissions.py tests/unit/test_drain_containment_flow.py tests/unit/test_drain_detach.py tests/integration/test_spawn_detached_real.py tests/unit/test_drain_reentry.py tests/unit/test_drain_signals.py tests/unit/test_drain_upgrade.py tests/integration/test_exec_seam_inherited_stdio.py tests/unit/test_driver.py tests/unit/test_echo_stage.py --collect-only -q` reports the same number of tests as `./dev.py test tests/integration/test_drain_admissions.py tests/integration/test_drain_containment.py tests/integration/test_drain_detach.py tests/integration/test_drain_reentry.py tests/integration/test_drain_signals.py tests/integration/test_drain_upgrade.py tests/integration/test_driver.py tests/integration/test_echo_stage.py --collect-only -q` on the base commit; both counts are recorded in `run.md`. A smaller count means a test was deleted or lost a parametrization.
4. `ls tests/integration/test_drain_admissions.py tests/integration/test_drain_containment.py tests/integration/test_drain_detach.py tests/integration/test_drain_reentry.py tests/integration/test_drain_signals.py tests/integration/test_drain_upgrade.py tests/integration/test_driver.py tests/integration/test_echo_stage.py` fails for every listed path (each moved file exists only at its new path), and `grep -rn "tests.integration.test_drain_admissions\|tests.integration.test_drain_containment\|tests.integration.test_drain_detach" tests` finds no import of a moved module at its old path.
5. `grep -n "test_spawn_detached_real.py\|test_exec_seam_inherited_stdio.py" tests/integration/conftest.py` shows each real-I/O file named in Scope in exactly once inside `REAL_IO_TESTS`, and `git diff --stat` shows no other line of that file changed.
6. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file broke and no restored integration test tripped the I/O guard.
7. `grep -nE "^class (FakeClock|FakeFS|FakeExec|FakeGit|FakeJournal|FakeFileSystem)\b" tests/unit/test_drain_admissions.py tests/unit/test_drain_containment_flow.py tests/unit/test_drain_detach.py tests/integration/test_spawn_detached_real.py tests/unit/test_drain_reentry.py tests/unit/test_drain_signals.py tests/unit/test_drain_upgrade.py tests/integration/test_exec_seam_inherited_stdio.py tests/unit/test_driver.py tests/unit/test_echo_stage.py` prints nothing, so no restored file defines a stand-in for a shared fake in `tests/fakes.py`.

## Verification
```
./dev.py test tests/unit/test_drain_admissions.py tests/unit/test_drain_containment_flow.py tests/unit/test_drain_detach.py tests/integration/test_spawn_detached_real.py tests/unit/test_drain_reentry.py tests/unit/test_drain_signals.py tests/unit/test_drain_upgrade.py tests/integration/test_exec_seam_inherited_stdio.py tests/unit/test_driver.py tests/unit/test_echo_stage.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, xfailed or weakened, or the collected count drops without the extraction named in Scope in.
- A new `Fake*` class, stand-in or helper copy appears in a test file, or a shared module is edited.
- A restored integration test writes disk, starts a process or runs git outside a `REAL_IO_TESTS` file, or a `sleep` is added.
- Any `clutch/` production file changes.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files that share fixtures stay together.
