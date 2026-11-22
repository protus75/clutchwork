---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- integration-disk-io-skip

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
- clutch/testguard.py
- tests/integration/conftest.py
- tests/fakes.py
- tests/integration/test_testguard.py

## Goal / Why
Nothing stops an integration test from writing to disk, starting a process, or running real git. The only I/O guard, `clutch/testguard.py`, runs for `tests/unit` alone, and its own error message tells the agent to "move the test to the integration suite", which is how disk-writing tests piled up there: on 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories, saturating the disk during every Check and merge. `integration-disk-io-skip` turns the existing offenders off; this ticket keeps new ones from landing.

When this ticket is done, every integration test outside an explicit allowlist runs under a guard. During its setup, call and teardown, the guard raises `IntegrationIOBlocked` on any of: opening a file for writing, appending, creating or exclusive creation; renaming, replacing, removing or unlinking a path; `shutil` copy, move or tree removal; starting a process (`subprocess`, `os.system`, `os.posix_spawn`, `os.posix_spawnp`, and the `asyncio` subprocess functions, which go through `subprocess.Popen`); opening a network connection; and `duckdb.connect` with any database other than `":memory:"`. Reading files stays allowed, and so does creating an empty directory under pytest's base temporary directory, which the autouse `isolate_working_directory` fixture needs. The message names the paved road: use the in-memory fakes in `tests/fakes.py` (`FakeFileSystem`, `FakeExec`, `FakeJournal`) and the shared git fake, and only when the test's subject is a real I/O function itself, add the file to `REAL_IO_TESTS` in `tests/integration/conftest.py`.

`REAL_IO_TESTS` holds exactly the ten I/O-function files that `integration-disk-io-skip` leaves running. The unit guard's message stops pointing at the integration suite.

## Boundary contract
### Integration I/O guard
- disposition: create
- owner: clutch/ioguard.py
- consumers: tests/integration/conftest.py, which applies it to every integration test outside `REAL_IO_TESTS`; follow-up tickets that rewrite skipped tests onto fakes
- observable change: a guarded integration test that writes a file, starts a process, opens a network connection, or opens an on-disk DuckDB database fails with `clutch.ioguard.IntegrationIOBlocked` naming the operation and the paved road
- compatibility: tests in `REAL_IO_TESTS` and tests skipped by `DISK_IO_SKIP` are unaffected; reads and empty-directory creation under the pytest base temporary directory stay allowed
- acceptance: each blocked operation raises inside the guard, and each allowed operation succeeds
- tests: tests/unit/test_ioguard.py
- post-merge source of truth: clutch/ioguard.py and `REAL_IO_TESTS` in tests/integration/conftest.py
- closest existing: `clutch/testguard.py::_guards` blocks process and network calls by patching functions for unit tests
- earning reason: `testguard` cannot be reused as is because unit tests may write under `tmp_path`, so it has no write blocking, and it also carries the unit time budget; the integration guard adds file-write and on-disk DuckDB blocking, which needs a process-wide `sys.addaudithook` and a `duckdb.connect` patch that the unit plugin must not install. It does not reuse `testguard._guards`, whose `_block` raises `UnitIOBlocked` with the unit message; the same audit hook blocks processes and network, so one hook raises `IntegrationIOBlocked` with one message before the process starts or the connection opens.

### Unit guard message
- disposition: extend
- owner: clutch/testguard.py
- consumers: agents reading a failed unit test; tests/integration/test_testguard.py
- observable change: the `UnitIOBlocked` message ends with "inject the <seam> seam (or a fake) instead" and no longer suggests moving the test to the integration suite
- compatibility: the blocked set and exception type are unchanged
- acceptance: the message no longer contains "integration suite"
- tests: tests/integration/test_testguard.py
- post-merge source of truth: clutch/testguard.py

