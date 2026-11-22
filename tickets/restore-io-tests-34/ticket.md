---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-25

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/integration/test_supervise_cap_lineage.py
- tests/integration/test_supervisor_rework.py
- tests/integration/test_terminal.py
- tests/integration/test_testguard.py

## On-demand
- tests/integration/test_storm_notification_activation.py
- tests/integration/test_storm_producer.py

## Goal / Why
`integration-io-guard` fails any integration test that writes disk, starts a process or runs git, and `integration-disk-io-skip` skipped 184 integration files; each now carries the line `pytestmark = pytest.mark.disk_io_skip` (from `disk-io-skip-per-file`). The owner wants them back fast and on the shared fakes. When this ticket is done, these six files run again, with every test function and assertion they have today, in under one second per test, and none carries the skip line:

- `tests/integration/test_storm_notification_activation.py` (92 tests)
- `tests/integration/test_storm_producer.py` (24)
- `tests/integration/test_supervise_cap_lineage.py` (1)
- `tests/integration/test_supervisor_rework.py` (3)
- `tests/integration/test_terminal.py` (8)
- `tests/integration/test_testguard.py` (6)

That is 134 tests at the base commit. The helper chain ending in `restore-helpers-misc` has already moved the names other files import from the hub files into `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py` (git on `tests/git_fake.py::GitFake`, no process, writes only under a passed `tmp_path`). These modules are created by dependencies and are not on main yet: read each in your worktree before use. `restore-io-tests-25` restores `test_requisition_gate.py`, whose `setup`, `dispatch` and `reply` `test_supervisor_rework.py` imports; read where it left them.

## Boundary contract
none
- reason: tests encoding an existing contract; production code, CLI, journal formats and documents are unchanged.

## Scope in / Scope out
Scope in. For each file delete its `pytestmark = pytest.mark.disk_io_skip` line, then rewrite onto shared fakes per the authoring guide section "Unit and integration tests" (read-only context): git on `GitFake`, process on `FakeExec` or in-process `clutch.__main__.main([...])`, journal on `FakeJournal` unless the test's subject is journal persistence, time on `FakeClock` plus `tests.fakes.until`/`turn` and never a sleep, code that takes the `clutch.seams.FileSystem` seam on `FakeFileSystem`. Reuse only `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and the seven `*_helpers.py` modules; define no new `Fake*` or stand-in class and copy no helper. Keep every test function, parametrization and assertion; delete, skip or weaken none.

