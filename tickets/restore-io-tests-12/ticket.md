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
- tests/integration/test_effects.py
- tests/integration/test_evidence_captures_verb.py
- tests/integration/test_evidence_envelope.py
- tests/integration/test_evidence_verbs.py
- tests/integration/test_extension_draw_failure.py
- tests/integration/test_fault_injection.py

## On-demand
- tests/integration/test_eval_harness.py

## Goal / Why
`integration-disk-io-skip` turned off 7 integration test files in this batch (1141 lines in all) because they write disk, start processes or run git. `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that does. When this ticket is done each file below runs again: its `pytestmark = pytest.mark.disk_io_skip` line is gone and its tests pass under the rules in the host authoring guide's `Unit and integration tests` section (listed in Context), driven by the shared fakes in `tests/fakes.py` and `tests/git_fake.py::GitFake` and by the shared helper modules the chain behind `restore-helpers-misc` created. Owner requirements: every restored test is fast (no restored test over 1.0 s) and reuses shared fixtures and fakes; no per-file fake class or helper copy.

`test_control.py` and `test_kill_signal_journal.py` import `Crash` and `FakeClock` from `tests.integration.test_effects`: `Crash` now comes from `tests.unit.test_effects` and `FakeClock` from `tests.fakes`; `test_shared_fakes_adoption.py` imports the module `test_effects` and asserts `test_effects.FakeExec is fakes.FakeExec`, so it now imports `test_effects` from `tests.unit` (only that name). Grep for the exact current import text first: `restore-helpers-misc` may already have rewritten the `test_kill_signal_journal.py` line.

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
- `tests/integration/test_effects.py` (206 lines) -> `tests/unit/test_effects.py`. 11 tests of `Effects` over a real `Journal(tmp_path, FakeClock())` that is re-opened after a `Crash`; replay across a reopened journal is the tested contract, so the journal stays real under `tmp_path`. Its local `FakeClock` (ticks one second per call) and `FakeFS` are per-file stand-ins: replace them with `tests/fakes.py::FakeClock` and `FakeFileSystem` (assert `fs.files` where it asserted `fs.writes`); if the shared `FakeClock`, which does not advance on call, makes equal timestamps break a test, stop as a premise failure naming that missing behavior (an auto-advancing clock). `Crash` is an exception, not a fake, and stays defined here. Moves to unit; `FakeExec` already comes from `tests/fakes.py`.
- `tests/integration/test_eval_harness.py` (409 lines) -> `tests/integration/test_eval_harness.py`. Reads `clutch/specs/*.md` and the repo `config.yaml` through `ROOT` (`harness.run_baseline(specs_dir=ROOT/'clutch'/'specs')`, `load_config(None, cwd=ROOT)`), builds `Journal((cfg).state_dir, ...)` and uses `provider_session`. Because it reads repo files it stays in `tests/integration/` under the same name; configs come from `load_config_text`, journals are `FakeJournal`, `provider_session` is the fake-backed one from `tests/config_helpers.py`, and `workspace=tmp_path` is only a path (nothing is written: use `FakeFileSystem` where the harness writes). If any single test both reads a repo file and needs a real write, stop as a premise failure naming it. `report_fixture`, `corpus_results`, `CODEX`, `NOW` stay importable by `test_go_grade.py`, `test_go_ai_panel.py` (batch 14, same path) and `test_stages.py`.
- `tests/integration/test_evidence_captures_verb.py` (64 lines) -> `tests/unit/test_evidence_captures_verb.py`. `main(['evidence','captures', ...], cwd=tmp_path)` over a real store written with `LocalFileSystem`, config text from `CONFIG` (cli/config helpers). Moves to unit.
- `tests/integration/test_evidence_envelope.py` (52 lines) -> `tests/integration/test_evidence_envelope.py`. Already fake-backed (`CoreRig` fake file system: it asserts the real `evidence` directory does not exist) and reads repo sources and docs through `ROOT`; stays integration under the same name (a unit file of that name exists, so it must not move).
- `tests/integration/test_evidence_verbs.py` (123 lines) -> `tests/unit/test_evidence_verbs.py` and `tests/integration/test_evidence_renormalize_real.py`. Ten `main(['evidence', ...], cwd=tmp_path)` calls over a real evidence store (`seed_end` from `tests/evidence_records.py` writes with `LocalFileSystem`): every test except one moves to `tests/unit/test_evidence_verbs.py`. `test_renormalize_show_and_coverage` also reads `tests/fixtures/evidence/codex/stream.jsonl` through `Path(__file__)` and renormalizes it into the real store (its subject is the on-disk normalized store), so it moves verbatim to the new file `tests/integration/test_evidence_renormalize_real.py`, added to `REAL_IO_TESTS`.
- `tests/integration/test_extension_draw_failure.py` (59 lines) -> `tests/integration/test_extension_draw_failure.py`. Three tests start `node tests/vscode_draw_failure.js` with `subprocess.run`; their subject is the real extension drawing under node, which cannot be a fake. The file writes nothing. Its marker line is deleted and its name is added to `REAL_IO_TESTS`; the repo-reading README test rides along unchanged. Exempt from the 1.0 s bound.
- `tests/integration/test_fault_injection.py` (228 lines) -> `tests/unit/test_fault_injection.py`. Crash-point harness: `FaultyOS` replaces `os` inside `clutch.journal` to die at a chosen `write`/`fsync`, so the subject is journal persistence on real files under `tmp_path`; moves to unit unchanged apart from the marker line. Its local `Clock` and `Crash` are existing helpers (`Clock` ticks per call and may be replaced by `tests.fakes.FakeClock` only if no test depends on the tick).

Importers whose import line changes because a file moved: `tests/integration/test_control.py`, `tests/integration/test_kill_signal_journal.py`, `tests/integration/test_shared_fakes_adoption.py`.

New files this ticket creates: `tests/integration/test_evidence_renormalize_real.py`.

Real-I/O entries added to `REAL_IO_TESTS`: `test_extension_draw_failure.py`, `test_evidence_renormalize_real.py`.

Scope out:
- Any shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/*_helpers.py`, `tests/stage_replies.py`, `tests/config_fixture.py`) and any production file under `clutch/`.
- Files of other batches: `restore-io-tests-NN` tickets restore the other skipped files; a name imported from a file of another batch is imported from where that file lives when this ticket runs (grep for it).

## Scope fence
- tests/integration/test_effects.py
- tests/integration/test_eval_harness.py
- tests/integration/test_evidence_captures_verb.py
- tests/integration/test_evidence_envelope.py
- tests/integration/test_evidence_verbs.py
- tests/integration/test_extension_draw_failure.py
- tests/integration/test_fault_injection.py
- tests/unit/test_effects.py
- tests/unit/test_evidence_captures_verb.py
- tests/unit/test_evidence_verbs.py
- tests/integration/test_evidence_renormalize_real.py
- tests/unit/test_fault_injection.py
- tests/integration/test_control.py
- tests/integration/test_kill_signal_journal.py
- tests/integration/test_shared_fakes_adoption.py
- tests/integration/conftest.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_effects.py tests/integration/test_eval_harness.py tests/unit/test_evidence_captures_verb.py tests/integration/test_evidence_envelope.py tests/unit/test_evidence_verbs.py tests/integration/test_evidence_renormalize_real.py tests/integration/test_extension_draw_failure.py tests/unit/test_fault_injection.py` lists no file (it exits 1), so none of the batch's restored files still carries the marker.
2. `./dev.py test tests/unit/test_effects.py tests/integration/test_eval_harness.py tests/unit/test_evidence_captures_verb.py tests/integration/test_evidence_envelope.py tests/unit/test_evidence_verbs.py tests/integration/test_evidence_renormalize_real.py tests/integration/test_extension_draw_failure.py tests/unit/test_fault_injection.py --durations=0` passes, and its durations table shows no restored test over 1.0 s except the tests in the real-I/O files named in Scope in; the table is pasted into `run.md`.
3. `./dev.py test tests/unit/test_effects.py tests/integration/test_eval_harness.py tests/unit/test_evidence_captures_verb.py tests/integration/test_evidence_envelope.py tests/unit/test_evidence_verbs.py tests/integration/test_evidence_renormalize_real.py tests/integration/test_extension_draw_failure.py tests/unit/test_fault_injection.py --collect-only -q` reports the same number of tests as `./dev.py test tests/integration/test_effects.py tests/integration/test_eval_harness.py tests/integration/test_evidence_captures_verb.py tests/integration/test_evidence_envelope.py tests/integration/test_evidence_verbs.py tests/integration/test_extension_draw_failure.py tests/integration/test_fault_injection.py --collect-only -q` on the base commit; both counts are recorded in `run.md`. A smaller count means a test was deleted or lost a parametrization.
4. `ls tests/integration/test_effects.py tests/integration/test_evidence_captures_verb.py tests/integration/test_evidence_verbs.py tests/integration/test_fault_injection.py` fails for every listed path (each moved file exists only at its new path), and `grep -rn "tests.integration.test_effects\|tests.integration.test_evidence_captures_verb\|tests.integration.test_evidence_verbs" tests` finds no import of a moved module at its old path.
5. `grep -n "test_extension_draw_failure.py\|test_evidence_renormalize_real.py" tests/integration/conftest.py` shows each real-I/O file named in Scope in exactly once inside `REAL_IO_TESTS`, and `git diff --stat` shows no other line of that file changed.
6. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, so no importer of a moved file broke and no restored integration test tripped the I/O guard.
7. `grep -nE "^class (FakeClock|FakeFS|FakeExec|FakeGit|FakeJournal|FakeFileSystem)\b" tests/unit/test_effects.py tests/integration/test_eval_harness.py tests/unit/test_evidence_captures_verb.py tests/integration/test_evidence_envelope.py tests/unit/test_evidence_verbs.py tests/integration/test_evidence_renormalize_real.py tests/integration/test_extension_draw_failure.py tests/unit/test_fault_injection.py` prints nothing, so no restored file defines a stand-in for a shared fake in `tests/fakes.py`.

## Verification
```
./dev.py test tests/unit/test_effects.py tests/integration/test_eval_harness.py tests/unit/test_evidence_captures_verb.py tests/integration/test_evidence_envelope.py tests/unit/test_evidence_verbs.py tests/integration/test_evidence_renormalize_real.py tests/integration/test_extension_draw_failure.py tests/unit/test_fault_injection.py --durations=0
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
