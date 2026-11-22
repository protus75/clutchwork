---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-05

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/integration/test_covgate.py
- tests/integration/test_covmap.py
- tests/integration/test_daemon_admission.py

## On-demand
- tests/integration/test_control_cli.py

## Goal / Why
`integration-disk-io-skip` turned off 4 integration test files in this batch (`test_control_cli.py`, `test_covgate.py`, `test_covmap.py` and `test_daemon_admission.py`, 1141 lines) because they write real files, run real git and processes, and sleep; `integration-io-guard` fails any such test, and `disk-io-skip-per-file` marks each skipped file with `pytestmark = pytest.mark.disk_io_skip`. The owner wants these tests back, FAST (no restored test above 1.0 s) and on the shared fakes, not on per-file copies.

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
- Placement follows the host guide section "Unit and integration tests" (in Context): a test that still writes files (only under `tmp_path`) lives under `tests/unit/`; a test that reads a repo file (anchored on `Path(__file__)`) and writes nothing lives under `tests/integration/`. Reading packaged spec or doc files inside production code (for example `ask.render` loading `clutch/specs/ask/*.md`) is not a test reading a repo file. A file whose tests need both is split, and the ticket names both paths. A moved file keeps its name under `tests/unit/` unless that name exists there, in which case it is `test_<name>_flow.py`.
- Where code under test builds its own real `Git`, `SubprocessExec` or `Journal` and `main` exposes no seam for it, drive the code through the function the unit tests beside it call, with the fakes. If neither route exists, the run stops as a premise failure that names the code path.
- Any name a moved file defines that another test module imports gets its importers' import lines updated in the same change (grep `from tests.integration.<name> import` first); only import lines change in importers.

Per file:
- `tests/integration/test_control_cli.py` (621 lines): today it 16 tests of `confirm`/`reject`/`pause`/`resume`/`stop`/`retro` verbs against a live or absent writer: real git roots, real `Journal`, `Lockfile`, `CommitLock` with an injected `sleep`, `runner.Checkout`, real file reads of the state dir (`rglob`); defines the helpers `invoke`, `acquire`, `discovery`, `requests` (imported by `test_kill_cli_activation.py` and, inline, by `test_daemon_composition.py`). Plan: moves whole to `tests/unit/test_control_cli.py` (name free) on the `tests/cli_helpers.py` root/stages rig, GitFake, FakeClock, and `FakeJournal` (real `Journal`/`Lockfile`/control files under `tmp_path` only where the written file is the subject); `test_live_pause_resume_publish_without_journal_write` and the restart-race test keep their assertions. Update the import lines in `tests/integration/test_kill_cli_activation.py` (`from tests.integration.test_control_cli import acquire, discovery, invoke, requests`) and `tests/integration/test_daemon_composition.py` (the two inline `import invoke` lines) to `tests.unit.test_control_cli`. The `Rig` import this file takes from `test_control` was already repointed by `restore-io-tests-05`.
- `tests/integration/test_covgate.py` (157 lines): today it 12 tests: 7 pure `evaluate`/`parse_gate`/`run_gate` tests plus 5 `main(['coverage', 'gate', ...])` tests that write `test-gate.toml`/`coverage.json` under `tmp_path` and run `sys.executable -c ...` as a real child through `subprocess.run` in `clutch/__main__.py`; `test_cli_runs_in_cwd_and_process_group` asserts the child shares the test process group. Plan: moves whole to `tests/unit/test_covgate_flow.py` (`tests/unit/test_covgate.py` already exists): files stay under `tmp_path`; the `main` tests replace `subprocess.run` as seen from `clutch.__main__` with `monkeypatch.setattr` (a callable that records `argv`, `cwd`, `env` and kwargs, writes the report the script would have written, and returns the exit code) and assert the same results: the same exit codes and messages, the child runs with `cwd=tmp_path`, and the process-group assertion becomes asserting that no `start_new_session`, `process_group` or `preexec_fn` kwarg is passed, which is the property the pgid comparison proved. The `no-such-binary-xyz` case makes the stand-in raise `FileNotFoundError`.
- `tests/integration/test_covmap.py` (66 lines): today it `reduce_map` is pure; `test_build` writes `raw.json` under `tmp_path` from a stand-in exec and uses per-file stand-ins `Exec`, `Git`, `FS`. Plan: moves whole to `tests/unit/test_covmap.py` (name free): `Exec` becomes `FakeExec` (a callable result that writes `raw.json` for the `success`/`invalid` cases), `Git` becomes `GitFake(rev_parse='main-sha')` with its `calls` list asserting `(repo, 'main')`, `FS` becomes `FakeFileSystem` seeded with the `previous` bytes.
- `tests/integration/test_daemon_admission.py` (297 lines): today it 7 tests of `DaemonAdmission` single-flight dispatch (asyncio only) over a `tickets` fixture that writes ticket files under `tmp_path`, `main` calls, `Clock`/`ticket`/`write`/`root` from `test_cli`; `test_daemon_admission_is_dormant` reads `clutch/*.py` via `Path(__file__)` (import closure); its `assert_idle`, `assert_reachable`, `tickets`, `turn` helpers were moved by `restore-helpers-daemon`. Plan: SPLIT. `test_daemon_admission_is_dormant` (repo reader, writes nothing) stays in `tests/integration/test_daemon_admission.py`; the other six move to `tests/unit/test_daemon_admission.py` (name free; `test_daemon_admission_busy.py` is a different file) on the daemon helper rig, FakeClock and `turn`/`until`, with ticket files under `tmp_path`.

