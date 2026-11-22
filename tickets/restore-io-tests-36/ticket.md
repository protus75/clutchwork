---
state: rejected
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
- tests/integration/test_tolerant_reader_callers.py
- tests/regress_context_binary.py
- tests/regress_context_directory.py
- tests/regress_new_skeleton_draft.py
- tests/integration/test_intake_scope.py
- tests/integration/test_shared_fakes_adoption.py

## On-demand
- tests/integration/test_tickets.py
- tests/integration/test_intake_keeps_draft.py
- tests/integration/test_requisition.py

## Goal / Why
`integration-io-guard` fails any integration test that writes disk, starts a process or runs git, and `integration-disk-io-skip` skipped 184 integration files; each now carries the line `pytestmark = pytest.mark.disk_io_skip` (from `disk-io-skip-per-file`). The owner wants them back fast and on the shared fakes. When this ticket is done, these two files run again with every test function and assertion they have today, and neither carries the skip line:

- `tests/integration/test_tickets.py` (79 tests)
- `tests/integration/test_tolerant_reader_callers.py` (2)

That is 81 tests at the base commit. The helper chain ending in `restore-helpers-misc` has already moved the names other files import from the hub files into `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py` (git on `tests/git_fake.py::GitFake`, no process, writes only under a passed `tmp_path`); `restore-helpers-misc` also provides the fake-backed equivalent of `commit_lock` that `test_tickets.py` imports from `tests/integration/test_git.py`. Those modules and `tests/git_fake.py` are created by dependencies and are not on main yet: read each in your worktree before use.

## Boundary contract
none
- reason: tests encoding an existing contract; production code, CLI, journal formats and documents are unchanged.

## Scope in / Scope out
Scope in. For each file delete its `pytestmark = pytest.mark.disk_io_skip` line, then rewrite per the authoring guide section "Unit and integration tests" (read-only context): git on `GitFake`, process on `FakeExec` or in-process `clutch.__main__.main([...])`, journal on `FakeJournal` unless the test's subject is journal persistence, time on `FakeClock` plus `tests.fakes.until`/`turn` and never a sleep, code taking the `clutch.seams.FileSystem` seam on `FakeFileSystem`. Reuse only `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and the seven `*_helpers.py` modules; define no new `Fake*` or stand-in class and copy no helper. Keep every test function, parametrization and assertion; delete, skip or weaken none.

- `test_tickets.py` (756 lines): the `repo` fixture builds a real repo with `Git(SubprocessExec())` (`git init`, `add`, `commit`), the `ENV` dict, a real `Journal` and `LocalFileSystem`; tests write ticket, evidence and symlink files under `tmp_path` and assert `intake` behavior that reads git status (staged changes outside ticket files, a gitignored evidence file, a ticket committed after status, commit-lock waiting with a patched `_commit_lock._sleep`, `git show HEAD:...` through `subprocess.run` in `test_new_skeleton_is_draft_until_intake`). Move git to `GitFake` (status, ls-files and commit behavior as `_run`/method overrides or `fake.calls`), the lock to the `restore-helpers-misc` equivalent, `Journal` to `FakeJournal`, and `subprocess.run(["git","show",...])` to the fake's recorded commit; keep `Clock` as the existing `FakeClock` alias. The tests write only under `tmp_path`, and `test_new_names_installed_authoring_guide` only builds the guide path string with `Path(clutch.__file__)`, so the file moves to `tests/unit/test_tickets.py` (no such unit file exists; `test_tickets_context.py` and `test_tickets_tolerant_reader.py` are different files). Importers, change only these import lines to `tests.unit.test_tickets`: `tests/integration/test_intake_keeps_draft.py` (`VALID, do_intake, repo, write`), `tests/integration/test_intake_scope.py` (`VALID, repo`), `tests/integration/test_requisition.py` (line 322, `ENV`), `tests/integration/test_shared_fakes_adoption.py` (`from tests.integration import ... test_tickets` and the `test_tickets.Clock is fakes.FakeClock` assertion keep passing from the new module), and the path strings and imports in `tests/regress_context_binary.py`, `tests/regress_context_directory.py` (`VALID, complete`) and `tests/regress_new_skeleton_draft.py` (`tests/integration/test_tickets.py` becomes `tests/unit/test_tickets.py`).
- `test_tolerant_reader_callers.py` (30 lines): reads `clutch/specs/*.md` and `clutch/{observe,retro,__main__}.py` through `Path(__file__).parents[2]` and writes nothing (`tmp_path` is only a `SimpleNamespace(root=...)`), so it stays at `tests/integration/test_tolerant_reader_callers.py`; delete only the skip line.

Scope out: hub files and helper modules, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, production code, other batches' files (batch 24 `restore-io-tests-24` owns `test_requisition.py`; only its line-322 import changes here). If `GitFake` plus the helper modules cannot express a git behavior `test_tickets.py` asserts (for example the staged-versus-committed status of a gitignored evidence file), stop as a premise failure naming that behavior and the test; never edit a shared module or add a stand-in.

## Scope fence
- tests/integration/test_tickets.py
- tests/integration/test_tolerant_reader_callers.py
- tests/integration/test_intake_keeps_draft.py
- tests/integration/test_intake_scope.py
- tests/integration/test_requisition.py
- tests/integration/test_shared_fakes_adoption.py
- tests/unit/test_tickets.py
- tests/regress_context_binary.py
- tests/regress_context_directory.py
- tests/regress_new_skeleton_draft.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_*.py tests/unit/test_*.py` lists neither `tests/unit/test_tickets.py` nor `tests/integration/test_tolerant_reader_callers.py`.
2. `./dev.py test tests/unit/test_tickets.py tests/integration/test_tolerant_reader_callers.py --durations=0` passes, and `run.md` records the durations output showing no test over 1.0 s.
3. `./dev.py test tests/unit/test_tickets.py tests/integration/test_tolerant_reader_callers.py --collect-only -q` collects 81 tests, equal to the base-commit count of the two original files (79 and 2), both recorded in `run.md`.
4. `grep -rn "tests.integration.test_tickets\|tests/integration/test_tickets.py" tests` prints nothing, and `./dev.py test tests/integration/test_shared_fakes_adoption.py` passes (it still asserts the `Clock is fakes.FakeClock` identity from the moved module).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0.

## Verification
```
./dev.py test tests/unit/test_tickets.py tests/integration/test_tolerant_reader_callers.py --durations=0
./dev.py test tests/integration/test_shared_fakes_adoption.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, parametrization-reduced or weakened.
- A new `Fake*` or stand-in class, or a copied helper, appears in a test file.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, a `*_helpers.py` module) is edited.
- A restored integration test writes disk, starts a process or runs git, or any test adds a sleep.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines (786 here) so files sharing fixtures stay together.
