---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-26
- restore-io-tests-36

## Context
- tests/integration/test_implement_related_files_prompt.py
- tests/integration/test_inbox.py
- tests/integration/test_index_cli.py
- tests/integration/test_index_extensions.py
- tests/integration/test_index_neighbors_fulltext.py
- tests/integration/test_intake_keeps_draft.py
- tests/integration/test_intake_scope.py
- tests/integration/test_issue_verb.py
- tests/unit/test_index_build.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## Goal / Why
`integration-disk-io-skip` turned off 184 integration test files because they write disk, start processes, or run git, and the owner wants them restored in batches that are fast and reuse the shared fakes. This ticket restores 8 of them: when it is done, none of the files listed under Scope in carries `pytestmark = pytest.mark.disk_io_skip`, every test in them runs (not skipped), each restored test finishes in at most 1.0 s, and none of them writes disk outside `tmp_path`, starts a process, or runs real git. The files were rewritten onto `tests/fakes.py`, `tests/git_fake.py` and the shared helper modules the dependencies create, so no per-file fake or copied helper remains.

Base-commit collected counts (`uv run pytest --collect-only -q`, recorded again in `run.md`): test_implement_related_files_prompt: 3, test_inbox: 10, test_index_cli: 1, test_index_extensions: 2, test_index_neighbors_fulltext: 1, test_intake_keeps_draft: 5, test_intake_scope: 5, test_issue_verb: 2; total 29.

The importers of `arrival` and `raw_report` (`test_author.py`, `test_box.py`, `test_drain.py`, `test_serve_lifecycle.py`, `test_triage.py`) are already repointed to `tests/misc_helpers.py` by `restore-helpers-misc`, so they are not fenced here.

## Boundary contract
none
- reason: tests encoding an existing contract; only test files change, and every test keeps its name and the behavior it asserts

