---
state: rejected
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc

## Context
- tests/integration/test_hot_paths_snapshot.py
- tests/integration/test_image_candidates_select.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_host_mechanical.py
- tests/integration/test_hostfiles.py

## Goal / Why
`integration-disk-io-skip` turned off 184 integration test files because they write disk, start processes, or run git, and the owner wants them restored in batches that are fast and reuse the shared fakes. This ticket restores 4 of them: when it is done, none of the files listed under Scope in carries `pytestmark = pytest.mark.disk_io_skip`, every test in them runs (not skipped), each restored test finishes in at most 1.0 s, and none of them writes disk outside `tmp_path`, starts a process, or runs real git. The files were rewritten onto `tests/fakes.py`, `tests/git_fake.py` and the shared helper modules the dependencies create, so no per-file fake or copied helper remains.

Base-commit collected counts (`uv run pytest --collect-only -q`, recorded again in `run.md`): test_host_mechanical: 47, test_hostfiles: 418, test_hot_paths_snapshot: 1, test_image_candidates_select: 7; total 473.

## Boundary contract
none
- reason: tests encoding an existing contract; only test files change, and every test keeps its name and the behavior it asserts

## Scope in / Scope out
Scope in (per file: what it touches today, what it moves to, final path):
- `tests/integration/test_host_mechanical.py` (29 tests, 619 lines): real git through the `ctx` fixture (`rev_parse`, `diff_names`, `status_porcelain`, `_run log/show` on autofix commits), a worktree where scripted `ctx.exec_` replacements write `results.json` / `coverage.json` / fixed files, and `config.yaml` rewrites under `tmp_path`. Moves to `GitFake` (the `ctx` fixture and `scripted`/`ready`/`host`/`approve`/`commit` come from `tests/daemon_helpers.py` after `restore-helpers-daemon`; `SECRET` from `tests/stages_helpers.py`; `list_captures`/`read_capture` stay in `tests/spool_captures.py`). Final path: `tests/unit/test_host_mechanical.py` (it still writes files under `tmp_path`).
- `tests/integration/test_hostfiles.py` (19 test functions, 418 collected, 482 lines): the pure tests (`test_core_template_*`, `test_core_golden_uses_branch_template`, `test_core_drift_*`, `test_core_remainder_*`, `test_core_classifier_is_pure`), the tests that read the repo's two conduct files at the root (`test_core_first_adoption_preserves_project_bytes`, whose parametrize list reads them at collection, and `test_core_activation_first_adoption`) and the `tmp_path` + `RecordingFS` tests (`test_core_refresh_preserves_remainder`, `test_core_marker_corruption_refuses_without_writes`, `test_core_render_is_byte_idempotent`) are rewritten onto `FakeFileSystem` (paths such as `Path("/repo/CLAUDE.md")`, assertions on its `files`) so they write nothing and stay in `tests/integration/test_hostfiles.py`; none of them keeps `tmp_path`, `RecordingFS`, `Git(SubprocessExec())`, or a `repo`/`root`/`context` fixture. The tests that need a worktree with git (`test_core_drift_reachable_from_production_gates`, `test_committed_core_preserves_raw_bytes`, `test_committed_core_template_extraction_refuses`, `test_stale_core_reads_head`) use the `root`/`repo`/`context` fixtures from `tests/cli_helpers.py` / `tests/config_helpers.py` with `GitFake`, write files under `tmp_path`, and move to `tests/unit/test_hostfiles_flow.py` (`tests/unit/test_hostfiles.py` already exists). `RecordingFS` stays defined in `tests/integration/test_hostfiles.py` unchanged only because the still-skipped `tests/integration/test_cli.py` imports it lazily (two places); no restored test uses it. The `if __name__ == "__main__"` golden regenerator stays beside `GOLDEN` in `tests/integration/test_hostfiles.py`.
- `tests/integration/test_hot_paths_snapshot.py` (1 test, 35 lines): `rig(tmp_path)` from the retro tests, `commit_ticket`/`confirmed` from `test_drain.py`, `ENV` from `test_cli.py`, journal files and real git under `tmp_path`. Moves to the shared helpers (`tests/misc_helpers.py`, `tests/drain_helpers.py`, `tests/cli_helpers.py`) and `GitFake`. Final path: `tests/unit/test_hot_paths_snapshot.py`.
- `tests/integration/test_image_candidates_select.py` (5 tests, 7 collected, 184 lines): a local `rig` that builds `Driver`, `Git(SubprocessExec())`, `LocalFileSystem` and runs `git add/commit/worktree add/rev-parse/log/diff` through the stages `git()` helper, plus PIL/numpy image files under `tmp_path`. Replace the local git rig with `GitFake` overrides (branch head, `log -1` subject, `diff_names`) and the stages helpers (`repo`, `author`, `git`, `ENV`, `SPECS`, `STEM` from `tests/stages_helpers.py`); `commit_lock` is not needed. `SPECS` points at the repo's `clutch/specs` directory today; a unit test may not read it, so use whatever specs source `tests/stages_helpers.py` provides for the unit suite (a copy under `tmp_path` or an in-memory spec set); if that module still returns the repo path, stop as a premise failure naming it. Final path: `tests/unit/test_image_candidates_select.py`.

