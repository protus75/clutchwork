---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-11
- restore-io-tests-12
- restore-io-tests-17

## Context
- tests/integration/test_kill_signal_journal.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_worker_stop.py

## Goal / Why
`integration-disk-io-skip` turned off 184 integration test files because they write disk, start processes, or run git, and the owner wants them restored in batches that are fast and reuse the shared fakes. This ticket restores 3 of them: when it is done, none of the files listed under Scope in carries `pytestmark = pytest.mark.disk_io_skip`, every test in them runs (not skipped), each restored test finishes in at most 1.0 s, and none of them writes disk outside `tmp_path`, starts a process, or runs real git. The files were rewritten onto `tests/fakes.py`, `tests/git_fake.py` and the shared helper modules the dependencies create, so no per-file fake or copied helper remains.

Base-commit collected counts (`uv run pytest --collect-only -q`, recorded again in `run.md`): test_kill_failure_suppression: 22, test_kill_signal_journal: 59, test_kill_worker_stop: 16; total 97.

No other file imports from the three moved modules (checked by grep: `test_kill_signal_journal` is imported only by the kill tests, `test_kill_worker_stop` only by `test_kill_failure_suppression`), so no importer is fenced here.

This ticket depends on `restore-io-tests-17` because that ticket moves `test_kill_executor_abort.py` and `test_kill_cli_activation.py` and edits the import lines of the three files restored here; it depends on batches 11 and 12 for the `test_driver.py` and `test_effects.py` names these files import.

## Boundary contract
none
- reason: tests encoding an existing contract; only test files change, and every test keeps its name and the behavior it asserts

## Scope in / Scope out
Scope in (per file: what it touches today, what it moves to, final path):
- `tests/integration/test_kill_signal_journal.py` (6 tests, 59 collected, 240 lines): the `Rig` and `decision` helpers were moved to `tests/misc_helpers.py` by `restore-helpers-misc`. Its tests publish control requests as JSON files and read the `Journal` back under `tmp_path`, so those files and the journal are the subject and stay real under `tmp_path`; `Crash` and `FakeClock` come from `test_effects.py` (batch 12): `FakeClock` becomes `tests/fakes.py::FakeClock`, `Crash` comes from wherever `restore-io-tests-12` leaves it. The lazy import of `applications`/`exercise_live_cli_kill` is already repointed by `restore-io-tests-17`. Final path: `tests/unit/test_kill_signal_journal.py`.
- `tests/integration/test_kill_failure_suppression.py` (7 tests, 22 collected, 422 lines): `build(tmp_path, ...)` from `test_driver.py` (batch 11), `Rig(tmp_path / "control")`, the `CoreRig`/`LiveDrain` daemon rig, the merge-queue `ctx`/`ready` fixtures with real git, and `tmp_path / "graph"` files. Journal/control/capture files stay real under `tmp_path`; git moves to `GitFake`; rig and fixtures come from `tests/daemon_helpers.py`, `tests/cli_helpers.py`, `tests/misc_helpers.py`. `Timer`, `Writer`, `cancelled`, `invoke`, `turn` come from `tests/unit/test_kill_executor_abort.py` (moved by `restore-io-tests-17`). `Worker`, `accepted`, `boundary`, `release_all` come from `test_kill_worker_stop` (this ticket moves it; update the import line to the new path). Final path: `tests/unit/test_kill_failure_suppression.py`.
- `tests/integration/test_kill_worker_stop.py` (7 tests, 16 collected, 414 lines): defines `Worker`, `accepted`, `boundary`, `release_all` that the suppression tests import, `build` from `test_driver.py`, `Rig`/`decision`, the daemon rig, and `tmp_path / "executor"` / `tmp_path / "graph"` files. Same treatment as above. Final path: `tests/unit/test_kill_worker_stop.py`.

