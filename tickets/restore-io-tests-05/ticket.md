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
- tests/integration/test_conflict_rerun_swap.py
- tests/integration/test_context_suggest_cli.py

## On-demand
- tests/integration/test_config.py
- tests/integration/test_control.py

## Goal / Why
`integration-disk-io-skip` turned off 4 integration test files in this batch (`test_config.py`, `test_conflict_rerun_swap.py`, `test_context_suggest_cli.py` and `test_control.py`, 1029 lines) because they write real files, run real git and processes, and sleep; `integration-io-guard` fails any such test, and `disk-io-skip-per-file` marks each skipped file with `pytestmark = pytest.mark.disk_io_skip`. The owner wants these tests back, FAST (no restored test above 1.0 s) and on the shared fakes, not on per-file copies.

When this ticket is done, none of the 4 files carries the `disk_io_skip` marker, each runs under the I/O guard (or under `tests/unit/` where it still writes under `tmp_path`), every test function in them still exists and asserts what it asserted before, and the shared modules `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py` are reused instead of copied. The helper hub names these files imported were moved to those helper modules by the `restore-helpers-*` chain, so `restore-helpers-misc` (end of the chain) is the dependency; read each shared module in your worktree before using it, and the run stops as a premise failure that names the missing behavior if a shared fake lacks one (never edit a shared module).

## Boundary contract
none
- reason: tests encoding an existing contract; the batch changes only test files and the `clutch/` behavior they assert stays as it is

## Scope in / Scope out
Scope in:
Rules every restored test follows (the owner requires FAST tests that REUSE the shared fixtures and fakes):
- Delete the `pytestmark = pytest.mark.disk_io_skip` line (and an `import pytest` it alone needed). Keep every test function, parametrization and assertion; no test is deleted, skipped, xfailed or weakened.
- Git goes through `tests/git_fake.py::GitFake` (overrides by member name, `fake.calls`); processes through `tests/fakes.py::FakeExec` or an in-process `clutch.__main__.main([...])`; journals through `FakeJournal` unless the test's subject is journal persistence; the `clutch.seams.FileSystem` seam through `FakeFileSystem`; time through `FakeClock` with `until`/`turn`, never `sleep`. Config text comes from `tests/config_fixture.py` / `tests/config_helpers.py`, model replies from `tests/stage_replies.py`, and test rigs from `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. Read those modules in the worktree before editing; they exist once the dependency has merged.
- No new `Fake*` or stand-in class and no copy of a shared helper in a test file. A per-file stand-in class that the file defines today (named per file below) is replaced by the shared fake or helper and its definition deleted. If a shared module lacks a behavior a test needs, the run stops as a premise failure that names the missing behavior and the test; it never edits a shared module, `clutch/` code or `tests/integration/conftest.py`.
- Placement follows the host guide section "Unit and integration tests" (in Context): a test that still writes files (only under `tmp_path`) lives under `tests/unit/`; a test that reads a repo file (anchored on `Path(__file__)`) and writes nothing lives under `tests/integration/`. Reading packaged spec or doc files inside production code (for example `ask.render` loading `clutch/specs/ask/*.md`) is not a test reading a repo file. When one test both writes under `tmp_path` and needs repo text (for example spec files), the repo text comes through the production reader (`clutch.specs`, `importlib.resources`, `inspect.getsource`), never a test-side `Path(__file__)` read, so the test qualifies for `tests/unit/`; if no such reader gives the text, the run stops as a premise failure naming the test. A file whose tests need both kinds of test is split by test function, and the ticket names both paths. A moved file keeps its name under `tests/unit/` unless that name exists there, in which case it is `test_<name>_flow.py`.
- Where code under test builds its own real `Git`, `SubprocessExec` or `Journal` and `main` exposes no seam for it, drive the code through the function the unit tests beside it call, with the fakes. If neither route exists, the run stops as a premise failure that names the code path.
- Any name a moved file defines that another test module imports gets its importers' import lines updated in the same change (grep `from tests.integration.<name> import` first); only import lines change in importers. At authoring time the grep found importers only where this ticket fences them; the run re-greps and fences nothing new (a new importer is a premise failure).

