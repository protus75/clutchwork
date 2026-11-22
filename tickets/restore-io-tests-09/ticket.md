---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- shared-serve-rig-config
- shared-review-script

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/integration/test_daemon_tasks.py
- tests/integration/test_dev.py
- tests/integration/test_dev_vscode_package_kept.py
- tests/integration/test_diagnose.py
- tests/integration/test_diagnose_eval.py
- tests/integration/test_doctor.py

## Goal / Why
`integration-disk-io-skip` turned off 6 integration test files in this batch (1234 lines in all) because they write disk, start processes or run git. `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that does. When this ticket is done each file below runs again: its `pytestmark = pytest.mark.disk_io_skip` line is gone and its tests pass under the rules in the host authoring guide's `Unit and integration tests` section (listed in Context), driven by the shared fakes in `tests/fakes.py` and `tests/git_fake.py::GitFake` and by the shared helper modules the chain behind `restore-helpers-misc` created. Owner requirements: every restored test is fast (no restored test over 1.0 s) and reuses shared fixtures and fakes; no per-file fake class or helper copy.



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
- `tests/integration/test_daemon_tasks.py` (400 lines) -> `tests/unit/test_daemon_tasks.py`. Mostly pure asyncio (`DaemonTasks` with scripted consumers); `test_background_consumers_are_dormant` runs `cli.main` on the `root` checkout and writes `config.yaml` and a `graph` directory under `tmp_path`; `test_merge_results_remain_consumer_owned` uses the `admission_context`/`ready` fixtures from `tests/daemon_helpers.py` (renamed from `test_mergequeue`), `CoreRig`/`assert_core_wiring` from `tests/daemon_helpers.py`, `turn` from `tests/loop_helpers.py` (or `tests.fakes.turn`), `activated_graph` from `tests/integration/serve_rig.py`. Moves to unit; the `Journal(root/'.clutch/state')` read in the dormant test is the subject of that test and stays on the real journal under `tmp_path`.
- `tests/integration/test_dev.py` (128 lines) -> `tests/unit/test_dev.py`. `dev.main` with `subprocess.run` replaced by `Mock`, and `tmp_path` fixture trees for the `vscode-package` tests; no process starts, nothing outside `tmp_path` is written. Moves to unit unchanged apart from the marker line.
- `tests/integration/test_dev_vscode_package_kept.py` (61 lines) -> `tests/unit/test_dev_vscode_package_kept.py` and `tests/integration/test_dev_vscode_package_kept.py`. `test_existing_package_is_untouched` and `test_new_package_restores_readme` write under `tmp_path` with `Mock` subprocess: they move to the unit file. `test_host_declares_package` reads the repo `config.yaml` through `Path(__file__)` and writes nothing: it stays in the integration file of the same name.
- `tests/integration/test_diagnose.py` (246 lines) -> `tests/unit/test_diagnose.py`. Drives `main(['engine','run'|'drain'])` through the `repo` fixture (a checkout under `tmp_path`: `tests/loop_helpers.py` `repo`/`author`/`clock`/`diagnosis_reply`), real `git(repo, ...)` calls from `test_stages` (rev-parse of the ticket blob, `git log --format=%s main`, `commit -am`) and files under `repo/tickets` and `.clutch/state`. Git moves to `GitFake` through the helper `repo`; the asserted blob sha and log lines come from `GitFake` overrides (`rev_parse`, `_run`). `NoChild` from `tests/drain_helpers.py`, `ROUTING_CONFIG` from `tests/config_helpers.py`, `agent`/`verdict`/`SNAG`/`STEM`/`ENV` from `tests/stages_helpers.py` and `tests/stage_replies.py`, `mechanical_first` from `tests/drain_helpers.py`, `order` from `tests/config_helpers.py`. Moves to unit.
- `tests/integration/test_diagnose_eval.py` (197 lines) -> `tests/integration/test_diagnose_eval.py`. Every test reads repo files (`eval/` fixtures through `diagnose.load_cases()`, the diagnose prompt spec) and also writes `config.yaml`, `report.json` and the journal under `tmp_path`; `eval/diagnose.py` writes and resumes its report through a hard-wired `LocalFileSystem()`, and report persistence and resume across runs is what `test_resume_only_deadline_skips_and_refuses_changed_corpus`, `test_verify_names_each_broken_check` and the deadline tests assert. Neither a unit file (repo read) nor an integration file (real write) fits, and `eval/diagnose.py` is production code this ticket may not change. Decision recorded here: its subject is the harness's real report file, so the marker is deleted and the name `test_diagnose_eval.py` is added to `REAL_IO_TESTS`; configs may use `load_config_text` and the clock `FakeClock`, but the report and corpus files stay real; exempt from the 1.0 s bound.
- `tests/integration/test_doctor.py` (202 lines) -> `tests/unit/test_doctor.py`. `doctor.check` over the `root` checkout with a local `Exec` class that stubs `git --version` (an existing per-file stand-in). `FakeExec` returns one fixed result and cannot raise, so build the exec seam from `unittest.mock.AsyncMock` objects (`run=AsyncMock(return_value=(0, 'git version fixture\n', ''))`, `side_effect=ExecutableNotFound('git')` for the git-missing case, and a `side_effect` function keyed on argv so `git show HEAD:<conduct file>` returns the drifted or the current bytes in `test_doctor_core_committed`); define no new class, and delete the local `Exec`. The tests write `config.yaml`, journal segments and a lock under `tmp_path` and call `main(['host','doctor'])`. Moves to unit.

Real-I/O entries added to `REAL_IO_TESTS`: `test_diagnose_eval.py`.

Scope out:
- Any shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/*_helpers.py`, `tests/stage_replies.py`, `tests/config_fixture.py`) and any production file under `clutch/`.
- Files of other batches: `restore-io-tests-NN` tickets restore the other skipped files; a name imported from a file of another batch is imported from where that file lives when this ticket runs (grep for it).