Rewrite rules for every file in this batch (from the owner requirements: restored tests are FAST and REUSE shared fixtures and fakes):
- Delete the `pytestmark = pytest.mark.disk_io_skip` line (and `import pytest` only if nothing else uses it).
- git -> `tests/git_fake.py::GitFake`; processes -> in-process `main([...])` or `FakeExec`; journal -> `FakeJournal` unless the test's subject is journal persistence; time -> `FakeClock` with `fakes.until` / `fakes.turn`, never a sleep; code that takes the `clutch.seams.FileSystem` seam -> `FakeFileSystem`.
- Reuse only shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. Those modules are created by the tickets this one depends on (`restore-helpers-misc` ends the chain that creates the helper modules); read each in the worktree before using it. Never define a new `Fake*` or stand-in class, and never copy a helper into a test file. A stand-in class or helper that a file already defines locally is replaced by the shared one, not kept. If a shared fake lacks a behavior a test needs, stop the run as a premise failure that names the missing behavior; never edit a shared module.
- Keep every test function and the behavior it asserts: no test deleted, skipped, or weakened. Where a real-git assertion (a log subject, a diff name list, a rev-parse) becomes an assertion on `GitFake` overrides and `fake.calls`, it asserts the same fact.
- Placement follows the host authoring guide's "Unit and integration tests" section (also in Context): a file whose rewritten tests still write real files (only under `tmp_path`) lives under tests/unit/; a file that reads repo files (anchored on `Path(__file__)`) and writes nothing stays under tests/integration/; a file needing both is split and each path is named below. Each test keeps its name, so the total collected count across a split equals the base count.
- Where a test drives production code that builds its own git (`main`, `run_drain`, `runner.bind`), the `GitFake` reaches it through the checkout/ctx builders in the helper modules (they take a git argument) or by `monkeypatch.setattr` of the `Git` name in the production module that constructs it; a private `Git._commit` / `Git._run` monkeypatch is re-expressed as an override of the matching `GitFake` member. If neither route can carry a `GitFake` into that code, or a test needs genuine git semantics (conflict, rebase, index refresh, worktree contents) that `GitFake` does not model, the run stops as a premise failure naming the test and the construction site or behavior.
- Any other test file that imports a name from a file this ticket moves gets only its import line changed (fenced below when such a file exists).

Scope out:
- Any file outside the fence, every shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, the `tests/*_helpers.py` modules, both `conftest.py` files), `REAL_IO_TESTS`, and `clutch/`.
- Restoring any other skipped file: those belong to the other `restore-io-tests-NN` tickets.

## Scope fence
- tests/integration/test_host_mechanical.py
- tests/unit/test_host_mechanical.py
- tests/integration/test_hostfiles.py
- tests/unit/test_hostfiles_flow.py
- tests/integration/test_hot_paths_snapshot.py
- tests/unit/test_hot_paths_snapshot.py
- tests/integration/test_image_candidates_select.py
- tests/unit/test_image_candidates_select.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip"` over every restored path (new location, or the same path when the file stays) lists none of them, and the same grep at the base commit over the original integration paths lists all of them (both outputs recorded in `run.md`).
2. `./dev.py test tests/integration/test_hostfiles.py tests/unit/test_host_mechanical.py tests/unit/test_hostfiles_flow.py tests/unit/test_hot_paths_snapshot.py tests/unit/test_image_candidates_select.py --durations=0` passes with no test skipped and no restored test taking more than 1.0 s; the `--durations=0` output is recorded in `run.md`.
3. `./dev.py test tests/integration/test_hostfiles.py tests/unit/test_host_mechanical.py tests/unit/test_hostfiles_flow.py tests/unit/test_hot_paths_snapshot.py tests/unit/test_image_candidates_select.py --collect-only -q` collects exactly 473 tests across the final paths, equal to the base-commit count of 473 from the original paths (not fewer because a test was dropped or a split lost one); both counts are recorded in `run.md`.
4. `./dev.py test tests/unit/test_hostfiles_flow.py tests/integration/test_hostfiles.py` passes and `grep -c RecordingFS tests/integration/test_hostfiles.py tests/unit/test_hostfiles_flow.py` shows the class defined once (in the integration file) and used by no restored test (not defined in both).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file and no other test regressed.

## Verification
```
./dev.py test tests/integration/test_hostfiles.py tests/unit/test_host_mechanical.py tests/unit/test_hostfiles_flow.py tests/unit/test_hot_paths_snapshot.py tests/unit/test_image_candidates_select.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, `xfail`ed, or weakened (an assertion dropped or loosened) to make a file pass.
- A new `Fake*` or stand-in class, or a copy of a helper, appears in a test file, or a shared module is edited.
- A restored integration test writes disk, starts a process, runs git, or opens an on-disk database; or a restored unit test reads or writes a repo file.
- A sleep or real wall-clock wait is added.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files that share fixtures stay together; splitting it would put importers and importees in different tickets
