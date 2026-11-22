---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-11

## Context
- tests/integration/test_ladder.py
- tests/integration/test_lint_verb.py
- tests/integration/test_llm_effect.py
- tests/integration/test_main_verb_groups.py
- tests/integration/test_menu_verb_parity.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## Goal / Why
`integration-disk-io-skip` turned off 184 integration test files because they write disk, start processes, or run git, and the owner wants them restored in batches that are fast and reuse the shared fakes. This ticket restores 5 of them: when it is done, none of the files listed under Scope in carries `pytestmark = pytest.mark.disk_io_skip`, every test in them runs (not skipped), each restored test finishes in at most 1.0 s, and none of them writes disk outside `tmp_path`, starts a process, or runs real git. The files were rewritten onto `tests/fakes.py`, `tests/git_fake.py` and the shared helper modules the dependencies create, so no per-file fake or copied helper remains.

Base-commit collected counts (`uv run pytest --collect-only -q`, recorded again in `run.md`): test_ladder: 16, test_lint_verb: 21, test_llm_effect: 10, test_main_verb_groups: 9, test_menu_verb_parity: 21; total 77.

## Boundary contract
none
- reason: tests encoding an existing contract; only test files change, and every test keeps its name and the behavior it asserts

## Scope in / Scope out
Scope in (per file: what it touches today, what it moves to, final path):
- `tests/integration/test_ladder.py` (10 tests, 16 collected): drains a scripted repo through `run_drain` with `FakeLLM`, journal files, and `git(repo, "rev-parse"/"status --porcelain")` through the stages helper; the `repo`/`clock`/`author` fixtures come from `test_terminal.py` (loop helper). Moves to `GitFake` and `tests/loop_helpers.py` / `tests/stages_helpers.py`; the porcelain-empty asserts become `GitFake` overrides, and `test_split_dispatches_reviewed_rework`'s `clutch.git.Git._commit` monkeypatch becomes an override of the `commit` member. Final path: `tests/unit/test_ladder.py`.
- `tests/integration/test_lint_verb.py` (14 tests, 21 collected): `root` fixture files under `tmp_path`, a local `git()` that runs real `Git(SubprocessExec())`, a `snapshot()` that reads file bytes and mtimes, and `test_lint_is_read_only_and_lock_free`, which spawns a second process with `multiprocessing` to hold a `Lockfile`. Real files stay under `tmp_path`; the local `git()` becomes `GitFake`; the spawned process is replaced by holding the `Lockfile` in the test process (an `flock` held on another open file description still conflicts), and the stale-index-stat part of that test becomes an assertion that lint made no mutating or index-refreshing git call in `fake.calls` (record in `run.md` that real index refresh is no longer observable). Final path: `tests/unit/test_lint_verb.py`. Importers get only import-line changes: `tests/integration/test_route_kinds_judge_lint.py` (`lint`) repoints to the new path, and the carried reproducer `tests/regress_lint_worktree_journal.py` (not collected by pytest, real git by design) imports `git` from this file: it now defines that two-line real `Git(SubprocessExec())` runner itself, because the moved `git` becomes a fake.
- `tests/integration/test_llm_effect.py` (10 tests, 204 lines): journal and `config.yaml` under `tmp_path`, a local `FakeSleep`, `Stub`, `Echo`, `echo_json`, `build`, `clock` that duplicate `test_driver.py`'s. Journal persistence is the subject, so the journal stays a real file under `tmp_path`; `FakeSleep` (a sleep callable that blocks until released, which `Driver.from_config` requires) has no counterpart in `tests/fakes.py`: use the sleep stand-in that `test_driver.py`'s helpers export after `restore-io-tests-11` if one exists, otherwise keep this one existing definition unchanged and state why in `run.md` (no new class is added); `Stub`/`Echo`/`echo_json`/`build` are imported from wherever `restore-io-tests-11` leaves `test_driver.py`'s helpers when behavior is identical (if a local one differs, keep that one definition and say why in `run.md`). Final path: `tests/unit/test_llm_effect.py`.
- `tests/integration/test_main_verb_groups.py` (5 test functions, 9 collected): the three `source_tree` test functions (7 collected: `test_shared_call_has_one_owner` has 5 cases) only parse `clutch/__main__.py` by `entry.__file__` and stay in `tests/integration/test_main_verb_groups.py`; `test_prompt_box_refusal_is_caught` and `test_dismiss_names_holder_and_preserves_lock` use the cli `root` fixture and a real `Lockfile` under `tmp_path` and move to `tests/unit/test_main_verb_groups_flow.py` (`tests/unit/test_main_verb_groups.py` exists).
- `tests/integration/test_menu_verb_parity.py` (3 tests, 21 collected): `make_root`, real `Git(SubprocessExec())`, `SubprocessExec()` inside `observe.Context`, `LocalFileSystem` and files written under `tmp_path`. Git becomes `GitFake`, exec becomes `FakeExec`, the root from `tests/drain_helpers.py`; written ticket files stay under `tmp_path`. Final path: `tests/unit/test_menu_verb_parity.py`.

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
- tests/integration/test_ladder.py
- tests/unit/test_ladder.py
- tests/integration/test_lint_verb.py
- tests/unit/test_lint_verb.py
- tests/integration/test_route_kinds_judge_lint.py
- tests/regress_lint_worktree_journal.py
- tests/integration/test_llm_effect.py
- tests/unit/test_llm_effect.py
- tests/integration/test_main_verb_groups.py
- tests/unit/test_main_verb_groups_flow.py
- tests/integration/test_menu_verb_parity.py
- tests/unit/test_menu_verb_parity.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip"` over every restored path (new location, or the same path when the file stays) lists none of them, and the same grep at the base commit over the original integration paths lists all of them (both outputs recorded in `run.md`).
2. `./dev.py test tests/integration/test_main_verb_groups.py tests/unit/test_ladder.py tests/unit/test_lint_verb.py tests/unit/test_llm_effect.py tests/unit/test_main_verb_groups_flow.py tests/unit/test_menu_verb_parity.py --durations=0` passes with no test skipped and no restored test taking more than 1.0 s; the `--durations=0` output is recorded in `run.md`.
3. `./dev.py test tests/integration/test_main_verb_groups.py tests/unit/test_ladder.py tests/unit/test_lint_verb.py tests/unit/test_llm_effect.py tests/unit/test_main_verb_groups_flow.py tests/unit/test_menu_verb_parity.py --collect-only -q` collects exactly 77 tests across the final paths, equal to the base-commit count of 77 from the original paths (not fewer because a test was dropped or a split lost one); both counts are recorded in `run.md`.
4. `uv run python tests/regress_lint_worktree_journal.py` prints `{"regression_result": "pass"}` and exits 0 (it still runs after `git` left `test_lint_verb`), and `grep -rn "tests.integration.test_lint_verb" tests` lists nothing (not a stale import).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file and no other test regressed.

## Verification
```
./dev.py test tests/integration/test_main_verb_groups.py tests/unit/test_ladder.py tests/unit/test_lint_verb.py tests/unit/test_llm_effect.py tests/unit/test_main_verb_groups_flow.py tests/unit/test_menu_verb_parity.py --durations=0
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
