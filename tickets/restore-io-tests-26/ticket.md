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
- tests/integration/test_retro_box.py
- tests/integration/test_review_command.py

## On-demand
- tests/integration/test_retro.py

## Goal / Why
Skipped by `integration-disk-io-skip`, these integration test files carry `pytestmark = pytest.mark.disk_io_skip` (set by `disk-io-skip-per-file`) and run nothing. The owner wants them restored FAST and on the shared fakes: each file below has its marker line deleted and its tests rewritten so they pass under the rules in `clutch/docs/host-authoring.md#Unit and integration tests`: git goes through `tests/git_fake.py::GitFake` (created by `shared-git-fake`), processes through `FakeExec` or in-process `clutch.__main__.main`, the journal through `FakeJournal` unless the test's subject is journal persistence, time through `FakeClock` with `fakes.until`/`fakes.turn` and never a sleep, and code that takes the `clutch.seams.FileSystem` seam through `FakeFileSystem`. `restore-helpers-misc` transitively depends on `shared-git-fake-integration` and `shared-fakes-guard` through the first helper ticket, so `tests/git_fake.py` exists when this ticket runs; the implementer reads it in its worktree. Names the files used to import from other test files now live in `tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py` and `tests/misc_helpers.py` (created by the `restore-helpers-*` chain that `restore-helpers-misc` ends). The implementer reads each of those modules in its worktree before editing and imports from them; it never defines a new `Fake*` or stand-in class and never copies a helper into a test file. Pre-existing in-file stand-in classes that do no real I/O may stay as they are. If a shared module lacks a behavior a test needs, the run stops as a premise failure naming the missing behavior; it never edits a shared module.

Files: `tests/integration/test_retro.py`, `test_retro_box.py`, `test_review_command.py` (977 lines together). Final paths: `tests/unit/test_retro.py`, `tests/unit/test_retro_box.py`, `tests/unit/test_review_command.py`.

## Boundary contract
none
- reason: tests encoding an existing contract; no production code, prompt, or shared test module changes

## Scope in / Scope out
Rules for every file in this batch:
- Delete the `pytestmark = pytest.mark.disk_io_skip` line (and `import pytest` only if nothing else uses it).
- Keep every test function and what it asserts. No test is deleted, skipped, xfailed or weakened; a test whose original check cannot be kept stops the run as a premise failure naming the test and the missing behavior.
- A file whose rewritten tests still write real files, only under `tmp_path`, moves to `tests/unit/` under the name this ticket gives. A file that reads repo files (anchored on `Path(__file__)`) and writes nothing stays in `tests/integration/`. A file needing both is split along whole test functions, each part at the path this ticket names. A moved file's `# relates:` and `# purpose:` meta lines are kept true, and its old path is removed.
- Imports in other files that name a moved file change to its new path; only those import lines change there.