Record in the run record (`run.md`): the `--collect-only -q` test count of the batch's files on the base commit and after the change, the `--durations=0` output of the restored paths, which tests of a split file went to which path, and for each moved file the `grep -rn "tests.integration.<name>" tests` result used to find importers.

`restore-io-tests-06` lists `restore-io-tests-05` under `## Depends on` because that ticket edits the `test_control` import line inside `tests/integration/test_control_cli.py`. `tests/integration/test_daemon_composition.py` is also restored by `restore-io-tests-07`, which lists this ticket under `## Depends on`; this ticket edits only its two inline import lines there.

Scope out: `tests/integration/conftest.py` (the marker line is the only switch), `tests/fakes.py`, `tests/conftest.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, every `tests/*_helpers.py`, all `clutch/` code, and test files outside this batch except the importer import lines named above. A hot test file (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `test_cli.py`, `test_watch.py`, `serve_rig.py`) gets no new test, fixture or helper from this change; code only leaves it or is repointed.

## Scope fence
- tests/integration/test_control_cli.py
- tests/unit/test_control_cli.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_covgate.py
- tests/unit/test_covgate_flow.py
- tests/integration/test_covmap.py
- tests/unit/test_covmap.py
- tests/integration/test_daemon_admission.py
- tests/unit/test_daemon_admission.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_control_cli.py tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_daemon_admission.py tests/unit/test_control_cli.py tests/unit/test_covgate_flow.py tests/unit/test_covmap.py tests/unit/test_daemon_admission.py` prints no file name (the marker is gone from every path the batch keeps), recorded in `run.md`; every path that the plan moves whole no longer exists under `tests/integration/` (`ls` of it fails), and the marker is not present in any new file.
2. `./dev.py test tests/integration/test_control_cli.py tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_daemon_admission.py tests/unit/test_control_cli.py tests/unit/test_covgate_flow.py tests/unit/test_covmap.py tests/unit/test_daemon_admission.py --durations=0` passes and its durations table lists no restored test above 1.0 s (a test that still takes 1.0 s or more fails this criterion, it is not allowed to stay slow); the output is recorded in `run.md`.
3. `./dev.py test tests/integration/test_control_cli.py tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_daemon_admission.py tests/unit/test_control_cli.py tests/unit/test_covgate_flow.py tests/unit/test_covmap.py tests/unit/test_daemon_admission.py --collect-only -q` reports exactly as many tests as `./dev.py test tests/integration/test_control_cli.py tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_daemon_admission.py --collect-only -q` reported on the base commit (a deleted, merged or skipped test makes the counts differ); both numbers are recorded in `run.md`.
4. `grep -nE "^\s*class (Fake|Script|Exec|Git|FS|Clock)" tests/integration/test_control_cli.py tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_daemon_admission.py tests/unit/test_control_cli.py tests/unit/test_covgate_flow.py tests/unit/test_covmap.py tests/unit/test_daemon_admission.py` prints no line (no per-file fake or stand-in class remains), and `grep -nE "subprocess|sys\.executable|time\.sleep|asyncio\.sleep" tests/integration/test_control_cli.py tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_daemon_admission.py` prints no line (a restored integration test starts no process and never sleeps).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, and `tests/integration` reports no `IntegrationIOBlocked` failure (the I/O guard stays on for every restored integration test).

## Verification
```
./dev.py test tests/integration/test_control_cli.py tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_daemon_admission.py tests/unit/test_control_cli.py tests/unit/test_covgate_flow.py tests/unit/test_covmap.py tests/unit/test_daemon_admission.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
A test is deleted, skipped, xfailed or weakened (an assertion removed or loosened, a parametrization dropped); a new or copied `Fake*`/stand-in class or helper appears in a test file; a shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, a `tests/*_helpers.py`), `tests/integration/conftest.py` or `clutch/` code is edited; a restored integration test writes disk, starts a process, runs git or sleeps; a restored test takes more than 1.0 s; or the collected test count of the batch differs from the base commit.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files that share fixtures stay together (1141 lines here)
