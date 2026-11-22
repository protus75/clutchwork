---
state: rejected
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc

## Context
- tests/integration/test_rework_failure_terminal_findings.py
- tests/integration/test_rework_supervise.py
- tests/integration/test_roadmap_author.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_roadmap_gate.py
- tests/integration/test_roadmap_merged.py
- tests/integration/test_roadmap_named_stem.py
- tests/integration/test_roadmap_refile.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_roadmap_ship.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_rework.py

## Goal / Why
`integration-disk-io-skip` skipped 184 integration test files after one run wrote 975 MB in 119,498 files and 1,531 real git repos. This ticket restores the Rework and roadmap files below (89 tests): each loses its `pytestmark = pytest.mark.disk_io_skip` line and passes under the rules of `clutch/docs/host-authoring.md#Unit and integration tests` and the owner's two requirements: fast (no test above 1.0 s) and built on the shared fakes with no per-file fake class or helper copy. Most of these files build a real git repo with `Git(SubprocessExec())` or `make_root`, run `git` through `git_out`, and run `sys.executable -c ...` as a gate or notify command; each becomes `GitFake`, `FakeExec`/`FakeFileSystem` or an in-process `main([...])` call. Done means the 89 tests run in the suites, none of them touches real git or a process, and the integration suite stays guard-clean.

## Boundary contract
none
- reason: tests encoding an existing contract; the production code under test, its callers, outputs, failures and side effects are unchanged and only test files move or change

