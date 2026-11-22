---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-06

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_daemon_composition.py

## Goal / Why
`integration-disk-io-skip` turned off 1 integration test file in this batch (`test_daemon_composition.py`, 2148 lines) because they write real files, run real git and processes, and sleep; `integration-io-guard` fails any such test, and `disk-io-skip-per-file` marks each skipped file with `pytestmark = pytest.mark.disk_io_skip`. The owner wants these tests back, FAST (no restored test above 1.0 s) and on the shared fakes, not on per-file copies.

When this ticket is done, none of the 1 file carries the `disk_io_skip` marker, each runs under the I/O guard (or under `tests/unit/` where it still writes under `tmp_path`), every test function in them still exists and asserts what it asserted before, and the shared modules `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py` are reused instead of copied. The helper hub names these files imported were moved to those helper modules by the `restore-helpers-*` chain, so `restore-helpers-misc` (end of the chain) is the dependency; read each shared module in your worktree before using it, and the run stops as a premise failure that names the missing behavior if a shared fake lacks one (never edit a shared module).

## Boundary contract
none
- reason: tests encoding an existing contract; the batch changes only test files and the `clutch/` behavior they assert stays as it is

## Scope in / Scope out
Scope in:
Rules every restored test follows (the owner requires FAST tests that REUSE the shared fixtures and fakes):
- Delete the `pytestmark = pytest.mark.disk_io_skip` line (and an `import pytest` it alone needed). Keep every test function, parametrization and assertion; no test is deleted, skipped, xfailed or weakened.
- Git goes through `tests/git_fake.py::GitFake` (overrides by member name, `fake.calls`); processes through `tests/fakes.py::FakeExec` or an in-process `clutch.__main__.main([...])`; journals through `FakeJournal` unless the test's subject is journal persistence; the `clutch.seams.FileSystem` seam through `FakeFileSystem`; time through `FakeClock` with `until`/`turn`, never `sleep`. Config text comes from `tests/config_fixture.py` / `tests/config_helpers.py`, model replies from `tests/stage_replies.py`, and test rigs from `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. Read those modules in the worktree before editing; they exist once the dependency has merged.
- No new `Fake*` or stand-in class and no copy of a shared helper in a test file. A per-file stand-in class that the file defines today (named per file below) is replaced by the shared fake or helper and its definition deleted. If a shared module lacks a behavior a test needs, the run stops as a premise failure that names the missing behavior and the test; it never edits a shared module, `clutch/` code or `tests/integration/conftest.py`.
- Placement follows the host guide section "Unit and integration tests" (in Context): a test that still writes files (only under `tmp_path`) lives under `tests/unit/`; a test that reads a repo file (anchored on `Path(__file__)`) and writes nothing lives under `tests/integration/`. Reading packaged spec or doc files inside production code (for example `ask.render` loading `clutch/specs/ask/*.md`) is not a test reading a repo file. A file whose tests need both is split, and the ticket names both paths. A moved file keeps its name under `tests/unit/` unless that name exists there, in which case it is `test_<name>_flow.py`.
- Where code under test builds its own real `Git`, `SubprocessExec` or `Journal` and `main` exposes no seam for it, drive the code through the function the unit tests beside it call, with the fakes. If neither route exists, the run stops as a premise failure that names the code path.
- Any name a moved file defines that another test module imports gets its importers' import lines updated in the same change (grep `from tests.integration.<name> import` first); only import lines change in importers.

