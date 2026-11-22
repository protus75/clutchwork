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
- tests/integration/test_ask.py
- tests/integration/test_ask_drafts.py
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_ask_plan_conduct_covered.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_priority_order.py
- tests/integration/test_ask_plan_read_queue.py
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_ask_plan_shared_paths.py
- tests/integration/test_ask_plan_subagent_models.py
- tests/integration/test_ask_roadmap.py
- tests/integration/test_ask_view_events.py
- tests/integration/test_audit.py

## On-demand
- tests/integration/test_author.py

## Goal / Why
`integration-disk-io-skip` turned off 15 integration test files in this batch (the `ask`/prompt-rendering tests, `test_audit.py` and `test_author.py`, 1398 lines) because they write real files, run real git and processes, and sleep; `integration-io-guard` fails any such test, and `disk-io-skip-per-file` marks each skipped file with `pytestmark = pytest.mark.disk_io_skip`. The owner wants these tests back, FAST (no restored test above 1.0 s) and on the shared fakes, not on per-file copies.

When this ticket is done, none of the 15 files carries the `disk_io_skip` marker, each runs under the I/O guard (or under `tests/unit/` where it still writes under `tmp_path`), every test function in them still exists and asserts what it asserted before, and the shared modules `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py` are reused instead of copied. The helper hub names these files imported were moved to those helper modules by the `restore-helpers-*` chain, so `restore-helpers-misc` (end of the chain) is the dependency; read each shared module in your worktree before using it, and the run stops as a premise failure that names the missing behavior if a shared fake lacks one (never edit a shared module).

## Boundary contract
none
- reason: tests encoding an existing contract; the batch changes only test files and the `clutch/` behavior they assert stays as it is

## Scope in / Scope out
Scope in:
Rules every restored test follows (the owner requires FAST tests that REUSE the shared fixtures and fakes):
- Delete the `pytestmark = pytest.mark.disk_io_skip` line (and an `import pytest` it alone needed). Keep every test function, parametrization and assertion; no test is deleted, skipped, xfailed or weakened.
- Git goes through `tests/git_fake.py::GitFake` (overrides by member name, `fake.calls`); processes through `tests/fakes.py::FakeExec` or an in-process `clutch.__main__.main([...])`; journals through `FakeJournal` unless the test's subject is journal persistence; the `clutch.seams.FileSystem` seam through `FakeFileSystem`; time through `FakeClock` with `until`/`turn`, never `sleep`. Config text comes from `tests/config_fixture.py` / `tests/config_helpers.py`, model replies from `tests/stage_replies.py`, and test rigs from `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. Read those modules in the worktree before editing; they exist once the dependency has merged.
- No new `Fake*` or stand-in class and no copy of a shared helper in a test file. A per-file stand-in class that the file defines today (named per file below) is replaced by the shared fake or helper and its definition deleted. If a shared module lacks a behavior a test needs, the run stops as a premise failure that names the missing behavior and the test; it never edits a shared module, `clutch/` code or `tests/integration/conftest.py`.
- Placement follows the host guide section "Unit and integration tests" (in Context): a test that still writes files (only under `tmp_path`) lives under `tests/unit/`; a test that reads a repo file (anchored on `Path(__file__)`) and writes nothing lives under `tests/integration/`. Reading packaged spec or doc files inside production code (for example `ask.render` loading `clutch/specs/ask/*.md`) is not a test reading a repo file. When one test both writes under `tmp_path` and needs repo text (for example spec files), the repo text comes through the production reader (`clutch.specs`, `importlib.resources`, `inspect.getsource`), never a test-side `Path(__file__)` read, so the test qualifies for `tests/unit/`; if no such reader gives the text, the run stops as a premise failure naming the test. A file whose tests need both kinds of test is split by test function, and the ticket names both paths. A moved file keeps its name under `tests/unit/` unless that name exists there, in which case it is `test_<name>_flow.py`.
- Where code under test builds its own real `Git`, `SubprocessExec` or `Journal` and `main` exposes no seam for it, drive the code through the function the unit tests beside it call, with the fakes. If neither route exists, the run stops as a premise failure that names the code path.
- Any name a moved file defines that another test module imports gets its importers' import lines updated in the same change (grep `from tests.integration.<name> import` first); only import lines change in importers. At authoring time the grep found importers only where this ticket fences them; the run re-greps and fences nothing new (a new importer is a premise failure).

