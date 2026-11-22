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
- tests/integration/test_reject_queue.py
- tests/integration/test_reject_reason_both_paths.py
- tests/integration/test_release.py
- tests/integration/test_release_publish.py
- tests/integration/test_reliability_battery.py
- tests/integration/test_requisition.py
- tests/integration/test_requisition_brief_check.py

## Goal / Why
Skipped by `integration-disk-io-skip`, these integration test files carry `pytestmark = pytest.mark.disk_io_skip` (set by `disk-io-skip-per-file`) and run nothing. The owner wants them restored FAST and on the shared fakes: each file below has its marker line deleted and its tests rewritten so they pass under the rules in `clutch/docs/host-authoring.md#Unit and integration tests`: git goes through `tests/git_fake.py::GitFake` (created by `shared-git-fake`), processes through `FakeExec` or in-process `clutch.__main__.main`, the journal through `FakeJournal` unless the test's subject is journal persistence, time through `FakeClock` with `fakes.until`/`fakes.turn` and never a sleep, and code that takes the `clutch.seams.FileSystem` seam through `FakeFileSystem`. `restore-helpers-misc` transitively depends on `shared-git-fake-integration` and `shared-fakes-guard` through the first helper ticket, so `tests/git_fake.py` exists when this ticket runs; the implementer reads it in its worktree. Names the files used to import from other test files now live in `tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`, `tests/config_helpers.py`, `tests/loop_helpers.py` and `tests/misc_helpers.py` (created by the `restore-helpers-*` chain that `restore-helpers-misc` ends). The implementer reads each of those modules in its worktree before editing and imports from them; it never defines a new `Fake*` or stand-in class and never copies a helper into a test file. Pre-existing in-file stand-in classes that do no real I/O may stay as they are. If a shared module lacks a behavior a test needs, the run stops as a premise failure naming the missing behavior; it never edits a shared module.

