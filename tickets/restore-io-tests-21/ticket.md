---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/integration/test_mergequeue_tree_moved.py
- tests/integration/test_meta_refresh_commit_lock.py

## On-demand
- tests/integration/test_mergequeue.py

## Goal / Why
Skipped by `integration-disk-io-skip`, these integration test files carry `pytestmark = pytest.mark.disk_io_skip` (set by `disk-io-skip-per-file`) and run nothing. The owner wants them restored FAST and on the shared fakes: each file below has its marker line deleted and its tests rewritten so they pass under the rules in `clutch/docs/host-authoring.md#Unit and integration tests`: git goes through `tests/git_fake.py::GitFake` (created by `shared-git-fake`), processes through `FakeExec` or in-process `clutch.__main__.main`, the journal through `FakeJournal` unless the test's subject is journal persistence, time through `FakeClock` with `fakes.until`/`fakes.turn` and never a sleep, and code that takes the `clutch.seams.FileSystem` seam through `FakeFileSystem`. Models are scripted with `tests/stage_replies.py` and config texts come from `tests/config_fixture.py` where those modules (created by `shared-review-script` and `shared-serve-rig-config`) already hold the helper. Names the files used to import from other test files now live in `tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py` and `tests/misc_helpers.py` (created by the `restore-helpers-*` chain that `restore-helpers-misc` ends). The implementer reads each of those modules in its worktree before editing and imports from them; it never defines a new `Fake*` or stand-in class and never copies a helper into a test file. Pre-existing in-file stand-in classes that do no real I/O may stay as they are. If a shared module lacks a behavior a test needs, the run stops as a premise failure naming the missing behavior; it never edits a shared module.

Files: `tests/integration/test_mergequeue.py`, `tests/integration/test_mergequeue_tree_moved.py`, `tests/integration/test_meta_refresh_commit_lock.py` (1,342 lines together). Final paths: `tests/unit/test_mergequeue.py`, `tests/integration/test_mergequeue_reachability.py`, `tests/unit/test_mergequeue_tree_moved.py`, `tests/unit/test_meta_refresh_commit_lock.py`.

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
- `tests/integration/test_mergequeue.py` (1242 lines, 34 tests): today the `ctx` fixture builds a real git repo under `tmp_path` with `SubprocessExec`, `LocalFileSystem`, a real `Journal`, and `commit_lock`; `ready`/`commit`/`approve` run real git; the regenerate-strategy tests run a real `python3 -c` generator; `test_merge_queue_is_reachable_from_production` reads `clutch/*.py` through `Path(__file__)`. Rewrite onto the `ctx`, `ready`, `commit`, `approve` helpers that `restore-helpers-daemon` moved into `tests/daemon_helpers.py` (GitFake, FakeExec, FakeFileSystem, FakeJournal; read it first), the FakeClock, and a FakeExec reply that performs the regenerate generator's write into the fake filesystem instead of `python3 -c`. The ticket-document test steps already call `tests/approval.py::approve`; if that module still runs real git or a process when this ticket runs, stop as a premise failure naming `tests/approval.py`. The tests keep writing a config file under `tmp_path` (`load_config` reads one), so the file moves to `tests/unit/test_mergequeue.py` (no such file exists today). `test_merge_queue_is_reachable_from_production` reads repo source and writes nothing: split it, unchanged, into the new `tests/integration/test_mergequeue_reachability.py` with its `import_closure` and `assert_reachable` helpers; those two helpers are used only by that test and move with it.
- `tests/integration/test_mergequeue_tree_moved.py` (42 lines): imports `commit`, `ctx`, `ready` from the mergequeue hub (now `tests/daemon_helpers.py`). It rewrites the same way and moves to `tests/unit/test_mergequeue_tree_moved.py` because `ctx` writes its config under `tmp_path`.
- `tests/integration/test_meta_refresh_commit_lock.py` (58 lines): `from tests.integration.test_git_tree_id import setup_repo` builds a real git repo, and `test_git_tree_id.py` is a REAL_IO file that no `restore-helpers-*` ticket covers. Drop that import, do not edit `test_git_tree_id.py`, and build the repo with GitFake plus a plain directory under `tmp_path`. `main([...], cwd=..., env=..., clock=...)` runs in-process but builds its own `SubprocessExec`; patch `clutch.__main__.SubprocessExec` to return the shared `FakeExec` (other restored tests do the same with `monkeypatch.setattr(cli, "SubprocessExec", ...)`). `Lockfile` and the `fcntl.flock` on `commit.lock` write real files under `tmp_path`, which is allowed in `tests/unit/`; the file moves to `tests/unit/test_meta_refresh_commit_lock.py`. If `meta refresh` needs a real git index that the fake cannot give, stop as a premise failure naming that behavior. `CONFIG`, `ENV`, `Clock` come from `tests/cli_helpers.py` or `tests/fakes.py`.
- Importers: none outside this batch import these three files after the helper chain (their names moved to `tests/daemon_helpers.py`); grep `from tests.integration.test_mergequeue`, `test_mergequeue_tree_moved`, `test_meta_refresh_commit_lock` in `tests/` and fence and fix any hit.

Scope out:
- Every shared module named in Goal / Why, `tests/integration/conftest.py`, `clutch/`, `docs/`, and every test file not named here.

## Scope fence
- tests/integration/test_mergequeue.py
- tests/integration/test_mergequeue_tree_moved.py
- tests/integration/test_meta_refresh_commit_lock.py
- tests/integration/test_mergequeue_reachability.py
- tests/unit/test_mergequeue.py
- tests/unit/test_mergequeue_tree_moved.py
- tests/unit/test_meta_refresh_commit_lock.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_mergequeue.py tests/integration/test_mergequeue_reachability.py tests/unit/test_mergequeue_tree_moved.py tests/unit/test_meta_refresh_commit_lock.py` lists none of the restored files (not one left carrying the marker).
2. `./dev.py test tests/unit/test_mergequeue.py tests/integration/test_mergequeue_reachability.py tests/unit/test_mergequeue_tree_moved.py tests/unit/test_meta_refresh_commit_lock.py --durations=0` passes, and no restored test takes more than 1.0 s (not a slower test left in); the durations output is recorded in the run record (`run.md`).
3. `./dev.py test tests/integration/test_mergequeue.py tests/integration/test_mergequeue_tree_moved.py tests/integration/test_meta_refresh_commit_lock.py --collect-only -q` on the base commit and `./dev.py test tests/unit/test_mergequeue.py tests/integration/test_mergequeue_reachability.py tests/unit/test_mergequeue_tree_moved.py tests/unit/test_meta_refresh_commit_lock.py --collect-only -q` on the branch report the same number of tests (not fewer), both counts recorded in `run.md`.
4. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.
5. `./dev.py test tests/integration/test_mergequeue_reachability.py` passes and still fails when `clutch.mergequeue` is unreachable from `clutch.__main__` (the original `pytest.raises(AssertionError)` mutation check is kept, not dropped).
6. `./dev.py test tests/unit/test_meta_refresh_commit_lock.py` passes, `main(['meta', 'refresh'])` returning 2 with `commit.lock is held` on stderr, not 0.

## Verification
```
./dev.py test tests/unit/test_mergequeue.py tests/integration/test_mergequeue_reachability.py tests/unit/test_mergequeue_tree_moved.py tests/unit/test_meta_refresh_commit_lock.py --durations=0
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
