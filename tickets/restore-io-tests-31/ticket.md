---
state: rejected
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc

## Context
- tests/integration/test_serve_upgrade.py
- tests/integration/test_snapshot_cache_facts.py
- tests/integration/test_snapshot_merged_cap.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## Goal / Why
`integration-disk-io-skip` skipped 184 integration test files after one run wrote 975 MB in 119,498 files and 1,531 real git repos. This ticket restores three files (10 tests): the serve self-upgrade tests and the two snapshot tests. Each loses its `pytestmark = pytest.mark.disk_io_skip` line and passes under the rules of `clutch/docs/host-authoring.md#Unit and integration tests`, fast (no test above 1.0 s) and on the shared fakes. The snapshot tests today shell out to `git` through `tests/snapshot_scale_fixture.py::git` and build a real `Git(SubprocessExec())`; they become `GitFake` overrides (`ls_files`, `rev_parse`, blob and tree lookups) with ticket files under `tmp_path`. `tests/integration/test_shakeout.py` (23 tests) is not in this ticket: its `Bench` runs the production drain on real git, a process and a real merge, and `restore-io-tests-31` is cut so the harness port stays a separate decision.

## Boundary contract
none
- reason: tests encoding an existing contract; the production code under test, its callers, outputs, failures and side effects are unchanged and only test files move or change

## Scope in / Scope out
Scope in, per file (base-commit facts; the implementer re-reads each file first):
- `tests/integration/test_serve_upgrade.py` (210 lines, 8 tests): a serve test over the rig (`serve_rig.py`, real-git parts now in `tests/loop_helpers.py`); `test_external_engine_change_at_admission` and `test_non_git_engine_disables_upgrade` build an `engine` directory under `tmp_path` that the upgrade check reads through git: the engine repo becomes `GitFake` overrides, `not-a-repo` a `GitFake` that raises. Final path: `tests/unit/test_serve_upgrade.py`.
- `tests/integration/test_snapshot_cache_facts.py` (96 lines, 1 tests): `git(tmp_path, 'init'|'config'|'add'|'commit'|'rev-parse')` through `tests/snapshot_scale_fixture.git` (a subprocess), `blob_sha` over a real ticket file, `observe.Context(... SubprocessExec(), Git(SubprocessExec(), ...))` and a journal under `tmp_path/.clutch/journal`. Git to `GitFake` (the committed-tree facts come from overrides, `sha` and `blob` from constants), `SubprocessExec` to `FakeExec`; ticket and journal files stay real under `tmp_path`. `VALID` comes from the config helpers and `confirmed` from the drain helpers. Final path: `tests/unit/test_snapshot_cache_facts.py`.
- `tests/integration/test_snapshot_merged_cap.py` (47 lines, 1 tests): same real-git setup as the cache-facts test, then `entry.main(['--config', ..., 'view', 'snapshot', ...])`: `main` builds its `Git` and `SubprocessExec` itself, so the construction point is replaced through `monkeypatch` with `GitFake`/`FakeExec` (read `clutch/__main__.py` for the `view snapshot` path first). (`tests/unit/test_snapshot_merged_cap.py` exists, hence `_flow`.) Final path: `tests/unit/test_snapshot_merged_cap_flow.py`.

Scope in, every file above:
- Delete the line `pytestmark = pytest.mark.disk_io_skip` (and `import pytest` only when nothing else in the file uses it).
- Rewrite the test body wiring, keeping every test function, parametrization, name and assertion: git becomes `GitFake` from `tests/git_fake.py` (overrides by member name, `fake.calls`); a process becomes `FakeExec` from `tests/fakes.py` or an in-process `clutch.__main__.main([...])` call (when `main` builds its own `SubprocessExec`, replace that construction point with the `fake_exec` fixture's object through `monkeypatch`); the journal becomes `FakeJournal` unless the test's subject is journal persistence; time becomes `FakeClock` plus `until`/`turn`, never a sleep; code taking the `clutch.seams.FileSystem` seam gets `FakeFileSystem`.
- Reuse only the shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. The modules created by `restore-helpers-misc` and its chain (`restore-helpers-cli` through `restore-helpers-misc`) and by `shared-git-fake-integration`, `shared-review-script` and `shared-serve-rig-config` are merged before this ticket runs; read them in the worktree before editing. Names the files import from `tests.integration.test_cli`, `test_drain`, `test_stages`, `test_scheduler`, `test_rework` and the other hubs already come from those helper modules; keep each import line that names a helper module as it is.
- Placement by the unit and integration test rules in the host authoring guide (the Context section): a file whose rewritten tests still write real files (only under `tmp_path`), or use only fakes, moves to `tests/unit/` (the final path above; same file name, `_flow` suffix where `tests/unit/` already has that name); a test that reads a repo file anchored on `Path(__file__)` and writes nothing stays under `tests/integration/`; a file needing both is split into the two paths named above, each test function keeping its name. Moving a file means deleting the old path in the same change.
- Update the import lines of every other file that imports a name from a file this ticket moves (the fence lists them); only those import lines change in them.
- If a shared fake lacks a behavior a test needs, stop as a premise failure naming the missing behavior and the test; never edit a shared module and never add a `Fake*`/stand-in class or a copy of a helper to a test file.

Scope out: every file under `tests/` not listed above except the importers named in the fence, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, `tests/integration/conftest.py`, `tests/integration/serve_rig.py`, the helper modules, `clutch/`, and `docs/`. No test is deleted, skipped, weakened or given a sleep; assertions keep their meaning.

## Scope fence
- tests/integration/test_serve_upgrade.py
- tests/integration/test_snapshot_cache_facts.py
- tests/integration/test_snapshot_merged_cap.py
- tests/unit/test_serve_upgrade.py
- tests/unit/test_snapshot_cache_facts.py
- tests/unit/test_snapshot_merged_cap_flow.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_serve_upgrade.py tests/unit/test_snapshot_cache_facts.py tests/unit/test_snapshot_merged_cap_flow.py` lists none of the paths (exit 1 with no output; every file still carrying the marker is a rejection).
2. `./dev.py test tests/unit/test_serve_upgrade.py tests/unit/test_snapshot_cache_facts.py tests/unit/test_snapshot_merged_cap_flow.py --durations=0` passes, and its durations output (recorded in `run.md`) lists no restored test above 1.0 s.
3. `./dev.py test tests/unit/test_serve_upgrade.py tests/unit/test_snapshot_cache_facts.py tests/unit/test_snapshot_merged_cap_flow.py --collect-only -q` collects 10 tests, equal to the count `./dev.py test tests/integration/test_serve_upgrade.py tests/integration/test_snapshot_cache_facts.py tests/integration/test_snapshot_merged_cap.py --collect-only -q` gives on the base commit; `run.md` records both counts (fewer collected means a test was deleted).
4. `grep -nE "^\s*class (Fake|Stub|Empty)\w*|time\.sleep|import subprocess|SubprocessExec\(\)" tests/unit/test_serve_upgrade.py tests/unit/test_snapshot_cache_facts.py tests/unit/test_snapshot_merged_cap_flow.py` prints nothing (no new fake class, no real sleep, no real process).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.

## Verification
```
./dev.py test tests/unit/test_serve_upgrade.py tests/unit/test_snapshot_cache_facts.py tests/unit/test_snapshot_merged_cap_flow.py --durations=0
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
- reason: the batch is cut at about 1,400 lines (353 here) so files sharing fixtures stay together; the files are restored by mechanical edits to import lines and fake wiring.
