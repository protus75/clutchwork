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
- tests/integration/test_testreport.py
- tests/integration/test_ticket_write_serialization.py

## On-demand
- tests/integration/test_thresh.py

## Goal / Why
`integration-io-guard` fails any integration test that writes disk, starts a process or runs git, and `integration-disk-io-skip` skipped 184 integration files; each now carries the line `pytestmark = pytest.mark.disk_io_skip` (from `disk-io-skip-per-file`). The owner wants them back fast and on the shared fakes. When this ticket is done, these three files run again with every test function and assertion they have today, and none carries the skip line:

- `tests/integration/test_testreport.py` (19 tests)
- `tests/integration/test_thresh.py` (42)
- `tests/integration/test_ticket_write_serialization.py` (7)

That is 68 tests at the base commit. The helper chain ending in `restore-helpers-misc` has already moved the names other files import from the hub files into `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py` (git on `tests/git_fake.py::GitFake`, no process, writes only under a passed `tmp_path`). Those modules and `tests/git_fake.py` are created by dependencies and are not on main yet: read each in your worktree before use.

## Boundary contract
none
- reason: tests encoding an existing contract; production code, CLI, journal formats and documents are unchanged.

## Scope in / Scope out
Scope in. For each file delete its `pytestmark = pytest.mark.disk_io_skip` line, then rewrite per the authoring guide section "Unit and integration tests" (read-only context): git on `GitFake`, process on `FakeExec` or in-process `clutch.__main__.main([...])`, journal on `FakeJournal` unless the test's subject is journal persistence, time on `FakeClock` plus `tests.fakes.until`/`turn` and never a sleep, code taking the `clutch.seams.FileSystem` seam on `FakeFileSystem`. Reuse only `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and the seven `*_helpers.py` modules; define no new `Fake*` or stand-in class and copy no helper. Keep every test function, parametrization and assertion; delete, skip or weaken none.

- `test_testreport.py` (111 lines): `test_reports_all_phases_and_nodeids` (2 params) and `test_no_option_writes_no_file` run `inner_tests.runpytest_subprocess(...)`, with `-n 2` xdist workers in one case, so their subject is a real child pytest process; `test_worker_does_not_write`, `test_read_schema_2`, `test_invalid_results` (13 params) and `test_invalid_json` use only `SimpleNamespace`, strings and an unwritten `tmp_path`. Split: the 16 pure tests move to `tests/unit/test_testreport.py`; the 3 subprocess tests (with the `inner_tests` fixture and `pytest_plugins = ["pytester"]`) move unchanged to a new `tests/integration/test_testreport_subprocess.py`, whose name is added to `REAL_IO_TESTS` in `tests/integration/conftest.py` (a real-I/O test of the plugin's cross-process output).
- `test_thresh.py` (558 lines): the `Time` clock stand-in and `Rig` write `config.yaml` under `tmp_path`, read it with `load_config(None, cwd=path)` and keep a real `Journal` on disk. Replace `Time` by `FakeClock` for `clock=` and, for `sleep=`, a module-level `async def sleep(seconds)` that asserts `seconds == 0` and awaits `tests.fakes.turn()` (no class); replace `Journal` by `FakeJournal`. Split: `test_thresh_is_active` walks `(ROOT / "clutch").rglob("*.py")` (a repo read, no write) and stays at `tests/integration/test_thresh_active.py` (its helper `cli_import_closure` moves with it); the other 41 tests move to `tests/unit/test_thresh.py` (they write only `config.yaml` under `tmp_path`).
- `test_ticket_write_serialization.py` (212 lines): `race` and `test_merge_squash_waits_for_commit_lock` drive the real `Git` (`SubprocessExec`) against a real repo and a real commit lock (`commit_lock` from `tests/integration/test_git.py`), pausing `commit_edit`/`merge_squash` mid-write and asserting the committed bytes (`git show HEAD:...`); that real serialization is the subject. The file stays at `tests/integration/test_ticket_write_serialization.py` and is added to `REAL_IO_TESTS` in `tests/integration/conftest.py`. Everything not under test (clock, `FakeLLM` replies, journal, filesystem for non-ticket paths) uses the shared fakes, the repo is built with the real-git helpers of `tests/integration/test_git.py` (import, never copy), and its other imports (`commit_ticket`, `confirmed`, `make_root`, `pause_checkout`, `_box`, `_failure`, `_routes`, `requisition_reply`, `author_reply`, `reply`, `SNAG`, `order`, `original`, `requisition`, `ctx`) come from the helper modules that now own them; read whether they build a real repo and if one cannot, build it with the `test_git.py` helpers.

Scope out: hub files and helper modules, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, production code, other batches' files. If a shared fake lacks a behavior a test needs, stop as a premise failure naming the missing behavior; never edit a shared module or add a stand-in. If `test_ticket_write_serialization.py` cannot be made to run under a `REAL_IO_TESTS` entry plus the helper modules without defining a new rig class, stop as a premise failure naming the helper.

## Scope fence
- tests/integration/test_testreport.py
- tests/integration/test_testreport_subprocess.py
- tests/integration/test_thresh.py
- tests/integration/test_thresh_active.py
- tests/integration/test_ticket_write_serialization.py
- tests/integration/conftest.py
- tests/unit/test_testreport.py
- tests/unit/test_thresh.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_*.py tests/unit/test_*.py` lists none of `test_testreport`, `test_testreport_subprocess`, `test_thresh`, `test_thresh_active`, `test_ticket_write_serialization`, and `tests/integration/conftest.py` adds only `test_testreport_subprocess.py` and `test_ticket_write_serialization.py` to `REAL_IO_TESTS`.
2. `./dev.py test tests/unit/test_testreport.py tests/unit/test_thresh.py tests/integration/test_thresh_active.py tests/integration/test_testreport_subprocess.py tests/integration/test_ticket_write_serialization.py --durations=0` passes, and `run.md` records the durations output showing no test over 1.0 s except those in the two `REAL_IO_TESTS` files (real process or real git), whose times are recorded.
3. `./dev.py test <the final paths of criterion 2> --collect-only -q` collects 68 tests, equal to the base-commit count of the three original files (19, 42, 7), both recorded in `run.md`; 16 + 3 for the testreport split and 41 + 1 for the thresh split.
4. `tests/unit/test_thresh.py` defines no `Time` class and builds no real `Journal`, checked by `grep -nE "class Time|(^|[^A-Za-z])Journal\(" tests/unit/test_thresh.py` printing nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0.

## Verification
```
./dev.py test tests/unit/test_testreport.py tests/unit/test_thresh.py tests/integration/test_thresh_active.py tests/integration/test_testreport_subprocess.py tests/integration/test_ticket_write_serialization.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, parametrization-reduced or weakened.
- A new `Fake*` or stand-in class, or a copied helper, appears in a test file.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, a `*_helpers.py` module) is edited.
- A restored non-allowlisted integration test writes disk, starts a process or runs git, or any test adds a sleep.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines (881 here) so files sharing fixtures stay together.
