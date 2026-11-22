---
state: rejected
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc

## Context
- tests/integration/test_serve_confirm_during_check.py
- tests/integration/test_serve_dispatch.py
- tests/integration/test_serve_driver.py
- tests/integration/test_serve_driver_overlap.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_serve_admission.py

## Goal / Why
`integration-disk-io-skip` skipped 184 integration test files after one run wrote 975 MB in 119,498 files and 1,531 real git repos. This ticket restores five serve test files (38 tests): admission, confirm-during-check, dispatch, driver and driver-overlap. Each loses its `pytestmark = pytest.mark.disk_io_skip` line and passes under the rules of `clutch/docs/host-authoring.md#Unit and integration tests`, fast (no test above 1.0 s) and on the shared fakes. The serve rig now builds on `GitFake`, so tests that read or move git state (`rev_parse`, `add`, `commit`, `status_porcelain`, `_run('log' ...)`) assert through `GitFake` overrides and `fake.calls`; tests that ran `python3 -c` mechanical checks or review commands run them as `FakeExec` results. Done means the 38 tests run with no real git, process or repo write.

## Boundary contract
none
- reason: tests encoding an existing contract; the production code under test, its callers, outputs, failures and side effects are unchanged and only test files move or change

## Scope in / Scope out
Scope in, per file (base-commit facts; the implementer re-reads each file first):
- `tests/integration/test_serve_admission.py` (575 lines, 17 tests): serve tests run the `serve` loop over the rig from `tests/integration/serve_rig.py` (`graph`, `script`, `terminals`, `until`, `write`, `finish`, `admission_graph`, `start_admission`; `restore-helpers-loop` moved its real-git and process parts into `tests/loop_helpers.py` and `serve_rig.py` imports them), using the `root` fixture from the cli helpers. It drives admission, merge, tree-mismatch and conflict paths through real git calls on the rig repo (`git.add`, `commit`, `rev_parse`, `merge_squash`, `_run('log' ...)`, `_call('show' ...)`) and mechanical review commands that run `python3 -c` over repo files. Each becomes `GitFake` overrides and `FakeExec` results; file reads of the rig repo (`clutch/thing.py`, `clutch/green.py`, `generated.txt`) become reads of the `FakeFileSystem`/`tmp_path` tree the rig owns. Final path: `tests/unit/test_serve_admission.py`.
- `tests/integration/test_serve_confirm_during_check.py` (128 lines, 2 tests): serve tests run the `serve` loop over the rig from `tests/integration/serve_rig.py` (`graph`, `script`, `terminals`, `until`, `write`, `finish`, `admission_graph`, `start_admission`; `restore-helpers-loop` moved its real-git and process parts into `tests/loop_helpers.py` and `serve_rig.py` imports them), using the `root` fixture from the cli helpers. Git inspection `git._run(root, 'show', 'main:tickets/two/ticket.md')` becomes a `GitFake` override. `tests/regress_serve_confirm_during_check.py` runs `tests/integration/test_serve_confirm_during_check.py::test_confirmation_during_queued_merge_and_check` by that exact path, so moving the file changes the one path string in it (`tests/unit/test_serve_confirm_during_check.py`) and nothing else; keep the `CONFIRM_NOT_APPLIED_WHILE_CHECK_HELD` output marker the runner greps for. Final path: `tests/unit/test_serve_confirm_during_check.py`.
- `tests/integration/test_serve_dispatch.py` (220 lines, 13 tests): serve tests run the `serve` loop over the rig from `tests/integration/serve_rig.py` (`graph`, `script`, `terminals`, `until`, `write`, `finish`, `admission_graph`, `start_admission`; `restore-helpers-loop` moved its real-git and process parts into `tests/loop_helpers.py` and `serve_rig.py` imports them), using the `root` fixture from the cli helpers. It uses git `add`/`commit(only=...)` to move ticket files on the rig repo and reads `tickets/work/ticket.md`; git to `GitFake`, ticket files to the rig's fake file system. Final path: `tests/unit/test_serve_dispatch.py`.
- `tests/integration/test_serve_driver.py` (57 lines, 2 tests): serve tests run the `serve` loop over the rig from `tests/integration/serve_rig.py` (`graph`, `script`, `terminals`, `until`, `write`, `finish`, `admission_graph`, `start_admission`; `restore-helpers-loop` moved its real-git and process parts into `tests/loop_helpers.py` and `serve_rig.py` imports them), using the `root` fixture from the cli helpers, and `text` from the loop helpers; it only writes ticket files and roadmap text under the rig root. Final path: `tests/unit/test_serve_driver.py`.
- `tests/integration/test_serve_driver_overlap.py` (146 lines, 4 tests): serve tests run the `serve` loop over the rig from `tests/integration/serve_rig.py` (`graph`, `script`, `terminals`, `until`, `write`, `finish`, `admission_graph`, `start_admission`; `restore-helpers-loop` moved its real-git and process parts into `tests/loop_helpers.py` and `serve_rig.py` imports them), using the `root` fixture from the cli helpers; it imports `RecordingLog` from `tests/unit/test_phase_events.py`. (`tests/unit/test_serve_driver_overlap.py` exists, hence `_flow`.) Final path: `tests/unit/test_serve_driver_overlap_flow.py`.