Files: `tests/integration/test_reject_queue.py`, `test_reject_reason_both_paths.py`, `test_release.py`, `test_release_publish.py`, `test_reliability_battery.py` (plus its harness `tests/harness/reliability_battery.py`), `test_requisition.py`, `test_requisition_brief_check.py` (1,246 lines together). Final paths: `tests/unit/test_reject_queue.py`, `tests/unit/test_reject_reason_both_paths.py` plus `tests/integration/test_reject_reason_docs.py`, `tests/unit/test_release_flow.py`, `tests/unit/test_release_publish_flow.py`, `tests/unit/test_reliability_battery.py`, `tests/integration/test_requisition.py` (stays), `tests/integration/test_requisition_brief_check.py` (stays).

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
- `tests/integration/test_reject_queue.py` (265 lines): real git repo through `make_root`/`commit_ticket`/`drain` (`tests/drain_helpers.py`), `git_out` and `ENV` (`tests/cli_helpers.py`), `commit_lock` (REAL_IO `test_git.py`; use the `tests/misc_helpers.py` equivalent), terminal fixtures `author, clock, diagnosis_reply, implement_reply, repo` (`tests/loop_helpers.py`), and `test_dead_dependencies_resolve_through_supersedes` builds `Git(SubprocessExec(), ...)` and `LocalFileSystem()` itself: give it `GitFake`, `FakeExec`, `FakeFileSystem`. Tickets and `config.yaml` are written under `tmp_path`, so it moves to `tests/unit/test_reject_queue.py`.
- `tests/integration/test_reject_reason_both_paths.py` (73 lines): `test_reject_both_paths` uses the mergequeue `ctx` fixture through `context_fixture.__wrapped__(tmp_path)` and runs `entry.main` in a thread, which builds its own `SubprocessExec`; patch `clutch.__main__.SubprocessExec` to the shared `FakeExec`. It keeps writing config under `tmp_path`: it goes to `tests/unit/test_reject_reason_both_paths.py`. `test_help_docs_and_prompt` reads two documentation files through `ROOT` (read only, not changed); replace its `tmp_path / "config.yaml"` write with `clutch.config.load_config_text(VALID, path=tmp_path / "config.yaml", cwd=tmp_path)` so it writes nothing and split it, unchanged otherwise, into `tests/integration/test_reject_reason_docs.py`. `ctx`, `ready`, `commit`, `admission_control` come from `tests/daemon_helpers.py`, `VALID` from `tests/config_helpers.py`.
- `tests/integration/test_release.py` (112 lines, 2 tests) and `tests/integration/test_release_publish.py` (140 lines, 5 tests): the `repository` and `published_repo` fixtures run real `git init/add/commit/tag` under `tmp_path`, wrap `SubprocessExec.run` to fake only `uv`, and `main(["release", ...], cwd=repo, env=ENV)` builds its own `Git(SubprocessExec())`. Replace the real repo with `GitFake` (commit, tag, rev-parse, status, staged and unstaged edits) and patch `clutch.__main__.SubprocessExec` (and whatever Git factory `release` uses; read the `release` branch of `clutch/__main__.py` first) to the shared `FakeExec`, with `uv` replies scripted as today; `release_publish` also patches `dev.subprocess.run` (keep that, it is already a fake). The original assertions are about git effects (an unstaged edit stays unstaged, the staged edit stays staged, a tag exists): if `GitFake` cannot model one, stop as a premise failure naming it. `tests/unit/test_release.py` and `tests/unit/test_release_publish.py` already exist, so the final paths are `tests/unit/test_release_flow.py` and `tests/unit/test_release_publish_flow.py`; `release_publish` imports `clock, repository` from the release file's new path. Files written under `tmp_path` (`config.yaml`, `pyproject.toml`, dist files) keep them in unit.
- `tests/integration/test_reliability_battery.py` (286 lines, 8 tests) imports `tests/harness/reliability_battery.py` (492 lines), which is not named in any helper ticket: its `_Member` builds a real git repo with `Git(SubprocessExec())`, `commit_lock` from REAL_IO `test_git.py`, a `_Exec` wrapping a real `SubprocessExec`, runs `git worktree list` through `git._run`, and `_observe` reads the real repo `HEAD` of `Path(__file__)`. Fence and rewrite that harness onto `GitFake`, the shared `FakeExec` and `FakeFileSystem` (its only importer is this test file; grep `reliability_battery` in `tests/`, `dev.py`, `clutch/` first and fence any other hit), take the sha from the fake rather than the repo `.git`, and keep `battery._Member`'s public names. `await asyncio.sleep(0)` yields stay. `test_cooling_recovery_after_many_turns` keeps asserting more than 100000 turns; if it cannot finish under 1.0 s on the fakes without lowering that count, stop as a premise failure naming it. In `test_reliability_battery_requires_member_local_evidence` the `rglob`, `unlink` and `read_bytes` steps over `m.root/tickets` become `FakeFileSystem` operations (its `files` keys and `remove`), and the test asserts that at least one `harvest.json` and one `run.md` were visited, so an empty listing fails it. The members write repo files under `tmp_path`, so the test moves to `tests/unit/test_reliability_battery.py`.
- `tests/integration/test_requisition.py` (341 lines, 14 tests): `setup(tmp_path, responses)` writes `context.txt` and `config.yaml` and builds a real `Journal`; `test_committed_ticket_lint_snags_without_provider` builds real `Git(SubprocessExec())` with `commit_lock`; every test reads `SPECS = clutch/specs` through `Path(__file__)`, so the file reads repo files and must stay in `tests/integration/` and write nothing: put file content in the fake filesystem the stage context already takes (`ctx.fs`/`FakeFileSystem`), config through `load_config_text`, the journal in `FakeJournal`, git in `GitFake`. `ENV` is imported inline from the skipped `tests/integration/test_tickets.py` (not a hub): import it from `tests/cli_helpers.py` instead and do not edit `test_tickets.py`. If a code path under test reads real disk outside the `FileSystem` seam so a test cannot avoid writing a real file, stop as a premise failure naming the test and the path. Keep the path unchanged: `tests/integration/test_watchdog_activation.py` imports `TICKET` from it and needs no edit.
- `tests/integration/test_requisition_brief_check.py` (29 lines): writes `config.yaml` only to call `load_config`, and reads the requisition review prompt spec through `ROOT` (read only, not changed). Use `load_config_text(VALID, path=tmp_path / "config.yaml", cwd=tmp_path)` so it writes nothing and stays at `tests/integration/test_requisition_brief_check.py` (the unit file of the same name tests another thing and is not touched). `VALID` comes from `tests/config_helpers.py`.
- Importers: `tests/integration/test_release_publish.py` imports `test_release` (same ticket). Grep `from tests.integration.test_reject_queue`, `test_reject_reason_both_paths`, `test_release`, `test_release_publish`, `test_reliability_battery` in `tests/` and fence and fix any other hit.