## Scope in / Scope out
Scope in (per file: what it touches today, what it moves to, final path):
- `tests/integration/test_implement_related_files_prompt.py` (3 tests): `test_spec_and_single_call` only reads repo files (the implement prompt spec and `clutch/stages.py`) and stays in `tests/integration/test_implement_related_files_prompt.py`; `test_rendered_block` and `test_implement_skips_index_when_no_room` write `tickets/sample/ticket.md` under `tmp_path` (production `implement_stage` reads it with `Path.read_text`) and move to `tests/unit/test_implement_related_files_prompt.py`. `test_rendered_block` also reads the implement prompt spec from the repo; a unit test may not, so it must obtain the spec through the production `stages._spec` loader or an injected spec; if no fake route exists that avoids both a repo read and a real ticket file, stop as a premise failure naming that test.
- `tests/integration/test_inbox.py` (5 tests, 10 collected): `tmp_path` report/evidence files, `symlink_to`, a restarted `Journal` and `Box` on `LocalFileSystem`, and `test_report_replay_to_regression` which builds a host with `scaffold.copy_host` (reads `hosts/fixture` in the repo), real `Git(SubprocessExec())`, runs `replay.py` through `SubprocessExec`, and runs the real `check` stage, which executes the regression reproducer as a process on the branch head and on the merge base with different results. Moves to `FakeFileSystem`/`FakeJournal` where persistence is not the subject (the custody and retry tests keep real `Journal`/`LocalFileSystem` under `tmp_path`), and `GitFake` for the replay test. For that one test: the host is built in memory (`FakeFileSystem`) or from a `tmp_path` copy supplied by a shared helper, never from a repo read in a unit test, and the two reproducer runs go through `FakeExec`; because `FakeExec` returns one fixed result, if no shared fake can give the head run `pass` and the base run `defect`, stop as a premise failure naming that behavior. `test_report_evidence_bounds` writes `tmp_path.parent / "outside"`: rewrite it so the evidence root is a subdirectory of `tmp_path` and `outside` sits beside it inside `tmp_path`, keeping every assertion; `Clock`, `commit_lock` equivalents, `context` come from `tests/drain_helpers.py`, `tests/misc_helpers.py`, `tests/config_helpers.py`. `arrival` and `raw_report` are already moved to `tests/misc_helpers.py` by `restore-helpers-misc`. Final path: `tests/unit/test_inbox.py`.
- `tests/integration/test_index_cli.py` (1 test): `setup_repo` from `test_git_tree_id.py` builds a real git repo, then `main(["index", "build"])` writes an on-disk DuckDB file `index.duckdb` and a `Lockfile` under `tmp_path`. Replace the real repo with `GitFake` (tracked file list) and `FakeClock`; the DuckDB file under `tmp_path` stays (this test's subject). Final path: `tests/unit/test_index_cli.py`. If `main` has no seam to receive a `GitFake`, stop as a premise failure naming it.
- `tests/integration/test_index_extensions.py` (2 tests): `test_index_source_uses_seams` only reads `clutch/index.py` (stays in `tests/integration/test_index_extensions.py`); `test_real_extensions_reopened` writes an on-disk DuckDB file and loads the real `vss`/`fts` extensions (it already skips itself when they are unavailable offline). It moves to `tests/unit/test_index_extensions.py` keeping that existing availability skip unchanged. `RealCreator` is the one local class kept: it wraps the real `default_creator` to record calls and is the subject of that test; it is not replaced. `Exec`, `rig`, `rows`, `run` keep coming from the existing non-skipped `tests/unit/test_index_build.py`; do not add another copy.
- `tests/integration/test_index_neighbors_fulltext.py` (1 test): on-disk DuckDB fulltext/embedding index under `tmp_path`, with a local `Vectors(Exec)` stand-in that answers by reading `stdin_path`. `Vectors` answers by reading `stdin_path`, and the shared `FakeExec` returns one fixed result; replace `Vectors` with the existing `Exec` from `tests/unit/test_index_build.py` and its fixed reply sequence when the embed call order is deterministic and gives the same assertions; otherwise stop as a premise failure naming the missing stdin-keyed reply. Same availability skip as today. Final path: `tests/unit/test_index_neighbors_fulltext.py`.
- `tests/integration/test_intake_keeps_draft.py` (3 tests, 5 collected): `test_author_and_drafts_guidance` only reads repo spec and doc files and stays in `tests/integration/test_intake_keeps_draft.py`; `test_intake_preserves_authored_state` and `test_drain_waits_for_human_confirmation` run real git through the `repo` fixture from `test_tickets.py` (batch 36) and the `root`/`pause_checkout` helpers; they move to `GitFake` and `tests/drain_helpers.py` / `tests/cli_helpers.py` (the `main`/`drain` git seam is the general rule above) into `tests/unit/test_intake_keeps_draft.py`. The `repo`, `VALID`, `do_intake`, `write` names come from wherever `restore-io-tests-36` leaves `test_tickets.py`'s helpers; read its import lines in the worktree.
- `tests/integration/test_intake_scope.py` (2 tests, 5 collected): real git `add`/`diff --cached`/`show` through the `repo` fixture from `test_tickets.py` and `make_root`, `main(...)` with `FakeLLM`, and a `reply` helper from `test_review_command.py` (batch 26). Moves to `GitFake` and the shared helpers. Final path: `tests/unit/test_intake_scope_flow.py` (`tests/unit/test_intake_scope.py` already exists).
- `tests/integration/test_issue_verb.py` (2 tests): writes `body.md` / `config.yaml` under `tmp_path` and calls `main` in-process with `cwd=tmp_path`; no git or process. Final path: `tests/unit/test_issue_verb.py` (no other change; `CONFIG` comes from `tests/cli_helpers.py`).

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
- tests/integration/test_implement_related_files_prompt.py
- tests/unit/test_implement_related_files_prompt.py
- tests/integration/test_inbox.py
- tests/unit/test_inbox.py
- tests/integration/test_index_cli.py
- tests/unit/test_index_cli.py
- tests/integration/test_index_extensions.py
- tests/unit/test_index_extensions.py
- tests/integration/test_index_neighbors_fulltext.py
- tests/unit/test_index_neighbors_fulltext.py
- tests/integration/test_intake_keeps_draft.py
- tests/unit/test_intake_keeps_draft.py
- tests/integration/test_intake_scope.py
- tests/unit/test_intake_scope_flow.py
- tests/integration/test_issue_verb.py
- tests/unit/test_issue_verb.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip"` over every restored path (new location, or the same path when the file stays) lists none of them, and the same grep at the base commit over the original integration paths lists all of them (both outputs recorded in `run.md`).
2. `./dev.py test tests/integration/test_implement_related_files_prompt.py tests/integration/test_index_extensions.py tests/integration/test_intake_keeps_draft.py tests/unit/test_implement_related_files_prompt.py tests/unit/test_inbox.py tests/unit/test_index_cli.py tests/unit/test_index_extensions.py tests/unit/test_index_neighbors_fulltext.py tests/unit/test_intake_keeps_draft.py tests/unit/test_intake_scope_flow.py tests/unit/test_issue_verb.py --durations=0` passes with no test skipped and no restored test taking more than 1.0 s; the `--durations=0` output is recorded in `run.md`.
3. `./dev.py test tests/integration/test_implement_related_files_prompt.py tests/integration/test_index_extensions.py tests/integration/test_intake_keeps_draft.py tests/unit/test_implement_related_files_prompt.py tests/unit/test_inbox.py tests/unit/test_index_cli.py tests/unit/test_index_extensions.py tests/unit/test_index_neighbors_fulltext.py tests/unit/test_intake_keeps_draft.py tests/unit/test_intake_scope_flow.py tests/unit/test_issue_verb.py --collect-only -q` collects exactly 29 tests across the final paths, equal to the base-commit count of 29 from the original paths (not fewer because a test was dropped or a split lost one); both counts are recorded in `run.md`.
4. `./dev.py test tests/integration/test_implement_related_files_prompt.py tests/integration/test_index_extensions.py tests/integration/test_intake_keeps_draft.py` passes with every test in those three files reading only repo files (`grep -n "tmp_path" ` over them lists no use), not writing disk.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file and no other test regressed.

## Verification
```
./dev.py test tests/integration/test_implement_related_files_prompt.py tests/integration/test_index_extensions.py tests/integration/test_intake_keeps_draft.py tests/unit/test_implement_related_files_prompt.py tests/unit/test_inbox.py tests/unit/test_index_cli.py tests/unit/test_index_extensions.py tests/unit/test_index_neighbors_fulltext.py tests/unit/test_intake_keeps_draft.py tests/unit/test_intake_scope_flow.py tests/unit/test_issue_verb.py --durations=0
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
