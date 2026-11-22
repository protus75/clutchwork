---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-27
- restore-io-tests-19

## Context
- tests/integration/test_roadmap_start_gates.py
- tests/integration/test_roadmap_status.py
- tests/integration/test_route_kinds_judge_lint.py
- tests/integration/test_scorecard.py
- tests/integration/test_second_problems.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_scheduler.py

## Goal / Why
`integration-disk-io-skip` skipped 184 integration test files after one run wrote 975 MB in 119,498 files and 1,531 real git repos. This ticket restores six of them (33 tests): the scheduler, scorecard, second-problems, route-kinds judge lint, roadmap start-gate and roadmap status tests. Each loses its `pytestmark = pytest.mark.disk_io_skip` line and passes under the rules of `clutch/docs/host-authoring.md#Unit and integration tests`, fast (no test above 1.0 s) and on the shared fakes with no per-file fake class or helper copy. The scheduler tests build their `Rig` over `LocalFileSystem` and a `Time` class; those definitions moved to the loop helper module (`restore-helpers-loop`) and the rig runs on the shared fakes. The scorecard tests build the retro `rig`, which `restore-helpers-misc` made fake-backed. Done means the 33 tests run in the suites with no real git, process or repo write.

## Boundary contract
none
- reason: tests encoding an existing contract; the production code under test, its callers, outputs, failures and side effects are unchanged and only test files move or change

## Scope in / Scope out
Scope in, per file (base-commit facts; the implementer re-reads each file first):
- `tests/integration/test_roadmap_start_gates.py` (86 lines, 2 tests): `test_status_and_author_start` runs `roadmap status` and the author start with a `sys.executable -c pass` start command, real `Git(SubprocessExec())`, `LocalFileSystem`, `CommitLock` and `setup_repo` from `test_roadmap_author` (`restore-io-tests-27`, a dependency, moves it to `tests/unit/test_roadmap_author_flow.py` as a fake-backed `setup_repo` and repoints this import line; if `setup_repo` still runs real git or `git_out` when this ticket runs, stop as a premise failure naming it). The test's assertions that the start gate blocks and then passes authoring across commits are kept against `GitFake.calls` and overrides; `test_repository_start_and_ship_blocks` reads the repo roadmap anchored on `Path(__file__)` and writes nothing. Split: the first goes to `tests/unit/test_roadmap_start_gates_flow.py` (`tests/unit/test_roadmap_start_gates.py` exists) with git on `GitFake` and the start command on `FakeExec`, the second to `tests/integration/test_roadmap_start_gates_repo.py`. It already imports `fixture` from `tests/unit/test_roadmap_status.py`. Final path: `tests/unit/test_roadmap_start_gates_flow.py` and `tests/integration/test_roadmap_start_gates_repo.py`.
- `tests/integration/test_roadmap_status.py` (53 lines, 1 tests): real `Git(SubprocessExec())` init, add, commit, `git rev-parse`/`status --porcelain` through `git._run`, a real `Journal` and `main(['roadmap', 'status'])`/`gate`; it asserts the status verb leaves HEAD, porcelain and the journal segment bytes unchanged. Git to `GitFake` (the `calls` list proves no write call), journal segments stay real files under `tmp_path` for the byte comparison. Final path: `tests/unit/test_roadmap_status_flow.py`.
- `tests/integration/test_route_kinds_judge_lint.py` (27 lines, 1 tests): writes `config.yaml` and ticket files under the `root` fixture and runs `lint` imported from `tests/integration/test_lint_verb.py` (`restore-io-tests-19`, a dependency, moves `test_lint_verb.py` and repoints this import line); real files under `tmp_path` only. Final path: `tests/unit/test_route_kinds_judge_lint.py`.
- `tests/integration/test_scheduler.py` (578 lines, 20 tests): `Rig`/`CoreRig` tests over `Scheduler` and `Watcher` with `LocalFileSystem`, real ticket files and `state/queue.json` under `tmp_path`, a hand-made clock (`Time`, `turn`, `text`, `import_closure` moved to the loop helpers by `restore-helpers-loop`, and other files import them from there). The fs seam goes to `FakeFileSystem` where the tests only use the seam. `test_scheduler_and_watcher_are_dormant` reads `clutch/**/*.py` anchored on `Path(__file__)` and writes nothing. Split: it goes to `tests/integration/test_scheduler_dormant.py`; the other 19 tests go to `tests/unit/test_scheduler.py`. Final path: `tests/unit/test_scheduler.py` and `tests/integration/test_scheduler_dormant.py`.
- `tests/integration/test_scorecard.py` (271 lines, 6 tests): builds the retro `rig(tmp_path)` and real invoices; journal and ticket files under `tmp_path`; the retro `rig`, `completed`, `merged` come from `restore-helpers-misc`. Its `invoice`, `review` and `rows` are imported by `tests/integration/test_status.py` (`restore-io-tests-33`): moving this file changes that import line to `tests.unit.test_scorecard`, so `test_status.py` is fenced here for that one line. Final path: `tests/unit/test_scorecard.py`.
- `tests/integration/test_second_problems.py` (97 lines, 3 tests): uses the `repo` fixture from the loop helpers (`test_terminal`), `main([...])`, `Box` on `LocalFileSystem` and a `run.md` read from the repo under `tmp_path`; box to `FakeFileSystem` where possible, git to `GitFake`. Final path: `tests/unit/test_second_problems.py`.