Per file:
- `tests/integration/test_config.py` (457 lines): today it 30 tests of `load_config`/`migrate_config`, every one writing `config.yaml` through `write(tmp_path, text)` (97 `tmp_path` uses); `VALID`, `write`, `edit` and `refusal` were moved by `restore-helpers-config`; defines the per-file stand-in `MigrationFS` (wraps `LocalFileSystem` and records writes). Plan: moves whole to `tests/unit/test_config.py` (name free): `load_config` reads a real file, so tests keep real `config.yaml` files under `tmp_path`; `MigrationFS` is replaced by `FakeFileSystem` (its `writes` are read from the fake, and the migrate tests assert the same published bytes).
- `tests/integration/test_conflict_rerun_swap.py` (59 lines): today it one async test driving `MergeQueue`, `caps`, `drain`, `TicketWriter` and `FakeLLM` over a real git repo (`ctx.git.conflicted_paths`, `rev_parse`, `worktree_add`, `_call`, and a diff text assertion). Plan: moves whole to `tests/unit/test_conflict_rerun_swap_flow.py` (`tests/unit/test_conflict_rerun_swap.py` is a different, existing file): the test imports `ctx`, `conflict` and `commit` from `tests/integration/test_mergequeue.py`, which `restore-helpers-daemon` moved to `tests/daemon_helpers.py` as GitFake-backed rigs with files only under `tmp_path`; the test imports them from there. Git results come from `GitFake` overrides (the conflicted-path list, equal `rev_parse` shas, the `diff --git a/clutch/thing.py` text and the `+ok work` line), and every file assertion (`worktree(...).exists()`, `prior.diff`, `thing.py` contents) reads the real files the helper rig and the test write under `tmp_path`. An assertion only real git could satisfy stops the run as a premise failure naming it, never a weakened assertion.
- `tests/integration/test_context_suggest_cli.py` (64 lines): today it `test_documentation` reads the run guide, the how-it-works document and the readme via `Path(__file__)`; `test_context_suggest_end_to_end` builds a real git repo with `setup_repo` (from the REAL_IO file `test_git_tree_id.py`), commits twice, runs `index build`, holds a real `Lockfile`, and reads the on-disk `index.duckdb`. Plan: SPLIT. `test_documentation` stays in `tests/integration/test_context_suggest_cli.py`. `test_context_suggest_end_to_end` moves to `tests/unit/test_context_suggest_cli.py`: the repo history becomes `GitFake` overrides, files stay under `tmp_path`, and the index file and lock stay real under `tmp_path` (an on-disk database is allowed in `tests/unit/`). `CONFIG`, `ENV` and `Clock` come from `tests/cli_helpers.py` (`FakeClock` for `Clock`); `setup_repo` is not imported. `main` builds its own real `Git`, so the test drives `clutch.__main__._run_context_suggest(config, repo, stem, fs=..., connect=...)` and the `clutch.index` build function with `GitFake(log=...)` overrides, the way `tests/unit/test_context_suggest_verb.py` drives `_run_context_suggest`, and asserts the same output line and the same unchanged `index.duckdb` bytes; if the index build has no Git seam either, the run stops as a premise failure naming it.
- `tests/integration/test_control.py` (449 lines): today it 17 tests of control-request publication, decision and projection: real files under `tmp_path` (durability, no-overwrite, crash points, `stat` modes), `ThreadPoolExecutor`/`Barrier` races, real `Journal`; defines the harness class `Rig` (imported by `test_control_cli.py` and `test_daemon_pause.py`); imports `Crash` and `FakeClock` from the skipped non-hub `test_effects.py`. Plan: moves whole to `tests/unit/test_control.py` (name free): publication durability and permission tests keep a real `LocalFileSystem` under `tmp_path` (the file system is their subject), other tests use `FakeFileSystem`; `FakeClock` comes from `tests/fakes.py` and `Crash` stays a plain exception class; `Rig` keeps its definition in the moved file and builds on the shared fakes. Update the import lines `from tests.integration.test_control import Rig` in `tests/integration/test_control_cli.py` and `tests/integration/test_daemon_pause.py` to `tests.unit.test_control`.