Per file:
- `tests/integration/test_daemon_composition.py` (2148 lines): today it 32 tests of the production daemon graph: real git roots (`root`, `Git`, `commit_lock`, 46 git mentions), real `Journal`, `tmp_path` (43 uses), 21 `sleep` references wired through the rig, `FakeLLM`, `Scheduler`, `Watcher`, `MergeQueue`, `ProviderLLM`; defines the per-file stand-ins `ScriptFS`, `ScriptExec`, `LiveDrain` (and the rig classes `CoreRig`, `assert_core_wiring`, which `restore-helpers-daemon` moved to `tests/daemon_helpers.py`); several tests read `clutch/*.py` through `Path(__file__)` (`sources`, `without_core_import`, `assert_reachable`: `test_without_core_import_handles_multiline_and_nested_imports`, `test_daemon_core_is_reachable_from_cli`, `test_production_serve_graph_is_reachable`); imports from skipped non-hub modules `test_daemon_config` (`assert_detached`, `python_values`) and `test_storm_notification_activation` (`SITES`, `exercise_site`), and `invoke` from `test_control_cli`. Plan: SPLIT. The tests that read `clutch/*.py` and write nothing stay in `tests/integration/test_daemon_composition.py` (the implementer lists them in run.md by the rule). All other tests move to `tests/unit/test_daemon_composition.py` (name free): git becomes GitFake, the real journal becomes FakeJournal (a real `Journal` under `tmp_path` only for the pause/resume control-lifecycle tests whose written file is the subject), `ScriptFS` becomes `FakeFileSystem`, `ScriptExec` becomes `FakeExec` (scripted results), `time`/`sleep` use `FakeClock` with `turn`/`until`, and `LiveDrain` is built from `tests/drain_helpers.py`. A name imported from `test_daemon_config.py` or `test_storm_notification_activation.py` that does real I/O stops the run as a premise failure naming it. `invoke` is imported from `tests.unit.test_control_cli` (after `restore-io-tests-06`).

Record in the run record (`run.md`): the `--collect-only -q` test count of the batch's files on the base commit and after the change, the `--durations=0` output of the restored paths, which tests of a split file went to which path, and for each moved file the `grep -rn "tests.integration.<name>" tests` result used to find importers.

Twenty-five other modules imported helper names from this file; `restore-helpers-daemon` repointed them to `tests/daemon_helpers.py`, so grep confirms none remains and fences any that does.

Scope out: `tests/integration/conftest.py` (the marker line is the only switch), `tests/fakes.py`, `tests/conftest.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, every `tests/*_helpers.py`, all `clutch/` code, and test files outside this batch except the importer import lines named above. A hot test file (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `test_cli.py`, `test_watch.py`, `serve_rig.py`) gets no new test, fixture or helper from this change; code only leaves it or is repointed.

## Scope fence
- tests/integration/test_daemon_composition.py
- tests/unit/test_daemon_composition.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_daemon_composition.py tests/unit/test_daemon_composition.py` prints no file name (the marker is gone from every path the batch keeps), recorded in `run.md`; every path that the plan moves whole no longer exists under `tests/integration/` (`ls` of it fails), and the marker is not present in any new file.
2. `./dev.py test tests/integration/test_daemon_composition.py tests/unit/test_daemon_composition.py --durations=0` passes and its durations table lists no restored test above 1.0 s (a test that still takes 1.0 s or more fails this criterion, it is not allowed to stay slow); the output is recorded in `run.md`.
3. `./dev.py test tests/integration/test_daemon_composition.py tests/unit/test_daemon_composition.py --collect-only -q` reports exactly as many tests as `./dev.py test tests/integration/test_daemon_composition.py --collect-only -q` reported on the base commit (a deleted, merged or skipped test makes the counts differ); both numbers are recorded in `run.md`.
4. `grep -nE "^\s*class (Fake|Script|Exec|Git|FS|Clock|LiveDrain)" tests/integration/test_daemon_composition.py tests/unit/test_daemon_composition.py` prints no line (no per-file fake or stand-in class remains), and `grep -nE "subprocess|sys\.executable|time\.sleep|asyncio\.sleep" tests/integration/test_daemon_composition.py` prints no line (a restored integration test starts no process and never sleeps).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, and `tests/integration` reports no `IntegrationIOBlocked` failure (the I/O guard stays on for every restored integration test).

## Verification
```
./dev.py test tests/integration/test_daemon_composition.py tests/unit/test_daemon_composition.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
A test is deleted, skipped, xfailed or weakened (an assertion removed or loosened, a parametrization dropped); a new or copied `Fake*`/stand-in class or helper appears in a test file; a shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, a `tests/*_helpers.py`), `tests/integration/conftest.py` or `clutch/` code is edited; a restored integration test writes disk, starts a process, runs git or sleeps; a restored test takes more than 1.0 s; or the collected test count of the batch differs from the base commit.

## Time budget
- expected: 30m
- stuck: 60m
- reason: a single file of 2148 lines that shares one rig and one set of fixtures cannot be cut by test function range because the skip marker is per file
