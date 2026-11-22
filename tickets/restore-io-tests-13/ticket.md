---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- shared-serve-rig-config

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/integration/test_fixture_host.py
- tests/integration/test_gates.py
- tests/integration/test_gemini_provider.py

## On-demand
- tests/integration/test_flake.py

## Goal / Why
`integration-disk-io-skip` turned off 4 integration test files in this batch (1380 lines in all) because they write disk, start processes or run git. `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that does. When this ticket is done each file below runs again: its `pytestmark = pytest.mark.disk_io_skip` line is gone and its tests pass under the rules in the host authoring guide's `Unit and integration tests` section (listed in Context), driven by the shared fakes in `tests/fakes.py` and `tests/git_fake.py::GitFake` and by the shared helper modules the chain behind `restore-helpers-misc` created. Owner requirements: every restored test is fast (no restored test over 1.0 s) and reuses shared fixtures and fakes; no per-file fake class or helper copy.



## Boundary contract
none
- reason: tests encoding an existing contract; no production code, CLI, document or journal behavior changes.

## Scope in / Scope out
Scope in:
Every file in the batch is handled the same way (the per-file list below gives each file's current touches and final path):
- Delete the line `pytestmark = pytest.mark.disk_io_skip` (`disk-io-skip-per-file` added it).
- Git: `tests/git_fake.py::GitFake` (read it in the worktree; overrides by member name, defaults from return annotations, `fake.calls`). Processes: in-process `clutch.__main__.main([...])` or `tests/fakes.py::FakeExec`. Journal: `FakeJournal` unless the test's subject is journal persistence. Time: `FakeClock` plus `tests.fakes.until`/`turn`, never `sleep` or `asyncio.sleep` polling. A config in a test that only reads it: `clutch.config.load_config_text` instead of writing `config.yaml`. Code taking the `clutch.seams.FileSystem` seam gets `FakeFileSystem`.
- Names the file imports from the old hubs now come from the shared modules the helper tickets created (`tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py`, `tests/misc_helpers.py`, `tests/stage_replies.py`, `tests/config_fixture.py`). Read each in the worktree and grep it for the name before writing the import; never define a new `Fake*` or stand-in class, and never copy a helper. If a shared fake lacks a behavior a test needs, stop as a premise failure that names the missing behavior and the test; never edit a shared module.
- Placement by the rules in the host authoring guide's `Unit and integration tests` section (listed in Context): tests that still write real files (only under `tmp_path`) go to `tests/unit/` under the file's name (or `test_<name>_flow.py` when that name already exists in `tests/unit`); tests that read repo files (anchored on `Path(__file__)`) and write nothing stay in `tests/integration/`. A file with both kinds is split by whole test function into one file per place, each keeping the original name; a single test that needs both a repo read and a real write is not split, and the run stops as a premise failure naming that test. The final path of each file is in the list below.
- The helper fixtures and builders these files use (`root`, `repo`, `make_root`, `CoreRig`, `activated_graph`, `Stages`, `Script`) are rewritten by the helper tickets to run no git, start no process and write only under the `tmp_path` they are given; read each in the worktree before relying on it, and if one still runs git or starts a process, stop as a premise failure naming the helper and the test.
- Keep every test function and parametrization and the behavior each asserts; delete, skip or weaken none. A test with `@pytest.mark.asyncio` stays async. Update the import line in every other file that imports a name from a file this ticket moves (named in the list); only the import line changes there.
- Real-I/O subjects: a test whose subject is a real I/O function itself (a real process, real signals, node) goes verbatim into the file named for it below, and that file name is added as one new entry to `REAL_IO_TESTS` in `tests/integration/conftest.py` (that tuple entry is the only edit there). Those tests are exempt from the 1.0 s bound; run.md records their durations.

Per-file list (current touches, fakes, final path):
- `tests/integration/test_fixture_host.py` (398 lines) -> `tests/integration/test_fixture_host.py`. Copies `hosts/fixture` to `tmp_path`, runs its scripts and `regression_test.py` with real `SubprocessExec`, makes real git commits with `Git(SubprocessExec(), commit_lock=...)` and snapshots the engine and fixture files byte-for-byte; the subject is the real scaffold host and its real processes, which neither `GitFake` nor `FakeExec` can reproduce. Its marker is deleted and its name is added to `REAL_IO_TESTS`; imports (`commit_lock` from `tests/integration/test_git.py`) are unchanged and its tests are exempt from the 1.0 s bound. `environment` stays importable by `test_gates.py` (same batch). If the owner rejects the allowlist route this file stops the batch as a premise failure.
- `tests/integration/test_flake.py` (538 lines) -> `tests/unit/test_flake.py`. 19 tests over `CoreRig`, `root`/`Stages`/`ticket`/`write`/`ENV`/`Clock` (cli helpers) and the real `Journal`/`LocalFileSystem` on a `root` checkout under `tmp_path`; `assert_startup_pause_wiring` from `tests/daemon_helpers.py`. Moves to unit; journal stays real only where a test asserts on journal files.
- `tests/integration/test_gates.py` (382 lines) -> `tests/unit/test_gates.py` and `tests/integration/test_gates.py` and `tests/integration/test_gates_host_loop_real.py`. Pure artifact/gate tests that write `tmp_path` trees (`run_gates`, `lint_gate`) move to `tests/unit/test_gates.py`; `test_core_drift_default_hard(repo)` and `test_core_drift_gate_reports` use the helper `repo` fixture (GitFake, `SubprocessExec.run` patched as forbidden) and move to unit; `test_core_activation_committed_conduct` runs real git on the repo's own HEAD through `Git(SubprocessExec(), env=os.environ, ...)` and reads repo files: it stays in `tests/integration/test_gates.py` with `GitFake(_run=...)` returning the committed bytes (reads repo files, writes nothing). `test_host_loop_regression_uses_real_bug_gate` builds a real fixture host with real git and processes, so it moves verbatim to the new file `tests/integration/test_gates_host_loop_real.py`, added to `REAL_IO_TESTS`. `environment` comes from `tests/integration/test_fixture_host.py` (same batch, same path).
- `tests/integration/test_gemini_provider.py` (62 lines) -> `tests/unit/test_gemini_provider.py` and `tests/integration/test_gemini_provider.py`. `test_packaged_settings_files` reads `clutch/gemini-*.json` through `clutch.__file__` and writes nothing: it stays in `tests/integration/test_gemini_provider.py`. `test_calls_through_provider_llm` writes `config.yaml` under `tmp_path` and uses `LocalFileSystem` with `FakeExec` and `provider_session` (from `tests/config_helpers.py`): it moves to `tests/unit/test_gemini_provider.py` with `FakeFileSystem` for `fs=` and `load_config_text`; `T02`/`T06_ERR`/`T27`/`adapter` come from `tests/unit/test_gemini_adapter.py` (unchanged).

New files this ticket creates: `tests/integration/test_gates_host_loop_real.py`.

Real-I/O entries added to `REAL_IO_TESTS`: `test_fixture_host.py`, `test_gates_host_loop_real.py`.

Scope out:
- Any shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/*_helpers.py`, `tests/stage_replies.py`, `tests/config_fixture.py`) and any production file under `clutch/`.
- Files of other batches: `restore-io-tests-NN` tickets restore the other skipped files; a name imported from a file of another batch is imported from where that file lives when this ticket runs (grep for it).

