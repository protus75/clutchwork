---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- io-helpers-cli
- shared-git-fake-integration

## Context
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_drain.py
- tests/integration/test_drain_reentry.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` now fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in batch tickets authored after this helper chain merges. Most skipped files import their scaffolding from a few large skipped files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is step 2 of 7 in the helper chain (`io-helpers-cli`, `-drain`, `-stages`, `-daemon`, `-config`, `-loop`, `-misc`); each step depends on the one before it.

`tests/integration/test_drain.py` (1746 lines) is imported by 52 files for `make_root`, `Script`, `commit_ticket`, `confirmed`, `drain` and more, and `tests/integration/test_drain_reentry.py` by 14 for `NoChild` and a second `drain`; both build their repository with real git and run `engine drain` in a subprocess-backed checkout.

When this ticket is done, `tests/drain_helpers.py` defines every name that another test file imports from `tests/integration/test_drain.py` and `tests/integration/test_drain_reentry.py` (the names are listed under Scope in), and each of those 57 importers takes it from `tests.drain_helpers`. The helpers use the shared fakes, so a restored test file that needs them does not start a process or run git, and a later batch ticket can turn a file back on without first fixing a helper that sits in a skipped file.

The helpers follow the rules in `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`, created by `shared-git-fake`; read it in the worktree), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a journal as `tests.fakes.FakeJournal` unless the helper's subject is journal persistence, and a disk write only under a `tmp_path` the caller passes in. A model-reply helper or config text reuses `tests/stage_replies.py` and `tests/config_fixture.py` (created by `shared-review-script` and `shared-serve-rig-config`, merged before `shared-fakes-guard`); a helper never copies either. The owner requires restored tests to be fast and to reuse shared fixtures: this module is the one place each helper below lives.

## Boundary contract
### Shared drain test helpers
- disposition: create
- owner: tests/drain_helpers.py
- consumers: the 57 test files listed in `## Scope fence` that import from `tests/integration/test_drain.py` and `tests/integration/test_drain_reentry.py`, and the later batch tickets that restore the skipped ones
- observable change: the names listed under Scope in move from `tests/integration/test_drain.py` and `tests/integration/test_drain_reentry.py` into `tests/drain_helpers.py`, rewritten onto the shared fakes; every importer's import line changes to `tests.drain_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub (for example `test_cli.Clock` in `tests/integration/test_shared_fakes_adoption.py`) stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_drain_helpers.py` imports each moved name from `tests.drain_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_drain_helpers.py
- post-merge source of truth: tests/drain_helpers.py
- closest existing: `tests/fakes.py` (FakeClock, FakeExec, FakeFileSystem, FakeJournal, `turn`, `until`) and `tests/git_fake.py::GitFake` supply the fake seams but none of the scaffolding below; the hub definitions today do real git and processes, so a skipped file cannot reuse them
- earning reason: consolidation of evidenced duplicates and shared use: 57 files import these names from `tests/integration/test_drain.py` and `tests/integration/test_drain_reentry.py`, and the hub is skipped, so no importer can be restored until the names live in an unskipped module that follows the I/O rules

