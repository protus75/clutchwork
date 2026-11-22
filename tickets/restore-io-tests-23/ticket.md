---
state: rejected
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
- tests/integration/test_reconcile.py
- tests/integration/test_regress_scripts_guarded.py

## On-demand
- tests/integration/test_providers.py

## Goal / Why
Skipped by `integration-disk-io-skip`, these integration test files carry `pytestmark = pytest.mark.disk_io_skip` (set by `disk-io-skip-per-file`) and run nothing. The owner wants them restored FAST and on the shared fakes: each file below has its marker line deleted and its tests rewritten so they pass under the rules in `clutch/docs/host-authoring.md#Unit and integration tests`: git goes through `tests/git_fake.py::GitFake` (created by `shared-git-fake`), processes through `FakeExec` or in-process `clutch.__main__.main`, the journal through `FakeJournal` unless the test's subject is journal persistence, time through `FakeClock` with `fakes.until`/`fakes.turn` and never a sleep, and code that takes the `clutch.seams.FileSystem` seam through `FakeFileSystem`. `restore-helpers-misc` transitively depends on `shared-git-fake-integration` and `shared-fakes-guard` through the first helper ticket, so `tests/git_fake.py` exists when this ticket runs; the implementer reads it in its worktree. Names the files used to import from other test files now live in `tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py` and `tests/misc_helpers.py` (created by the `restore-helpers-*` chain that `restore-helpers-misc` ends). The implementer reads each of those modules in its worktree before editing and imports from them; it never defines a new `Fake*` or stand-in class and never copies a helper into a test file. Pre-existing in-file stand-in classes that do no real I/O may stay as they are. If a shared module lacks a behavior a test needs, the run stops as a premise failure naming the missing behavior; it never edits a shared module.

Files: `tests/integration/test_providers.py`, `test_reconcile.py`, `test_regress_scripts_guarded.py` (1,399 lines together). Final paths: `tests/unit/test_providers.py`, `tests/integration/test_providers_instance_config.py` (the one repo-reading test), `tests/unit/test_reconcile.py`, `tests/integration/test_regress_scripts_guarded.py` (stays).

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
- `tests/integration/test_providers.py` (1020 lines, 40 tests): hub moved by `restore-helpers-config` (`CONFIG`, `ENV`, `FakeExec`, `config`, `llm`, `req`, `claude_ok`, `codex_ok` now live in `tests/config_helpers.py`; the file imports them back). Today `config(tmp_path)` writes `config.yaml`, `llm()` uses `LocalFileSystem()` and a real `Journal`, and the tests from `PythonProviderExec` (a `SubprocessExec` subclass that runs `sys.executable -c` and signals real process groups) through `test_event_callback_unwind_kills_group` start real processes and call `os.kill`/`group_exited`. Rewrite: `LocalFileSystem` to `FakeFileSystem`, the provider session journal to `FakeJournal`, and `provider_session`'s `sleep=asyncio.sleep` to the FakeClock sleep. Replace the real-process tests (`test_raising_line_callback_still_drains_and_reaps`, `test_consumer_error_keeps_call_capture`, `test_inflight_events_are_scrubbed_and_capture_is_preserved`, `test_event_callback_unwind_kills_group` and any other using `PythonProviderExec`) with the shared `FakeExec` driving `on_spawn`, `on_stdout_line` and a recorded kill list (the file's `FakeExec` already records `killed`); the assertions `os.kill(pgid, 0)` and `group_exited` become assertions on that kill list, and the `tests.waiting` imports go. Their subject is `ProviderLLM`'s capture, scrub and unwind handling, not OS group reaping (`test_exec_seam_reap.py` owns that). If a test's kill-group behavior cannot be driven through `FakeExec`, stop as a premise failure naming that test. `config(tmp_path)` writes under `tmp_path`, so the file moves to `tests/unit/test_providers.py` (no such file exists). `test_instance_config_routes_every_tier_for_review_author_implement` calls `load_config(None, cwd=ROOT)` on the repo's own `config.yaml` and writes nothing: split that one test, unchanged, into the new `tests/integration/test_providers_instance_config.py`.
- `tests/integration/test_reconcile.py` (338 lines, 11 tests): real `git(root)` via `SubprocessExec` and `commit_lock` from `test_git.py` (REAL_IO; use the `tests/misc_helpers.py` fake-backed equivalent), real worktrees (`orphan_worktree` runs `worktree_add`, writes `half-done.py`), and `cli(root, "engine", "run", ...)` through `tests/cli_helpers.py`. Replace the real git with `GitFake` (worktree add/remove/prune/list, status) and the `path.exists()` checks on worktrees with `GitFake`/`FakeFileSystem` state; the `monkeypatch.setattr(g, "worktree_remove", ...)` interception keeps working on a `GitFake` member. The journal-fsync ordering test (`test_recovery_alert_precedes_worktree_removal` patches `journal_module.os.fsync`) and `test_recovery_alert_is_once_per_reaped_run` (reopens a closed `Journal`) have journal persistence as their subject: keep a real `Journal` under `tmp_path` for those, and `FakeJournal` elsewhere. It moves to `tests/unit/test_reconcile.py` (writes tickets and journal under `tmp_path`).
- `tests/integration/test_regress_scripts_guarded.py` (41 lines): reads `tests/regress_*.py` through `Path(__file__)` and writes nothing, so it stays at its path. `test_premise_park_script_runs` starts `sys.executable tests/regress_premise_park_keep.py` through `subprocess.run`: replace it with `runpy.run_path` or an import of that script and a call of its `main()`, catching `SystemExit` and `capsys`, asserting exit code 0 and stdout lines equal to `['{"regression_result": "pass"}']`; the script's `if __name__ == "__main__"` guard is still checked by the first test. Remove the `subprocess` import.
- Importers: grep `from tests.integration.test_providers`, `test_reconcile`, `test_regress_scripts_guarded` in `tests/` after the helper chain; the hub importers already use `tests/config_helpers.py`. Fence and fix any remaining hit.

