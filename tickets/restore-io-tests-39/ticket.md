---
state: rejected
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-24

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_watchdog.py
- tests/integration/test_watchdog_activation.py

## Goal / Why
`integration-io-guard` fails any integration test that writes disk, starts a process or runs git, and `integration-disk-io-skip` skipped 184 integration files; each now carries the line `pytestmark = pytest.mark.disk_io_skip` (from `disk-io-skip-per-file`). The owner wants them back fast and on the shared fakes. When this ticket is done, these two files run again with every test function and assertion they have today, and neither carries the skip line:

- `tests/integration/test_watchdog.py` (21 tests)
- `tests/integration/test_watchdog_activation.py` (4)

That is 25 tests at the base commit. The helper chain ending in `restore-helpers-misc` has already moved the names other files import from the hub files into `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py` (git on `tests/git_fake.py::GitFake`, no process, writes only under a passed `tmp_path`). Those modules and `tests/git_fake.py` are created by dependencies and are not on main yet: read each in your worktree before use. `restore-io-tests-24` restores `test_requisition.py`, whose `TICKET` constant `test_watchdog_activation.py` imports; read where it left it.

## Boundary contract
none
- reason: tests encoding an existing contract; production code, CLI, journal formats and documents are unchanged.

## Scope in / Scope out
Scope in. For each file delete its `pytestmark = pytest.mark.disk_io_skip` line, then rewrite per the authoring guide section "Unit and integration tests" (read-only context): git on `GitFake`, process on `FakeExec` or in-process `clutch.__main__.main([...])`, journal on `FakeJournal` unless the test's subject is journal persistence, time on `FakeClock` plus `tests.fakes.until`/`turn` and never a sleep, code taking the `clutch.seams.FileSystem` seam on `FakeFileSystem`. Reuse only `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and the seven `*_helpers.py` modules; define no new `Fake*` or stand-in class and copy no helper. Keep every test function, parametrization and assertion; delete, skip or weaken none.

- `test_watchdog.py` (528 lines): its own `Time` clock stand-in and detector rig (`root.mkdir`, `Journal(root / "state", self.time)`), `CoreRig`, and `python_client(cfg, PythonProviderExec(script), tmp_path)` from `test_providers`, whose scripted child is a real python process (`os.write(1, ...)` stream read through `on_stdout_line`); the spend tests write `outside.write_text(...)` and a fenced path under `tmp_path`. Replace `Time` by `FakeClock` (and `tests.fakes.turn` for any `sleep=`), `Journal` by `FakeJournal`, `CoreRig` and the provider client/exec by their fake-backed `daemon_helpers`/`config_helpers` equivalents, which must feed the same stream lines to `on_stdout_line` and the same terminal. Final path `tests/unit/test_watchdog.py` (the spend tests still write under `tmp_path`). If the fake-backed provider exec cannot deliver `on_stdout_line` callbacks in order and report a terminal for a paused child, stop as a premise failure naming that behavior.
- `test_watchdog_activation.py` (471 lines): three tests drive `CoreRig`/`serve_rig` with `FakeLLM` and a patched `cli.SubprocessExec` (`NotificationExec`), write `context.txt` and `clutch/thing.py`, and pass `specs_dir=SPECS` (the packaged prompt specs, a repo read by the code under test). They read a repo file, so they stay at `tests/integration/test_watchdog_activation.py` and must write nothing: route the two writes through the rig's `FakeFileSystem` (`rig.fs`) and use no `tmp_path` file. If a write cannot go through the fake, stop as a premise failure naming it. `test_production_hard_timeout_group_kill_is_harvested` starts a real process group (`PythonProviderExec` subclass with `kill_group`, a real socket server, `os.kill(pgid, 0)`), and the real group kill and reaping is its subject. It moves unchanged in behavior to a new `tests/integration/test_watchdog_group_kill.py`, whose name is added to `REAL_IO_TESTS` in `tests/integration/conftest.py`; its imports come from the helper modules. Imports from `serve_rig` (`finish, graph, terminals, until`), `test_cli`, `test_daemon_composition`, `test_providers`, `test_scheduler` come from the helper modules that now own them; `TICKET` comes from `test_requisition.py` at the path `restore-io-tests-24` left it.

Scope out: hub files and helper modules, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, production code, the plan documents that name these paths, other batches' files. If a shared fake lacks a behavior a test needs, stop as a premise failure naming the missing behavior; never edit a shared module or add a stand-in.

## Scope fence
- tests/integration/test_watchdog.py
- tests/integration/test_watchdog_activation.py
- tests/integration/test_watchdog_group_kill.py
- tests/integration/conftest.py
- tests/unit/test_watchdog.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_*.py tests/unit/test_*.py` lists none of `test_watchdog`, `test_watchdog_activation`, `test_watchdog_group_kill`, and `tests/integration/conftest.py` adds only `test_watchdog_group_kill.py` to `REAL_IO_TESTS`.
2. `./dev.py test tests/unit/test_watchdog.py tests/integration/test_watchdog_activation.py tests/integration/test_watchdog_group_kill.py --durations=0` passes, and `run.md` records the durations output showing no test over 1.0 s except `test_production_hard_timeout_group_kill_is_harvested` (a real process group in a `REAL_IO_TESTS` file), whose time is recorded.
3. `./dev.py test <the same paths> --collect-only -q` collects 25 tests, equal to the base-commit count of the two original files (21 and 4), both recorded in `run.md`.
4. `grep -n "class Time\|PythonProviderExec" tests/unit/test_watchdog.py tests/integration/test_watchdog_activation.py` prints nothing, so no restored non-allowlisted test starts a scripted real child or defines a clock stand-in.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0.

## Verification
```
./dev.py test tests/unit/test_watchdog.py tests/integration/test_watchdog_activation.py tests/integration/test_watchdog_group_kill.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, parametrization-reduced or weakened.
- A new `Fake*` or stand-in class, or a copied helper, appears in a test file.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, a `*_helpers.py` module) is edited.
- A restored non-allowlisted test writes outside `tmp_path`, starts a process or runs git, or any test adds a sleep.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines (999 here) so files sharing fixtures stay together.
