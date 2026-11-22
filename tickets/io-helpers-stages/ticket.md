---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- io-helpers-drain
- shared-git-fake-integration
- shared-review-script
- shared-serve-rig-config

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_stages.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in batch tickets authored after this helper chain merges. Most skipped files import their scaffolding from a few large skipped files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is step 3 of 7 in the helper chain (`io-helpers-cli`, `-drain`, `-stages`, `-daemon`, `-config`, `-loop`, `-misc`); each step depends on the one before it.

`tests/integration/test_stages.py` (944 lines) is imported by 38 files for `ENV`, `CONFIG`, `TICKET`, `STEM`, `repo`, `run`, `agent`, `verdict` and more; its `repo` fixture and `agent` helper run real git, and `run` builds a real `StageContext` over `SubprocessExec`.

When this ticket is done, `tests/stages_helpers.py` defines every name that another test file imports from `tests/integration/test_stages.py` (the names are listed under Scope in), and each of those 38 importers takes it from `tests.stages_helpers`. The helpers use the shared fakes, so a restored test file that needs them does not start a process or run git, and a later batch ticket can turn a file back on without first fixing a helper that sits in a skipped file.

The helpers follow the rules in `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`, created by `shared-git-fake`; read it in the worktree), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a journal as `tests.fakes.FakeJournal` unless the helper's subject is journal persistence, and a disk write only under a `tmp_path` the caller passes in. A model-reply helper or config text reuses `tests/stage_replies.py` and `tests/config_fixture.py` (created by `shared-review-script` and `shared-serve-rig-config`, merged before `shared-fakes-guard`); a helper never copies either. The owner requires restored tests to be fast and to reuse shared fixtures: this module is the one place each helper below lives.

## Boundary contract
### Shared stage-run test helpers
- disposition: create
- owner: tests/stages_helpers.py
- consumers: the 38 test files listed in `## Scope fence` that import from `tests/integration/test_stages.py`, and the later batch tickets that restore the skipped ones
- observable change: the names listed under Scope in move from `tests/integration/test_stages.py` into `tests/stages_helpers.py`, rewritten onto the shared fakes; every importer's import line changes to `tests.stages_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub (for example `test_cli.Clock` in `tests/integration/test_shared_fakes_adoption.py`) stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_stages_helpers.py` imports each moved name from `tests.stages_helpers` and exercises each name that needs no repo file without a process, real git or a write outside `tmp_path`; `tests/integration/test_stages_helpers_repo.py` exercises `run`, `adopt_conduct`, `report_context` and `SPECS`, which read repo files; no importer still imports a moved name from the hub
- tests: tests/unit/test_stages_helpers.py, tests/integration/test_stages_helpers_repo.py
- post-merge source of truth: tests/stages_helpers.py
- closest existing: `tests/fakes.py` (FakeClock, FakeExec, FakeFileSystem, FakeJournal, `turn`, `until`) and `tests/git_fake.py::GitFake` supply the fake seams but none of the scaffolding below; the hub definitions today do real git and processes, so a skipped file cannot reuse them
- earning reason: consolidation of evidenced duplicates and shared use: 38 files import these names from `tests/integration/test_stages.py`, and the hub is skipped, so no importer can be restored until the names live in an unskipped module that follows the I/O rules