Scope in, per file:
- `tests/integration/test_retro.py` (524 lines, 17 tests): hub moved by `restore-helpers-misc` (`rig`, `merged`, `escape_rig` and kin live in `tests/misc_helpers.py`). Today `rig` builds `pause_checkout(make_root(tmp_path))` (real git) with a real `Journal`, and `list_captures` from `tests/spool_captures.py` reads a real store. Rewrite onto `make_root`/`pause_checkout`/`commit_ticket` from `tests/drain_helpers.py`, `FakeJournal`, `FakeFileSystem`, and the `tests/misc_helpers.py` capture readers; `test_failed_retro_suppresses_window_until_completion` replaces the journal with `Journal(c.config.state_dir, c.clock)` to simulate a restart and `test_report_commit_replays_without_advancing_unfinished_window` replays after a crash: both have journal persistence as subject, keep a real `Journal` under `tmp_path` there only. Retro reports and box records are files under `tmp_path`, so it moves to `tests/unit/test_retro.py` (no such file exists).
- `tests/integration/test_retro_box.py` (232 lines, 5 tests): async tests over `root_with_box` and `author_reply, reply, requisition_reply` (`tests/loop_helpers.py`), `pause_checkout` (drain), `implement_reply, verdict` (`tests/stages_helpers.py`); the retro, requisition, and implement stages run on scripted replies (`tests/stage_replies.py`, created by `shared-review-script` which this ticket depends on: read it and reuse its helpers) and a `Box` over files on `tmp_path`, so it moves to `tests/unit/test_retro_box.py`. `ctx.driver.journal = Journal(...)` and `RereportJournal(c.journal)` swap to `FakeJournal` unless the test checks durability.
- `tests/integration/test_review_command.py` (221 lines, 12 tests): `make_root`/`commit_ticket`/`confirmed`/`Clock` (`tests/drain_helpers.py`), `ENV, git_out, ticket, write` (`tests/cli_helpers.py`); `main(["ticket", "review", ...])` runs in-process and builds its own `SubprocessExec`/`Git`: patch `clutch.__main__.SubprocessExec` to the shared `FakeExec` and `GitFake` as the helper modules show. The tests read the journal back through `Journal(root / ".clutch/state", Clock())`: the command itself writes that real journal under `tmp_path`, so that file persistence stays real and the file moves to `tests/unit/test_review_command.py`; `test_review_commit_lock_timeout` keeps its injected `CommitLock` sleep seam (no real sleep). Its names `reply` and `run` are imported by `tests/integration/test_intake_scope.py` and `tests/integration/test_requisition_identity_record.py`: change those import lines to `tests.unit.test_review_command` (import lines only; `restore-io-tests-25` depends on this ticket, so the identity-record edit happens here first, at its integration path).
- Importers outside the batch: `tests/integration/test_intake_scope.py`, `tests/integration/test_requisition_identity_record.py` (import lines only). The hub importers of `test_retro` (`test_scorecard`, `test_hot_paths_snapshot`, `test_paved_roads`, `test_status`) and of `test_retro_box` (`test_status`, `test_author`, `test_daemon_composition`, `test_box`) already use `tests/misc_helpers.py` after `restore-helpers-misc`; grep `from tests.integration.test_retro`, `test_retro_box`, `test_review_command` in `tests/` and fence and fix any other hit.

Scope out:
- Every shared module named in Goal / Why, `tests/integration/conftest.py`, `clutch/`, `docs/`, and every test file not named here.

## Scope fence
- tests/integration/test_retro.py
- tests/integration/test_retro_box.py
- tests/integration/test_review_command.py
- tests/unit/test_retro.py
- tests/unit/test_retro_box.py
- tests/unit/test_review_command.py
- tests/integration/test_intake_scope.py
- tests/integration/test_requisition_identity_record.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_retro.py tests/unit/test_retro_box.py tests/unit/test_review_command.py` lists none of the restored files (not one left carrying the marker).
2. `./dev.py test tests/unit/test_retro.py tests/unit/test_retro_box.py tests/unit/test_review_command.py --durations=0` passes, and no restored test takes more than 1.0 s (not a slower test left in); the durations output is recorded in the run record (`run.md`).
3. `./dev.py test tests/integration/test_retro.py tests/integration/test_retro_box.py tests/integration/test_review_command.py --collect-only -q` on the base commit and `./dev.py test tests/unit/test_retro.py tests/unit/test_retro_box.py tests/unit/test_review_command.py --collect-only -q` on the branch report the same number of tests (not fewer), both counts recorded in `run.md`.
4. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.
5. `grep -n "tests.unit.test_review_command" tests/integration/test_intake_scope.py tests/integration/test_requisition_identity_record.py` lists both import lines, and `./dev.py test tests/integration/test_intake_scope.py --collect-only -q` imports without error.
6. `./dev.py test tests/unit/test_review_command.py` passes with `test_review_commit_lock_timeout` still asserting the commit-lock timeout refusal, not a skipped or sleeping version.

## Verification
```
./dev.py test tests/unit/test_retro.py tests/unit/test_retro_box.py tests/unit/test_review_command.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, xfailed, or weakened, or the collected count of the batch differs from the base commit.
- A new `Fake*` class, stand-in class, or copy of a helper appears in a test file, or a shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`, any `conftest.py`) is edited.
- A restored integration test writes disk, starts a process, or runs git, or a restored test adds a sleep.
- A restored test takes more than 1.0 s in the `--durations=0` output.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files sharing fixtures stay together