## Scope fence
- tests/integration/test_daemon_tasks.py
- tests/integration/test_dev.py
- tests/integration/test_dev_vscode_package_kept.py
- tests/integration/test_diagnose.py
- tests/integration/test_diagnose_eval.py
- tests/integration/test_doctor.py
- tests/unit/test_daemon_tasks.py
- tests/unit/test_dev.py
- tests/unit/test_dev_vscode_package_kept.py
- tests/unit/test_diagnose.py
- tests/unit/test_doctor.py
- tests/integration/conftest.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_daemon_tasks.py tests/unit/test_dev.py tests/unit/test_dev_vscode_package_kept.py tests/integration/test_dev_vscode_package_kept.py tests/unit/test_diagnose.py tests/integration/test_diagnose_eval.py tests/unit/test_doctor.py` lists no file (it exits 1), so none of the batch's restored files still carries the marker.
2. `./dev.py test tests/unit/test_daemon_tasks.py tests/unit/test_dev.py tests/unit/test_dev_vscode_package_kept.py tests/integration/test_dev_vscode_package_kept.py tests/unit/test_diagnose.py tests/integration/test_diagnose_eval.py tests/unit/test_doctor.py --durations=0` passes, and its durations table shows no restored test over 1.0 s except the tests in the real-I/O files named in Scope in; the table is pasted into `run.md`.
3. `./dev.py test tests/unit/test_daemon_tasks.py tests/unit/test_dev.py tests/unit/test_dev_vscode_package_kept.py tests/integration/test_dev_vscode_package_kept.py tests/unit/test_diagnose.py tests/integration/test_diagnose_eval.py tests/unit/test_doctor.py --collect-only -q` reports the same number of tests as `./dev.py test tests/integration/test_daemon_tasks.py tests/integration/test_dev.py tests/integration/test_dev_vscode_package_kept.py tests/integration/test_diagnose.py tests/integration/test_diagnose_eval.py tests/integration/test_doctor.py --collect-only -q` on the base commit; both counts are recorded in `run.md`. A smaller count means a test was deleted or lost a parametrization.
4. `ls tests/integration/test_daemon_tasks.py tests/integration/test_dev.py tests/integration/test_diagnose.py tests/integration/test_doctor.py` fails for every listed path (each moved file exists only at its new path), and `grep -rn "tests.integration.test_daemon_tasks\|tests.integration.test_dev\|tests.integration.test_diagnose" tests` finds no import of a moved module at its old path.
5. `grep -n "test_diagnose_eval.py" tests/integration/conftest.py` shows each real-I/O file named in Scope in exactly once inside `REAL_IO_TESTS`, and `git diff --stat` shows no other line of that file changed.
6. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file broke and no restored integration test tripped the I/O guard.
7. `grep -nE "^class (FakeClock|FakeFS|FakeExec|FakeGit|FakeJournal|FakeFileSystem)\b" tests/unit/test_daemon_tasks.py tests/unit/test_dev.py tests/unit/test_dev_vscode_package_kept.py tests/integration/test_dev_vscode_package_kept.py tests/unit/test_diagnose.py tests/integration/test_diagnose_eval.py tests/unit/test_doctor.py` prints nothing, so no restored file defines a stand-in for a shared fake in `tests/fakes.py`.

## Verification
```
./dev.py test tests/unit/test_daemon_tasks.py tests/unit/test_dev.py tests/unit/test_dev_vscode_package_kept.py tests/integration/test_dev_vscode_package_kept.py tests/unit/test_diagnose.py tests/integration/test_diagnose_eval.py tests/unit/test_doctor.py --durations=0
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
