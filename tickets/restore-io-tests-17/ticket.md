---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-06
- restore-io-tests-11

## Context
- tests/integration/test_kill_executor_abort.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_kill_cli_activation.py

## Goal / Why
`integration-disk-io-skip` turned off 184 integration test files because they write disk, start processes, or run git, and the owner wants them restored in batches that are fast and reuse the shared fakes. This ticket restores 3 of them: when it is done, none of the files listed under Scope in carries `pytestmark = pytest.mark.disk_io_skip`, every test in them runs (not skipped), each restored test finishes in at most 1.0 s, and none of them writes disk outside `tmp_path`, starts a process, or runs real git. The files were rewritten onto `tests/fakes.py`, `tests/git_fake.py` and the shared helper modules the dependencies create, so no per-file fake or copied helper remains.

Base-commit collected counts (`uv run pytest --collect-only -q`, recorded again in `run.md`): test_kill_cli_activation: 41, test_kill_executor_abort: 11; total 52.

The batch-17 files import names from `test_control_cli.py` (batch 06) and `test_driver.py` (batch 11), which no helper ticket moves; the two `Depends on` edges to those batches make their final locations available.

## Boundary contract
none
- reason: tests encoding an existing contract; only test files change, and every test keeps its name and the behavior it asserts

## Scope in / Scope out
Scope in (per file: what it touches today, what it moves to, final path):
- `tests/integration/test_kill_cli_activation.py` (9 tests, 41 collected, 889 lines): a live CLI kill through `main`, the `CoreRig`/`LiveDrain`/`assert_core_wiring` daemon rig, control inbox files and a journal under `tmp_path` (`tmp_path / "composition"`), and real git inside the cli `root` fixture. The control files and journal are this test's subject, so they stay real files under `tmp_path`; git moves to `GitFake`, the rig to `tests/daemon_helpers.py`, `root`/`ENV`/`Clock`/`Stages`/`write` to `tests/cli_helpers.py`, `confirmed`/`offer_events`/`NoChild` to `tests/drain_helpers.py`, `agent`/`implement_reply`/`verdict` to `tests/stages_helpers.py`/`tests/stage_replies.py`, `acquire`/`discovery`/`invoke`/`requests` from wherever `restore-io-tests-06` leaves `test_control_cli.py`'s helpers, and `Timer`/`Writer`/`turn` from this ticket's own `test_kill_executor_abort.py`. The `sleep=lambda _: turn()` and `Timer` waits stay event-loop barriers, not wall-clock sleeps. `decision` already comes from `tests/misc_helpers.py` after `restore-helpers-misc`. Final path: `tests/unit/test_kill_cli_activation.py`.
- `tests/integration/test_kill_executor_abort.py` (10 tests, 11 collected, 328 lines): `build(tmp_path, writer)` from `test_driver.py` (batch 11) creates a real `Driver`, journal and captures under `tmp_path`; `Writer`/`Timer` are local classes that other kill tests import. Journal and capture files are the subject, so they stay under `tmp_path`; `build`, `ECHO`, `Stub`, `echo_json`, `log_events` come from wherever `restore-io-tests-11` leaves `test_driver.py`'s helpers (read its import lines in the worktree), `Rig`/`decision` from `tests/misc_helpers.py`. `Writer`/`Timer` remain defined here as the exported helpers the kill tests share, with the one change that `Timer` uses `FakeClock` and `fakes.turn` from `tests/fakes.py` if it duplicates them (if it does not, it stays as is, and is not extended). The lazy import of `exercise_live_cli_kill` from `test_kill_cli_activation` repoints to the new path. Final path: `tests/unit/test_kill_executor_abort.py`.
- Importers of the moved files get only their import lines changed: `tests/integration/test_kill_failure_suppression.py` and `tests/integration/test_kill_worker_stop.py` (`Timer`, `Writer`, `cancelled`, `invoke`, `turn` from `test_kill_executor_abort`), and `tests/integration/test_kill_signal_journal.py` (`applications`, `exercise_live_cli_kill` from `test_kill_cli_activation`). Those three files are restored by `restore-io-tests-18`, which depends on this ticket.

Rewrite rules for every file in this batch (from the owner requirements: restored tests are FAST and REUSE shared fixtures and fakes):
- Delete the `pytestmark = pytest.mark.disk_io_skip` line (and `import pytest` only if nothing else uses it).
- git -> `tests/git_fake.py::GitFake`; processes -> in-process `main([...])` or `FakeExec`; journal -> `FakeJournal` unless the test's subject is journal persistence; time -> `FakeClock` with `fakes.until` / `fakes.turn`, never a sleep; code that takes the `clutch.seams.FileSystem` seam -> `FakeFileSystem`.
- Reuse only shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. Those modules are created by the tickets this one depends on (`restore-helpers-misc` ends the chain that creates the helper modules); read each in the worktree before using it. Never define a new `Fake*` or stand-in class, and never copy a helper into a test file. A stand-in class or helper that a file already defines locally is replaced by the shared one, not kept. If a shared fake lacks a behavior a test needs, stop the run as a premise failure that names the missing behavior; never edit a shared module.
- Keep every test function and the behavior it asserts: no test deleted, skipped, or weakened. Where a real-git assertion (a log subject, a diff name list, a rev-parse) becomes an assertion on `GitFake` overrides and `fake.calls`, it asserts the same fact.
- Placement follows the host authoring guide's "Unit and integration tests" section (also in Context): a file whose rewritten tests still write real files (only under `tmp_path`) lives under tests/unit/; a file that reads repo files (anchored on `Path(__file__)`) and writes nothing stays under tests/integration/; a file needing both is split and each path is named below. Each test keeps its name, so the total collected count across a split equals the base count.
- Any other test file that imports a name from a file this ticket moves gets only its import line changed (fenced below).

Scope out:
- Any file outside the fence, every shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, the `tests/*_helpers.py` modules, both `conftest.py` files), `REAL_IO_TESTS`, and `clutch/`.
- Restoring any other skipped file: those belong to the other `restore-io-tests-NN` tickets.

## Scope fence
- tests/integration/test_kill_cli_activation.py
- tests/unit/test_kill_cli_activation.py
- tests/integration/test_kill_executor_abort.py
- tests/unit/test_kill_executor_abort.py
- tests/integration/test_kill_failure_suppression.py
- tests/integration/test_kill_signal_journal.py
- tests/integration/test_kill_worker_stop.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip"` over every path listed in Scope in (old and new locations) lists none of them, and a pre-edit run of the same grep over the integration originals lists all of them (both outputs recorded in `run.md`).
2. `./dev.py test tests/unit/test_kill_cli_activation.py tests/unit/test_kill_executor_abort.py --durations=0` passes with no test skipped and no restored test taking more than 1.0 s; the `--durations=0` output is recorded in `run.md`.
3. `./dev.py test tests/unit/test_kill_cli_activation.py tests/unit/test_kill_executor_abort.py --collect-only -q` collects exactly 52 tests across the final paths, equal to the base-commit count of 52 from the original paths (not fewer because a test was dropped or a split lost one); both counts are recorded in `run.md`.
4. `grep -rn "tests.integration.test_kill_executor_abort\|tests.integration.test_kill_cli_activation" tests` lists nothing (no importer left on a moved path).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file and no other test regressed.

## Verification
```
./dev.py test tests/unit/test_kill_cli_activation.py tests/unit/test_kill_executor_abort.py --durations=0
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
