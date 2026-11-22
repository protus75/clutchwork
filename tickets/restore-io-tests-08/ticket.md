---
state: rejected
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
- tests/integration/test_daemon_core_queue_seams.py
- tests/integration/test_daemon_pause.py
- tests/integration/test_daemon_soak.py
- tests/integration/test_daemon_soak_runner.py

## On-demand
- tests/integration/test_daemon_config.py

## Goal / Why
`integration-disk-io-skip` turned off 5 integration test files in this batch (1269 lines in all) because they write disk, start processes or run git. `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that does. When this ticket is done each file below runs again: its `pytestmark = pytest.mark.disk_io_skip` line is gone and its tests pass under the rules in the host authoring guide's `Unit and integration tests` section (listed in Context), driven by the shared fakes in `tests/fakes.py` and `tests/git_fake.py::GitFake` and by the shared helper modules the chain behind `restore-helpers-misc` created. Owner requirements: every restored test is fast (no restored test over 1.0 s) and reuses shared fixtures and fakes; no per-file fake class or helper copy.

`tests/integration/test_daemon_composition.py` imports `assert_detached` and `python_values` from `tests.integration.test_daemon_config`; once that file moves it imports them from `tests.unit.test_daemon_config` (import line only; composition is a hot file and `restore-helpers-daemon` has already moved its own helpers).

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
- `tests/integration/test_daemon_config.py` (441 lines) -> `tests/unit/test_daemon_config.py` and `tests/integration/test_daemon_config_reachable.py`. Writes `config.yaml` under `tmp_path` through `LocalFileSystem`, runs `main(['engine','run'|'drain'])` on the `root` checkout (journal and lock files under it), and its last test `test_config_snapshot_is_dormant` also reads every `clutch/*.py` through `Path(__file__)`. Config texts come from `tests/config_helpers.py`/`tests/config_fixture.py` (`VALID`), `root`/`ticket`/`write`/`ENV`/`Clock` from `tests/cli_helpers.py`, `assert_idle`/`assert_reachable`/`tickets`/`turn` from `tests/daemon_helpers.py`. All tests move to the unit file. The repo-reading tail of `test_config_snapshot_is_dormant` (from `repo = Path(__file__)...` to the end: `assert_reachable`, `without_core_import`, `CoreRig`, `assert_core_wiring`, `assert_idle`) is extracted unchanged into one new test `test_config_snapshot_core_reachable` in the integration file `tests/integration/test_daemon_config_reachable.py` (it writes nothing: `CoreRig` is fake-backed; it reads repo sources). That extraction is the only change to the test count: the collected total after is the base total plus 1, and the criterion below accounts for it.
- `tests/integration/test_daemon_core_queue_seams.py` (41 lines) -> `tests/integration/test_daemon_core_queue_seams.py`. Already fake-backed (`CoreRig` from `tests/daemon_helpers.py` with a fake file system; `tests/dispatch_settle.py::dispatch_settled`); writes nothing and reads no repo file, so it stays integration under the same name; only the marker line and the `CoreRig` import change.
- `tests/integration/test_daemon_pause.py` (221 lines) -> `tests/unit/test_daemon_pause.py`. Writes `config.yaml` under `tmp_path` (`CONFIG` from the cli/config helpers), runs `main(['engine','drain'])` on the `root` checkout, and builds `Rig` (real `Journal` and `LocalFileSystem` under `tmp_path`) from `tests/integration/test_control.py`, which `restore-io-tests-05` restores (import `Rig` from wherever that file lives when this ticket runs). `Script`/`journal` come from `tests/drain_helpers.py`, `CoreRig`/`assert_core_wiring`/`assert_startup_pause_wiring` from `tests/daemon_helpers.py`. Moves to unit; asyncio tests keep `asyncio.Event` hand-offs and use `tests.fakes.turn`, no sleeps.
- `tests/integration/test_daemon_soak.py` (183 lines) -> `tests/integration/test_daemon_soak.py`. `report(root)` builds a real `Git(SubprocessExec())` only to call `rev_parse(root, 'HEAD')` for `produced_at_sha`; replace it with `GitFake(rev_parse=<40-hex sha>)` (the schema requires a non-blank sha) and drop the `root` fixture and `commit_lock`. Everything else is pydantic schema checks, so the file writes nothing and stays integration under the same name.
- `tests/integration/test_daemon_soak_runner.py` (383 lines) -> `tests/integration/test_daemon_soak_runner.py`. Its subject is the real supervised soak: `tests/harness/daemon_soak.py::produce` builds real git repos, a `LocalFileSystem` and `SubprocessExec`, and tests assert on real commits (`git show <sha>:union.txt`), worktrees and `engine.log` files. That cannot run on `GitFake`, which has no file contents, and the harness is not a shared module this ticket may rewrite. Decision recorded here: the file stays real-I/O, so its marker line is deleted and the name `test_daemon_soak_runner.py` is added to `REAL_IO_TESTS`; its tests and imports (`commit_lock` from `tests/integration/test_git.py`, `read_capture`/`write_capture` from `tests/spool_captures.py`) are unchanged and exempt from the 1.0 s bound. If the owner rejects the allowlist route, this file is the one that stops the batch as a premise failure.

Importers whose import line changes because a file moved: `tests/integration/test_daemon_composition.py`.

New files this ticket creates: `tests/integration/test_daemon_config_reachable.py`.

Real-I/O entries added to `REAL_IO_TESTS`: `test_daemon_soak_runner.py`.

Scope out:
- Any shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/*_helpers.py`, `tests/stage_replies.py`, `tests/config_fixture.py`) and any production file under `clutch/`.
- Files of other batches: `restore-io-tests-NN` tickets restore the other skipped files; a name imported from a file of another batch is imported from where that file lives when this ticket runs (grep for it).

## Scope fence
- tests/integration/test_daemon_config.py
- tests/integration/test_daemon_core_queue_seams.py
- tests/integration/test_daemon_pause.py
- tests/integration/test_daemon_soak.py
- tests/integration/test_daemon_soak_runner.py
- tests/unit/test_daemon_config.py
- tests/integration/test_daemon_config_reachable.py
- tests/unit/test_daemon_pause.py
- tests/integration/test_daemon_composition.py
- tests/integration/conftest.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_daemon_config.py tests/integration/test_daemon_config_reachable.py tests/integration/test_daemon_core_queue_seams.py tests/unit/test_daemon_pause.py tests/integration/test_daemon_soak.py tests/integration/test_daemon_soak_runner.py` lists no file (it exits 1), so none of the batch's restored files still carries the marker.
2. `./dev.py test tests/unit/test_daemon_config.py tests/integration/test_daemon_config_reachable.py tests/integration/test_daemon_core_queue_seams.py tests/unit/test_daemon_pause.py tests/integration/test_daemon_soak.py tests/integration/test_daemon_soak_runner.py --durations=0` passes, and its durations table shows no restored test over 1.0 s except the tests in the real-I/O files named in Scope in; the table is pasted into `run.md`.
3. `./dev.py test tests/unit/test_daemon_config.py tests/integration/test_daemon_config_reachable.py tests/integration/test_daemon_core_queue_seams.py tests/unit/test_daemon_pause.py tests/integration/test_daemon_soak.py tests/integration/test_daemon_soak_runner.py --collect-only -q` reports the same number of tests as `./dev.py test tests/integration/test_daemon_config.py tests/integration/test_daemon_core_queue_seams.py tests/integration/test_daemon_pause.py tests/integration/test_daemon_soak.py tests/integration/test_daemon_soak_runner.py --collect-only -q` on the base commit plus 1 (the extracted `test_config_snapshot_core_reachable`); both counts are recorded in `run.md`. A smaller count means a test was deleted or lost a parametrization.
4. `ls tests/integration/test_daemon_config.py tests/integration/test_daemon_pause.py` fails for every listed path (each moved file exists only at its new path), and `grep -rn "tests.integration.test_daemon_config\|tests.integration.test_daemon_pause" tests` finds no import of a moved module at its old path.
5. `grep -n "test_daemon_soak_runner.py" tests/integration/conftest.py` shows each real-I/O file named in Scope in exactly once inside `REAL_IO_TESTS`, and `git diff --stat` shows no other line of that file changed.
6. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file broke and no restored integration test tripped the I/O guard.
7. `grep -nE "^class (FakeClock|FakeFS|FakeExec|FakeGit|FakeJournal|FakeFileSystem)\b" tests/unit/test_daemon_config.py tests/integration/test_daemon_config_reachable.py tests/integration/test_daemon_core_queue_seams.py tests/unit/test_daemon_pause.py tests/integration/test_daemon_soak.py tests/integration/test_daemon_soak_runner.py` prints nothing, so no restored file defines a stand-in for a shared fake in `tests/fakes.py`.

## Verification
```
./dev.py test tests/unit/test_daemon_config.py tests/integration/test_daemon_config_reachable.py tests/integration/test_daemon_core_queue_seams.py tests/unit/test_daemon_pause.py tests/integration/test_daemon_soak.py tests/integration/test_daemon_soak_runner.py --durations=0
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
