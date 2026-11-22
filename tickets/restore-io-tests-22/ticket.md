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
- tests/integration/test_notify.py
- tests/integration/test_open_tickets_closed.py
- tests/integration/test_paved_roads.py
- tests/integration/test_policy.py
- tests/integration/test_provider_capture_overwrite.py
- tests/integration/test_provider_failure_surface.py

## On-demand
- tests/integration/test_provider_cooldown_failover.py

## Goal / Why
Skipped by `integration-disk-io-skip`, these integration test files carry `pytestmark = pytest.mark.disk_io_skip` (set by `disk-io-skip-per-file`) and run nothing. The owner wants them restored FAST and on the shared fakes: each file below has its marker line deleted and its tests rewritten so they pass under the rules in `clutch/docs/host-authoring.md#Unit and integration tests`: git goes through `tests/git_fake.py::GitFake` (created by `shared-git-fake`), processes through `FakeExec` or in-process `clutch.__main__.main`, the journal through `FakeJournal` unless the test's subject is journal persistence, time through `FakeClock` with `fakes.until`/`fakes.turn` and never a sleep, and code that takes the `clutch.seams.FileSystem` seam through `FakeFileSystem`. Models are scripted with `tests/stage_replies.py` and config texts come from `tests/config_fixture.py` where those modules (created by `shared-review-script` and `shared-serve-rig-config`) already hold the helper. Names the files used to import from other test files now live in `tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py` and `tests/misc_helpers.py` (created by the `restore-helpers-*` chain that `restore-helpers-misc` ends). The implementer reads each of those modules in its worktree before editing and imports from them; it never defines a new `Fake*` or stand-in class and never copies a helper into a test file. Pre-existing in-file stand-in classes that do no real I/O may stay as they are. If a shared module lacks a behavior a test needs, the run stops as a premise failure naming the missing behavior; it never edits a shared module.

Files: `tests/integration/test_notify.py`, `test_open_tickets_closed.py`, `test_paved_roads.py`, `test_policy.py`, `test_provider_capture_overwrite.py`, `test_provider_cooldown_failover.py`, `test_provider_failure_surface.py` (1,320 lines together). Final paths: `tests/unit/test_notify.py`, `tests/unit/test_open_tickets_closed.py`, `tests/unit/test_paved_roads_flow.py`, `tests/integration/test_policy.py` (stays), `tests/unit/test_provider_capture_overwrite.py`, `tests/unit/test_provider_cooldown_failover.py`, `tests/unit/test_provider_failure_surface.py`.

## Boundary contract
none
- reason: tests encoding an existing contract; no production code, prompt, or shared test module changes

## Scope in / Scope out
Rules for every file in this batch:
- Delete the `pytestmark = pytest.mark.disk_io_skip` line (and `import pytest` only if nothing else uses it).
- Keep every test function and what it asserts. No test is deleted, skipped, xfailed or weakened; a test whose original check cannot be kept stops the run as a premise failure naming the test and the missing behavior.
- A file whose rewritten tests still write real files, only under `tmp_path`, moves to `tests/unit/` under the name this ticket gives. A file that reads repo files (anchored on `Path(__file__)`) and writes nothing stays in `tests/integration/`. A file needing both is split along whole test functions, each part at the path this ticket names. A moved file's `# relates:` and `# purpose:` meta lines are kept true, and its old path is removed.
- Imports in other files that name a moved file change to its new path; only those import lines change there.

