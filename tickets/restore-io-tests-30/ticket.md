---
state: rejected
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc

## Context
- tests/integration/test_serve_kill.py
- tests/integration/test_serve_merge_overlap.py
- tests/integration/test_serve_notify.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/test_serve_scan_head.py
- tests/integration/test_serve_scan_watch_overlap.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_serve_lifecycle.py

## Goal / Why
`integration-disk-io-skip` skipped 184 integration test files after one run wrote 975 MB in 119,498 files and 1,531 real git repos. This ticket restores seven serve test files (50 tests): kill, lifecycle, merge-overlap, notify, parallel-admission, scan-head and scan-watch-overlap. Each loses its `pytestmark = pytest.mark.disk_io_skip` line and passes under the rules of `clutch/docs/host-authoring.md#Unit and integration tests`, fast (no test above 1.0 s) and on the shared fakes. `test_serve_parallel_admission.py` exports `parallel_rig`, which `test_serve_scan_head.py` and `test_serve_scan_watch_overlap.py` import, so the three move together. Done means the 50 tests run with no real git, process, signal delivery or repo write.

## Boundary contract
none
- reason: tests encoding an existing contract; the production code under test, its callers, outputs, failures and side effects are unchanged and only test files move or change

## Scope in / Scope out
Scope in, per file (base-commit facts; the implementer re-reads each file first):
- `tests/integration/test_serve_kill.py` (314 lines, 21 tests): a serve test over the rig from `tests/integration/serve_rig.py` (its real-git and process parts live in `tests/loop_helpers.py` after `restore-helpers-loop`). It parametrizes ending modes (`exception`, `return`, `cancel`, `kill`, `signal`) and replaces the loop's signal handlers with recorders, so no real signal is sent; it reads the engine log and `TicketWriter`. Keep it on `FakeClock`/`until`/`turn`; the rig supplies the rest. Final path: `tests/unit/test_serve_kill.py`.
- `tests/integration/test_serve_lifecycle.py` (441 lines, 18 tests): a serve test over the rig from `tests/integration/serve_rig.py` (its real-git and process parts live in `tests/loop_helpers.py` after `restore-helpers-loop`). It imports `sources` from `test_daemon_composition`, `orphan` from `test_restart_timers`, `arrival`/`raw_report` from `test_inbox`, `ready` from `test_mergequeue` and `import_closure` from the scheduler helpers, all now from helper modules. The test that asserts `"clutch.serve" in import_closure(sources())` reads `clutch` sources from the repo and writes nothing: it goes to `tests/integration/test_serve_lifecycle_reachability.py`; the other 17 go to `tests/unit/test_serve_lifecycle.py`. Final path: `tests/unit/test_serve_lifecycle.py` and `tests/integration/test_serve_lifecycle_reachability.py`.
- `tests/integration/test_serve_merge_overlap.py` (82 lines, 1 tests): a serve test over the rig from `tests/integration/serve_rig.py` (its real-git and process parts live in `tests/loop_helpers.py` after `restore-helpers-loop`). It wraps `git.rebase_stop_at_conflict` and reads `HEAD:docs/one` and `main:docs/one` with `git._run('show' ...)`: `GitFake` overrides record the rebased text and return the merged text. Final path: `tests/unit/test_serve_merge_overlap.py`.
- `tests/integration/test_serve_notify.py` (208 lines, 4 tests): a serve test over the rig from `tests/integration/serve_rig.py` (its real-git and process parts live in `tests/loop_helpers.py` after `restore-helpers-loop`) with notify configuration; it reads the engine log (`notify_unset` events) from the rig's log path, which stays a file under `tmp_path` or moves to the fake file system. Final path: `tests/unit/test_serve_notify.py`.
- `tests/integration/test_serve_parallel_admission.py` (157 lines, 4 tests): a serve test over the rig from `tests/integration/serve_rig.py` (its real-git and process parts live in `tests/loop_helpers.py` after `restore-helpers-loop`). It defines `parallel_rig`, imported by `test_serve_scan_head.py` and `test_serve_scan_watch_overlap.py`; those two import lines point at `tests.unit.test_serve_parallel_admission` after the move. It edits `config.yaml` through `yaml` and reads ticket files back. Final path: `tests/unit/test_serve_parallel_admission.py`.
- `tests/integration/test_serve_scan_head.py` (110 lines, 1 tests): a serve test over the rig from `tests/integration/serve_rig.py` (its real-git and process parts live in `tests/loop_helpers.py` after `restore-helpers-loop`). It swaps `rig.fs.entries` for `LocalFileSystem().entries` so the scan lists real directory entries under `tmp_path` (allowed in the unit suite), and uses `git.add`, `commit(only=...)`, `status_porcelain` and `_call('show' ...)` on the rig repo: those become `GitFake` overrides. (`tests/unit/test_serve_scan_head.py` exists, hence `_flow`.) Final path: `tests/unit/test_serve_scan_head_flow.py`.
- `tests/integration/test_serve_scan_watch_overlap.py` (63 lines, 1 tests): a serve test over the rig from `tests/integration/serve_rig.py` (its real-git and process parts live in `tests/loop_helpers.py` after `restore-helpers-loop`), importing `parallel_rig` from `test_serve_parallel_admission`. Final path: `tests/unit/test_serve_scan_watch_overlap.py`.