## Scope in / Scope out
Scope in:
- `clutch/ioguard.py` (new): `class IntegrationIOBlocked(RuntimeError)`, a pure function `blocked_operation(event: str, args: tuple, basetemp: Path) -> str | None` that returns the blocked operation name or `None`, and a context manager `guard(basetemp: Path)`. All event decisions live in `blocked_operation`; the audit hook body only checks the module-level flag, calls `blocked_operation`, and raises. This split exists because CPython runs `sys.addaudithook` callbacks with tracing paused, so coverage never records the hook body. On first use `guard` installs one `sys.addaudithook` that does nothing unless the flag is set. Before it sets the flag, `guard` calls `tempfile.gettempdir()`, so the one-time temp-directory probe file written by `tempfile._get_default_tempdir` happens outside the guard. Inside `guard` the flag is set and `blocked_operation` blocks the `open` event with a write, append, create or exclusive mode or flags, and `os.rename`, `os.replace`, `os.remove`, `os.unlink`, `os.rmdir`, `shutil.copyfile`, `shutil.copytree`, `shutil.move`, `shutil.rmtree`, and `os.mkdir` for any path not under `basetemp`. It also blocks the process events `subprocess.Popen`, `os.system`, `os.posix_spawn` (which `os.posix_spawnp` also raises) and `os.exec`, and the network event `socket.connect`. Two carve-outs keep pytest's own machinery working, and nothing else is allowed: (a) `os.remove` and `os.unlink` of a direct child of `basetemp` whose name ends in `current`, which is the symlink pytest's `make_numbered_dir` replaces on every `tmp_path_factory.mktemp` after the first (`os.symlink` is not blocked); (b) the anonymous file `tempfile.TemporaryFile` uses for pytest capture fixtures, which leaves nothing on disk: allow an `open` event whose flags include `os.O_TMPFILE`, and allow a write-mode `open` event whose path is an existing directory (on Python 3.14 `tempfile.TemporaryFile()` first emits `open(<tempdir>, 'w+', O_RDWR|O_CREAT|O_TRUNC|O_CLOEXEC)` before the opener's `O_TMPFILE` `os.open`; opening a directory for writing cannot create a file). Every other write-mode `open` stays blocked. Inside the context `guard` sets `sys.dont_write_bytecode = True` and restores the prior value on exit, so an import during a guarded phase never tries to write a `.pyc` (importlib checks the flag before its `os.open(O_CREAT|O_EXCL|O_WRONLY)` and `os.replace`), and no bytecode carve-out exists. `guard` does not use `clutch.testguard._guards()`. It also patches `duckdb.connect` to raise unless the database argument is `":memory:"` or omitted. The message for every block reads `<operation> is blocked in integration tests; use the in-memory fakes in tests/fakes.py (FakeFileSystem, FakeExec, FakeJournal) and the shared git fake; only a test of a real I/O function belongs in REAL_IO_TESTS in tests/integration/conftest.py`.
- `tests/integration/conftest.py`: add `REAL_IO_TESTS`, a sorted tuple of exactly these file names: `test_exec_seam_reap.py`, `test_exec_seam_unwind_capture.py`, `test_git.py`, `test_git_merged_tickets.py`, `test_git_tree_id.py`, `test_journal.py`, `test_journal_duckdb_cache.py`, `test_journal_incremental.py`, `test_journal_roll.py`, `test_lockfile.py`. Add `pytest_runtest_setup`, `pytest_runtest_call` and `pytest_runtest_teardown` wrapper hooks that run the phase inside `clutch.ioguard.guard(item.config._tmp_path_factory.getbasetemp())` unless `item.path.name` is in `REAL_IO_TESTS`. `DISK_IO_SKIP` and `isolate_working_directory` stay as they are.
- `clutch/testguard.py`: in `_block`, drop `, or move the test to the integration suite` from the message, so it ends `inject the {seam} seam (or a fake) instead` with `{seam}` still interpolated (for example `inject the process-exec seam (or a fake) instead`).
- `tests/integration/test_testguard.py`: change the assertion on that message text to assert the new ending `instead` and that "integration suite" is absent.
- `tests/unit/test_ioguard.py` (new): end-to-end tests that enter `guard(tmp_path)` and check every blocked and allowed case in Acceptance criteria, including the on-disk `duckdb.connect` raise; each blocked case catches the exception before any side effect happens, since the audit hook raises before the file is opened and before the process starts. Plus direct calls to `blocked_operation` for each event case: `open` with write, append, create, exclusive and `O_TMPFILE` flags, `open` of an existing directory in write mode, `os.rename`, `os.replace`, `os.remove`, `os.unlink`, `os.rmdir`, the `shutil` events, `os.mkdir` inside and outside `basetemp`, the `*current` symlink carve-out, `subprocess.Popen`, `os.system`, `os.posix_spawn`, `os.exec`, `socket.connect`, and an unrelated event returning `None`.

Scope out:
- Rewriting skipped tests or building a filesystem or git fake (follow-up tickets).
- Prompt specs, guides and agent rule files (the separate `test-io-rules` ticket).
- `config.yaml`, `pyproject.toml`, `test-gate.toml` and its coverage floor, `-n auto`, and the unit suite's guard set.

## Scope fence
- clutch/ioguard.py
- clutch/testguard.py
- tests/integration/conftest.py
- tests/integration/test_testguard.py
- tests/unit/test_ioguard.py

## Acceptance criteria
1. `tests/unit/test_ioguard.py` asserts that inside `guard(tmp_path)`, `open(tmp_path / "f", "w")`, `open(..., "a")`, `open(..., "x")`, `os.open(..., os.O_WRONLY | os.O_CREAT)`, `os.rename`, `os.remove`, `shutil.rmtree`, `os.mkdir` of a path outside `tmp_path`, `subprocess.Popen(["true"])` and `duckdb.connect(str(tmp_path / "db.duckdb"))` each raise `IntegrationIOBlocked`, not succeed, and that the target file, directory or database does not exist afterwards, run by `./dev.py test tests/unit/test_ioguard.py`.
2. `tests/unit/test_ioguard.py` asserts that inside `guard(tmp_path)` reading an existing file, `os.mkdir(tmp_path / "d")`, and `duckdb.connect(":memory:")` succeed, and that after the `with` block exits `open(tmp_path / "g", "w")` succeeds (a guard that stays on after exit fails it), run by `./dev.py test tests/unit/test_ioguard.py`.
3. `tests/unit/test_ioguard.py` asserts that the `IntegrationIOBlocked` message names `tests/fakes.py` and `REAL_IO_TESTS`, run by `./dev.py test tests/unit/test_ioguard.py`.
4. `tests/integration/test_testguard.py` asserts the unit guard message ends with `instead` and does not contain `integration suite`, run by `./dev.py test tests/integration/test_testguard.py` when that file is not in `DISK_IO_SKIP`; when it is skipped, the run record shows the message string from `clutch/testguard.py` (`run.md`).
5. `tests/unit/test_ioguard.py` asserts that inside `guard(tmp_path_factory.getbasetemp())`, calling `tmp_path_factory.mktemp("same")` twice succeeds, that `tempfile.TemporaryFile()` succeeds on the installed Python (3.14), and that `sys.dont_write_bytecode` is true inside `guard` and back to its prior value after the `with` block exits, run by `./dev.py test tests/unit/test_ioguard.py`.
6. `./dev.py test tests/integration` exits 0 with the guard active on every non-skipped file outside `REAL_IO_TESTS`.
7. `tests/unit/test_ioguard.py` calls `blocked_operation` directly for every event case named in Scope in, asserting a write-mode `open` of a regular file path returns an operation and a write-mode `open` of an existing directory returns `None`, and `clutch/ioguard.py` reaches the coverage floor under `uv run clutch coverage gate -- uv run python -m pytest tests/unit -p clutch.testguard --cov=clutch --cov-branch --cov-report=json:coverage.json -n auto`.

## Verification
```
./dev.py test tests/unit/test_ioguard.py
./dev.py test tests/integration
./dev.py test tests/unit
uv run clutch coverage gate -- uv run python -m pytest tests/unit -p clutch.testguard --cov=clutch --cov-branch --cov-report=json:coverage.json -n auto
```

## Definition of rejected
- A file is added to `REAL_IO_TESTS` beyond the ten named, or to `DISK_IO_SKIP`, to make the suite pass.
- The guard blocks reads, or lets a file write, process start, or on-disk DuckDB connection through.
- `config.yaml`, `pyproject.toml`, `test-gate.toml`, or the xdist worker count changes.

## Time budget
- expected: 30m
- stuck: 60m