## Scope in / Scope out
Scope in, per file (base-commit facts; the implementer re-reads each file first):
- `tests/integration/test_rework.py` (632 lines, 61 tests): builds the `ctx` merge-queue context with real git (`ctx.git.rev_parse`, `status_porcelain`, `worktree_add_detached`, `commit`) and real ticket files under `ctx.repo` (`tickets/` read back with `read_bytes`); two tests patch `ctx.driver.sleep`; `test_rework_is_reachable_from_production` reads `clutch/*.py` anchored on `Path(__file__)`. It is also the source of names other files import (`order`, `requisition`, `successors`, `invoke`, `original`, `signals`); `restore-helpers-config` moved them and this file imports them back, so those definitions are not here to move. Git moves to `GitFake`, ticket files to `FakeFileSystem` or `tmp_path`. The file is split: `test_rework_is_reachable_from_production` (reads repo sources, writes nothing) goes to `tests/integration/test_rework_reachability.py`; every other test goes to `tests/unit/test_rework.py` (a spec read through `ctx.specs_dir` stays in the unit file only when the spec comes from a `tmp_path` directory, as `tests/unit/test_roadmap_author.py` does with `SPECS_DIR`). Final path: `tests/unit/test_rework.py` and `tests/integration/test_rework_reachability.py`.
- `tests/integration/test_rework_failure_terminal_findings.py` (50 lines, 4 tests): uses the admission context (real git and ticket files through `ctx` from the daemon/mergequeue helpers) and `production_writer`; git to `GitFake`, journal to `FakeJournal` unless it asserts persisted events. Final path: `tests/unit/test_rework_failure_terminal_findings.py`.
- `tests/integration/test_rework_supervise.py` (107 lines, 8 tests): uses `ctx` (real git, `ctx.worktree('original').mkdir`) and `FakeLLM`; git to `GitFake`, worktree directories under `tmp_path` or `FakeFileSystem`. At base it imports `SNAG, order, original, requisition, run, signals, ticket_bytes` from `tests.integration.test_rework`; `restore-helpers-config` moves every name other files import from `test_rework.py` into `tests/config_helpers.py` and rewrites this import line, so when this ticket runs the line names the helper module (if it still names `tests.integration.test_rework`, point it at the helper module that exports the name, since `test_rework.py` itself moves to `tests/unit/test_rework.py`). Final path: `tests/unit/test_rework_supervise.py`.
- `tests/integration/test_roadmap_author.py` (96 lines, 2 tests): `setup_repo` makes a real repo with `make_root` and the tests call `main([...])` and `git_out` (a `git` subprocess); git to `GitFake`, `git_out` replaced by `GitFake.calls`/overrides. `setup_repo` is imported by `test_roadmap_driver.py` (this batch) and `test_roadmap_start_gates.py` (`restore-io-tests-28`); both import lines change to the new module path (`tests/unit/test_roadmap_author.py` already exists, hence the `_flow` name). Final path: `tests/unit/test_roadmap_author_flow.py`.
- `tests/integration/test_roadmap_driver.py` (72 lines, 3 tests): real repo from `setup_repo`/`make_root`, a notify command `[sys.executable, '-c', ...]` that writes a digest file (a process), `main` and `drain` calls; the notify process becomes `FakeExec` (assert the argv it received in place of reading the digest file, keeping the sentinel check on the not-called path) and git becomes `GitFake`. Final path: `tests/unit/test_roadmap_driver.py`.
- `tests/integration/test_roadmap_gate.py` (73 lines, 2 tests): `test_roadmap_gate_runs_real_commands` runs gate commands built from `sys.executable` through `main(['roadmap', 'gate', ...])` and a real `Journal` in `tmp_path`: the commands become `FakeExec` results (exit 1 then exit 0) through the `main` exec construction point. `test_real_roadmap_gate_blocks` reads the repo roadmap anchored on `Path(__file__)` and writes nothing. Split: the first goes to `tests/unit/test_roadmap_gate_flow.py` (`tests/unit/test_roadmap_gate.py` exists), the second to `tests/integration/test_roadmap_gate_repo.py`. Final path: `tests/unit/test_roadmap_gate_flow.py` and `tests/integration/test_roadmap_gate_repo.py`.
- `tests/integration/test_roadmap_merged.py` (56 lines, 1 tests): real `Git(SubprocessExec())` init, commit and tag with a `CommitLock`, then `main(['roadmap', 'merged', ...])` and a byte comparison of journal segments; git to `GitFake` overrides (commit log and tag lookups), journal segments stay real files under `tmp_path` since the test asserts the journal is untouched. Final path: `tests/unit/test_roadmap_merged_flow.py`.
- `tests/integration/test_roadmap_named_stem.py` (102 lines, 5 tests): real git repo with `Git(SubprocessExec())` and `git._run(... 'log' ...)`, `Box` on `LocalFileSystem`, real `Journal`; git to `GitFake` (commit subject read from `fake.calls`/override), `Box` on `FakeFileSystem`, journal to `FakeJournal`. Final path: `tests/unit/test_roadmap_named_stem_flow.py`.
- `tests/integration/test_roadmap_refile.py` (42 lines, 1 tests): same shape as `test_roadmap_named_stem.py`: real git init and commit, `Box`, `Journal`, `LocalFileSystem`; to `GitFake`, `FakeFileSystem`, `FakeJournal`. The test's name says real journal and box; keep the assertion on the box resolution and journal events. Final path: `tests/unit/test_roadmap_refile_flow.py`.
- `tests/integration/test_roadmap_row_author.py` (60 lines, 1 tests): `make_root` repo, `git_out` (a `git` subprocess), `main([...])` triage and a read of the triage spec anchored on `Path(__file__)` for the spec version. The spec text comes from a `tmp_path` specs directory installed with `monkeypatch.setattr` on `SPECS_DIR` (the pattern of `tests/unit/test_roadmap_author.py`), so nothing reads the repo; git to `GitFake`. Final path: `tests/unit/test_roadmap_row_author.py`.
- `tests/integration/test_roadmap_ship.py` (96 lines, 1 tests): two real repositories (`repository(tmp_path/'first')`, a dirty one) with real `Git`, `SubprocessExec`, `LocalFileSystem`, edits to `pyproject.toml`/`uv.lock`, a release publish step and `sys.executable` commands; git to `GitFake` (dirty state through the `status_porcelain` override), exec to `FakeExec`, fs to `FakeFileSystem`. (`tests/unit/test_roadmap_ship.py` exists, hence `_flow`.) Final path: `tests/unit/test_roadmap_ship_flow.py`.

