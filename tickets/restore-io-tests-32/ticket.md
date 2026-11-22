---
state: rejected
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc

## Context
- tests/integration/test_stale_running.py
- tests/integration/test_stats.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_stages.py

## Goal / Why
`integration-disk-io-skip` skipped 184 integration test files after one run wrote 975 MB in 119,498 files and 1,531 real git repos. This ticket restores the stage tests (`test_stages.py`, 59 tests), the stale-running tests and the stats tests (70 tests together). Each loses its `pytestmark = pytest.mark.disk_io_skip` line and passes under the rules of `clutch/docs/host-authoring.md#Unit and integration tests`, fast (no test above 1.0 s) and on the shared fakes. `test_stages.py` is the hub other files imported fixtures and helpers from; `restore-helpers-stages` moved them to `tests/stages_helpers.py`, so what stays here is its own tests, which build their repo through those helpers. Path pins: `tests/integration/test_contention_rules.py` asserts `tests/integration/test_stages.py` exists and `CLAUDE.md`/`AGENTS.md` name it, and `tests/regress_base_red_branch_only_path.py` runs it by that path, so the file stays at `tests/integration/test_stages.py` and keeps every test that reads the repo's `clutch/specs` (`SPECS`, anchored on `Path(__file__)`) and writes nothing real.

## Boundary contract
none
- reason: tests encoding an existing contract; the production code under test, its callers, outputs, failures and side effects are unchanged and only test files move or change

## Scope in / Scope out
Scope in, per file (base-commit facts; the implementer re-reads each file first):
- `tests/integration/test_stages.py` (944 lines, 59 tests): each test runs a stage (`implement`, `review`, `check`, `author`, `report_context`) over the `repo` fixture: a real git repo with real files under `tickets/<stem>/` (`run.md`, `checks.json`, `review.md`) and `ctx.git` calls. The repo fixture comes from `tests/stages_helpers.py` on `GitFake` and the fake file system; read it first. A test whose rewritten body needs no real file stays in `tests/integration/test_stages.py` (it still reads `clutch/specs` by the `SPECS` anchor); a test that still has to write real files under `tmp_path` moves to the new `tests/unit/test_stages_flow.py`. State the split by test name in `run.md`. If `tests/regress_base_red_branch_only_path.py`'s target `test_red_command_naming_a_branch_added_file_is_not_base_red` moves, change its path string only (`tests/unit/test_stages_flow.py`), which is why that file is fenced; keep the test in `tests/integration/test_stages.py` when it needs no real file. Final path: `tests/integration/test_stages.py` and `tests/unit/test_stages_flow.py`.
- `tests/integration/test_stale_running.py` (159 lines, 7 tests): `make_root` repo, `Lockfile`, `main([...])` reject/priority verbs, `Git(SubprocessExec(), commit_lock=commit_lock(...))` with `commit_lock` imported from `test_git.py` (a REAL_IO file; `restore-helpers-misc` provides the fake-backed equivalent in `tests/misc_helpers.py`), and ticket files read back from `tmp_path`. Git to `GitFake`, exec to `FakeExec`, journal to `FakeJournal`. It imports `held_events` from `tests/unit/test_stale_running.py` and `fake_snapshot_inputs` from `tests/unit/test_menu_admission.py`. (`tests/unit/test_stale_running.py` exists, hence `_flow`.) Final path: `tests/unit/test_stale_running_flow.py`.
- `tests/integration/test_stats.py` (116 lines, 4 tests): `Journal(tmp_path, clock)` real segments (the tests read segment bytes before and after to prove the verb writes nothing) and `make_root` plus `main(['stats', ...])`. Journal files stay real under `tmp_path` because journal persistence is the subject; the repo from `make_root` becomes the fake-backed root from the drain helpers. (`tests/unit/test_stats.py` exists, hence `_flow`.) Final path: `tests/unit/test_stats_flow.py`.