## Scope in / Scope out
Scope in:
- Create `tests/drain_helpers.py` holding these moved names, each rewritten as described, keeping its signature unless a change is named: `Clock`, `NoChild`, `START`, `Script`, `commit_ticket`, `confirmed`, `drain`, `journal`, `make_root`, `mechanical_first`, `offer_events`, `pause_checkout`, `reentry_drain`, `retry_draws`, `root`, `tos`.
  - From `test_drain.py`: `START` (constant), `Script` (the per-stem scripted stage seam; its lock probe writes a lockfile under `state_dir` inside the `tmp_path` repo), `make_root(tmp_path, caps="")` and the `root` fixture (same files as today, no `git init`/`add`/`commit`: a `GitFake` stands in), `drain(root, script, clock=None)` (in-process `main(["engine","drain"], ...)` with the shared fakes), `journal(root)` (`FakeJournal` as in `tests/cli_helpers.py`), `confirmed(depends, priority)` (pure text), `commit_ticket(root, stem, text)` (writes the ticket file, then records the add and commit on the registered `GitFake` instead of running git), `retry_draws(root, stem)`, `tos(root, stem)`, `offer_events(root)`, `mechanical_first(monkeypatch, stem, workspace=True)`, `pause_checkout(root)` (builds the `Checkout` over `GitFake`, `FakeExec` and `FakeFileSystem` in place of `Git(SubprocessExec(), ...)` and `LocalFileSystem()`), and the `Clock` name (`tests.fakes.FakeClock`).
  - From `test_drain_reentry.py`: `NoChild`, which is the name `NoChild = tests.fakes.FakeExec` (its `run(argv, *, cwd, env, timeout, stdin_path=None)` already returns `(0, "", "")` and records `calls`, which no `NoChild` user reads) and `drain(repo, script, *, green_base=True)`. This second `drain` has a different signature from the `test_drain.py` one, so it is named `reentry_drain` in the new module; its only importer, `tests/integration/test_audit.py`, imports it as `from tests.drain_helpers import reentry_drain as drain`, and the hub keeps the old name through the same alias.
  - The two helpers that need names from hubs not yet moved keep importing them from where they live: `Script`/`make_root` use `PLAN`, `CONFIG`, `ENV`, `git_out`, `ticket`, `with_retro_driver`, `write` from `tests.cli_helpers` (moved by `io-helpers-cli`), and `adopt_conduct` from `tests.integration.test_stages` until `io-helpers-stages`. Because `test_stages.py` itself imports moved names from `tests.drain_helpers`, a module-level import of `test_stages` in `tests/drain_helpers.py` would be an import cycle: `tests/drain_helpers.py` imports `adopt_conduct` inside the body of the one function that calls it (a function-level `from tests.integration.test_stages import adopt_conduct`), never at module level, so importing `tests.drain_helpers` first or `tests.integration.test_stages` first both succeed.