Per file:
- `tests/integration/test_ask.py` (102 lines): today it writes `config.yaml` and ticket files under `tmp_path`, drives `main(['prompt', ...])` with `cwd=tmp_path`, builds a `Box(..., LocalFileSystem())` and a real git root (`make_root`, `git_out`) in the drafts test; imports `VALID` from `test_config`. Plan: SPLIT. Tests that only render (`test_each_kind_renders_stem_ticket_and_state_dir`, `test_host_notes_appended_as_data_block_only_when_set`, `test_state_dir_outside_repo_renders_absolute`) build the `config` fixture in memory with `clutch.config.load_config_text(VALID_text, path=tmp_path / 'config.yaml', cwd=tmp_path)` (no file written) and stay in `tests/integration/test_ask.py`. Tests that need files on disk for `main` (`test_prompt_verb_refuses_missing_ticket`, `test_prompt_verb_writes_no_state`, `test_box_prompt_names_requested_files`, `test_box_prompt_unknown_id_refuses`, `test_drafts_prompt_selects_committed_drafts`) move to the new `tests/unit/test_ask.py` with the shared git helpers (GitFake, fake-backed root) for the drafts test.
- `tests/integration/test_ask_drafts.py` (23 lines): today it writes `config.yaml` under `tmp_path` only to call `load_config`. Plan: stays; config from `load_config_text` (nothing written).
- `tests/integration/test_ask_drain_loop.py` (36 lines): today it writes `config.yaml` under `tmp_path`; one test calls `main(['prompt', 'drain-loop'], cwd=tmp_path)`. Plan: stays; config from `load_config_text`, and the `main` test replaces `clutch.__main__.load_config` with `monkeypatch.setattr` returning that config (the way `tests/unit/test_ask_plan_drain.py` does); the read-only `not config.state_dir.exists()` assertion is kept.
- `tests/integration/test_ask_drain_loop_agent.py` (79 lines): today it defines `render(tmp_path, config_text)` that writes `config.yaml`. Plan: stays; its `render` helper builds the config with `load_config_text` and writes nothing.
- `tests/integration/test_ask_plan_conduct_covered.py` (27 lines): today it writes `config.yaml` under `tmp_path`. Plan: stays; `load_config_text`.
- `tests/integration/test_ask_plan_drain.py` (165 lines): today it `prompts` fixture writes `config.yaml`; reads repo files via `ROOT = Path(__file__).resolve().parents[2]`. Plan: stays (repo reader); `prompts` fixture uses `load_config_text`.
- `tests/integration/test_ask_plan_priority_order.py` (30 lines): today it writes `config.yaml` under `tmp_path`. Plan: stays; `load_config_text`.
- `tests/integration/test_ask_plan_read_queue.py` (33 lines): today it writes `config.yaml` under `tmp_path`. Plan: stays; `load_config_text`.
- `tests/integration/test_ask_plan_serve.py` (41 lines): today it writes `config.yaml`; reads the run guide and how-it-works documents via `Path(__file__)`. Plan: stays (repo reader); `load_config_text`.
- `tests/integration/test_ask_plan_shared_paths.py` (26 lines): today it writes `config.yaml` under `tmp_path`. Plan: stays; `load_config_text`.
- `tests/integration/test_ask_plan_subagent_models.py` (28 lines): today it writes `config.yaml` under `tmp_path`. Plan: stays; `load_config_text`.
- `tests/integration/test_ask_roadmap.py` (28 lines): today it writes `config.yaml`, calls `main(['prompt', 'roadmap'], cwd=tmp_path)`, reads the packaged roadmap facet through `SPECS_DIR`. Plan: stays; the test replaces `clutch.__main__.load_config` with `monkeypatch.setattr` returning a `load_config_text` config; the two `not ... exists()` assertions are kept.
- `tests/integration/test_ask_view_events.py` (25 lines): today it writes `config.yaml`; reads the how-it-works document and the readme via `Path(__file__)`. Plan: stays (repo reader); `load_config_text`.
- `tests/integration/test_audit.py` (91 lines): today it builds `Event`s in memory, but also runs a real production drain (`drain`, `agent`, `implement_reply`, `verdict`, `author`, `repo` fixture from the drain, stages and terminal hubs) over a real git repo and a real `Journal`. Plan: stays at `tests/integration/test_audit.py` when the drain runs on `GitFake` + `FakeJournal` (the helper modules supply the rig); `audit_journal` is fed `FakeJournal.read()` events. If `audit_journal` needs a real `Journal` file, the run stops as a premise failure naming it.
- `tests/integration/test_author.py` (664 lines): today it real git roots (`make_root`, `commit_ticket`, `pause_checkout`, `git_out`), real `Journal`, `Box(..., LocalFileSystem())`, `commit_lock`, ticket files under `tmp_path`; three tests read the author prompt spec and the authoring guide via `Path(__file__).resolve().parents[2]` (`test_author_spec_requires_criteria_to_name_wrong_results`, `test_author_spec_states_ticket_rules`, `test_author_prompt_contains_guide_and_skeletons`). Plan: SPLIT. The three repo-reading tests stay in `tests/integration/test_author.py`. The other 21 move to `tests/unit/test_author_flow.py` (`tests/unit/test_author.py` already exists), with GitFake, FakeJournal (box and journal-persistence subjects excepted, which keep a real `Journal` or `Box` under `tmp_path`), FakeClock, and the `tests/stage_replies.py` / `tests/misc_helpers.py` replies. Other modules (`test_ticket_write_serialization`, `test_roadmap_row_author`, `test_requisition_identity_record`, `test_triage`, `test_roadmap_author`) imported `_routes`, `block`, `requisition_reply`, `_box`, `_events`, `_failure`, `_run`, `bug_reply` from this file; `restore-helpers-misc` moved them, so grep confirms none remains and fences any that does.

