---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- shared-review-script

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/integration/test_go_ai_panel.py
- tests/integration/test_go_grade.py
- tests/integration/test_handoff_replace.py
- tests/integration/test_harvest.py
- tests/integration/test_harvest_cost_source.py
- tests/integration/test_harvest_orphans.py
- tests/integration/test_heartbeat.py
- tests/integration/test_host_contract.py
- tests/integration/test_host_loop.py

## Goal / Why
`integration-disk-io-skip` turned off 9 integration test files in this batch (1341 lines in all) because they write disk, start processes or run git. `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that does. When this ticket is done each file below runs again: its `pytestmark = pytest.mark.disk_io_skip` line is gone and its tests pass under the rules in the host authoring guide's `Unit and integration tests` section (listed in Context), driven by the shared fakes in `tests/fakes.py` and `tests/git_fake.py::GitFake` and by the shared helper modules the chain behind `restore-helpers-misc` created. Owner requirements: every restored test is fast (no restored test over 1.0 s) and reuses shared fixtures and fakes; no per-file fake class or helper copy.



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
- `tests/integration/test_go_ai_panel.py` (97 lines) -> `tests/integration/test_go_ai_panel.py`. Five tests build `report_fixture(tmp_path)` and write `out.json`/`measured.json`; `harness.write_report(path, report, fs=...)` takes the file-system seam, and `main`/`harness.main` is called in-process. Use `FakeFileSystem` for `fs=` and for the paths the tests write, and `FakeJournal`, so nothing real is written; it then writes nothing and reads no repo file, and stays in `tests/integration/` under the same name. `report_fixture`, `CODEX`, `NOW` come from `tests/integration/test_eval_harness.py` (restored in `restore-io-tests-12` at the same path). If one test cannot avoid a real write, move that whole test to `tests/unit/test_go_ai_panel.py` and record it.
- `tests/integration/test_go_grade.py` (124 lines) -> `tests/integration/test_go_grade.py`. `test_record_go_requires_complete_floors_identity_and_operator_judgment` reads the repo corpus (`harness.FIXTURES.glob('*/*')`, `p.read_bytes()`) and writes `operator-report.json` and `measured.json`; `harness.write_report(..., fs=fs)` takes the seam, so it uses `FakeFileSystem` and stays in `tests/integration/test_go_grade.py` (repo reads, no real writes). `test_review_baseline_report_closed_schema` likewise. Names `corpus_results`, `report_fixture`, `CODEX`, `NOW` come from `tests/integration/test_eval_harness.py` (batch 12, same path). If a test cannot avoid a real write, move that whole test to `tests/unit/test_go_grade.py` and record it.
- `tests/integration/test_handoff_replace.py` (34 lines) -> `tests/integration/test_handoff_replace.py` and `tests/integration/test_exec_seam_replace_real.py`. `test_replacement_preserves_pid_exit_code_and_buffered_output` starts a real python child that calls `SubprocessExec().replace`: its subject is that real process function, so it moves verbatim to the new file `tests/integration/test_exec_seam_replace_real.py`, added to `REAL_IO_TESTS`. `test_handoffs_do_not_spawn_unbounded_children` only reads repo files and stays in `tests/integration/test_handoff_replace.py`.
- `tests/integration/test_harvest.py` (151 lines) -> `tests/unit/test_harvest.py`. Six tests that run `main(['engine','run'|'drain'])` through the helper `repo` fixture with real `git(repo, ...)` and `seed_end` (`tests/evidence_records.py`, real `LocalFileSystem` under the state dir), `NoChild`, replies from `tests/stage_replies.py`. Git to `GitFake`; moves to unit.
- `tests/integration/test_harvest_cost_source.py` (50 lines) -> `tests/unit/test_harvest_cost_source.py`. Two tests using `invoke`/`orphan` from `test_harvest_orphans.py` (same batch), the helper `repo`, and `LocalFileSystem` for the box; moves to unit; its import of `test_harvest_orphans` becomes `tests.unit.test_harvest_orphans`.
- `tests/integration/test_harvest_orphans.py` (97 lines) -> `tests/unit/test_harvest_orphans.py`. Three tests over the helper `repo`, `main(...)`, `Journal`, `write_capture` (real state dir) and 8 `git` uses; git to `GitFake`; moves to unit. `invoke` and `orphan` are imported by `test_harvest_cost_source.py`.
- `tests/integration/test_heartbeat.py` (269 lines) -> `tests/unit/test_heartbeat.py`. Six tests: `test_heartbeat_is_dormant` runs `main(...)` on `root` (helper checkout under `tmp_path`, `Stages`/`ENV`/`Clock` from `tests/cli_helpers.py`); `test_heartbeat_is_active_in_serve` uses `activated_graph` from `tests/integration/serve_rig.py` (loop helpers); `CoreRig`/`assert_core_wiring` come from `tests/daemon_helpers.py`; the one real `Git(SubprocessExec(), commit_lock=commit_lock(...))` that asserts `ls_files`/`status_porcelain` becomes `GitFake(ls_files=[...], status_porcelain='')` and `commit_lock` is no longer imported; heartbeat and journal files are real under `tmp_path`. Moves to unit.
- `tests/integration/test_host_contract.py` (352 lines) -> `tests/integration/test_host_contract.py` and `tests/integration/test_host_contract_real.py`. Every test reads the host contract guide through `ROOT` (`DOC`, `block()`, `mentions()`) or `inspect.getsource`, so the file stays in `tests/integration/test_host_contract.py`; `load(tmp_path, raw)` writes `config.yaml` and becomes `config.load_config_text(...)` with no write, and `routed_conduct_paths(cfg, tmp_path)` only uses `tmp_path` as a path. `test_host_contract_migration_and_managed_ownership` (real `migrate_config` writes plus byte-exact reads, subject: the real file-system seam) and `test_host_contract_report_custody_and_cutover` (a real `Lockfile` flock on `tmp_path`, subject: the real lock) move verbatim to the new file `tests/integration/test_host_contract_real.py`, added to `REAL_IO_TESTS`; they share `DOC`/`block`/`load` through an import from `tests.integration.test_host_contract`. `test_host_contract_seam_inventory` starts no process (`inspect.getsource` only).
- `tests/integration/test_host_loop.py` (167 lines) -> `tests/integration/test_host_loop.py`. Its subject is `tests/harness/host_loop.py` driving real supervised subprocesses on disposable hosts (`RecordingExec(SubprocessExec)`); `test_host_loop_closed_schema` is pure schema. Marker deleted, name added to `REAL_IO_TESTS`, tests unchanged and exempt from the 1.0 s bound. If the owner rejects the allowlist route this file stops the batch as a premise failure.

New files this ticket creates: `tests/integration/test_exec_seam_replace_real.py`, `tests/integration/test_host_contract_real.py`.

Real-I/O entries added to `REAL_IO_TESTS`: `test_host_loop.py`, `test_exec_seam_replace_real.py`, `test_host_contract_real.py`.

Scope out:
- Any shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/*_helpers.py`, `tests/stage_replies.py`, `tests/config_fixture.py`) and any production file under `clutch/`.
- Files of other batches: `restore-io-tests-NN` tickets restore the other skipped files; a name imported from a file of another batch is imported from where that file lives when this ticket runs (grep for it).