Record in the run record (`run.md`): the `--collect-only -q` test count of the batch's files on the base commit and after the change, the `--durations=0` output of the restored paths, which tests of a split file went to which path, and for each moved file the `grep -rn "tests.integration.<name>" tests` result used to find importers.

`tests/integration/test_control_cli.py` is also the file `restore-io-tests-06` restores; this ticket edits only its one `from tests.integration.test_control import Rig` import line, and `restore-io-tests-06` lists this ticket under `## Depends on`.

Scope out: `tests/integration/conftest.py` (the marker line is the only switch), `tests/fakes.py`, `tests/conftest.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, every `tests/*_helpers.py`, all `clutch/` code, and test files outside this batch except the importer import lines named above. A hot test file (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `test_cli.py`, `test_watch.py`, `serve_rig.py`) gets no new test, fixture or helper from this change; code only leaves it or is repointed.

## Scope fence
- tests/integration/test_config.py
- tests/unit/test_config.py
- tests/integration/test_conflict_rerun_swap.py
- tests/unit/test_conflict_rerun_swap_flow.py
- tests/integration/test_context_suggest_cli.py
- tests/unit/test_context_suggest_cli.py
- tests/integration/test_control.py
- tests/unit/test_control.py
- tests/integration/test_control_cli.py
- tests/integration/test_daemon_pause.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_context_suggest_cli.py tests/unit/test_config.py tests/unit/test_conflict_rerun_swap_flow.py tests/unit/test_context_suggest_cli.py tests/unit/test_control.py` prints no file name (the marker is gone from every path the batch keeps), recorded in `run.md`; every path that the plan moves whole no longer exists under `tests/integration/` (`ls` of it fails), and the marker is not present in any new file.
2. `./dev.py test tests/integration/test_context_suggest_cli.py tests/unit/test_config.py tests/unit/test_conflict_rerun_swap_flow.py tests/unit/test_context_suggest_cli.py tests/unit/test_control.py --durations=0` passes and its durations table lists no restored test above 1.0 s (a test that still takes 1.0 s or more fails this criterion, it is not allowed to stay slow); the output is recorded in `run.md`.
3. `./dev.py test tests/integration/test_context_suggest_cli.py tests/unit/test_config.py tests/unit/test_conflict_rerun_swap_flow.py tests/unit/test_context_suggest_cli.py tests/unit/test_control.py --collect-only -q` reports exactly as many tests as `./dev.py test tests/integration/test_config.py tests/integration/test_conflict_rerun_swap.py tests/integration/test_context_suggest_cli.py tests/integration/test_control.py --collect-only -q` reported on the base commit (a deleted, merged or skipped test makes the counts differ); both numbers are recorded in `run.md`.
4. `grep -nE "^\s*class (Fake|Script|Exec|Git|FS|MigrationFS|Recording)" tests/integration/test_context_suggest_cli.py tests/unit/test_config.py tests/unit/test_conflict_rerun_swap_flow.py tests/unit/test_context_suggest_cli.py tests/unit/test_control.py` prints no line (no per-file fake or stand-in class remains), and `grep -nE "subprocess|sys\.executable|time\.sleep|asyncio\.sleep" tests/integration/test_context_suggest_cli.py` prints no line (a restored integration test starts no process and never sleeps).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, and `tests/integration` reports no `IntegrationIOBlocked` failure (the I/O guard stays on for every restored integration test).

## Verification
```
./dev.py test tests/integration/test_context_suggest_cli.py tests/unit/test_config.py tests/unit/test_conflict_rerun_swap_flow.py tests/unit/test_context_suggest_cli.py tests/unit/test_control.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
A test is deleted, skipped, xfailed or weakened (an assertion removed or loosened, a parametrization dropped); a new or copied `Fake*`/stand-in class or helper appears in a test file; a shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, a `tests/*_helpers.py`), `tests/integration/conftest.py` or `clutch/` code is edited; a restored integration test writes disk, starts a process, runs git or sleeps; a restored test takes more than 1.0 s; or the collected test count of the batch differs from the base commit.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files that share fixtures stay together (1029 lines here)