## Scope fence
- tests/integration/test_fixture_host.py
- tests/integration/test_flake.py
- tests/integration/test_gates.py
- tests/integration/test_gemini_provider.py
- tests/unit/test_flake.py
- tests/unit/test_gates.py
- tests/integration/test_gates_host_loop_real.py
- tests/unit/test_gemini_provider.py
- tests/integration/conftest.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_fixture_host.py tests/unit/test_flake.py tests/unit/test_gates.py tests/integration/test_gates.py tests/integration/test_gates_host_loop_real.py tests/unit/test_gemini_provider.py tests/integration/test_gemini_provider.py` lists no file (it exits 1), so none of the batch's restored files still carries the marker.
2. `./dev.py test tests/integration/test_fixture_host.py tests/unit/test_flake.py tests/unit/test_gates.py tests/integration/test_gates.py tests/integration/test_gates_host_loop_real.py tests/unit/test_gemini_provider.py tests/integration/test_gemini_provider.py --durations=0` passes, and its durations table shows no restored test over 1.0 s except the tests in the real-I/O files named in Scope in; the table is pasted into `run.md`.
3. `./dev.py test tests/integration/test_fixture_host.py tests/unit/test_flake.py tests/unit/test_gates.py tests/integration/test_gates.py tests/integration/test_gates_host_loop_real.py tests/unit/test_gemini_provider.py tests/integration/test_gemini_provider.py --collect-only -q` reports the same number of tests as `./dev.py test tests/integration/test_fixture_host.py tests/integration/test_flake.py tests/integration/test_gates.py tests/integration/test_gemini_provider.py --collect-only -q` on the base commit; both counts are recorded in `run.md`. A smaller count means a test was deleted or lost a parametrization.
4. `ls tests/integration/test_flake.py` fails for every listed path (each moved file exists only at its new path), and `grep -rn "tests.integration.test_flake" tests` finds no import of a moved module at its old path.
5. `grep -n "test_fixture_host.py\|test_gates_host_loop_real.py" tests/integration/conftest.py` shows each real-I/O file named in Scope in exactly once inside `REAL_IO_TESTS`, and `git diff --stat` shows no other line of that file changed.
6. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file broke and no restored integration test tripped the I/O guard.
7. `grep -nE "^class (FakeClock|FakeFS|FakeExec|FakeGit|FakeJournal|FakeFileSystem)\b" tests/integration/test_fixture_host.py tests/unit/test_flake.py tests/unit/test_gates.py tests/integration/test_gates.py tests/integration/test_gates_host_loop_real.py tests/unit/test_gemini_provider.py tests/integration/test_gemini_provider.py` prints nothing, so no restored file defines a stand-in for a shared fake in `tests/fakes.py`.

## Verification
```
./dev.py test tests/integration/test_fixture_host.py tests/unit/test_flake.py tests/unit/test_gates.py tests/integration/test_gates.py tests/integration/test_gates_host_loop_real.py tests/unit/test_gemini_provider.py tests/integration/test_gemini_provider.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, xfailed or weakened, or the collected count drops without the extraction named in Scope in.
- A new `Fake*` class, stand-in or helper copy appears in a test file, or a shared module is edited.
- A restored integration test writes disk, starts a process or runs git outside a `REAL_IO_TESTS` file, or a `sleep` is added.
- Any `clutch/` production file changes.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files that share fixtures stay together.
