---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- io-helpers-daemon
- shared-git-fake-integration
- shared-serve-rig-config

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_config.py
- tests/integration/test_providers.py
- tests/integration/test_rework.py
- tests/integration/test_merge.py
- tests/integration/watch_fixture_repo.py
- tests/integration/test_shared_fakes_guard.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in batch tickets authored after this helper chain merges. Most skipped files import their scaffolding from a few large skipped files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is step 5 of 7 in the helper chain (`io-helpers-cli`, `-drain`, `-stages`, `-daemon`, `-config`, `-loop`, `-misc`); each step depends on the one before it.

Five files supply config text, provider fakes, rework scripts, the merge repository and the snapshot fixture repository: `test_config.py` (`VALID` imported by 23 files, `MigrationFS`), `test_providers.py` (`FakeExec`, `PythonProviderExec`, `claude_ok` and more, 11 importers), `test_rework.py` (9 importers), `test_merge.py` (`repo`, `context`, 7 importers) and `watch_fixture_repo.py`, whose builder runs `git init` and `git commit` in a subprocess.

When this ticket is done, `tests/config_helpers.py` defines every name that another test file imports from `tests/integration/test_config.py`, `test_providers.py`, `test_rework.py`, `test_merge.py` and `watch_fixture_repo.py` (all under `tests/integration/`) (the names are listed under Scope in), and each of those 47 importers takes it from `tests.config_helpers`. The helpers use the shared fakes, so a restored test file that needs them does not start a process or run git, and a later batch ticket can turn a file back on without first fixing a helper that sits in a skipped file.

The helpers follow the rules in `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`, created by `shared-git-fake`; read it in the worktree), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a journal as `tests.fakes.FakeJournal` unless the helper's subject is journal persistence, and a disk write only under a `tmp_path` the caller passes in. A model-reply helper or config text reuses `tests/stage_replies.py` and `tests/config_fixture.py` (created by `shared-review-script` and `shared-serve-rig-config`, merged before `shared-fakes-guard`); a helper never copies either. The owner requires restored tests to be fast and to reuse shared fixtures: this module is the one place each helper below lives.

## Boundary contract
### Shared config, provider, rework and merge test helpers
- disposition: create
- owner: tests/config_helpers.py
- consumers: the 47 test files listed in `## Scope fence` that import from `tests/integration/test_config.py`, `test_providers.py`, `test_rework.py`, `test_merge.py` and `watch_fixture_repo.py` (all under `tests/integration/`), and the later batch tickets that restore the skipped ones
- observable change: the names listed under Scope in move from `tests/integration/test_config.py`, `test_providers.py`, `test_rework.py`, `test_merge.py` and `watch_fixture_repo.py` (all under `tests/integration/`) into `tests/config_helpers.py`, rewritten onto the shared fakes; every importer's import line changes to `tests.config_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub (for example `test_cli.Clock` in `tests/integration/test_shared_fakes_adoption.py`) stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_config_helpers.py` imports each moved name from `tests.config_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_config_helpers.py
- post-merge source of truth: tests/config_helpers.py
- closest existing: `tests/fakes.py` (FakeClock, FakeExec, FakeFileSystem, FakeJournal, `turn`, `until`) and `tests/git_fake.py::GitFake` supply the fake seams but none of the scaffolding below; the hub definitions today do real git and processes, so a skipped file cannot reuse them
- earning reason: consolidation of evidenced duplicates and shared use: 47 files import these names from `tests/integration/test_config.py`, `test_providers.py`, `test_rework.py`, `test_merge.py` and `watch_fixture_repo.py` (all under `tests/integration/`), and the hub is skipped, so no importer can be restored until the names live in an unskipped module that follows the I/O rules

