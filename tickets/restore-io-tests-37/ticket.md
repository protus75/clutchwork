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
- tests/integration/test_vocabularies.py
- tests/integration/test_vscode_command_not_found.py
- tests/vscode_command_not_found.js

## On-demand
- tests/integration/test_triage.py

## Goal / Why
`integration-io-guard` fails any integration test that writes disk, starts a process or runs git, and `integration-disk-io-skip` skipped 184 integration files; each now carries the line `pytestmark = pytest.mark.disk_io_skip` (from `disk-io-skip-per-file`). The owner wants them back fast and on the shared fakes. When this ticket is done, these three files run again with every test function and assertion they have today, and none carries the skip line:

- `tests/integration/test_triage.py` (24 tests)
- `tests/integration/test_vocabularies.py` (10)
- `tests/integration/test_vscode_command_not_found.py` (2)

That is 36 tests at the base commit. The helper chain ending in `restore-helpers-misc` has already moved the names other files import from the hub files into `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py` (git on `tests/git_fake.py::GitFake`, no process, writes only under a passed `tmp_path`). `restore-helpers-loop` moved the names other files import from `test_triage.py` (`root_with_box`, `enqueue`, `reply`, `run`, `author_reply`, `requisition_reply`, `escape_report`, `escape_rig`) into `tests/loop_helpers.py`, so no other file imports from `test_triage.py` any more. Those modules and `tests/git_fake.py` are created by dependencies and are not on main yet: read each in your worktree before use.

## Boundary contract
none
- reason: tests encoding an existing contract; production code, CLI, journal formats and documents are unchanged.

## Scope in / Scope out
Scope in. For each file delete its `pytestmark = pytest.mark.disk_io_skip` line, then rewrite per the authoring guide section "Unit and integration tests" (read-only context): git on `GitFake`, process on `FakeExec` or in-process `clutch.__main__.main([...])`, journal on `FakeJournal` unless the test's subject is journal persistence, time on `FakeClock` plus `tests.fakes.until`/`turn` and never a sleep, code taking the `clutch.seams.FileSystem` seam on `FakeFileSystem`. Reuse only `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and the seven `*_helpers.py` modules; define no new `Fake*` or stand-in class and copy no helper. Keep every test function, parametrization and assertion; delete, skip or weaken none.

- `test_triage.py` (693 lines): tests call `main(["box", "triage"], cwd=root, env=ENV, clock=Clock())` in-process with `FakeLLM`, on a repo from `make_root` (real git), a `Box` on `LocalFileSystem`, a real `Journal`, and assert `git_out(root, "log"|"rev-parse"|"show"|"status"|"add"|"commit" ...)` results (decision records committed once, uncommitted records committed before resolution, `tickets/broken` absent from `status --porcelain`, escape attribution from the first-parent squash trailers); `test_lock_contention_exits_two_without_pass` takes a real `Lockfile`. Move git to `GitFake` (override methods or `_run` and assert `fake.calls`, keeping each committed-once and commit-subject assertion), `Box` to `FakeFileSystem`, `Journal` to `FakeJournal`; keep the `Lockfile` under `tmp_path`. Its imports from `test_cli`, `test_drain` (`ENV`, `git_out`, `Clock`, `commit_ticket`, `confirmed`, `make_root`), `spool_captures.read_capture`, `test_author` and `test_inbox` come from the helper modules that now own them. Split: `test_triage_spec_places_reopen_condition_in_json` reads the triage prompt spec (a file under `clutch/specs/`) through `Path(__file__).parents[2]` and writes nothing, so it stays as the only test in a new `tests/integration/test_triage_spec.py`; the other 23 tests write files under `tmp_path` and move to `tests/unit/test_triage.py` (no such unit file exists). `tests/regress_triage_author_invoked_boundary.py` runs `tests/integration/test_triage.py -k stale_author_invoked`: change only that path string to `tests/unit/test_triage.py`.
- `test_vocabularies.py` (147 lines): `test_every_engine_signal_name_is_listed` parses `clutch/`, `eval/` and `tests/harness/` source through `Path(__file__).parents[2]` and writes nothing; `test_dispatch_vocabulary_is_closed` is in-memory; `test_unknown_signal_name_is_refused_at_append` (6 params) and `test_listed_signal_names_are_accepted` (2 params) build a real `Journal(tmp_path, ...)` and read `journal.dir` (their subject is the journal append refusal, so the real `Journal` stays, on `tmp_path`). Split: the first two (2 tests, with `_engine_signal_names` and its helpers) stay at `tests/integration/test_vocabularies.py`; the last two (8 tests) move to `tests/unit/test_vocabularies.py`.
- `test_vscode_command_not_found.py` (38 lines): runs `node tests/vscode_command_not_found.js` with `subprocess.run`, reads that repo script and makes `tickets/` under `tmp_path`; the real child process is the subject and nothing fakes `node`. It stays at `tests/integration/test_vscode_command_not_found.py`, and its name is added to `REAL_IO_TESTS` in `tests/integration/conftest.py`; delete the skip line and change nothing else in the file.

Scope out: hub files and helper modules, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, production code, other batches' files. If `GitFake` plus the helper modules cannot express a git behavior a triage test asserts (for example the committed-once check of a decision record or the squash-trailer escape attribution), stop as a premise failure naming that behavior and the test; never edit a shared module or add a stand-in.

## Scope fence
- tests/integration/test_triage.py
- tests/integration/test_triage_spec.py
- tests/integration/test_vocabularies.py
- tests/integration/test_vscode_command_not_found.py
- tests/integration/conftest.py
- tests/unit/test_triage.py
- tests/unit/test_vocabularies.py
- tests/regress_triage_author_invoked_boundary.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_*.py tests/unit/test_*.py` lists none of `test_triage`, `test_triage_spec`, `test_vocabularies`, `test_vscode_command_not_found`, and `tests/integration/conftest.py` adds only `test_vscode_command_not_found.py` to `REAL_IO_TESTS`.
2. `./dev.py test tests/unit/test_triage.py tests/integration/test_triage_spec.py tests/unit/test_vocabularies.py tests/integration/test_vocabularies.py tests/integration/test_vscode_command_not_found.py --durations=0` passes, and `run.md` records the durations output showing no test over 1.0 s except the two in `test_vscode_command_not_found.py` (a real `node` process), whose times are recorded.
3. `./dev.py test <the same paths> --collect-only -q` collects 36 tests, equal to the base-commit count of the three original files (24, 10, 2), both recorded in `run.md`; the splits are 1 + 23 (triage) and 2 + 8 (vocabularies).
4. `grep -rn "test_triage" tests/regress_triage_author_invoked_boundary.py` shows only `tests/unit/test_triage.py`, and `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0.

## Verification
```
./dev.py test tests/unit/test_triage.py tests/integration/test_triage_spec.py tests/unit/test_vocabularies.py tests/integration/test_vocabularies.py tests/integration/test_vscode_command_not_found.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, parametrization-reduced or weakened.
- A new `Fake*` or stand-in class, or a copied helper, appears in a test file.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, a `*_helpers.py` module) is edited.
- A restored non-allowlisted integration test writes disk, starts a process or runs git, or any test adds a sleep.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines (878 here) so files sharing fixtures stay together.