- In every importer listed in `## Scope fence`, change only the import line (also an import line inside a function) so each moved name comes from `tests.drain_helpers`. Every name any file imports from these hubs is moved, except where Scope in says otherwise, so no importer keeps an import from a hub. Names an importer takes from other hubs stay as they are. A module import (`from tests.integration import <hub>`) is not an import of a name and stays.
- Each hub file (`tests/integration/test_drain.py`, `tests/integration/test_drain_reentry.py`) deletes its definition of every moved name it defines and imports the name back from `tests.drain_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line, and every name it defines that no other file imports). Its own tests keep working through the name it imports back; the hub module keeps each moved name as a module attribute.
- Earlier helper modules (`tests/cli_helpers.py`) change only where one of them imports a name this ticket moves.
- Create `tests/unit/test_drain_helpers.py`: one test per moved name that runs without reading a repo file, calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name above is importable from `tests.drain_helpers`. 
- `clutch.__main__.main` builds its own `SubprocessExec` and `Git` (see `clutch/__main__.py`, where `SubprocessExec()` is constructed in each verb branch) and has no parameter for either, so a helper that calls `main` replaces those two names on the `clutch.__main__` module with the shared `FakeExec` and `GitFake` for the duration of the call (a patch inside the helper, never a change under `clutch/`). When a verb a helper drives still reaches a real process after that, the run stops as a premise failure naming the verb and the construction site.
- `test_drain.py` also imports `repo` from `tests/integration/test_merge.py` and `tests/integration/test_terminal.py`; those lines are for later steps and stay. Every function-level `from tests.integration.test_drain_reentry import NoChild` line in `tests/integration/test_drain.py` (in `paused_drain` and the 14 other functions that have one) becomes `from tests.drain_helpers import NoChild`. Each hub's import-back lines, including `test_drain_reentry.py`'s import of `drain` as `reentry_drain`, import from `tests.drain_helpers`, never from the other hub.
- `tests/regress_drain_detach.py`, `tests/regress_drain_park_findings.py`, `tests/regress_drain_signals.py`, `tests/regress_stale_running.py` and `tests/snapshot_scale_fixture.py` import from the hub (outside `tests/integration`) and stay green.

Scope out:
- Restoring any skipped test file (later batch tickets): a hub file stays skipped and its tests are unchanged.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior.
- Defining in `tests/drain_helpers.py` a class that duplicates `tests/fakes.py` or `tests/git_fake.py`: use the shared fakes. A thin subclass is not needed by any moved name. `prior_failure`, `intake_at`, `paused_drain` and `Pause` are imported by no other file and stay in the hub, which keeps its own `from tests.drain_helpers import ...` lines for them to use `journal`, `pause_checkout` and `NoChild`.
- Skipped importers may still break semantically; their batch ticket fixes that.

## Scope fence
- tests/drain_helpers.py
- tests/unit/test_drain_helpers.py
- tests/integration/test_drain.py
- tests/integration/test_drain_reentry.py
- tests/integration/serve_rig.py
- tests/integration/test_ask.py
- tests/integration/test_audit.py
- tests/integration/test_author.py
- tests/integration/test_baseline.py
- tests/integration/test_box.py
- tests/integration/test_box_triage_inbox.py
- tests/integration/test_caps.py
- tests/integration/test_control_cli.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_pause.py
- tests/integration/test_diagnose.py
- tests/integration/test_drain_admissions.py
- tests/integration/test_drain_containment.py
- tests/integration/test_drain_detach.py
- tests/integration/test_drain_signals.py
- tests/integration/test_drain_upgrade.py
- tests/integration/test_harvest.py
- tests/integration/test_hot_paths_snapshot.py
- tests/integration/test_inbox.py
- tests/integration/test_intake_keeps_draft.py
- tests/integration/test_intake_scope.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_ladder.py
- tests/integration/test_menu_verb_parity.py
- tests/integration/test_merge.py
- tests/integration/test_open_tickets_closed.py
- tests/integration/test_paved_roads.py
- tests/integration/test_reject_queue.py
- tests/integration/test_requisition_gate.py
- tests/integration/test_requisition_identity_record.py
- tests/integration/test_retro.py
- tests/integration/test_retro_box.py
- tests/integration/test_review_command.py
- tests/integration/test_roadmap_author.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_roadmap_start_gates.py
- tests/integration/test_scorecard.py
- tests/integration/test_shared_fakes_adoption.py
- tests/integration/test_snapshot_cache_facts.py
- tests/integration/test_snapshot_merged_cap.py
- tests/integration/test_stages.py
- tests/integration/test_stale_running.py
- tests/integration/test_stats.py
- tests/integration/test_status.py
- tests/integration/test_storm_hold.py
- tests/integration/test_storm_notification_activation.py
- tests/integration/test_storm_producer.py
- tests/integration/test_ticket_write_serialization.py
- tests/integration/test_triage.py
- tests/integration/test_watch.py
- tests/regress_drain_detach.py
- tests/regress_drain_park_findings.py
- tests/regress_drain_signals.py
- tests/regress_stale_running.py
- tests/snapshot_scale_fixture.py
- tests/cli_helpers.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_drain_helpers.py` passes, and `tests/unit/test_drain_helpers.py` checks that `make_root(tmp_path)` leaves no `.git` directory, that `commit_ticket` writes `tickets/<stem>/ticket.md` and records an add and a commit in the registered `GitFake`'s `fake.calls` (not a real commit), and that `reentry_drain` and `drain` are two different functions.
2. `grep -rnE "from tests\.integration\.(test_drain|test_drain_reentry) import" tests --include=*.py` prints nothing: every name any file imports from these hubs is moved, so a leftover line names the importer that was missed.
3. `grep -nE "^(async def|def|class) (START|Script|commit_ticket|confirmed|drain|journal|make_root|mechanical_first|offer_events|pause_checkout|retry_draws|root|tos|NoChild)\b|^(START|Script|commit_ticket|confirmed|drain|journal|make_root|mechanical_first|offer_events|pause_checkout|retry_draws|root|tos|NoChild) =" tests/integration/test_drain.py tests/integration/test_drain_reentry.py` prints nothing: the hub files no longer define a moved name.
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/drain_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the same number of passed and skipped tests as on the base commit, both recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object).

## Verification
```
./dev.py test tests/unit/test_drain_helpers.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test that runs today fails or is skipped, or a skipped test becomes unskipped.
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/drain_helpers.py` defines a class that duplicates a shared fake or a copied reply or config helper.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 30m
- stuck: 60m
- reason: 57 import lines and the hub definitions move in one change because a name must resolve in every importer at once; splitting by importer leaves a name defined in two places, and the files share one module so they stay together