## Scope in / Scope out
Scope in:
- Create `tests/stages_helpers.py` holding these moved names, each rewritten as described, keeping its signature unless a change is named: `CONFIG`, `ENV`, `SAMPLE_REPORT`, `SECRET`, `SNAG`, `SPECS`, `STEM`, `SampleReport`, `TICKET`, `_report_bytes`, `adopt_conduct`, `agent`, `author`, `evidence`, `git`, `implement_reply`, `repo`, `report_context`, `run`, `verdict`.
  - Constants moved verbatim: `SAMPLE_REPORT`, `SECRET`, `SNAG`, `SPECS` (still anchored on the repo's `clutch/specs` through `Path(__file__)`, now `parents[1]` of `tests/stages_helpers.py`), `STEM`, `TICKET`, and `SampleReport` (the `Artifact` subclass) with `_report_bytes()`. `ENV` and `CONFIG` come from `tests.cli_helpers`/`tests/config_fixture.py` where equal to today's text; the stages `ENV` carries the extra `FAKE_KEY` entry and its `CONFIG` names the provider `fake` with `auth: FAKE_KEY`, so each is built with `build_config(...)` arguments that reproduce today's text byte for byte, never a copy.
  - `implement_reply` and `verdict` are the model-reply helpers `tests/stage_replies.py` already owns after `shared-review-script`; the module re-exports those names (it does not redefine them). `agent(files, outcome)` writes the files into `req.worktree` through the worktree path it is given and records the add and commit on the registered `GitFake` instead of running git; `author(repo, bypass)` writes the ticket file and records its commit; `evidence(**kw)` moves unchanged (pure); `git(root, *args)` answers from the registered `GitFake` as `tests.cli_helpers.git_out` does; `adopt_conduct(root)` moves unchanged (it renders routed conduct files under `root`).
  - `repo` (fixture): same files as today under `tmp_path / "repo"`, no `git init`/`add`/`commit`; `GitFake` stands in. `run(repo, script, bypass="")` builds `StageContext` with `FakeExec`, the `GitFake`, a `FakeFileSystem` or `tmp_path`-backed `LocalFileSystem` (never a process) and a `FakeClock`, then returns `(asyncio.run(run_stages(...)), llm, config)`. `report_context(repo, *, verification, source, script)` keeps its signature.
- In every importer listed in `## Scope fence`, change only the import line (also an import line inside a function) so each moved name comes from `tests.stages_helpers`. Every name any file imports from these hubs is moved, except where Scope in says otherwise, so no importer keeps an import from a hub. Names an importer takes from other hubs stay as they are. A module import (`from tests.integration import <hub>`) is not an import of a name and stays.
- Each hub file (`tests/integration/test_stages.py`) deletes its definition of every moved name it defines and imports the name back from `tests.stages_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line, and every name it defines that no other file imports). Its own tests keep working through the name it imports back; the hub module keeps each moved name as a module attribute.
- Earlier helper modules (`tests/cli_helpers.py`, `tests/drain_helpers.py`) change only where one of them imports a name this ticket moves.
- Create `tests/unit/test_stages_helpers.py`: one test per moved name that needs no repo file (every moved name except `run`, `adopt_conduct`, `report_context` and `SPECS`), calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name above is importable from `tests.stages_helpers`.
- Create `tests/integration/test_stages_helpers_repo.py` (a new fenced integration file, not in `REAL_IO_TESTS`, so it runs under the I/O guard) holding one test each for `run`, `adopt_conduct`, `report_context` and `SPECS`. These names need the repo's `clutch/specs` (read through the `Path(__file__)` anchor) or `context` from `tests/integration/test_merge.py`, so a unit test cannot run them; the integration tests read tracked repo files only through that anchor and write only under `tmp_path`, with no process or real git.
- `test_stages.py::_report_ticket` patches the `TICKET` global of the hub module through `__import__(__name__, ...)` so `author` reads the patched text; once `author` lives in `tests/stages_helpers.py` it reads that module's `TICKET`, so the patch retargets `tests.stages_helpers` (one line in the hub; the only non-import edit allowed in the hub).
- `report_context` imports `context` from `tests/integration/test_merge.py` inside the function; it keeps that import until `io-helpers-config` moves `context`, which then edits the line. `tests.spool_captures.list_captures`/`read_capture` (real filesystem reads) stay where they are; `io-helpers-misc` provides the fake-backed equivalents.
- Earlier helper modules (`tests/cli_helpers.py`, `tests/drain_helpers.py`) import `adopt_conduct` from this hub; those lines change to `tests.stages_helpers`. `tests/integration/test_shared_fakes_adoption.py` asserts `test_merge.CONFIG is test_stages.CONFIG`, so the hub keeps `CONFIG` as a module attribute holding the one shared object.
- `tests/regress_drain_signals.py` imports `agent` from the hub and stays green.

- Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.
Scope out:
- Restoring any skipped test file (later batch tickets): a hub file stays skipped and its tests are unchanged.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior.
- Defining in `tests/stages_helpers.py` a class that duplicates `tests/fakes.py` or `tests/git_fake.py`: use the shared fakes. A thin subclass is not needed by any moved name. Test functions that call `run`, `repo`, `agent` and `verdict` inside the hub keep their bodies.
- Skipped importers may still break semantically; their batch ticket fixes that.

## Scope fence
- tests/stages_helpers.py
- tests/unit/test_stages_helpers.py
- tests/integration/test_stages_helpers_repo.py
- tests/integration/test_stages.py
- tests/integration/serve_rig.py
- tests/integration/test_audit.py
- tests/integration/test_bug_gate.py
- tests/integration/test_cli.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_diagnose.py
- tests/integration/test_drain.py
- tests/integration/test_drain_reentry.py
- tests/integration/test_drain_signals.py
- tests/integration/test_gates.py
- tests/integration/test_harvest.py
- tests/integration/test_harvest_cost_source.py
- tests/integration/test_harvest_orphans.py
- tests/integration/test_host_mechanical.py
- tests/integration/test_hostfiles.py
- tests/integration/test_image_candidates_select.py
- tests/integration/test_inbox.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_ladder.py
- tests/integration/test_merge.py
- tests/integration/test_merge_model_resolve.py
- tests/integration/test_mergequeue.py
- tests/integration/test_provider_failure_surface.py
- tests/integration/test_reject_queue.py
- tests/integration/test_requisition_gate.py
- tests/integration/test_restart_timers.py
- tests/integration/test_retro_box.py
- tests/integration/test_rework.py
- tests/integration/test_scorecard.py
- tests/integration/test_second_problems.py
- tests/integration/test_shared_fakes_adoption.py
- tests/integration/test_step_events.py
- tests/integration/test_storm_notification_activation.py
- tests/integration/test_storm_producer.py
- tests/integration/test_supervisor_rework.py
- tests/integration/test_terminal.py
- tests/integration/test_triage.py
- tests/regress_drain_signals.py
- tests/cli_helpers.py
- tests/drain_helpers.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_stages_helpers.py tests/integration/test_stages_helpers_repo.py` passes, `tests/integration/test_stages_helpers_repo.py` has one test each for `run`, `adopt_conduct`, `report_context` and `SPECS`, and `tests/unit/test_stages_helpers.py` (which reads no repo file) checks that `agent({...})` called on a `LLMRequest` whose worktree is a `tmp_path` directory writes the file there and appends an add and a commit to `GitFake.calls`, and that `TICKET.format(bypass="")` contains `STEM`'s ticket text, and that `repo` leaves no `.git` directory and `git_fake(repo).calls` records the `author` commit.
2. `grep -rnE "from tests\.integration\.(test_stages) import" tests --include=*.py` prints nothing: every name any file imports from these hubs is moved, so a leftover line names the importer that was missed.
3. `grep -nE "^(async def|def|class) (CONFIG|ENV|SAMPLE_REPORT|SECRET|SNAG|SPECS|STEM|SampleReport|TICKET|_report_bytes|adopt_conduct|agent|author|evidence|git|implement_reply|repo|report_context|run|verdict)\b|^(CONFIG|ENV|SAMPLE_REPORT|SECRET|SNAG|SPECS|STEM|SampleReport|TICKET|_report_bytes|adopt_conduct|agent|author|evidence|git|implement_reply|repo|report_context|run|verdict) =" tests/integration/test_stages.py` prints nothing: the hub files no longer define a moved name.
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/stages_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the base commit's passed count plus the 4 new tests in `tests/integration/test_stages_helpers_repo.py`, the same skipped count as on the base commit, and no failures; both numbers are recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object).

## Verification
```
./dev.py test tests/unit/test_stages_helpers.py
./dev.py test tests/integration/test_stages_helpers_repo.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test that runs today fails or is skipped, or a skipped test becomes unskipped.
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/stages_helpers.py` defines a class that duplicates a shared fake or a copied reply or config helper.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 30m
- stuck: 60m
- reason: 38 import lines and the hub definitions move in one change because a name must resolve in every importer at once; splitting by importer leaves a name defined in two places, and the files share one module so they stay together