Scope in, every file above:
- Delete the line `pytestmark = pytest.mark.disk_io_skip` (and `import pytest` only when nothing else in the file uses it).
- Rewrite the test body wiring, keeping every test function, parametrization, name and assertion: git becomes `GitFake` from `tests/git_fake.py` (overrides by member name, `fake.calls`); a process becomes `FakeExec` from `tests/fakes.py` or an in-process `clutch.__main__.main([...])` call (when `main` builds its own `SubprocessExec`, replace that construction point with the `fake_exec` fixture's object through `monkeypatch`); the journal becomes `FakeJournal` unless the test's subject is journal persistence; time becomes `FakeClock` plus `until`/`turn`, never a sleep; code taking the `clutch.seams.FileSystem` seam gets `FakeFileSystem`.
- Reuse only the shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. The modules created by `restore-helpers-misc` and its chain (`restore-helpers-cli` through `restore-helpers-misc`) and by `shared-git-fake-integration`, `shared-review-script` and `shared-serve-rig-config` are merged before this ticket runs; read them in the worktree before editing. Names the files import from `tests.integration.test_cli`, `test_drain`, `test_stages`, `test_scheduler`, `test_rework` and the other hubs already come from those helper modules; keep each import line that names a helper module as it is.
- Placement by the unit and integration test rules in the host authoring guide (the Context section): a file whose rewritten tests still write real files (only under `tmp_path`), or use only fakes, moves to `tests/unit/` (the final path above; same file name, `_flow` suffix where `tests/unit/` already has that name); a test that reads a repo file anchored on `Path(__file__)` and writes nothing stays under `tests/integration/`; a file needing both is split into the two paths named above, each test function keeping its name. Moving a file means deleting the old path in the same change.
- Update the import lines of every other file that imports a name from a file this ticket moves (the fence lists them); only those import lines change in them.
- If a shared fake lacks a behavior a test needs, stop as a premise failure naming the missing behavior and the test; never edit a shared module and never add a `Fake*`/stand-in class or a copy of a helper to a test file.

Scope out: every file under `tests/` not listed above except the importers named in the fence, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, `tests/integration/conftest.py`, `tests/integration/serve_rig.py`, the helper modules, `clutch/`, and `docs/`. No test is deleted, skipped, weakened or given a sleep; assertions keep their meaning.

## Scope fence
- tests/integration/test_roadmap_start_gates.py
- tests/integration/test_roadmap_status.py
- tests/integration/test_route_kinds_judge_lint.py
- tests/integration/test_scheduler.py
- tests/integration/test_scorecard.py
- tests/integration/test_second_problems.py
- tests/unit/test_roadmap_start_gates_flow.py
- tests/integration/test_roadmap_start_gates_repo.py
- tests/unit/test_roadmap_status_flow.py
- tests/unit/test_route_kinds_judge_lint.py
- tests/unit/test_scheduler.py
- tests/integration/test_scheduler_dormant.py
- tests/unit/test_scorecard.py
- tests/unit/test_second_problems.py
- tests/integration/test_status.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_roadmap_start_gates_flow.py tests/integration/test_roadmap_start_gates_repo.py tests/unit/test_roadmap_status_flow.py tests/unit/test_route_kinds_judge_lint.py tests/unit/test_scheduler.py tests/integration/test_scheduler_dormant.py tests/unit/test_scorecard.py tests/unit/test_second_problems.py` lists none of the paths (exit 1 with no output; every file still carrying the marker is a rejection).
2. `./dev.py test tests/unit/test_roadmap_start_gates_flow.py tests/integration/test_roadmap_start_gates_repo.py tests/unit/test_roadmap_status_flow.py tests/unit/test_route_kinds_judge_lint.py tests/unit/test_scheduler.py tests/integration/test_scheduler_dormant.py tests/unit/test_scorecard.py tests/unit/test_second_problems.py --durations=0` passes, and its durations output (recorded in `run.md`) lists no restored test above 1.0 s.
3. `./dev.py test tests/unit/test_roadmap_start_gates_flow.py tests/integration/test_roadmap_start_gates_repo.py tests/unit/test_roadmap_status_flow.py tests/unit/test_route_kinds_judge_lint.py tests/unit/test_scheduler.py tests/integration/test_scheduler_dormant.py tests/unit/test_scorecard.py tests/unit/test_second_problems.py --collect-only -q` collects 33 tests, equal to the count `./dev.py test tests/integration/test_roadmap_start_gates.py tests/integration/test_roadmap_status.py tests/integration/test_route_kinds_judge_lint.py tests/integration/test_scheduler.py tests/integration/test_scorecard.py tests/integration/test_second_problems.py --collect-only -q` gives on the base commit; `run.md` records both counts (fewer collected means a test was deleted).
4. `grep -nE "^\s*class (Fake|Stub|Empty)\w*|time\.sleep|import subprocess|SubprocessExec\(\)" tests/unit/test_roadmap_start_gates_flow.py tests/integration/test_roadmap_start_gates_repo.py tests/unit/test_roadmap_status_flow.py tests/unit/test_route_kinds_judge_lint.py tests/unit/test_scheduler.py tests/integration/test_scheduler_dormant.py tests/unit/test_scorecard.py tests/unit/test_second_problems.py` prints nothing (no new fake class, no real sleep, no real process).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_start_gates_flow.py tests/integration/test_roadmap_start_gates_repo.py tests/unit/test_roadmap_status_flow.py tests/unit/test_route_kinds_judge_lint.py tests/unit/test_scheduler.py tests/integration/test_scheduler_dormant.py tests/unit/test_scorecard.py tests/unit/test_second_problems.py --durations=0
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
- reason: the batch is cut at about 1,400 lines (1112 here) so files sharing fixtures stay together; the files are restored by mechanical edits to import lines and fake wiring.
