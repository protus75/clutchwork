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

## On-demand
- tests/integration/test_drain.py

## Goal / Why
`integration-disk-io-skip` turned off 1 integration test files in this batch (1746 lines in all) because they write disk, start processes or run git. `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that does. When this ticket is done each file below runs again: its `pytestmark = pytest.mark.disk_io_skip` line is gone and its tests pass under the rules in the host authoring guide's `Unit and integration tests` section (listed in Context), driven by the shared fakes in `tests/fakes.py` and `tests/git_fake.py::GitFake` and by the shared helper modules the chain behind `restore-helpers-misc` created. Owner requirements: every restored test is fast (no restored test over 1.0 s) and reuses shared fixtures and fakes; no per-file fake class or helper copy.

`tests/integration/test_shared_fakes_adoption.py` imports the modules `test_cli, test_drain, test_driver, test_effects, test_merge, test_stages, test_tickets` from `tests.integration` and asserts `test_drain.Clock is fakes.FakeClock` and runs `test_drain.Clock()`: after this ticket it imports `test_drain` from `tests.unit` (that line only; `restore-io-tests-11` and `-12` edit the lines naming `test_driver` and `test_effects`, so only the `test_drain` name changes here).

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
- `tests/integration/test_drain.py` (1746 lines) -> `tests/unit/test_drain.py`. 65 tests of `main(['engine','drain'])` on a checkout built under `tmp_path` (`make_root`/`root` now live in `tests/drain_helpers.py`), with a real `git` repo (`git_out(root, 'init'|'add'|'commit'|'rev-parse'|'status --porcelain'|'log --format=%s'|'show')`), real `Git(SubprocessExec())` for `intake` and `pause_checkout`, `Box(... LocalFileSystem())` messages, `engine.log`, and in `_exercise_retro_drain` a `Process(SubprocessExec)` subclass patched into `cli`. Git moves to `GitFake` (blob shas via `rev_parse`, `status --porcelain` text via the `status_porcelain` override, log lines via `_run`), `Process` to `tests/fakes.py::FakeExec`, sleeps to `tests.fakes.turn`/`until`. `Script`, `START`, `Clock`, `confirmed`, `commit_ticket`, `intake_at`, `retry_draws`, `tos`, `pause_checkout`, `offer_events`, `mechanical_first` are in `tests/drain_helpers.py`: this file imports them back. It also calls `test_bootstrap_pipeline_keeps_inline_admission` from `tests/integration/test_merge.py` (a merge-batch file; import it from where it lives) and the `admission_repo`/`rework_repo` fixtures from `tests/config_helpers.py`/`tests/loop_helpers.py`. The drain code under test still writes real journal, lock and ticket files, so the file moves to `tests/unit/test_drain.py` and keeps the three tests that assert on `.clutch` files on `tmp_path`. At 1,746 lines it is one ticket because the marker is per file and a split by test range is not allowed.

Importers whose import line changes because a file moved: `tests/integration/test_shared_fakes_adoption.py`.

Scope out:
- Any shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/*_helpers.py`, `tests/stage_replies.py`, `tests/config_fixture.py`) and any production file under `clutch/`.
- Files of other batches: `restore-io-tests-NN` tickets restore the other skipped files; a name imported from a file of another batch is imported from where that file lives when this ticket runs (grep for it).

## Scope fence
- tests/integration/test_drain.py
- tests/unit/test_drain.py
- tests/integration/test_shared_fakes_adoption.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_drain.py` lists no file (it exits 1), so none of the batch's restored files still carries the marker.
2. `./dev.py test tests/unit/test_drain.py --durations=0` passes, and its durations table shows no restored test over 1.0 s; the table is pasted into `run.md`.
3. `./dev.py test tests/unit/test_drain.py --collect-only -q` reports the same number of tests as `./dev.py test tests/integration/test_drain.py --collect-only -q` on the base commit; both counts are recorded in `run.md`. A smaller count means a test was deleted or lost a parametrization.
4. `ls tests/integration/test_drain.py` fails for every listed path (each moved file exists only at its new path), and `grep -rn "tests.integration.test_drain" tests` finds no import of a moved module at its old path.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file broke and no restored integration test tripped the I/O guard.
6. `grep -nE "^class (FakeClock|FakeFS|FakeExec|FakeGit|FakeJournal|FakeFileSystem)\b" tests/unit/test_drain.py` prints nothing, so no restored file defines a stand-in for a shared fake in `tests/fakes.py`.

## Verification
```
./dev.py test tests/unit/test_drain.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, xfailed or weakened, or the collected count drops without the extraction named in Scope in.
- A new `Fake*` class, stand-in or helper copy appears in a test file, or a shared module is edited.
- A restored integration test writes disk, starts a process or runs git outside a `REAL_IO_TESTS` file, or a `sleep` is added.
- Any `clutch/` production file changes.

## Time budget
- expected: 45m
- stuck: 90m
- reason: the batch is cut at about 1,400 lines so files that share fixtures stay together; `tests/integration/test_drain.py` alone is 1,746 lines and a split by test function range is not allowed because the skip marker is per file.