Scope out:
- Every shared module named in Goal / Why, `tests/integration/conftest.py`, `clutch/`, `docs/`, and every test file not named here.

## Scope fence
- tests/integration/test_reject_queue.py
- tests/integration/test_reject_reason_both_paths.py
- tests/integration/test_release.py
- tests/integration/test_release_publish.py
- tests/integration/test_reliability_battery.py
- tests/integration/test_requisition.py
- tests/integration/test_requisition_brief_check.py
- tests/unit/test_reject_queue.py
- tests/unit/test_reject_reason_both_paths.py
- tests/integration/test_reject_reason_docs.py
- tests/unit/test_release_flow.py
- tests/unit/test_release_publish_flow.py
- tests/unit/test_reliability_battery.py
- tests/harness/reliability_battery.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_reject_queue.py tests/unit/test_reject_reason_both_paths.py tests/integration/test_reject_reason_docs.py tests/unit/test_release_flow.py tests/unit/test_release_publish_flow.py tests/unit/test_reliability_battery.py tests/integration/test_requisition.py tests/integration/test_requisition_brief_check.py` lists none of the restored files (not one left carrying the marker).
2. `./dev.py test tests/unit/test_reject_queue.py tests/unit/test_reject_reason_both_paths.py tests/integration/test_reject_reason_docs.py tests/unit/test_release_flow.py tests/unit/test_release_publish_flow.py tests/unit/test_reliability_battery.py tests/integration/test_requisition.py tests/integration/test_requisition_brief_check.py --durations=0` passes, and no restored test takes more than 1.0 s (not a slower test left in); the durations output is recorded in the run record (`run.md`).
3. `./dev.py test tests/integration/test_reject_queue.py tests/integration/test_reject_reason_both_paths.py tests/integration/test_release.py tests/integration/test_release_publish.py tests/integration/test_reliability_battery.py tests/integration/test_requisition.py tests/integration/test_requisition_brief_check.py --collect-only -q` on the base commit and `./dev.py test tests/unit/test_reject_queue.py tests/unit/test_reject_reason_both_paths.py tests/integration/test_reject_reason_docs.py tests/unit/test_release_flow.py tests/unit/test_release_publish_flow.py tests/unit/test_reliability_battery.py tests/integration/test_requisition.py tests/integration/test_requisition_brief_check.py --collect-only -q` on the branch report the same number of tests (not fewer), both counts recorded in `run.md`.
4. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.
5. `./dev.py test tests/unit/test_release_flow.py tests/unit/test_release_publish_flow.py` passes and still asserts the unstaged `modified` edit and the staged `staged` edit survive a release commit and a tag exists, not a bump that discards them.
6. `grep -nE "SubprocessExec\(|LocalFileSystem\(|commit_lock" tests/harness/reliability_battery.py tests/unit/test_reliability_battery.py` prints nothing.
7. `grep -n "ENV" tests/integration/test_requisition.py` shows `ENV` imported from `tests.cli_helpers`, and `grep -n test_tickets tests/integration/test_requisition.py` prints nothing.

## Verification
```
./dev.py test tests/unit/test_reject_queue.py tests/unit/test_reject_reason_both_paths.py tests/integration/test_reject_reason_docs.py tests/unit/test_release_flow.py tests/unit/test_release_publish_flow.py tests/unit/test_reliability_battery.py tests/integration/test_requisition.py tests/integration/test_requisition_brief_check.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, xfailed, or weakened, or the collected count of the batch differs from the base commit.
- A new `Fake*` class, stand-in class, or copy of a helper appears in a test file, or a shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`, any `conftest.py`) is edited.
- A restored integration test writes disk, starts a process, or runs git, or a restored test adds a sleep.
- A restored test takes more than 1.0 s in the `--durations=0` output.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files sharing fixtures stay together