Rewrite rules for every file in this batch (from the owner requirements: restored tests are FAST and REUSE shared fixtures and fakes):
- Delete the `pytestmark = pytest.mark.disk_io_skip` line (and `import pytest` only if nothing else uses it).
- git -> `tests/git_fake.py::GitFake`; processes -> in-process `main([...])` or `FakeExec`; journal -> `FakeJournal` unless the test's subject is journal persistence; time -> `FakeClock` with `fakes.until` / `fakes.turn`, never a sleep; code that takes the `clutch.seams.FileSystem` seam -> `FakeFileSystem`.
- Reuse only shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. Those modules are created by the tickets this one depends on (`restore-helpers-misc` ends the chain that creates the helper modules); read each in the worktree before using it. Never define a new `Fake*` or stand-in class, and never copy a helper into a test file. A stand-in class or helper that a file already defines locally is replaced by the shared one, not kept. If a shared fake lacks a behavior a test needs, stop the run as a premise failure that names the missing behavior; never edit a shared module.
- Keep every test function and the behavior it asserts: no test deleted, skipped, or weakened. Where a real-git assertion (a log subject, a diff name list, a rev-parse) becomes an assertion on `GitFake` overrides and `fake.calls`, it asserts the same fact.
- Placement follows the host authoring guide's "Unit and integration tests" section (also in Context): a file whose rewritten tests still write real files (only under `tmp_path`) lives under tests/unit/; a file that reads repo files (anchored on `Path(__file__)`) and writes nothing stays under tests/integration/; a file needing both is split and each path is named below. Each test keeps its name, so the total collected count across a split equals the base count.
- Where a test drives production code that builds its own git (`main`, `run_drain`, `runner.bind`), the `GitFake` reaches it through the checkout/ctx builders in the helper modules (they take a git argument) or by `monkeypatch.setattr` of the `Git` name in the production module that constructs it; a private `Git._commit` / `Git._run` monkeypatch is re-expressed as an override of the matching `GitFake` member. If neither route can carry a `GitFake` into that code, or a test needs genuine git semantics (conflict, rebase, index refresh, worktree contents) that `GitFake` does not model, the run stops as a premise failure naming the test and the construction site or behavior.
- Any other test file that imports a name from a file this ticket moves gets only its import line changed (fenced below when such a file exists).

Scope out:
- Any file outside the fence, every shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, the `tests/*_helpers.py` modules, both `conftest.py` files), `REAL_IO_TESTS`, and `clutch/`.
- Restoring any other skipped file: those belong to the other `restore-io-tests-NN` tickets.

## Scope fence
- tests/integration/test_kill_failure_suppression.py
- tests/unit/test_kill_failure_suppression.py
- tests/integration/test_kill_signal_journal.py
- tests/unit/test_kill_signal_journal.py
- tests/integration/test_kill_worker_stop.py
- tests/unit/test_kill_worker_stop.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip"` over every restored path (new location, or the same path when the file stays) lists none of them, and the same grep at the base commit over the original integration paths lists all of them (both outputs recorded in `run.md`).
2. `./dev.py test tests/unit/test_kill_failure_suppression.py tests/unit/test_kill_signal_journal.py tests/unit/test_kill_worker_stop.py --durations=0` passes with no test skipped and no restored test taking more than 1.0 s; the `--durations=0` output is recorded in `run.md`.
3. `./dev.py test tests/unit/test_kill_failure_suppression.py tests/unit/test_kill_signal_journal.py tests/unit/test_kill_worker_stop.py --collect-only -q` collects exactly 97 tests across the final paths, equal to the base-commit count of 97 from the original paths (not fewer because a test was dropped or a split lost one); both counts are recorded in `run.md`.
4. `grep -rn "tests.integration.test_kill" tests` lists nothing (every kill-test import points at `tests.unit.test_kill_*` or a shared helper module).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file and no other test regressed.

## Verification
```
./dev.py test tests/unit/test_kill_failure_suppression.py tests/unit/test_kill_signal_journal.py tests/unit/test_kill_worker_stop.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, `xfail`ed, or weakened (an assertion dropped or loosened) to make a file pass.
- A new `Fake*` or stand-in class, or a copy of a helper, appears in a test file, or a shared module is edited.
- A restored integration test writes disk, starts a process, runs git, or opens an on-disk database; or a restored unit test reads or writes a repo file.
- A sleep or real wall-clock wait is added.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files that share fixtures stay together; splitting it would put importers and importees in different tickets
