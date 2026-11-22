---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Context
- tests/conftest.py
- .gitignore
- docs/how-clutch-works.md#2.2

## Goal / Why
Every pytest run in this repo puts `tmp_path`, `tmp_path_factory` and `tempfile` output under `/tmp`. pytest keeps the last three runs per user, so on 2026-11-21 `/tmp/pytest-of-djp` held 4.8 GB, written by Check runs in many worktrees. The owner's rule: tests never write to `/tmp`; test temporary files go to a gitignored folder inside the checkout running the tests, and nothing goes to RAM-backed storage such as `/dev/shm`.

When this ticket is done, a pytest run started in a checkout (the main checkout or a ticket worktree) puts its pytest base temporary directory at `<rootpath>/.test-tmp/<pid>`, where `<rootpath>` is pytest's `config.rootpath` and `<pid>` is the controller process id. xdist workers use subdirectories of that directory, which xdist already derives from an explicit `basetemp`. Python's `tempfile` module in the controller and in every worker also resolves to that directory, so `tempfile.TemporaryDirectory()` inside a test lands there too. The controller deletes its own `<pid>` directory when the session ends, and at start it deletes any sibling `<pid>` directory whose process no longer exists, so killed runs do not pile up. `.test-tmp/` is gitignored. An explicit `--basetemp` on the command line still wins.

## Boundary contract
### Test temporary directory location
- disposition: extend
- owner: tests/conftest.py
- consumers: every test using `tmp_path`, `tmp_path_factory` or `tempfile` under `tests/unit` and `tests/integration`, the `unit` and `integration` mechanical checks in `config.yaml`, and `./dev.py test`
- observable change: `tmp_path` and `tempfile.gettempdir()` resolve under `<rootpath>/.test-tmp/<pid>` instead of `/tmp`; that directory is removed at session end
- compatibility: tests still receive a fresh empty `tmp_path`; an explicit `--basetemp` option is honored unchanged; parallel runs in different checkouts never share a directory, and two runs in the same checkout use different `<pid>` directories
- acceptance: a test's `tmp_path` and `tempfile.gettempdir()` are both under the checkout's `.test-tmp/`, never under `/tmp`
- tests: tests/unit/test_test_tmp_location.py
- post-merge source of truth: tests/conftest.py

## Scope in / Scope out
Scope in:
- `tests/conftest.py`: add a `pytest_configure(config)` hook (marked `tryfirst=True` so it runs before pytest's own temporary-path setup reads the option). In the xdist controller or a non-xdist run (no `config.workerinput`) and only when `config.option.basetemp` is unset, it sets `config.option.basetemp` to `config.rootpath / ".test-tmp" / str(os.getpid())`, deletes each sibling directory under `.test-tmp/` whose name is a process id that no longer exists (checked with `os.kill(pid, 0)`), creates the directory, and sets `os.environ["TMPDIR"]` and `tempfile.tempdir` to it so `tempfile` in this process and in xdist workers started afterwards resolves there. In a worker (`config.workerinput` present) it sets `tempfile.tempdir` and `os.environ["TMPDIR"]` to the worker's own `basetemp` value as given by xdist. A `pytest_unconfigure(config)` hook in the controller removes the `<pid>` directory it created, and only that directory. The existing fixtures stay unchanged.
- `.gitignore`: add `.test-tmp/`.
- `tests/unit/test_test_tmp_location.py` (new): a test that asserts `tmp_path` is under `Path(__file__).resolve().parents[2] / ".test-tmp"` and that `tempfile.gettempdir()` is under the same directory, and that neither is under `/tmp`.
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
3. After `./dev.py test tests/unit` exits 0, the checkout's `.test-tmp/` directory holds no directory named for that run's controller process id, and `git status --porcelain` lists nothing under `.test-tmp/` (the run record shows both, `run.md`).
4. `./dev.py test` exits 0 for the whole suite.

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