Scope out:
- Every shared module named in Goal / Why, `tests/integration/conftest.py`, `clutch/`, `docs/`, and every test file not named here.

## Scope fence
- tests/integration/test_providers.py
- tests/integration/test_reconcile.py
- tests/integration/test_regress_scripts_guarded.py
- tests/unit/test_providers.py
- tests/integration/test_providers_instance_config.py
- tests/unit/test_reconcile.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_providers.py tests/integration/test_providers_instance_config.py tests/unit/test_reconcile.py tests/integration/test_regress_scripts_guarded.py` lists none of the restored files (not one left carrying the marker).
2. `./dev.py test tests/unit/test_providers.py tests/integration/test_providers_instance_config.py tests/unit/test_reconcile.py tests/integration/test_regress_scripts_guarded.py --durations=0` passes, and no restored test takes more than 1.0 s (not a slower test left in); the durations output is recorded in the run record (`run.md`).
3. `./dev.py test tests/integration/test_providers.py tests/integration/test_reconcile.py tests/integration/test_regress_scripts_guarded.py --collect-only -q` on the base commit and `./dev.py test tests/unit/test_providers.py tests/integration/test_providers_instance_config.py tests/unit/test_reconcile.py tests/integration/test_regress_scripts_guarded.py --collect-only -q` on the branch report the same number of tests (not fewer), both counts recorded in `run.md`.
4. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.
5. `./dev.py test tests/integration/test_regress_scripts_guarded.py` passes with `subprocess` no longer imported (`grep -n subprocess tests/integration/test_regress_scripts_guarded.py` prints nothing), and the script run still asserts stdout equals one `regression_result: pass` line, not any other output.
6. `grep -nE "PythonProviderExec|sys.executable|os.kill|group_exited" tests/unit/test_providers.py` prints nothing.

## Verification
```
./dev.py test tests/unit/test_providers.py tests/integration/test_providers_instance_config.py tests/unit/test_reconcile.py tests/integration/test_regress_scripts_guarded.py --durations=0
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