- `test_storm_notification_activation.py` (633 lines): builds `CoreRig`, `make_root`/`commit_ticket`/`confirmed`/`Script` rigs (real git), a real `Journal` and `Box` on `LocalFileSystem` (`rig.fs.write = LocalFileSystem().write`, `daemon.storm_producer(... fs=LocalFileSystem() ...)`), restarts journals from `ctx.config.state_dir`. Move the rigs to `daemon_helpers`/`drain_helpers` rigs, `LocalFileSystem` to `FakeFileSystem`, `Journal` to `FakeJournal`; its `FakeClock, T0` import from `tests/integration/test_journal.py` becomes `tests.fakes.FakeClock`. Final path `tests/unit/test_storm_notification_activation.py` (tests that still write real files write only under `tmp_path`). Importers: `tests/integration/test_daemon_composition.py` (line 2107 imports `SITES, exercise_site`) and `tests/integration/test_storm_hold.py` (imports `digest, occurrences, six, trips`); change only those import lines to `tests.unit.test_storm_notification_activation`.
- `test_storm_producer.py` (290): `compose` builds `daemon.storm_producer(... fs=LocalFileSystem() ...)`; one test defines `class OrderedFS(LocalFileSystem)`; others `Mock(wraps=LocalFileSystem())`, `box.root.mkdir()`, `(box.root / "bad.json").write_text`, `CoreRig`. Use `FakeFileSystem` (wrap the instance's `write` with `monkeypatch.setattr` to record order, no subclass), `FakeJournal`, `FakeClock`. Final path `tests/unit/test_storm_producer.py`. Importers: `test_storm_notification_activation.py` (same ticket, `ARRIVAL, compose`), `tests/integration/test_storm.py` (line 281, `assert_production_reachable`) and `tests/integration/test_storm_hold.py` (`ARRIVAL`); change only those import lines to `tests.unit.test_storm_producer`.
- `test_supervise_cap_lineage.py` (24): writes `tickets/work/ticket.md` under `tmp_path` and calls `observe.capability`, which reads that file. Moves to `tests/unit/test_supervise_cap_lineage_flow.py` (`tests/unit/test_supervise_cap_lineage.py` already exists and is unrelated). No fake needed.
- `test_supervisor_rework.py` (82): `setup`, `dispatch`, `reply` from `test_requisition_gate` run a real git repo; the tests also read `HEAD:tickets/gate/ticket.md`, `git log -1 --format=%s` and `rework.md` through `checkout.git._run`. Rewrite with `GitFake` (`_run` override or `fake.calls`), keeping each commit-subject and committed-bytes assertion. Writes `tickets/gate/*` under `tmp_path`. Final path `tests/unit/test_supervisor_rework.py`.
- `test_terminal.py` (167): `repo` fixture runs `git init`, `git add`, `git commit` and the tests read `ls-files`, `rev-parse`, `show main:...`, a squash merge refusal and a moved `main`; it calls `main([...])` in-process, `FakeLLM`, `load_config`, `Journal` on disk. Replace git with `GitFake` and `FakeJournal`; the `repo`, `author`, `clock`, `diagnosis_reply`, `transitions`, `implement_reply`, `ENV`, `STEM` names that other files import were moved by `restore-helpers-loop`, so this file imports them from `tests/loop_helpers.py`. Final path `tests/unit/test_terminal.py`.
- `test_testguard.py` (161): in-process `pytester` sessions with `-p clutch.testguard`; writes only `pytester` temp files; `ROOT` is used only to build `PYTHONPATH`. Moves to `tests/unit/test_testguard.py`. Two tests start real processes and cannot run under the unit guard: `test_guards_are_phase_scoped` (the inner `pytest_configure` runs a real `subprocess.run(["true"])` to prove the guard is absent outside test phases) and `test_xdist_budget` (`-n 2` spawns xdist workers). Both move unchanged, with the `inner_path` fixture, `run` and `fake_clock` helpers they use (imported from the unit file, never copied), to a new `tests/integration/test_testguard_process.py`, whose name is added to `REAL_IO_TESTS` in `tests/integration/conftest.py`; the other 4 tests stay in `tests/unit/test_testguard.py`. Importer: `tests/regress_testguard_slowest_load.py` names `tests/integration/test_testguard.py::test_budget_and_slowest`; change only that path string to `tests/unit/test_testguard.py::test_budget_and_slowest`.

Scope out: the hub files and helper modules, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, production code, and every other batch's files. If a shared fake lacks a behavior a test needs (for example a `GitFake` that must return committed file bytes or a squash-merge refusal), stop as a premise failure naming the missing behavior; never edit a shared module or add a stand-in. If any file still imports a name from `tests/integration/test_terminal.py` after `restore-helpers-loop`, stop as a premise failure naming the importer.

## Scope fence
- tests/integration/test_storm_notification_activation.py
- tests/integration/test_storm_producer.py
- tests/integration/test_supervise_cap_lineage.py
- tests/integration/test_supervisor_rework.py
- tests/integration/test_terminal.py
- tests/integration/test_testguard.py
- tests/integration/test_testguard_process.py
- tests/integration/conftest.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_storm_hold.py
- tests/integration/test_storm.py
- tests/unit/test_storm_notification_activation.py
- tests/unit/test_storm_producer.py
- tests/unit/test_supervise_cap_lineage_flow.py
- tests/unit/test_supervisor_rework.py
- tests/unit/test_terminal.py
- tests/unit/test_testguard.py
- tests/regress_testguard_slowest_load.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_*.py tests/unit/test_*.py` lists none of the batch's final files (`test_storm_notification_activation`, `test_storm_producer`, `test_supervise_cap_lineage_flow`, `test_supervisor_rework`, `test_terminal`, `test_testguard`, `test_testguard_process`), and `tests/integration/test_testguard_process.py` is the only file added to `REAL_IO_TESTS`.
2. `./dev.py test tests/unit/test_storm_notification_activation.py tests/unit/test_storm_producer.py tests/unit/test_supervise_cap_lineage_flow.py tests/unit/test_supervisor_rework.py tests/unit/test_terminal.py tests/unit/test_testguard.py tests/integration/test_testguard_process.py --durations=0` passes, and `run.md` records the durations output showing no restored test over 1.0 s except `test_xdist_budget` and `test_guards_are_phase_scoped` (real-process tests in a `REAL_IO_TESTS` file), whose times are recorded.
3. `./dev.py test <the final paths of criterion 2> --collect-only -q` collects 134 tests, equal to the base-commit count of the six original files (92, 24, 1, 3, 8, 6), both recorded in `run.md`.
4. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0.
5. `grep -rn "test_storm_notification_activation\|test_storm_producer\|test_testguard" tests` names only the new `tests.unit.` or `tests/unit/` paths (and `test_testguard_process`), not `tests.integration.test_storm_notification_activation`, `tests.integration.test_storm_producer` or `tests/integration/test_testguard.py`.

## Verification
```
./dev.py test tests/unit/test_storm_notification_activation.py tests/unit/test_storm_producer.py tests/unit/test_supervise_cap_lineage_flow.py tests/unit/test_supervisor_rework.py tests/unit/test_terminal.py tests/unit/test_testguard.py tests/integration/test_testguard_process.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, parametrization-reduced or weakened.
- A new `Fake*` or stand-in class, or a copied helper, appears in a test file.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, a `*_helpers.py` module) is edited.
- A restored integration test writes disk, starts a process or runs git, or any test adds a sleep.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines (1,357 here) so files sharing fixtures stay together.
