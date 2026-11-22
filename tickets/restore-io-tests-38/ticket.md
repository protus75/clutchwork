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
- tests/integration/test_watch_surface_tier.py
- tests/integration/test_contention_rules.py
- tests/regress_watch_surface_tier_truth.py
- tests/regress_watch_tests_fixture_repo.py

## On-demand
- tests/integration/test_watch.py
- CLAUDE.md
- AGENTS.md

## Goal / Why
`integration-io-guard` fails any integration test that writes disk, starts a process or runs git, and `integration-disk-io-skip` skipped 184 integration files; each now carries the line `pytestmark = pytest.mark.disk_io_skip` (from `disk-io-skip-per-file`). The owner wants them back fast and on the shared fakes. When this ticket is done, these two files run again with every test function and assertion they have today, and neither carries the skip line:

- `tests/integration/test_watch.py` (31 tests)
- `tests/integration/test_watch_surface_tier.py` (6)

That is 37 tests at the base commit. The helper chain ending in `restore-helpers-misc` has already moved the names other files import from the hub files into `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py` (git on `tests/git_fake.py::GitFake`, no process, writes only under a passed `tmp_path`); `restore-helpers-config` rebuilt `watch_fixture_repo` (git-free, `tmp_path` only) in `tests/config_helpers.py`, and `VALID` (imported from `test_config.py`) lives there too. Those modules and `tests/git_fake.py` are created by dependencies and are not on main yet: read each in your worktree before use.

## Boundary contract
none
- reason: tests encoding an existing contract; production code, CLI, journal formats and documents are unchanged.

## Scope in / Scope out
Scope in. For each file delete its `pytestmark = pytest.mark.disk_io_skip` line, then rewrite per the authoring guide section "Unit and integration tests" (read-only context): git on `GitFake`, process on `FakeExec` or in-process `clutch.__main__.main([...])`, journal on `FakeJournal` unless the test's subject is journal persistence, time on `FakeClock` plus `tests.fakes.until`/`turn` and never a sleep, code taking the `clutch.seams.FileSystem` seam on `FakeFileSystem`. Reuse only `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and the seven `*_helpers.py` modules; define no new `Fake*` or stand-in class and copy no helper. Keep every test function, parametrization and assertion; delete, skip or weaken none.

- `test_watch.py` (863 lines): almost every test writes `config.yaml` (autouse `config_fixture`, `VALID` from `test_config`), ticket files, `state/journal/*.jsonl`, `engine.log` and `clutch.lock` under `tmp_path` and calls `clutch.observe` functions or `main(["--config", ..., "view", "snapshot"], cwd=repo)` in-process; `watch_fixture_repo` and a `Box` on `LocalFileSystem` are used in several; `test_running_needs_a_live_lock_holder_that_journaled_it` starts a real child with `subprocess.Popen([sys.executable, "-c", "pass"])` only to obtain a dead pid. Imports from `test_cli`, `test_config`, `test_drain` and `test_git` come from the helper modules that now own them. The `observe` functions read real files under `ctx.root`/`ctx.state`, so the tests keep writing under `tmp_path`: the file moves to `tests/unit/test_watch.py`. Replace the child process by a pid that `os.kill(pid, 0)` reports gone (no process is started) and `LocalFileSystem` by `FakeFileSystem`. `test_snapshot_display_fields` also reads `vscode-clutchwork/package.json` (a repo file) and writes `engine.log`; it moves, unchanged except that its `engine.log` write is replaced by a `monkeypatch.setattr` of the `observe` reader of that log (as the test already patches `journal`, `commits`, `lock_holder`), to a new `tests/integration/test_watch_display_fields.py` that writes nothing. If no single `observe` function reads that log, stop as a premise failure naming it.
- `test_watch_surface_tier.py` (74 lines): the `ctx` fixture writes `config.yaml`, `tickets/alpha/ticket.md`, a journal, `engine.log` and `clutch.lock` under `tmp_path`; `observe.capability` itself reads the packaged `resolve` and `requisition_review` prompt specs and the test's `effort` fixture takes its expected value from that same packaged spec through `load_spec`. It moves to `tests/unit/test_watch_surface_tier.py` with `VALID` imported from `tests/config_helpers.py` and nothing else changed. The packaged-spec read is the code under test and the oracle for the expected value; keep it exactly as is and name it in `run.md`.
- Hot-file list: `test_watch.py` is named in the do-not-grow rule. Change its path in that rule to `tests/unit/test_watch.py` in `CLAUDE.md` and `AGENTS.md` (the one `Keep new tests out of the hot test files` bullet in each, outside the managed block) and in the `DO_NOT_GROW` tuple of `tests/integration/test_contention_rules.py`, which asserts each listed path is a file. Nothing else in those three files changes. Rule home: these are repo rules about working on clutch's own tests, so they stay in `CLAUDE.md` and `AGENTS.md`, not in `CORE_TEMPLATE`.
- Importers: `tests/regress_watch_tests_fixture_repo.py` (`ROOT / "tests/integration/test_watch.py"` becomes `tests/unit/test_watch.py`) and `tests/regress_watch_surface_tier_truth.py` (`tests/integration/test_watch_surface_tier.py` becomes `tests/unit/test_watch_surface_tier.py`); change only those path strings.

Scope out: hub files and helper modules, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, `tests/unit/test_menu_admission.py` (its `fake_snapshot_inputs` is imported as is), production code, the historical mentions of the old path in the plan and roadmap documents, other batches' files. If a shared fake lacks a behavior a test needs, stop as a premise failure naming it; never edit a shared module or add a stand-in.

## Scope fence
- tests/integration/test_watch.py
- tests/integration/test_watch_display_fields.py
- tests/integration/test_watch_surface_tier.py
- tests/integration/test_contention_rules.py
- tests/unit/test_watch.py
- tests/unit/test_watch_surface_tier.py
- tests/regress_watch_surface_tier_truth.py
- tests/regress_watch_tests_fixture_repo.py
- CLAUDE.md
- AGENTS.md

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_*.py tests/unit/test_*.py` lists none of `test_watch`, `test_watch_display_fields`, `test_watch_surface_tier`.
2. `./dev.py test tests/unit/test_watch.py tests/integration/test_watch_display_fields.py tests/unit/test_watch_surface_tier.py --durations=0` passes, and `run.md` records the durations output showing no test over 1.0 s.
3. `./dev.py test <the same paths> --collect-only -q` collects 37 tests, equal to the base-commit count of the two original files (31 and 6), both recorded in `run.md`.
4. `./dev.py test tests/integration/test_contention_rules.py` passes with `tests/unit/test_watch.py` in `DO_NOT_GROW` and in the `CLAUDE.md` and `AGENTS.md` bullet, and `grep -rn "tests/integration/test_watch.py" CLAUDE.md AGENTS.md tests` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and `grep -n "subprocess\|Popen" tests/unit/test_watch.py` prints nothing.

## Verification
```
./dev.py test tests/unit/test_watch.py tests/integration/test_watch_display_fields.py tests/unit/test_watch_surface_tier.py --durations=0
./dev.py test tests/integration/test_contention_rules.py
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
- reason: the batch is cut at about 1,400 lines (937 here) so files sharing fixtures stay together.
