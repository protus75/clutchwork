---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-26

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/integration/test_requisition_gate.py
- tests/integration/test_requisition_identity_record.py

## On-demand
- tests/integration/test_restart_timers.py

## Goal / Why
Skipped by `integration-disk-io-skip`, these integration test files carry `pytestmark = pytest.mark.disk_io_skip` (set by `disk-io-skip-per-file`) and run nothing. The owner wants them restored FAST and on the shared fakes: each file below has its marker line deleted and its tests rewritten so they pass under the rules in `clutch/docs/host-authoring.md#Unit and integration tests`: git goes through `tests/git_fake.py::GitFake` (created by `shared-git-fake`), processes through `FakeExec` or in-process `clutch.__main__.main`, the journal through `FakeJournal` unless the test's subject is journal persistence, time through `FakeClock` with `fakes.until`/`fakes.turn` and never a sleep, and code that takes the `clutch.seams.FileSystem` seam through `FakeFileSystem`. Models are scripted with `tests/stage_replies.py` and config texts come from `tests/config_fixture.py` where those modules (created by `shared-review-script` and `shared-serve-rig-config`) already hold the helper. Names the files used to import from other test files now live in `tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py` and `tests/misc_helpers.py` (created by the `restore-helpers-*` chain that `restore-helpers-misc` ends). The implementer reads each of those modules in its worktree before editing and imports from them; it never defines a new `Fake*` or stand-in class and never copies a helper into a test file. Pre-existing in-file stand-in classes that do no real I/O may stay as they are. If a shared module lacks a behavior a test needs, the run stops as a premise failure naming the missing behavior; it never edits a shared module.

