---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Context
- tests/integration/conftest.py
- docs/how-clutch-works.md#2.2
- pyproject.toml

## Goal / Why
Every Check and every merge runs `tests/integration` under `-n auto`, and those tests write to disk on a scale that saturates the machine. Measured on 2026-11-21 (`/tmp/pytest-of-djp/pytest-2679`, one integration run): 975 MB written in 119,498 files, 1,531 real git repositories (about 368 KB each, including about 68 KB of template hook samples per repo) and 114 DuckDB files (about 110 MB). While Check ran for `serve-flaky-tests-deterministic` and later `reconcile-spares-confirming-draft`, vmstat showed 40-60 MB/s sustained writes and 32-34% iowait, with all 16-18 xdist workers in uninterruptible disk wait (`D` state). pytest keeps the last three runs, so `/tmp/pytest-of-djp` reached 4.8 GB. 161 of the 255 `tests/integration/test_*.py` files use `tmp_path`, a subprocess, or real git.

The owner's decision: turn these tests off now, then rewrite them in follow-up tickets onto one shared in-memory git and filesystem fake that never writes to disk. Only tests whose subject is an I/O function itself (the real git CLI wrapper, the journal, the lockfile, the process-exec seam) keep running against real disk and processes.

When this ticket is done, `tests/integration/conftest.py` holds one sorted tuple, `DISK_IO_SKIP`, naming every integration test file (by file name, for example `"test_drain.py"`) any of whose tests creates or writes a file or directory, starts a process, or runs git, other than the ten I/O-function files listed in Scope in. A `pytest_collection_modifyitems` hook in that conftest adds a skip marker to every collected item whose file name is in `DISK_IO_SKIP`, with the reason `disk-io-skip: writes disk, starts a process, or runs git; rewrite onto the in-memory fakes and remove this file from DISK_IO_SKIP`. A file leaves the list only when a follow-up ticket rewrites it so it no longer does any of these. The integration suite stays green with every listed file skipped.

The integration suite stays parallel under `-n auto`; this ticket does not change worker count.

## Boundary contract
### Integration suite collection
- disposition: extend
- owner: tests/integration/conftest.py
- consumers: the `integration` mechanical check in `config.yaml`, `./dev.py test tests/integration`, and the follow-up rewrite tickets, each of which removes its files from `DISK_IO_SKIP`
- observable change: every test collected from a file named in `DISK_IO_SKIP` is reported skipped with the `disk-io-skip:` reason; tests from all other files run unchanged
- compatibility: the autouse `isolate_working_directory` fixture is unchanged; no test outside the listed files changes outcome
- acceptance: a listed file's items carry the skip marker and an unlisted file's items do not
- tests: tests/integration/test_disk_io_skip_list.py
- post-merge source of truth: tests/integration/conftest.py `DISK_IO_SKIP`

## Scope in / Scope out
Scope in:
- `tests/integration/conftest.py`: add the module-level tuple `DISK_IO_SKIP` (sorted, no duplicates, bare file names) and the `pytest_collection_modifyitems(config, items)` hook that adds `pytest.mark.skip(reason=...)` with the reason text in Goal / Why to each item whose `item.path.name` is in `DISK_IO_SKIP`. The existing `isolate_working_directory` fixture stays as it is.
- Building the list. Before editing, run the integration suite once with a temporary local pytest plugin, not committed, that installs `sys.addaudithook` and records, per test file, every `open` event with a write, append, create or exclusive mode, every `os.mkdir`, `os.rename`, `os.remove`, `shutil.*` copy or move, `subprocess.Popen` and `os.posix_spawn` event, raised during that file's test setup, call or teardown. The audit discards exactly one kind of event: the `os.mkdir` that the autouse `isolate_working_directory` fixture's own `tmp_path_factory.mktemp("integration-cwd")` call raises (identify it by a path whose final component starts with `integration-cwd`, or by recording nothing while that fixture's setup runs), together with pytest's own basetemp creation before the first test. Every other event counts as the test's own disk, process or git work, including writes inside the `integration-cwd` directory after it exists and every `tmp_path` or `tmp_path_factory` use by the test or its other fixtures. Every file with at least one recorded event goes in `DISK_IO_SKIP`, except these ten I/O-function files, which keep running: `test_git.py`, `test_git_tree_id.py`, `test_git_merged_tickets.py`, `test_journal.py`, `test_journal_duckdb_cache.py`, `test_journal_incremental.py`, `test_journal_roll.py`, `test_lockfile.py`, `test_exec_seam_reap.py`, `test_exec_seam_unwind_capture.py`. Record in the run record the audit command, the number of files recorded, and the count left after the exemptions.
- `tests/integration/test_disk_io_skip_list.py` (new): tests that call the conftest hook with minimal in-memory stand-in items (objects with a `path` attribute and an `add_marker` method); the test bodies do no disk, process or git work beyond the autouse `isolate_working_directory` fixture, so under the audit rule above this file is not listed.
- `docs/how-clutch-works.md` section 2.2: one sentence after the `tests/unit/` and `tests/integration/` sentence saying that integration test files listed in `DISK_IO_SKIP` in `tests/integration/conftest.py` are skipped until rewritten onto in-memory fakes. Nothing else in that document changes.

Scope out:
- Rewriting any skipped test, or creating the shared in-memory git and filesystem fake (follow-up tickets).
- A guard that fails new disk-writing integration tests, and changes to the test rules in prompt specs and guides (separate cause ticket).
- Changing where pytest's temporary directory lives, `-n auto`, `config.yaml`, or `pyproject.toml`.
- Deleting any test file.

## Scope fence
- tests/integration/conftest.py
- tests/integration/test_disk_io_skip_list.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `tests/integration/test_disk_io_skip_list.py` checks that an item whose `path.name` is in `DISK_IO_SKIP` gets exactly one skip marker whose reason starts with `disk-io-skip:`, and that an item from a file not in the list gets no marker (not a skip on every item, not a skip on none), run by `./dev.py test tests/integration/test_disk_io_skip_list.py`.
2. `tests/integration/test_disk_io_skip_list.py` checks that `DISK_IO_SKIP` is sorted and has no duplicates, that every entry names an existing file in `tests/integration/` (anchored on `Path(__file__)`), and that none of the ten I/O-function files named in Scope in is listed, run by `./dev.py test tests/integration/test_disk_io_skip_list.py`.
3. `./dev.py test tests/integration` exits 0, and its summary shows every test from a listed file as skipped.
4. The run record names the audit command, the number of files with recorded disk, process or git events, and the final length of `DISK_IO_SKIP`, and that length equals the recorded count minus the exempted I/O-function files the audit recorded (`run.md`).

## Verification
```
./dev.py test tests/integration/test_disk_io_skip_list.py
./dev.py test tests/integration
```

## Definition of rejected
- A test file is deleted, or any test outside the listed files changes outcome.
- One of the ten I/O-function files is skipped, or a file the audit recorded is left off the list without being one of those ten.
- The audit plugin is committed, or `config.yaml`, `pyproject.toml`, or the xdist worker count changes.

## Time budget
- expected: 25m
- stuck: 50m