Scope in, every file above:
- Delete the line `pytestmark = pytest.mark.disk_io_skip` (and `import pytest` only when nothing else in the file uses it).
- Rewrite the test body wiring, keeping every test function, parametrization, name and assertion: git becomes `GitFake` from `tests/git_fake.py` (overrides by member name, `fake.calls`); a process becomes `FakeExec` from `tests/fakes.py` or an in-process `clutch.__main__.main([...])` call (when `main` builds its own `SubprocessExec`, replace that construction point with the `fake_exec` fixture's object through `monkeypatch`); the journal becomes `FakeJournal` unless the test's subject is journal persistence; time becomes `FakeClock` plus `until`/`turn`, never a sleep; code taking the `clutch.seams.FileSystem` seam gets `FakeFileSystem`.
- Reuse only the shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. The modules created by `restore-helpers-misc` and its chain (`restore-helpers-cli` through `restore-helpers-misc`) and by `shared-git-fake-integration`, `shared-review-script` and `shared-serve-rig-config` are merged before this ticket runs; read them in the worktree before editing. Names the files import from `tests.integration.test_cli`, `test_drain`, `test_stages`, `test_scheduler`, `test_rework` and the other hubs already come from those helper modules; keep each import line that names a helper module as it is.
- Placement by the unit and integration test rules in the host authoring guide (the Context section): a file whose rewritten tests still write real files (only under `tmp_path`), or use only fakes, moves to `tests/unit/` (the final path above; same file name, `_flow` suffix where `tests/unit/` already has that name); a test that reads a repo file anchored on `Path(__file__)` and writes nothing stays under `tests/integration/`; a file needing both is split into the two paths named above, each test function keeping its name. Moving a file means deleting the old path in the same change.
- Update the import lines of every other file that imports a name from a file this ticket moves (the fence lists them); only those import lines change in them.
- If a shared fake lacks a behavior a test needs, stop as a premise failure naming the missing behavior and the test; never edit a shared module and never add a `Fake*`/stand-in class or a copy of a helper to a test file.

Scope out: every file under `tests/` not listed above except the importers named in the fence, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, `tests/integration/conftest.py`, `tests/integration/serve_rig.py`, the helper modules, `clutch/`, and `docs/`. No test is deleted, skipped, weakened or given a sleep; assertions keep their meaning.

## Scope fence
- tests/integration/test_serve_admission.py
- tests/integration/test_serve_confirm_during_check.py
- tests/integration/test_serve_dispatch.py
- tests/integration/test_serve_driver.py
- tests/integration/test_serve_driver_overlap.py
- tests/unit/test_serve_admission.py
- tests/unit/test_serve_confirm_during_check.py
- tests/unit/test_serve_dispatch.py
- tests/unit/test_serve_driver.py
- tests/unit/test_serve_driver_overlap_flow.py
- tests/regress_serve_confirm_during_check.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_serve_admission.py tests/unit/test_serve_confirm_during_check.py tests/unit/test_serve_dispatch.py tests/unit/test_serve_driver.py tests/unit/test_serve_driver_overlap_flow.py` lists none of the paths (exit 1 with no output; every file still carrying the marker is a rejection).
2. `./dev.py test tests/unit/test_serve_admission.py tests/unit/test_serve_confirm_during_check.py tests/unit/test_serve_dispatch.py tests/unit/test_serve_driver.py tests/unit/test_serve_driver_overlap_flow.py --durations=0` passes, and its durations output (recorded in `run.md`) lists no restored test above 1.0 s.
3. `./dev.py test tests/unit/test_serve_admission.py tests/unit/test_serve_confirm_during_check.py tests/unit/test_serve_dispatch.py tests/unit/test_serve_driver.py tests/unit/test_serve_driver_overlap_flow.py --collect-only -q` collects 38 tests, equal to the count `./dev.py test tests/integration/test_serve_admission.py tests/integration/test_serve_confirm_during_check.py tests/integration/test_serve_dispatch.py tests/integration/test_serve_driver.py tests/integration/test_serve_driver_overlap.py --collect-only -q` gives on the base commit; `run.md` records both counts (fewer collected means a test was deleted).
4. `grep -nE "^\s*class (Fake|Stub|Empty)\w*|time\.sleep|import subprocess|SubprocessExec\(\)" tests/unit/test_serve_admission.py tests/unit/test_serve_confirm_during_check.py tests/unit/test_serve_dispatch.py tests/unit/test_serve_driver.py tests/unit/test_serve_driver_overlap_flow.py` prints nothing (no new fake class, no real sleep, no real process).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.

## Verification
```
./dev.py test tests/unit/test_serve_admission.py tests/unit/test_serve_confirm_during_check.py tests/unit/test_serve_dispatch.py tests/unit/test_serve_driver.py tests/unit/test_serve_driver_overlap_flow.py --durations=0
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
- reason: the batch is cut at about 1,400 lines (1126 here) so files sharing fixtures stay together; the files are restored by mechanical edits to import lines and fake wiring.
