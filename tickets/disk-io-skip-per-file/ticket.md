---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Context
- tests/integration/conftest.py
- tests/integration/test_disk_io_skip_list.py
- docs/how-clutch-works.md#2.2

## Goal / Why
`integration-disk-io-skip` turned off 184 integration test files by listing their names in one sorted tuple, `DISK_IO_SKIP`, in `tests/integration/conftest.py`. The owner wants those tests restored soon, in batches: each batch ticket rewrites a set of files onto the shared in-memory fakes and turns them back on. With one shared tuple, every batch ticket must fence and edit `tests/integration/conftest.py`, and two batches that remove neighboring lines of the tuple conflict at merge. Batches then serialize on one file instead of running in parallel.

When this ticket is done, the skip is declared inside each skipped file, so a batch ticket turns a file back on by editing only that file:

- `tests/integration/conftest.py` registers a marker `disk_io_skip` in a `pytest_configure(config)` hook (`config.addinivalue_line("markers", ...)`) and its `pytest_collection_modifyitems` adds `pytest.mark.skip(reason=...)` to every item that carries the `disk_io_skip` marker (`item.get_closest_marker("disk_io_skip")`), with the same reason text as today except that its last clause reads `remove the disk_io_skip marker from this file` in place of `remove this file from DISK_IO_SKIP`.
- Each of the 184 files named in `DISK_IO_SKIP` today gets one module-level line `pytestmark = pytest.mark.disk_io_skip` after its imports (adding `import pytest` when the file lacks it). No listed file defines `pytestmark` today.
- The `DISK_IO_SKIP` tuple is deleted. `REAL_IO_TESTS`, the three I/O guard hook wrappers, and the `isolate_working_directory` fixture are unchanged.

The set of skipped tests is exactly the set skipped today.

## Boundary contract
### Integration suite skip declaration
- disposition: replace
- owner: tests/integration/conftest.py
- consumers: the `integration` mechanical check, `./dev.py test tests/integration`, and the follow-up batch tickets that restore skipped files
- observable change: a test file is skipped by carrying the module marker `disk_io_skip` instead of by being named in `DISK_IO_SKIP`; the old tuple is removed in the same change and every listed file migrates to the marker
- compatibility: the same 184 files are skipped with a `disk-io-skip:` reason, and no other test changes outcome
- acceptance: an item carrying the marker gets exactly one skip marker whose reason starts with `disk-io-skip:`; an item without it gets none; no `REAL_IO_TESTS` file carries the marker
- tests: tests/integration/test_disk_io_skip_list.py
- post-merge source of truth: the `pytestmark = pytest.mark.disk_io_skip` line in each skipped file under tests/integration/

## Scope in / Scope out
Scope in:
- `tests/integration/conftest.py`: the changes in Goal / Why, and its `purpose:` meta line says it skips files that carry the `disk_io_skip` marker in place of `skips the files in DISK_IO_SKIP`.
- Every file currently named in `DISK_IO_SKIP`: add the one `pytestmark` line (and `import pytest` when missing). Nothing else in those files changes. Record in the run record the count of files given the marker; it equals the length of `DISK_IO_SKIP` on the base commit (184).
- `tests/integration/test_disk_io_skip_list.py`: rewrite its two tests to (1) call the conftest hook with stand-in items whose `get_closest_marker` returns a marker for one and `None` for the other, and (2) scan `tests/integration/test_*.py` (anchored on `Path(__file__)`) and assert that no `REAL_IO_TESTS` file has a line matching the regex `^pytestmark = pytest\.mark\.disk_io_skip$` and that `DISK_IO_SKIP` no longer exists on the conftest module. This test file itself carries no such line (it is not skipped), so it holds the pattern only inside a string literal.
- `docs/how-clutch-works.md` section 2.2: the sentence naming `DISK_IO_SKIP` says that integration test files carrying the `disk_io_skip` marker are skipped until rewritten onto in-memory fakes. Nothing else in that document changes.

Scope out:
- Restoring, rewriting, moving or deleting any skipped test (follow-up batch tickets).
- `REAL_IO_TESTS`, the I/O guard, `clutch/ioguard.py`, `pyproject.toml`, and `config.yaml`.

## Scope fence
- tests/integration
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/integration/test_disk_io_skip_list.py` passes and checks that a stand-in item carrying the `disk_io_skip` marker gets exactly one skip marker with a reason starting `disk-io-skip:`, and an item without the marker gets none (not a skip on every item, not on none).
2. `./dev.py test tests/integration/test_disk_io_skip_list.py` checks that no `REAL_IO_TESTS` file carries the marker and that `conftest.DISK_IO_SKIP` is gone.
3. `./dev.py test tests/integration` exits 0 and its summary reports the same number of skipped tests as on the base commit, recorded in the run record from both runs (`run.md`).
4. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_*.py` lists 184 files, excluding `test_disk_io_skip_list.py`, the same names as `DISK_IO_SKIP` on the base commit, recorded in the run record (`run.md`).

## Verification
```
./dev.py test tests/integration/test_disk_io_skip_list.py
./dev.py test tests/integration
```

## Definition of rejected
- A test that runs today is skipped, or a test skipped today runs.
- Any line other than the marker and its `import pytest` changes in a skipped file.
- `REAL_IO_TESTS`, the I/O guard hooks, or `isolate_working_directory` change.

## Time budget
- expected: 20m
- stuck: 40m