Scope in, every file above:
- Delete the line `pytestmark = pytest.mark.disk_io_skip` (and `import pytest` only when nothing else in the file uses it).
- Rewrite the test body wiring, keeping every test function, parametrization, name and assertion: git becomes `GitFake` from `tests/git_fake.py` (overrides by member name, `fake.calls`); a process becomes `FakeExec` from `tests/fakes.py` or an in-process `clutch.__main__.main([...])` call (when `main` builds its own `SubprocessExec`, replace that construction point with the `fake_exec` fixture's object through `monkeypatch`); the journal becomes `FakeJournal` unless the test's subject is journal persistence; time becomes `FakeClock` plus `until`/`turn`, never a sleep; code taking the `clutch.seams.FileSystem` seam gets `FakeFileSystem`.
- Reuse only the shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. The modules created by `restore-helpers-misc` and its chain (`restore-helpers-cli` through `restore-helpers-misc`) and by `shared-git-fake-integration`, `shared-review-script` and `shared-serve-rig-config` are merged before this ticket runs; read them in the worktree before editing. Names the files import from `tests.integration.test_cli`, `test_drain`, `test_stages`, `test_scheduler`, `test_rework` and the other hubs already come from those helper modules; keep each import line that names a helper module as it is.
- Placement by the unit and integration test rules in the host authoring guide (the Context section): a file whose rewritten tests still write real files (only under `tmp_path`), or use only fakes, moves to `tests/unit/` (the final path above; same file name, `_flow` suffix where `tests/unit/` already has that name); a test that reads a repo file anchored on `Path(__file__)` and writes nothing stays under `tests/integration/`; a file needing both is split into the two paths named above, each test function keeping its name. Moving a file means deleting the old path in the same change.
- Update the import lines of every other file that imports a name from a file this ticket moves (the fence lists them); only those import lines change in them.
- If a shared fake lacks a behavior a test needs, stop as a premise failure naming the missing behavior and the test; never edit a shared module and never add a `Fake*`/stand-in class or a copy of a helper to a test file.

Scope out: every file under `tests/` not listed above except the importers named in the fence, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, `tests/integration/conftest.py`, `tests/integration/serve_rig.py`, the helper modules, `clutch/`, and `docs/`. No test is deleted, skipped, weakened or given a sleep; assertions keep their meaning.

## Scope fence
- tests/integration/test_serve_kill.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_serve_merge_overlap.py
- tests/integration/test_serve_notify.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/test_serve_scan_head.py
- tests/integration/test_serve_scan_watch_overlap.py
- tests/unit/test_serve_kill.py
- tests/unit/test_serve_lifecycle.py
- tests/integration/test_serve_lifecycle_reachability.py
- tests/unit/test_serve_merge_overlap.py
- tests/unit/test_serve_notify.py
- tests/unit/test_serve_parallel_admission.py
- tests/unit/test_serve_scan_head_flow.py
- tests/unit/test_serve_scan_watch_overlap.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_serve_kill.py tests/unit/test_serve_lifecycle.py tests/integration/test_serve_lifecycle_reachability.py tests/unit/test_serve_merge_overlap.py tests/unit/test_serve_notify.py tests/unit/test_serve_parallel_admission.py tests/unit/test_serve_scan_head_flow.py tests/unit/test_serve_scan_watch_overlap.py` lists none of the paths (exit 1 with no output; every file still carrying the marker is a rejection).
2. `./dev.py test tests/unit/test_serve_kill.py tests/unit/test_serve_lifecycle.py tests/integration/test_serve_lifecycle_reachability.py tests/unit/test_serve_merge_overlap.py tests/unit/test_serve_notify.py tests/unit/test_serve_parallel_admission.py tests/unit/test_serve_scan_head_flow.py tests/unit/test_serve_scan_watch_overlap.py --durations=0` passes, and its durations output (recorded in `run.md`) lists no restored test above 1.0 s.
3. `./dev.py test tests/unit/test_serve_kill.py tests/unit/test_serve_lifecycle.py tests/integration/test_serve_lifecycle_reachability.py tests/unit/test_serve_merge_overlap.py tests/unit/test_serve_notify.py tests/unit/test_serve_parallel_admission.py tests/unit/test_serve_scan_head_flow.py tests/unit/test_serve_scan_watch_overlap.py --collect-only -q` collects 50 tests, equal to the count `./dev.py test tests/integration/test_serve_kill.py tests/integration/test_serve_lifecycle.py tests/integration/test_serve_merge_overlap.py tests/integration/test_serve_notify.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_scan_head.py tests/integration/test_serve_scan_watch_overlap.py --collect-only -q` gives on the base commit; `run.md` records both counts (fewer collected means a test was deleted).
4. `grep -nE "^\s*class (Fake|Stub|Empty)\w*|time\.sleep|import subprocess|SubprocessExec\(\)" tests/unit/test_serve_kill.py tests/unit/test_serve_lifecycle.py tests/integration/test_serve_lifecycle_reachability.py tests/unit/test_serve_merge_overlap.py tests/unit/test_serve_notify.py tests/unit/test_serve_parallel_admission.py tests/unit/test_serve_scan_head_flow.py tests/unit/test_serve_scan_watch_overlap.py` prints nothing (no new fake class, no real sleep, no real process).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.

## Verification
```
./dev.py test tests/unit/test_serve_kill.py tests/unit/test_serve_lifecycle.py tests/integration/test_serve_lifecycle_reachability.py tests/unit/test_serve_merge_overlap.py tests/unit/test_serve_notify.py tests/unit/test_serve_parallel_admission.py tests/unit/test_serve_scan_head_flow.py tests/unit/test_serve_scan_watch_overlap.py --durations=0
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
- reason: the batch is cut at about 1,400 lines (1375 here) so files sharing fixtures stay together; the files are restored by mechanical edits to import lines and fake wiring.