Scope in, every file above:
- Delete the line `pytestmark = pytest.mark.disk_io_skip` (and `import pytest` only when nothing else in the file uses it).
- Rewrite the test body wiring, keeping every test function, parametrization, name and assertion: git becomes `GitFake` from `tests/git_fake.py` (overrides by member name, `fake.calls`); a process becomes `FakeExec` from `tests/fakes.py` or an in-process `clutch.__main__.main([...])` call (when `main` builds its own `SubprocessExec`, replace that construction point with the `fake_exec` fixture's object through `monkeypatch`); the journal becomes `FakeJournal` unless the test's subject is journal persistence; time becomes `FakeClock` plus `until`/`turn`, never a sleep; code taking the `clutch.seams.FileSystem` seam gets `FakeFileSystem`.
- Reuse only the shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. The modules created by `restore-helpers-misc` and its chain (`restore-helpers-cli` through `restore-helpers-misc`) and by `shared-git-fake-integration`, `shared-review-script` and `shared-serve-rig-config` are merged before this ticket runs; read them in the worktree before editing. Names the files import from `tests.integration.test_cli`, `test_drain`, `test_stages`, `test_scheduler`, `test_rework` and the other hubs already come from those helper modules; keep each import line that names a helper module as it is.
- Placement by the unit and integration test rules in the host authoring guide (the Context section): a file whose rewritten tests still write real files (only under `tmp_path`), or use only fakes, moves to `tests/unit/` (the final path above; same file name, `_flow` suffix where `tests/unit/` already has that name); a test that reads a repo file anchored on `Path(__file__)` and writes nothing stays under `tests/integration/`; a file needing both is split into the two paths named above, each test function keeping its name. Moving a file means deleting the old path in the same change.
- Update the import lines of every other file that imports a name from a file this ticket moves (the fence lists them); only those import lines change in them.
- If a shared fake lacks a behavior a test needs, stop as a premise failure naming the missing behavior and the test; never edit a shared module and never add a `Fake*`/stand-in class or a copy of a helper to a test file.

Scope out: every file under `tests/` not listed above except the importers named in the fence, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, `tests/integration/conftest.py`, `tests/integration/serve_rig.py`, the helper modules, `clutch/`, and `docs/`. No test is deleted, skipped, weakened or given a sleep; assertions keep their meaning.

## Scope fence
- tests/integration/test_stages.py
- tests/integration/test_stale_running.py
- tests/integration/test_stats.py
- tests/unit/test_stages_flow.py
- tests/unit/test_stale_running_flow.py
- tests/unit/test_stats_flow.py
- tests/regress_base_red_branch_only_path.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_stages.py tests/unit/test_stages_flow.py tests/unit/test_stale_running_flow.py tests/unit/test_stats_flow.py` lists none of the paths (exit 1 with no output; every file still carrying the marker is a rejection).
2. `./dev.py test tests/integration/test_stages.py tests/unit/test_stages_flow.py tests/unit/test_stale_running_flow.py tests/unit/test_stats_flow.py --durations=0` passes, and its durations output (recorded in `run.md`) lists no restored test above 1.0 s.
3. `./dev.py test tests/integration/test_stages.py tests/unit/test_stages_flow.py tests/unit/test_stale_running_flow.py tests/unit/test_stats_flow.py --collect-only -q` collects 70 tests, equal to the count `./dev.py test tests/integration/test_stages.py tests/integration/test_stale_running.py tests/integration/test_stats.py --collect-only -q` gives on the base commit; `run.md` records both counts (fewer collected means a test was deleted).
4. `grep -nE "^\s*class (Fake|Stub|Empty)\w*|time\.sleep|import subprocess|SubprocessExec\(\)" tests/integration/test_stages.py tests/unit/test_stages_flow.py tests/unit/test_stale_running_flow.py tests/unit/test_stats_flow.py` prints nothing (no new fake class, no real sleep, no real process).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.

## Verification
```
./dev.py test tests/integration/test_stages.py tests/unit/test_stages_flow.py tests/unit/test_stale_running_flow.py tests/unit/test_stats_flow.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, weakened, or loses an assertion, or the collected-test count differs from the base commit.
- A new `Fake*`/stand-in class or a copy of a shared helper appears in a test file, or a shared module (`tests/fakes.py`, `tests/git_fake.py`, a helper module, `tests/conftest.py`, `tests/integration/conftest.py`, `tests/integration/serve_rig.py`) is edited.
- A restored integration test writes disk, starts a process, or runs git.
- A sleep is added, or a restored test takes more than 1.0 s.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines (1219 here) so files sharing fixtures stay together; the files are restored by mechanical edits to import lines and fake wiring.
