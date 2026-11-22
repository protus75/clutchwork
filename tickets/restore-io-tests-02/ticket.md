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
- tests/integration/test_baseline.py
- tests/integration/test_box.py
- tests/integration/test_box_triage_inbox.py

## On-demand
- tests/integration/test_bug_gate.py

## Goal / Why
`integration-disk-io-skip` turned off 4 integration test files in this batch (`test_baseline.py`, `test_box.py`, `test_box_triage_inbox.py` and `test_bug_gate.py`, 1187 lines) because they write real files, run real git and processes, and sleep; `integration-io-guard` fails any such test, and `disk-io-skip-per-file` marks each skipped file with `pytestmark = pytest.mark.disk_io_skip`. The owner wants these tests back, FAST (no restored test above 1.0 s) and on the shared fakes, not on per-file copies.

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
- `tests/integration/test_baseline.py` (198 lines): today it real `Journal` files under `tmp_path` (including a torn-tail journal), `load_spec`, `snapshot_config`; imports `ROOT`, `config`, `signal` from the skipped non-hub module `test_policy.py` and `Clock` from `test_drain`. Plan: moves whole to `tests/unit/test_baseline.py` (every test writes under `tmp_path`: journals, including the torn-tail file whose persistence is the subject, and spec copies in `tmp_path / 'specs'`). Each test-side read of `ROOT / 'clutch' / 'specs' / ...` becomes the production reader (`clutch.specs.load_spec` or the packaged-spec text it loads) and `specs_dir=ROOT / 'clutch' / 'specs'` is passed as the packaged specs directory `clutch.runner.SPECS_DIR`, so no test reads a repo path itself. `Clock` becomes `FakeClock`. Names imported from `test_policy.py` are read in the worktree: pure definitions stay imported from there; a name that does real I/O stops the run as a premise failure naming it (`test_policy.py` is not a helper hub).
- `tests/integration/test_box.py` (383 lines): today it `Box` over `LocalFileSystem` under `tmp_path`, real `Git(SubprocessExec(), ...)` with `commit_lock`, real `Journal` callbacks; 11 tests on enqueue, dedup, durability, corruption, registry format and tombstone re-report replay. Plan: moves whole to `tests/unit/test_box.py`: the durability, corruption and registry-format tests keep a real `Box` on `LocalFileSystem` under `tmp_path` (persistence is their subject); every other test uses `FakeFileSystem`; git becomes `GitFake`; journal callbacks use `FakeJournal`.
- `tests/integration/test_box_triage_inbox.py` (134 lines): today it real git root (`root`, `root_with_box`), real `Journal`, `Lockfile`, `Box(LocalFileSystem())`, `main` over `cwd=root`, `FakeLLM`; `test_prompt_bounds` reads the packaged drain-loop prompt spec via `Path(__file__)`. Plan: SPLIT. `test_prompt_bounds` (repo reader, writes nothing) stays in `tests/integration/test_box_triage_inbox.py`; the other four tests move to `tests/unit/test_box_triage_inbox.py` on GitFake, FakeClock and the loop/cli helper rigs, with a real `Lockfile` only where the lock file is the subject.
- `tests/integration/test_bug_gate.py` (472 lines): today it 16 tests over merge and stage gating: real git repos (`commit`, `ctx`, `ready`, `approve` from `test_mergequeue`), a regression command that runs a real child process (the `child` script at line 199 spawns `python3`), `read_capture` from `tests/spool_captures.py`, `SECRET`/`STEM`/`TICKET` from `test_stages`. Plan: stays whole at `tests/integration/test_bug_gate.py` (no unit file is created): every test runs on `GitFake`, a scripted `FakeExec` (the regression command and its child process are scripted results, the wrapper-execution-error tests raise `ExecutableNotFound` from the fake) and `FakeFileSystem`. A test that cannot do without a real file stops the run as a premise failure naming it.

Record in the run record (`run.md`): the `--collect-only -q` test count of the batch's files on the base commit and after the change, the `--durations=0` output of the restored paths, which tests of a split file went to which path, and for each moved file the `grep -rn "tests.integration.<name>" tests` result used to find importers.

Scope out: `tests/integration/conftest.py` (the marker line is the only switch), `tests/fakes.py`, `tests/conftest.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, every `tests/*_helpers.py`, all `clutch/` code, and test files outside this batch except the importer import lines named above. A hot test file (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `test_cli.py`, `test_watch.py`, `serve_rig.py`) gets no new test, fixture or helper from this change; code only leaves it or is repointed.

## Scope fence
- tests/integration/test_baseline.py
- tests/unit/test_baseline.py
- tests/integration/test_box.py
- tests/unit/test_box.py
- tests/integration/test_box_triage_inbox.py
- tests/unit/test_box_triage_inbox.py
- tests/integration/test_bug_gate.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_box_triage_inbox.py tests/integration/test_bug_gate.py tests/unit/test_baseline.py tests/unit/test_box.py tests/unit/test_box_triage_inbox.py` prints no file name (the marker is gone from every path the batch keeps), recorded in `run.md`; every path that the plan moves whole no longer exists under `tests/integration/` (`ls` of it fails), and the marker is not present in any new file.
2. `./dev.py test tests/integration/test_box_triage_inbox.py tests/integration/test_bug_gate.py tests/unit/test_baseline.py tests/unit/test_box.py tests/unit/test_box_triage_inbox.py --durations=0` passes and its durations table lists no restored test above 1.0 s (a test that still takes 1.0 s or more fails this criterion, it is not allowed to stay slow); the output is recorded in `run.md`.
3. `./dev.py test tests/integration/test_box_triage_inbox.py tests/integration/test_bug_gate.py tests/unit/test_baseline.py tests/unit/test_box.py tests/unit/test_box_triage_inbox.py --collect-only -q` reports exactly as many tests as `./dev.py test tests/integration/test_baseline.py tests/integration/test_box.py tests/integration/test_box_triage_inbox.py tests/integration/test_bug_gate.py --collect-only -q` reported on the base commit (a deleted, merged or skipped test makes the counts differ); both numbers are recorded in `run.md`.
4. `grep -nE "^\s*class (Fake|Script|Exec|Git|FS|Clock)" tests/integration/test_box_triage_inbox.py tests/integration/test_bug_gate.py tests/unit/test_baseline.py tests/unit/test_box.py tests/unit/test_box_triage_inbox.py` prints no line (no per-file fake or stand-in class remains), and `grep -nE "subprocess|sys\.executable|time\.sleep|asyncio\.sleep" tests/integration/test_box_triage_inbox.py tests/integration/test_bug_gate.py` prints no line (a restored integration test starts no process and never sleeps).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, and `tests/integration` reports no `IntegrationIOBlocked` failure (the I/O guard stays on for every restored integration test).

## Verification
```
./dev.py test tests/integration/test_box_triage_inbox.py tests/integration/test_bug_gate.py tests/unit/test_baseline.py tests/unit/test_box.py tests/unit/test_box_triage_inbox.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
A test is deleted, skipped, xfailed or weakened (an assertion removed or loosened, a parametrization dropped); a new or copied `Fake*`/stand-in class or helper appears in a test file; a shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, a `tests/*_helpers.py`), `tests/integration/conftest.py` or `clutch/` code is edited; a restored integration test writes disk, starts a process, runs git or sleeps; a restored test takes more than 1.0 s; or the collected test count of the batch differs from the base commit.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files that share fixtures stay together (1187 lines here)