Files: `tests/integration/test_requisition_gate.py`, `test_requisition_identity_record.py`, `test_restart_timers.py` (1,064 lines together). Final paths: `tests/unit/test_requisition_gate.py`, `tests/unit/test_requisition_identity_record.py`, `tests/unit/test_restart_timers.py` and `tests/integration/test_restart_timers_owner.py` (the one repo-reading test).

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
- `tests/integration/test_requisition_gate.py` (174 lines, 6 tests): `setup(tmp_path, script)` builds a real git repo through `make_root` and `commit_ticket` (`tests/drain_helpers.py`), reads `git_out`/`ENV` (`tests/cli_helpers.py`), `implement_reply` (`tests/stages_helpers.py`), and calls `tests/approval.py::approve` and `tests/dispatch_settle.py`. Rewrite onto those fake-backed helpers; if `tests/approval.py::approve` still runs real git or a process when this ticket runs, stop as a premise failure naming it. Tickets are written under `tmp_path`, so it moves to `tests/unit/test_requisition_gate.py`. Its names `dispatch`, `reply`, `setup` are imported by `tests/integration/test_supervisor_rework.py` and by `test_requisition_identity_record.py`: change those import lines to `tests.unit.test_requisition_gate` (fence `test_supervisor_rework.py`, import line only).
- `tests/integration/test_requisition_identity_record.py` (108 lines, 4 tests): imports `ctx` from the mergequeue hub (`tests/daemon_helpers.py`), and inside its tests imports `pause_checkout` (drain), `dispatch, reply` from `test_requisition_gate` (this ticket's new path), `run` from `test_review_command`, `_box, _events, _failure, _routes, _run, requisition_reply` from the author hub (`tests/misc_helpers.py`), `author_reply, reply` from the triage hub (`tests/loop_helpers.py`), and `invoke, order, original, requisition, signals` from the rework hub (`tests/config_helpers.py`). Real git and a real `Journal` read back by path (`Journal(root / ".clutch/state", clock).read()`) come from `make_root`; use the fake-backed forms. It moves to `tests/unit/test_requisition_identity_record.py`. The `run` import points at `tests/integration/test_review_command.py` until `restore-io-tests-26` moves it to `tests/unit/test_review_command.py`; this ticket depends on `restore-io-tests-26`, which fences and edits that import line first, so here the line already names the final path and is left alone.
- `tests/integration/test_restart_timers.py` (782 lines, 10 tests): hub moved by `restore-helpers-loop` (its `held`, `repository` and timers helpers). Today the rig uses `SubprocessExec()` and `LocalFileSystem()` (`process, fs = ...`), real git repos through `root` (`tests/cli_helpers.py`), `CoreRig` and `assert_startup_pause_wiring` (`tests/daemon_helpers.py`), `Time, turn` (`tests/loop_helpers.py`), `wait_until` (`tests/waiting.py`, replace with `fakes.until`). Rewrite onto `GitFake`, `FakeExec`, `FakeFileSystem` and the shared `FakeClock`. `test_timer_append_is_write_ahead`, `test_timers_rearm_from_journal` and the restart tests have journal persistence as their subject: keep a real `Journal` under `tmp_path` for the `timers(...)` owner there. The `.git` file written at the end of `test_restart_failures_do_not_report_ready` simulates broken worktree metadata and stays as a `tmp_path` write. `test_timer_records_and_identity` also scans `clutch/*.py` through `Path(__file__)` (the single-owner check for timer writes), so it is split whole into the new `tests/integration/test_restart_timers_owner.py`, its `Timers` built inline over `FakeJournal` (`Timers(journal=FakeJournal(...), clock=time, sleep=time.sleep)`, no helper copy) so it writes nothing; the other nine tests move to `tests/unit/test_restart_timers.py` (no such file exists).
- Importers: `tests/integration/test_supervisor_rework.py` (import line only); grep `from tests.integration.test_requisition_gate`, `test_requisition_identity_record`, `test_restart_timers` in `tests/` after the helper chain and fence and fix any other hit.

Scope out:
- Every shared module named in Goal / Why, `tests/integration/conftest.py`, `clutch/`, `docs/`, and every test file not named here.

## Scope fence
- tests/integration/test_requisition_gate.py
- tests/integration/test_requisition_identity_record.py
- tests/integration/test_restart_timers.py
- tests/unit/test_requisition_gate.py
- tests/unit/test_requisition_identity_record.py
- tests/unit/test_restart_timers.py
- tests/integration/test_restart_timers_owner.py
- tests/integration/test_supervisor_rework.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_requisition_gate.py tests/unit/test_requisition_identity_record.py tests/unit/test_restart_timers.py tests/integration/test_restart_timers_owner.py` lists none of the restored files (not one left carrying the marker).
2. `./dev.py test tests/unit/test_requisition_gate.py tests/unit/test_requisition_identity_record.py tests/unit/test_restart_timers.py tests/integration/test_restart_timers_owner.py --durations=0` passes, and no restored test takes more than 1.0 s (not a slower test left in); the durations output is recorded in the run record (`run.md`).
3. `./dev.py test tests/integration/test_requisition_gate.py tests/integration/test_requisition_identity_record.py tests/integration/test_restart_timers.py --collect-only -q` on the base commit and `./dev.py test tests/unit/test_requisition_gate.py tests/unit/test_requisition_identity_record.py tests/unit/test_restart_timers.py tests/integration/test_restart_timers_owner.py --collect-only -q` on the branch report the same number of tests (not fewer), both counts recorded in `run.md`.
4. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.
5. `./dev.py test tests/integration/test_restart_timers_owner.py` passes and still fails when a second module besides `timers.py` appends `timer_armed`, the writer-set assertion `writers == {'timers.py'}` kept, not removed.
6. `grep -n "tests.unit.test_requisition_gate" tests/integration/test_supervisor_rework.py tests/unit/test_requisition_identity_record.py` lists both import lines and `./dev.py test tests/integration/test_supervisor_rework.py --collect-only -q` imports without error.
7. `grep -nE "SubprocessExec\(|LocalFileSystem\(|wait_until" tests/unit/test_restart_timers.py` prints nothing.

## Verification
```
./dev.py test tests/unit/test_requisition_gate.py tests/unit/test_requisition_identity_record.py tests/unit/test_restart_timers.py tests/integration/test_restart_timers_owner.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, xfailed, or weakened, or the collected count of the batch differs from the base commit.
- A new `Fake*` class, stand-in class, or copy of a helper appears in a test file, or a shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`, any `conftest.py`) is edited.
- A restored integration test writes disk, starts a process, or runs git, or a restored test adds a sleep.
- A restored test takes more than 1.0 s in the `--durations=0` output.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files sharing fixtures stay together