Record in the run record (`run.md`): the `--collect-only -q` test count of the batch's files on the base commit and after the change, the `--durations=0` output of the restored paths, which tests of a split file went to which path, and for each moved file the `grep -rn "tests.integration.<name>" tests` result used to find importers.

Scope out: `tests/integration/conftest.py` (the marker line is the only switch), `tests/fakes.py`, `tests/conftest.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, every `tests/*_helpers.py`, all `clutch/` code, and test files outside this batch except the importer import lines named above. A hot test file (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `test_cli.py`, `test_watch.py`, `serve_rig.py`) gets no new test, fixture or helper from this change; code only leaves it or is repointed.

## Scope fence
- tests/integration/test_ask.py
- tests/unit/test_ask.py
- tests/integration/test_ask_drafts.py
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_ask_plan_conduct_covered.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_priority_order.py
- tests/integration/test_ask_plan_read_queue.py
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_ask_plan_shared_paths.py
- tests/integration/test_ask_plan_subagent_models.py
- tests/integration/test_ask_roadmap.py
- tests/integration/test_ask_view_events.py
- tests/integration/test_audit.py
- tests/integration/test_author.py
- tests/unit/test_author_flow.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_roadmap.py tests/integration/test_ask_view_events.py tests/integration/test_audit.py tests/integration/test_author.py tests/unit/test_ask.py tests/unit/test_author_flow.py` prints no file name (the marker is gone from every path the batch keeps), recorded in `run.md`; every path that the plan moves whole no longer exists under `tests/integration/` (`ls` of it fails), and the marker is not present in any new file.
2. `./dev.py test tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_roadmap.py tests/integration/test_ask_view_events.py tests/integration/test_audit.py tests/integration/test_author.py tests/unit/test_ask.py tests/unit/test_author_flow.py --durations=0` passes and its durations table lists no restored test above 1.0 s (a test that still takes 1.0 s or more fails this criterion, it is not allowed to stay slow); the output is recorded in `run.md`.
3. `./dev.py test tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_roadmap.py tests/integration/test_ask_view_events.py tests/integration/test_audit.py tests/integration/test_author.py tests/unit/test_ask.py tests/unit/test_author_flow.py --collect-only -q` reports exactly as many tests as `./dev.py test tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_roadmap.py tests/integration/test_ask_view_events.py tests/integration/test_audit.py tests/integration/test_author.py --collect-only -q` reported on the base commit (a deleted, merged or skipped test makes the counts differ); both numbers are recorded in `run.md`.
4. `grep -nE "^\s*class (Fake|Script|Exec|Git|FS|Clock)" tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_roadmap.py tests/integration/test_ask_view_events.py tests/integration/test_audit.py tests/integration/test_author.py tests/unit/test_ask.py tests/unit/test_author_flow.py` prints no line (no per-file fake or stand-in class remains), and `grep -nE "subprocess|sys\.executable|time\.sleep|asyncio\.sleep" tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_roadmap.py tests/integration/test_ask_view_events.py tests/integration/test_audit.py tests/integration/test_author.py` prints no line (a restored integration test starts no process and never sleeps).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0, and `tests/integration` reports no `IntegrationIOBlocked` failure (the I/O guard stays on for every restored integration test).

## Verification
```
./dev.py test tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_roadmap.py tests/integration/test_ask_view_events.py tests/integration/test_audit.py tests/integration/test_author.py tests/unit/test_ask.py tests/unit/test_author_flow.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
A test is deleted, skipped, xfailed or weakened (an assertion removed or loosened, a parametrization dropped); a new or copied `Fake*`/stand-in class or helper appears in a test file; a shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, a `tests/*_helpers.py`), `tests/integration/conftest.py` or `clutch/` code is edited; a restored integration test writes disk, starts a process, runs git or sleeps; a restored test takes more than 1.0 s; or the collected test count of the batch differs from the base commit.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines so files that share fixtures stay together (1398 lines here)