Scope in, per file:
- `tests/integration/test_notify.py` (166 lines): real `Journal` under `tmp_path`, `config.yaml` and `engine.log` on disk, and `test_notify_seam_uses_argv_and_secret_free_env` starts real `sys.executable` children through `SubprocessExec`. Move to `tests/unit/test_notify.py` (writes `config.yaml` and `engine.log` under `tmp_path`). Journal goes to `FakeJournal`; the `Time` clock class comes from `tests/loop_helpers.py` (hub `test_scheduler.py`) or `FakeClock`; `wait_until` becomes `fakes.until`. For the process test, build the seam with `cli.build_notifications` as today, assert the isolation checks (`seam.exec_` is neither work nor reexec executor, `cwd`, `timeout`) on the built seam, then swap in the shared `FakeExec` scripted with the child's stdout and stderr (containing the secret) and assert the argv list, the `cwd`, that `TEST_KEY` is absent from the env the executor received while `KEEP` is present, and that output is redacted to `[REDACTED:TEST_KEY]`; the missing-binary and exit-4 cases use a `FakeExec` that raises or returns rc 4. Read `CommandNotifications` first; if the real process is the only way to keep one of those assertions, stop as a premise failure naming it.
- `tests/integration/test_open_tickets_closed.py` (35 lines): imports `commit_ticket`, `pause_checkout` from the drain hub (`tests/drain_helpers.py`) and `enqueue`, `reply`, `root_with_box`, `run` from the triage hub (`tests/loop_helpers.py`); real git and box records under `tmp_path` come from those helpers, and the test reads box record files with `read_text`, so it moves to `tests/unit/test_open_tickets_closed.py`.
- `tests/integration/test_paved_roads.py` (95 lines): drain, `make_root` git repo, `Box(..., LocalFileSystem())`, retro `rig`. Imports `ticket, write` from `tests/cli_helpers.py`, the drain names from `tests/drain_helpers.py`, `merged, rig` from `tests/misc_helpers.py`. Writes files under `tmp_path`, so it moves; `tests/unit/test_paved_roads.py` already exists, so the final path is `tests/unit/test_paved_roads_flow.py`. The `Box` in `test_box_reads_name_a_repair` is on a real directory the test also writes `bad.json` into: keep it on `tmp_path`.
- `tests/integration/test_policy.py` (122 lines): `config(tmp_path)` writes `config.yaml` and calls `load_config`; the tests also read `ROOT / "clutch" / "specs"`. Replace the write with `clutch.config.load_config_text(text, path=tmp_path / "config.yaml", cwd=tmp_path)`, which reads and writes no file. The file then only reads repo specs and stays at `tests/integration/test_policy.py`. Keep the `ROOT`, `config(tmp_path)` and `signal` names and signatures: `tests/integration/test_baseline.py` (another batch) imports them, so it needs no edit here.
- `tests/integration/test_provider_capture_overwrite.py` (47 lines): imports `ENV, FakeExec, claude_ok, config, llm, req` from the providers hub (`tests/config_helpers.py`); `EvidenceStore` runs over `LocalFileSystem` on `cfg.state_dir`. Use `FakeFileSystem` for the store and the client, and list the `evidence/calls` entries through it, not `Path.iterdir`; `config(tmp_path)` writes `config.yaml`, so it moves to `tests/unit/test_provider_capture_overwrite.py`. `test_capture_survives_new_process` keeps its two independent clients over the same filesystem.
- `tests/integration/test_provider_cooldown_failover.py` (824 lines, 18 tests): `CoreRig` (from `tests/daemon_helpers.py`), `serve_rig` names `finish, graph, terminals`, `registry`, `held`, `repository` and `text, turn`. It currently sets `rig.fs.publish = LocalFileSystem().publish`, passes `reexec=SubprocessExec()` to `drain`, and patches `cli.SubprocessExec` with a `NotificationProcess` class. Replace the publish override with the fake filesystem's own, `reexec` with the shared `FakeExec`, and drive time with `rig.time` and `fakes.until`/`fakes.turn` (replacing `serve_rig.until` and `test_scheduler.turn` imports where the shared one is equivalent). `NotificationProcess` and `Reply` are pre-existing in-file classes; keep them if they do no real I/O. Files written by `CoreRig` configs live under `tmp_path`, so it moves to `tests/unit/test_provider_cooldown_failover.py`. `tests/spool_captures.py` reads and writes through `LocalFileSystem` by default: pass the fake filesystem (`fs=`) or use the `tests/misc_helpers.py` equivalent. `tests/dispatch_settle.py` and `tests/approval.py` are imported: if `approval.py` still runs real git or a process, stop as a premise failure naming it.
- `tests/integration/test_provider_failure_surface.py` (31 lines): imports `repo, run` from the stages hub (`tests/stages_helpers.py`); the `Box(...)` over `LocalFileSystem()` uses the fake filesystem the stages helper exposes. The `repo` fixture writes a config under `tmp_path`, so it moves to `tests/unit/test_provider_failure_surface.py`.
- Importers: `tests/integration/test_baseline.py` imports from `test_policy` (path unchanged, no edit). Grep `from tests.integration.test_notify`, `test_open_tickets_closed`, `test_paved_roads`, `test_provider_capture_overwrite`, `test_provider_cooldown_failover`, `test_provider_failure_surface` in `tests/` and fence and fix any hit.