## Scope in / Scope out
Scope in:
- Create `tests/config_helpers.py` holding these moved names, each rewritten as described, keeping its signature unless a change is named: `CONFIG`, `ENV`, `FakeExec`, `MigrationFS`, `SNAG`, `VALID`, `claude_ok`, `codex_ok`, `config`, `context`, `invoke`, `jsonl`, `llm`, `order`, `original`, `provider_request`, `provider_session`, `repo`, `req`, `requisition`, `run`, `signals`, `successors`, `bootstrap_pipeline_keeps_inline_admission`, `ticket_bytes`, `watch_fixture_repo`.
  - From `test_config.py`: `VALID` (the valid config text; built through `tests/config_fixture.py` when that module can express it byte for byte, else moved verbatim) and `MigrationFS`.
  - From `test_providers.py`: `CONFIG` (via `tests/config_fixture.py::build_config`, byte-identical), `ENV`, `config`, `llm`, `req`, `jsonl`, `claude_ok`, `codex_ok`, `provider_session`, `provider_request` and `FakeExec`. `PythonProviderExec` and `python_client` stay in `test_providers.py`: they run real Python child scripts with streamed output, timeouts and process-group kill, which `tests/fakes.py::FakeExec` cannot fake, and their only importers (`tests/integration/test_watchdog.py`, `tests/integration/test_watchdog_activation.py`) are skipped; the watchdog batch ticket moves them. Those two files import every other name they take from `test_providers.py` from `tests.config_helpers`, and keep a separate `from tests.integration.test_providers import` line for only `PythonProviderExec` and `python_client`.
  - `FakeExec` is the provider-script class at `test_providers.py:67-94` (scripted responses, `on_spawn`/`on_stdout_line` callbacks, `calls` dicts, a hang `Event`, `kill_group`). It already runs no process, and `tests.fakes.FakeExec` does not supply that behavior, so the class moves into `tests/config_helpers.py` unchanged; it is not a duplicate of the shared fake.
  - `provider_session` writes a real `Journal` under `cfg.state_dir`; it keeps its signature, and its unit test points `state_dir` at `tmp_path` (or passes `tests.fakes.FakeJournal` where callers allow it).
  - From `test_rework.py`: `SNAG`, `run`, `original`, `order`, `requisition`, `invoke`, `signals`, `ticket_bytes`, `successors`.
  - From `test_merge.py`: the `repo` fixture and `context(repo, script)` (real git and `SubprocessExec` today; `GitFake`, `FakeExec`, `FakeFileSystem`), and the body of `test_bootstrap_pipeline_keeps_inline_admission`: `test_drain.py::test_bootstrap_never_supervised_holds` imports and calls that test function. The body moves as a plain function named `bootstrap_pipeline_keeps_inline_admission` (no `test_` prefix, so pytest does not collect it from the new module). `test_merge.py` keeps a one-line `test_bootstrap_pipeline_keeps_inline_admission` that calls it, so that test still runs under its name; `test_drain.py` imports the new name and calls it.
  - From `watch_fixture_repo.py`: `watch_fixture_repo(tmp_path, state_dir)` writes `config.yaml` (from `VALID`) and `tickets/` under `tmp_path / "repo"` and no longer runs `git init`, `add` or `commit`; it still returns the repo `Path`, and it stores a `GitFake` reporting one commit named `fixture` in the module attribute `tests.config_helpers.WATCH_GIT`, replaced on every call; a caller that runs the CLI against the repo passes that fake through the `tests.cli_helpers` CLI helper, which patches `clutch.__main__`'s `Git`. The file `tests/integration/watch_fixture_repo.py` then holds only `from tests.config_helpers import watch_fixture_repo  # noqa: F401`, kept because the guidance text in `tests/integration/conftest.py` names it; `test_watch.py` imports from `tests.config_helpers`.
