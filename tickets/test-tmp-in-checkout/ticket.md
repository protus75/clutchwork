---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Runs before
- shared-fakes-guard
- shared-git-fake-integration
- shared-git-fake-unit-6
- shared-git-fake-unit-5
- shared-git-fake-unit-4
- shared-git-fake-unit-3
- shared-git-fake-unit-2
- shared-git-fake
- shared-serve-rig-config
- shared-review-script
- check-rerun-failed-only
- serve-flaky-tests-deterministic
- reconcile-spares-confirming-draft
- flake-fix-jumps-queue
- preflight-once-per-session
- serve-contains-dispatch-exception
- check-meta-fill-nested-stage
- supervisor-orders-by-depends
- gemini-provider-configured
- retry-keeps-prior-branch

## Context
- tests/conftest.py
- .gitignore
- docs/how-clutch-works.md#2.2

## Goal / Why
Every pytest run in this repo puts `tmp_path`, `tmp_path_factory` and `tempfile` output under `/tmp`. pytest keeps the last three runs per user, so on 2026-11-21 `/tmp/pytest-of-djp` held 4.8 GB, written by Check runs in many worktrees. The owner's rule: tests never write to `/tmp`; test temporary files go to a gitignored folder inside the checkout running the tests, and nothing goes to RAM-backed storage such as `/dev/shm`.

When this ticket is done, a pytest run started in a checkout (the main checkout or a ticket worktree) owns one run directory `<rootpath>/.test-tmp/<pid>`, where `<rootpath>` is pytest's `config.rootpath` and `<pid>` is the controller process id. pytest's base temporary directory is `<run>/pytest` (xdist workers use the subdirectories xdist already derives from an explicit `basetemp`), and Python's `tempfile` module in the controller and in every worker resolves to `<run>/tempfile`, a separate directory pytest never deletes or recreates, so `tempfile.TemporaryDirectory()` inside a test lands there even as the first temporary operation in a worker. The controller deletes its own `<pid>` directory when the session ends, and at start it deletes any sibling `<pid>` directory whose process no longer exists, so killed runs do not pile up. `.test-tmp/` is gitignored. An explicit `--basetemp` on the command line still wins.

## Boundary contract
### Test temporary directory location
- disposition: extend
- owner: tests/conftest.py
- consumers: every test using `tmp_path`, `tmp_path_factory` or `tempfile` under `tests/unit` and `tests/integration`, the `unit` and `integration` mechanical checks in `config.yaml`, and `./dev.py test`
- observable change: `tmp_path` and `tempfile.gettempdir()` resolve under `<rootpath>/.test-tmp/<pid>` instead of `/tmp`; that directory is removed at session end
- compatibility: tests still receive a fresh empty `tmp_path`; an explicit `--basetemp` option is honored unchanged; parallel runs in different checkouts never share a directory, and two runs in the same checkout use different `<pid>` directories
- acceptance: a test's `tmp_path` and `tempfile.gettempdir()` are both under the checkout's `.test-tmp/`, never under `/tmp`
- tests: tests/unit/test_test_tmp_location.py (location, first-use `tempfile.TemporaryDirectory()`, and `_reap_dead_pid_dirs` keeps live and non-numeric entries, explicit `--basetemp` untouched, unconfigure removes only its own run directory)
- post-merge source of truth: tests/conftest.py