Scope out:
- Every shared module named in Goal / Why, `tests/integration/conftest.py`, `clutch/`, `docs/`, and every test file not named here.

## Scope fence
- tests/integration/test_notify.py
- tests/integration/test_open_tickets_closed.py
- tests/integration/test_paved_roads.py
- tests/integration/test_policy.py
- tests/integration/test_provider_capture_overwrite.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_provider_failure_surface.py
- tests/unit/test_notify.py
- tests/unit/test_open_tickets_closed.py
- tests/unit/test_paved_roads_flow.py
- tests/unit/test_provider_capture_overwrite.py
- tests/unit/test_provider_cooldown_failover.py
- tests/unit/test_provider_failure_surface.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_notify.py tests/unit/test_open_tickets_closed.py tests/unit/test_paved_roads_flow.py tests/integration/test_policy.py tests/unit/test_provider_capture_overwrite.py tests/unit/test_provider_cooldown_failover.py tests/unit/test_provider_failure_surface.py` lists none of the restored files (not one left carrying the marker).
2. `./dev.py test tests/unit/test_notify.py tests/unit/test_open_tickets_closed.py tests/unit/test_paved_roads_flow.py tests/integration/test_policy.py tests/unit/test_provider_capture_overwrite.py tests/unit/test_provider_cooldown_failover.py tests/unit/test_provider_failure_surface.py --durations=0` passes, and no restored test takes more than 1.0 s (not a slower test left in); the durations output is recorded in the run record (`run.md`).
3. `./dev.py test tests/integration/test_notify.py tests/integration/test_open_tickets_closed.py tests/integration/test_paved_roads.py tests/integration/test_policy.py tests/integration/test_provider_capture_overwrite.py tests/integration/test_provider_cooldown_failover.py tests/integration/test_provider_failure_surface.py --collect-only -q` on the base commit and `./dev.py test tests/unit/test_notify.py tests/unit/test_open_tickets_closed.py tests/unit/test_paved_roads_flow.py tests/integration/test_policy.py tests/unit/test_provider_capture_overwrite.py tests/unit/test_provider_cooldown_failover.py tests/unit/test_provider_failure_surface.py --collect-only -q` on the branch report the same number of tests (not fewer), both counts recorded in `run.md`.
4. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.
5. `./dev.py test tests/unit/test_notify.py` passes and the process test asserts the executor received no `TEST_KEY` in its env and that stdout and stderr carry `[REDACTED:TEST_KEY]`, not the secret value.
6. `grep -n "load_config_text" tests/integration/test_policy.py` lists the config builder and `./dev.py test tests/integration/test_policy.py tests/integration/test_baseline.py --collect-only -q` still imports `ROOT`, `config`, `signal` from it without error.

## Verification
```
./dev.py test tests/unit/test_notify.py tests/unit/test_open_tickets_closed.py tests/unit/test_paved_roads_flow.py tests/integration/test_policy.py tests/unit/test_provider_capture_overwrite.py tests/unit/test_provider_cooldown_failover.py tests/unit/test_provider_failure_surface.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, xfailed, or weakened, or the collected count of the batch differs from the base commit.
- A new `Fake*` class, stand-in class, or copy of a helper appears in a test file, or a shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`, any `conftest.py`) is edited.
- A restored integration test writes disk, starts a process, or runs git, or a restored test adds a sleep.
- A restored test takes more than 1.0 s in the `--durations=0` output.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files sharing fixtures stay together