- In every importer listed in `## Scope fence`, change only the import line (also an import line inside a function) so each moved name comes from `tests.config_helpers` (for `test_drain.py` the one call of the renamed `bootstrap_pipeline_keeps_inline_admission` is also edited). Every name any file imports from these hubs is moved, except where Scope in says otherwise, so no importer keeps an import from a hub. Names an importer takes from other hubs stay as they are. A module import (`from tests.integration import <hub>`) is not an import of a name and stays.
- Each hub file (`tests/integration/test_config.py`, `tests/integration/test_providers.py`, `tests/integration/test_rework.py`, `tests/integration/test_merge.py`, `tests/integration/watch_fixture_repo.py`) deletes its definition of every moved name it defines and imports the name back from `tests.config_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line, and every name it defines that no other file imports). Its own tests keep working through the name it imports back; the hub module keeps each moved name as a module attribute.
- Earlier helper modules (`tests/cli_helpers.py`, `tests/drain_helpers.py`, `tests/stages_helpers.py`, `tests/daemon_helpers.py`) change only where one of them imports a name this ticket moves.
- `tests/integration/test_shared_fakes_guard.py::CONFIG_EXEMPT` names `tests/integration/test_config.py` today; moving `VALID` forces its entries to follow the config text. When `VALID` stays verbatim, add a `tests/config_helpers.py` entry whose reason says why `VALID` must stay verbatim (`tests/config_fixture.py` cannot express it byte for byte); drop the `tests/integration/test_config.py` entry once the hub holds no config text the guard flags. Change no other line of that file.
- Create `tests/unit/test_config_helpers.py`: one test per moved name that runs without reading a repo file, calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name above is importable from `tests.config_helpers`.
- `tests/integration/test_stages.py::report_context` imports `context` from `test_merge.py` inside the function; that line changes to `tests.config_helpers` and `tests/stages_helpers.py` (if `report_context` moved there) changes the same way.
- `tests/integration/test_shared_fakes_adoption.py` asserts `test_merge.CONFIG is test_stages.CONFIG`, that `test_merge.py` source has no `test_stages.py` text and no `split('CONFIG`: the hub keeps `CONFIG` as the one object from `tests.stages_helpers`.
- `tests/snapshot_scale_fixture.py` and `tests/integration/test_snapshot_cache_facts.py` import `VALID` and run today; they stay green.
- Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.

Scope out:
- Restoring any skipped test file (later batch tickets): a hub file stays skipped and its tests are unchanged.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior.
- Defining in `tests/config_helpers.py` a class that duplicates `tests/fakes.py` or `tests/git_fake.py`: use the shared fakes. `MigrationFS` may subclass `tests.fakes.FakeFileSystem`, adding only the behavior the importers need. The provider-script `FakeExec` moved unchanged is not such a duplicate. Tests defined in the five hubs stay there (including `test_merge.py::test_bootstrap_pipeline_keeps_inline_admission`, now a wrapper).
- Skipped importers may still break semantically; their batch ticket fixes that.

## Scope fence
- tests/config_helpers.py
- tests/unit/test_config_helpers.py
- tests/integration/test_config.py
- tests/integration/test_providers.py
- tests/integration/test_rework.py
- tests/integration/test_merge.py
- tests/integration/watch_fixture_repo.py
- tests/integration/test_shared_fakes_guard.py
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
- tests/integration/test_caps.py
- tests/integration/test_cli.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_config.py
- tests/integration/test_diagnose.py
- tests/integration/test_drain.py
- tests/integration/test_eval_harness.py
- tests/integration/test_evidence_envelope.py
- tests/integration/test_gates.py
- tests/integration/test_gemini_provider.py
- tests/integration/test_hostfiles.py
- tests/integration/test_inbox.py
- tests/integration/test_ladder.py
- tests/integration/test_notify.py
- tests/integration/test_provider_capture_overwrite.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_reject_reason_both_paths.py
- tests/integration/test_requisition_brief_check.py
- tests/integration/test_requisition_identity_record.py
- tests/integration/test_restart_timers.py
- tests/integration/test_rework_supervise.py
- tests/integration/test_shared_fakes_adoption.py
- tests/integration/test_snapshot_cache_facts.py
- tests/integration/test_snapshot_merged_cap.py
- tests/integration/test_stages.py
- tests/integration/test_step_events.py
- tests/integration/test_ticket_write_serialization.py
- tests/integration/test_watch.py
- tests/integration/test_watch_surface_tier.py
- tests/integration/test_watchdog.py
- tests/integration/test_watchdog_activation.py
- tests/regress_drain_park_findings.py
- tests/snapshot_scale_fixture.py
- tests/cli_helpers.py
- tests/drain_helpers.py
- tests/stages_helpers.py
- tests/daemon_helpers.py
- tests/unit/test_config_fixture.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_config_helpers.py` passes, and `tests/unit/test_config_helpers.py` checks that `watch_fixture_repo(tmp_path, "state")` writes `config.yaml` under `tmp_path / "repo"` whose `state_dir` line is `state_dir: state`, creates no `.git` directory, and leaves `tests.config_helpers.WATCH_GIT` a `GitFake` whose `calls` is empty until a test uses it (a version that still runs git passes only if a `.git` directory exists, which the test rules out), that `VALID` parses through `clutch.config.load_config`, and that the moved `repo` fixture leaves no `.git` directory.
2. `grep -rnE "from tests\.integration\.(test_config|test_providers|test_rework|test_merge|watch_fixture_repo) import" tests --include=*.py` prints only the two lines `from tests.integration.test_providers import PythonProviderExec, python_client` in `tests/integration/test_watchdog.py` and `from tests.integration.test_providers import PythonProviderExec` in `tests/integration/test_watchdog_activation.py`: every other name any file imports from these hubs is moved, so any other line names the importer that was missed.
3. `grep -nE "^(async def|def|class) (MigrationFS|VALID|CONFIG|ENV|FakeExec|claude_ok|codex_ok|config|jsonl|llm|provider_request|provider_session|req|SNAG|invoke|order|original|requisition|run|signals|successors|ticket_bytes|context|repo|watch_fixture_repo)\b|^(MigrationFS|VALID|CONFIG|ENV|FakeExec|claude_ok|codex_ok|config|jsonl|llm|provider_request|provider_session|req|SNAG|invoke|order|original|requisition|run|signals|successors|ticket_bytes|context|repo|watch_fixture_repo) =" tests/integration/test_config.py tests/integration/test_providers.py tests/integration/test_rework.py tests/integration/test_merge.py tests/integration/watch_fixture_repo.py` prints nothing: the hub files no longer define a moved name.
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/config_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the same number of passed and skipped tests as on the base commit, both recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py tests/integration/test_shared_fakes_guard.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object, and `CONFIG_EXEMPT` names the file that now holds verbatim config text).

## Verification
```
./dev.py test tests/unit/test_config_helpers.py
./dev.py test tests/unit
./dev.py test tests/integration
./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py tests/integration/test_shared_fakes_guard.py
```

## Definition of rejected
- A test that runs today fails or is skipped, or a skipped test becomes unskipped.
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/config_helpers.py` defines a class that duplicates a shared fake or a copied reply or config helper.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line (plus `test_drain.py`'s one call site of `bootstrap_pipeline_keeps_inline_admission`), `tests/integration/test_shared_fakes_guard.py` changes anything other than its `CONFIG_EXEMPT` entries, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 30m
- stuck: 60m
- reason: 47 import lines and the hub definitions move in one change because a name must resolve in every importer at once; splitting by importer leaves a name defined in two places, and the files share one module so they stay together