Scope in, every file above:
- Delete the line `pytestmark = pytest.mark.disk_io_skip` (and `import pytest` only when nothing else in the file uses it).
- Rewrite the test body wiring, keeping every test function, parametrization, name and assertion: git becomes `GitFake` from `tests/git_fake.py` (overrides by member name, `fake.calls`); a process becomes `FakeExec` from `tests/fakes.py` or an in-process `clutch.__main__.main([...])` call (when `main` builds its own `SubprocessExec`, replace that construction point with the `fake_exec` fixture's object through `monkeypatch`); the journal becomes `FakeJournal` unless the test's subject is journal persistence; time becomes `FakeClock` plus `until`/`turn`, never a sleep; code taking the `clutch.seams.FileSystem` seam gets `FakeFileSystem`.
- Reuse only the shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. The modules created by `restore-helpers-misc` and its chain (`restore-helpers-cli` through `restore-helpers-misc`) and by `shared-git-fake-integration`, `shared-review-script` and `shared-serve-rig-config` are merged before this ticket runs; read them in the worktree before editing. Names the files import from `tests.integration.test_cli`, `test_drain`, `test_stages`, `test_scheduler`, `test_rework` and the other hubs already come from those helper modules; keep each import line that names a helper module as it is.
- Placement by the unit and integration test rules in the host authoring guide (the Context section): a file whose rewritten tests still write real files (only under `tmp_path`), or use only fakes, moves to `tests/unit/` (the final path above; same file name, `_flow` suffix where `tests/unit/` already has that name); a test that reads a repo file anchored on `Path(__file__)` and writes nothing stays under `tests/integration/`; a file needing both is split into the two paths named above, each test function keeping its name. Moving a file means deleting the old path in the same change.
- Update the import lines of every other file that imports a name from a file this ticket moves (the fence lists them); only those import lines change in them.
- If a shared fake lacks a behavior a test needs, stop as a premise failure naming the missing behavior and the test; never edit a shared module and never add a `Fake*`/stand-in class or a copy of a helper to a test file.

Importers of the files this ticket moves (grep `from tests.integration.test_rework import`, `test_roadmap_author import`, `test_roadmap_gate import` before editing): `test_roadmap_driver.py` (this batch) and `test_roadmap_start_gates.py` (`restore-io-tests-28`, fenced here) import `setup_repo` from `test_roadmap_author.py`, and their import lines change to `tests.unit.test_roadmap_author_flow`. The importers of `test_rework.py` at base (`test_caps.py`, `test_daemon_composition.py`, `test_diagnose.py`, `test_drain.py`, `test_ladder.py`, `test_requisition_identity_record.py`, `test_rework_supervise.py`) are repointed to `tests/config_helpers.py` by `restore-helpers-config`; if the grep still finds one when this ticket runs, stop as a premise failure naming it. Nothing imports from `test_roadmap_gate.py`.

Scope out: every file under `tests/` not listed above except the importers named in the fence, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, `tests/integration/conftest.py`, `tests/integration/serve_rig.py`, the helper modules, `clutch/`, and `docs/`. No test is deleted, skipped, weakened or given a sleep; assertions keep their meaning.

## Scope fence
- tests/integration/test_rework.py
- tests/integration/test_rework_failure_terminal_findings.py
- tests/integration/test_rework_supervise.py
- tests/integration/test_roadmap_author.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_roadmap_gate.py
- tests/integration/test_roadmap_merged.py
- tests/integration/test_roadmap_named_stem.py
- tests/integration/test_roadmap_refile.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_roadmap_ship.py
- tests/unit/test_rework.py
- tests/integration/test_rework_reachability.py
- tests/unit/test_rework_failure_terminal_findings.py
- tests/unit/test_rework_supervise.py
- tests/unit/test_roadmap_author_flow.py
- tests/unit/test_roadmap_driver.py
- tests/unit/test_roadmap_gate_flow.py
- tests/integration/test_roadmap_gate_repo.py
- tests/unit/test_roadmap_merged_flow.py
- tests/unit/test_roadmap_named_stem_flow.py
- tests/unit/test_roadmap_refile_flow.py
- tests/unit/test_roadmap_row_author.py
- tests/unit/test_roadmap_ship_flow.py
- tests/integration/test_roadmap_start_gates.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_rework.py tests/integration/test_rework_reachability.py tests/unit/test_rework_failure_terminal_findings.py tests/unit/test_rework_supervise.py tests/unit/test_roadmap_author_flow.py tests/unit/test_roadmap_driver.py tests/unit/test_roadmap_gate_flow.py tests/integration/test_roadmap_gate_repo.py tests/unit/test_roadmap_merged_flow.py tests/unit/test_roadmap_named_stem_flow.py tests/unit/test_roadmap_refile_flow.py tests/unit/test_roadmap_row_author.py tests/unit/test_roadmap_ship_flow.py` lists none of the paths (exit 1 with no output; every file still carrying the marker is a rejection).
2. `./dev.py test tests/unit/test_rework.py tests/integration/test_rework_reachability.py tests/unit/test_rework_failure_terminal_findings.py tests/unit/test_rework_supervise.py tests/unit/test_roadmap_author_flow.py tests/unit/test_roadmap_driver.py tests/unit/test_roadmap_gate_flow.py tests/integration/test_roadmap_gate_repo.py tests/unit/test_roadmap_merged_flow.py tests/unit/test_roadmap_named_stem_flow.py tests/unit/test_roadmap_refile_flow.py tests/unit/test_roadmap_row_author.py tests/unit/test_roadmap_ship_flow.py --durations=0` passes, and its durations output (recorded in `run.md`) lists no restored test above 1.0 s.
3. `./dev.py test tests/unit/test_rework.py tests/integration/test_rework_reachability.py tests/unit/test_rework_failure_terminal_findings.py tests/unit/test_rework_supervise.py tests/unit/test_roadmap_author_flow.py tests/unit/test_roadmap_driver.py tests/unit/test_roadmap_gate_flow.py tests/integration/test_roadmap_gate_repo.py tests/unit/test_roadmap_merged_flow.py tests/unit/test_roadmap_named_stem_flow.py tests/unit/test_roadmap_refile_flow.py tests/unit/test_roadmap_row_author.py tests/unit/test_roadmap_ship_flow.py --collect-only -q` collects 89 tests, equal to the count `./dev.py test tests/integration/test_rework.py tests/integration/test_rework_failure_terminal_findings.py tests/integration/test_rework_supervise.py tests/integration/test_roadmap_author.py tests/integration/test_roadmap_driver.py tests/integration/test_roadmap_gate.py tests/integration/test_roadmap_merged.py tests/integration/test_roadmap_named_stem.py tests/integration/test_roadmap_refile.py tests/integration/test_roadmap_row_author.py tests/integration/test_roadmap_ship.py --collect-only -q` gives on the base commit; `run.md` records both counts (fewer collected means a test was deleted).
4. `grep -nE "^\s*class (Fake|Stub|Empty)\w*|time\.sleep|import subprocess|SubprocessExec\(\)" tests/unit/test_rework.py tests/integration/test_rework_reachability.py tests/unit/test_rework_failure_terminal_findings.py tests/unit/test_rework_supervise.py tests/unit/test_roadmap_author_flow.py tests/unit/test_roadmap_driver.py tests/unit/test_roadmap_gate_flow.py tests/integration/test_roadmap_gate_repo.py tests/unit/test_roadmap_merged_flow.py tests/unit/test_roadmap_named_stem_flow.py tests/unit/test_roadmap_refile_flow.py tests/unit/test_roadmap_row_author.py tests/unit/test_roadmap_ship_flow.py` prints nothing (no new fake class, no real sleep, no real process).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.

## Verification
```
./dev.py test tests/unit/test_rework.py tests/integration/test_rework_reachability.py tests/unit/test_rework_failure_terminal_findings.py tests/unit/test_rework_supervise.py tests/unit/test_roadmap_author_flow.py tests/unit/test_roadmap_driver.py tests/unit/test_roadmap_gate_flow.py tests/integration/test_roadmap_gate_repo.py tests/unit/test_roadmap_merged_flow.py tests/unit/test_roadmap_named_stem_flow.py tests/unit/test_roadmap_refile_flow.py tests/unit/test_roadmap_row_author.py tests/unit/test_roadmap_ship_flow.py --durations=0
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
- reason: the batch is cut at about 1,400 lines (1386 here) so files sharing fixtures stay together; the files are restored by mechanical edits to import lines and fake wiring.