## Scope in / Scope out
Scope in:
- `tests/conftest.py`: add a `pytest_configure(config)` hook (marked `tryfirst=True` so it runs before pytest's own temporary-path setup reads the option). In the xdist controller or a non-xdist run (no `config.workerinput`) and only when `config.option.basetemp` is unset, it calls `_reap_dead_pid_dirs(config.rootpath / ".test-tmp")`, then sets `config.option.basetemp` to `<run>/pytest` where `<run>` is `config.rootpath / ".test-tmp" / str(os.getpid())`, creates `<run>/tempfile`, and sets `os.environ["TMPDIR"]` and `tempfile.tempdir` to `<run>/tempfile`. xdist workers start after `pytest_configure` and inherit `TMPDIR`, so `tempfile` in a worker resolves to the same existing `<run>/tempfile` without the worker doing anything; the hook does nothing in a worker (`config.workerinput` present). `_reap_dead_pid_dirs(base)` is a module-level function that deletes each directory directly under `base` whose name is all digits and names a process that no longer exists (checked with `os.kill(pid, 0)` raising `ProcessLookupError`), and keeps every other entry. A `pytest_unconfigure(config)` hook in the controller removes the `<run>` directory it created, and only that directory. The existing fixtures stay unchanged.
- `.gitignore`: add `.test-tmp/`.
- `tests/unit/test_test_tmp_location.py` (new): tests that assert `tmp_path` is under `Path(__file__).resolve().parents[2] / ".test-tmp"`; that `tempfile.gettempdir()` is under the same directory and that `tempfile.TemporaryDirectory()` succeeds there when it is the first temporary operation in the test (the test requests no `tmp_path`); and that `_reap_dead_pid_dirs` called on a directory under `tmp_path` holding a directory named for a dead process id (find one by counting down from a high pid until `os.kill` raises `ProcessLookupError`), a directory named `str(os.getpid())`, and a directory named `keep-me` removes only the dead-pid directory. Two more tests call `pytest_configure` and `pytest_unconfigure` directly with a stub config (`rootpath` under `tmp_path`, no `workerinput`), saving and restoring `tempfile.tempdir` and `TMPDIR` with `monkeypatch`: with `option.basetemp` already set, `option.basetemp` is unchanged and nothing is created under `<rootpath>/.test-tmp`; with `option.basetemp` unset and a sibling `<rootpath>/.test-tmp/keep-me` directory present, unconfigure removes the `<run>` directory and `keep-me` remains.
- `docs/how-clutch-works.md` section 2.2: one sentence saying that test temporary files go to the gitignored `.test-tmp/` folder in the checkout, never `/tmp`. Nothing else in that document changes.

Scope out:
- `dev.py` (its `vscode` task's temporary directory is a build step, not a test).
- Standalone `tests/regress_*.py` reproducers run outside pytest, and agent scratch files outside tests (the separate test-I/O rules ticket covers agent scratch).
- Any change to which tests run, `config.yaml`, `pyproject.toml`, or `-n auto`.

## Scope fence
- tests/conftest.py
- .gitignore
- tests/unit/test_test_tmp_location.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `tests/unit/test_test_tmp_location.py` asserts that `tmp_path` resolves under the checkout's `.test-tmp/` directory, not under `/tmp` (a run that still uses `/tmp/pytest-of-<user>` fails it), run by `./dev.py test tests/unit/test_test_tmp_location.py`.
2. `tests/unit/test_test_tmp_location.py` asserts that `tempfile.gettempdir()` inside the test resolves under the same `.test-tmp/` directory, not `/tmp`, under `-n auto` (so a worker that did not inherit the setting fails it), run by `./dev.py test tests/unit/test_test_tmp_location.py`.
3. `tests/unit/test_test_tmp_location.py` asserts that `_reap_dead_pid_dirs` removes the dead-pid directory and keeps both the live-pid directory and `keep-me` (a reaper that deletes everything, or nothing, fails it), and that `tempfile.TemporaryDirectory()` as a test's first temporary operation succeeds under `-n auto` (not `FileNotFoundError`), run by `./dev.py test tests/unit/test_test_tmp_location.py`.
4. `tests/unit/test_test_tmp_location.py` asserts that a stub config with `option.basetemp` set leaves it unchanged and creates nothing under `.test-tmp` (a hook that overrides an explicit `--basetemp` fails it), and that unconfigure after an unset-basetemp configure removes the run directory while a sibling `keep-me` remains (a cleanup that removes all of `.test-tmp` fails it), run by `./dev.py test tests/unit/test_test_tmp_location.py`.
5. After `./dev.py test tests/unit` exits 0, the checkout's `.test-tmp/` directory holds no directory named for that run's controller process id, and `git status --porcelain` lists nothing under `.test-tmp/` (the run record shows both, `run.md`).
6. `./dev.py test` exits 0 for the whole suite.

## Verification
```
./dev.py test tests/unit/test_test_tmp_location.py
./dev.py test
```

## Definition of rejected
- Test temporary files go to `/tmp`, `/dev/shm`, or any other RAM-backed or system-wide directory.
- An explicit `--basetemp` is overridden, or the hook deletes anything under `.test-tmp/` other than its own directory and directories of dead process ids.
- `config.yaml`, `pyproject.toml`, `dev.py`, or the xdist worker count changes.

## Time budget
- expected: 20m
- stuck: 40m