## Scope fence
- tests/integration/test_go_ai_panel.py
- tests/integration/test_go_grade.py
- tests/integration/test_handoff_replace.py
- tests/integration/test_harvest.py
- tests/integration/test_harvest_cost_source.py
- tests/integration/test_harvest_orphans.py
- tests/integration/test_heartbeat.py
- tests/integration/test_host_contract.py
- tests/integration/test_host_loop.py
- tests/integration/test_exec_seam_replace_real.py
- tests/unit/test_harvest.py
- tests/unit/test_harvest_cost_source.py
- tests/unit/test_harvest_orphans.py
- tests/unit/test_heartbeat.py
- tests/integration/test_host_contract_real.py
- tests/integration/conftest.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_go_ai_panel.py tests/integration/test_go_grade.py tests/integration/test_handoff_replace.py tests/integration/test_exec_seam_replace_real.py tests/unit/test_harvest.py tests/unit/test_harvest_cost_source.py tests/unit/test_harvest_orphans.py tests/unit/test_heartbeat.py tests/integration/test_host_contract.py tests/integration/test_host_contract_real.py tests/integration/test_host_loop.py` lists no file (it exits 1), so none of the batch's restored files still carries the marker.
2. `./dev.py test tests/integration/test_go_ai_panel.py tests/integration/test_go_grade.py tests/integration/test_handoff_replace.py tests/integration/test_exec_seam_replace_real.py tests/unit/test_harvest.py tests/unit/test_harvest_cost_source.py tests/unit/test_harvest_orphans.py tests/unit/test_heartbeat.py tests/integration/test_host_contract.py tests/integration/test_host_contract_real.py tests/integration/test_host_loop.py --durations=0` passes, and its durations table shows no restored test over 1.0 s except the tests in the real-I/O files named in Scope in; the table is pasted into `run.md`.
3. `./dev.py test tests/integration/test_go_ai_panel.py tests/integration/test_go_grade.py tests/integration/test_handoff_replace.py tests/integration/test_exec_seam_replace_real.py tests/unit/test_harvest.py tests/unit/test_harvest_cost_source.py tests/unit/test_harvest_orphans.py tests/unit/test_heartbeat.py tests/integration/test_host_contract.py tests/integration/test_host_contract_real.py tests/integration/test_host_loop.py --collect-only -q` reports the same number of tests as `./dev.py test tests/integration/test_go_ai_panel.py tests/integration/test_go_grade.py tests/integration/test_handoff_replace.py tests/integration/test_harvest.py tests/integration/test_harvest_cost_source.py tests/integration/test_harvest_orphans.py tests/integration/test_heartbeat.py tests/integration/test_host_contract.py tests/integration/test_host_loop.py --collect-only -q` on the base commit; both counts are recorded in `run.md`. A smaller count means a test was deleted or lost a parametrization.
4. `ls tests/integration/test_harvest.py tests/integration/test_harvest_cost_source.py tests/integration/test_harvest_orphans.py tests/integration/test_heartbeat.py` fails for every listed path (each moved file exists only at its new path), and `grep -rn "tests.integration.test_harvest\|tests.integration.test_harvest_cost_source\|tests.integration.test_harvest_orphans" tests` finds no import of a moved module at its old path.
5. `grep -n "test_host_loop.py\|test_exec_seam_replace_real.py\|test_host_contract_real.py" tests/integration/conftest.py` shows each real-I/O file named in Scope in exactly once inside `REAL_IO_TESTS`, and `git diff --stat` shows no other line of that file changed.
6. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file broke and no restored integration test tripped the I/O guard.
7. `grep -nE "^class (FakeClock|FakeFS|FakeExec|FakeGit|FakeJournal|FakeFileSystem)\b" tests/integration/test_go_ai_panel.py tests/integration/test_go_grade.py tests/integration/test_handoff_replace.py tests/integration/test_exec_seam_replace_real.py tests/unit/test_harvest.py tests/unit/test_harvest_cost_source.py tests/unit/test_harvest_orphans.py tests/unit/test_heartbeat.py tests/integration/test_host_contract.py tests/integration/test_host_contract_real.py tests/integration/test_host_loop.py` prints nothing, so no restored file defines a stand-in for a shared fake in `tests/fakes.py`.

## Verification
```
./dev.py test tests/integration/test_go_ai_panel.py tests/integration/test_go_grade.py tests/integration/test_handoff_replace.py tests/integration/test_exec_seam_replace_real.py tests/unit/test_harvest.py tests/unit/test_harvest_cost_source.py tests/unit/test_harvest_orphans.py tests/unit/test_heartbeat.py tests/integration/test_host_contract.py tests/integration/test_host_contract_real.py tests/integration/test_host_loop.py --durations=0
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
