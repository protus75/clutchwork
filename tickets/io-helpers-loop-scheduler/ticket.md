---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- io-helpers-config
- shared-git-fake-integration
- shared-review-script
- shared-serve-rig-config

## Context
- tests/fakes.py
- tests/git_fake.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_scheduler.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in later batch tickets, and most of them import their scaffolding from a few large skipped hub files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is one of five per-hub tickets that replace `io-helpers-loop`, which stopped three runs in a row with an empty diff because 26 names and 48 importers did not fit one run. Each hub's names move together with that hub's importers, so every name still resolves in exactly one place. The five write one module and chain by `## Depends on`: `io-helpers-loop-scheduler` -> `io-helpers-loop-triage` -> `io-helpers-loop-terminal` -> `io-helpers-loop-restart` -> `io-helpers-loop-serve-rig`.

When this ticket is done, `tests/loop_helpers.py` and `tests/unit/test_loop_helpers.py` exist and `tests/loop_helpers.py` defines every name that another test file imports from `tests/integration/test_scheduler.py` (`Rig`, `Time`, `text`, `turn`, `scheduler_import_closure`), and each of the 16 importers takes it from `tests.loop_helpers`. This is the first link of the chain: it creates the two new files and the later tickets append to them.

The helpers follow `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a disk write only under a `tmp_path` the caller passes in. A model-reply helper reuses `tests/stage_replies.py` and config text reuses `tests/config_fixture.py`; a helper never copies either. `tests/loop_helpers.py` imports from no `tests/integration/` test file (it may import `tests/*_helpers.py` modules, `tests/stage_replies.py` and `tests/config_fixture.py`).

## Boundary contract
### Shared scheduler test rig
- disposition: create
- owner: tests/loop_helpers.py
- consumers: the 16 test files listed in `## Scope fence` that import `Rig`, `Time`, `text`, `turn`, `scheduler_import_closure` from `tests/integration/test_scheduler.py`, and the later batch tickets that restore the skipped ones
- observable change: `Rig`, `Time`, `text`, `turn` and `import_closure` (as `scheduler_import_closure`) move from `tests/integration/test_scheduler.py` into the new `tests/loop_helpers.py`, `Rig` and the others keep their behavior but run on the shared fakes where they touched a process or git; every importer's import line changes to `tests.loop_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_loop_helpers.py` imports each name this ticket moves from `tests.loop_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_loop_helpers.py
- post-merge source of truth: tests/loop_helpers.py
- closest existing: `tests/fakes.py` (FakeClock, FakeExec, FakeFileSystem, FakeJournal, `turn`, `until`) and `tests/git_fake.py::GitFake` supply the fake seams but none of the scaffolding below; `tests/fakes.py::FakeClock` has only `__call__` and `advance`, with no async `sleep` or advance-triggered wakeup, so it cannot stand in for `Time`; the hub's `Rig` and `Time` live in a skipped file, so a skipped importer cannot reuse them
- earning reason: consolidation of evidenced duplicates and shared use: 16 files import these names from `tests/integration/test_scheduler.py`, and the hub is skipped, so no importer can be restored until the names live in an unskipped module that follows the I/O rules

## Scope in / Scope out
Scope in:
- Create `tests/loop_helpers.py` holding the names `Rig`, `Time`, `text`, `turn`, `scheduler_import_closure`, each rewritten as described, keeping its signature unless a change is named.
- `Time` moves into `tests/loop_helpers.py` unchanged in body and signature (`__call__`, async `sleep` with deadline futures, and `advance` that resolves them). It does no I/O, and `tests.fakes.FakeClock` (`tests/fakes.py:19`) has only `__call__` and `advance`, without the deadline-driven async `sleep` that `Rig` passes to `Watcher`, so `Time` is not a re-export of `FakeClock` and `tests/fakes.py` is not edited. `Rig` keeps using `Time`.
- `Rig` moves with its writes of config and ticket files confined to the `tmp_path` its caller passes in, no process and no git. `text` moves unchanged in body and signature.
- `turn` is re-exported from `tests.fakes` (`from tests.fakes import turn`), with no second definition in `tests/loop_helpers.py`; the hub's own `async def turn` is deleted and the hub imports `turn` back from `tests.loop_helpers`. If the hub's `turn` differs in behavior from `tests.fakes.turn`, stop as a premise failure naming the difference.
- The hub's `import_closure` moves as `scheduler_import_closure` (the mergequeue function of the same name moved in `io-helpers-daemon`); the hub imports it back as `scheduler_import_closure as import_closure`, and the two importers `test_daemon_composition.py` and `test_serve_lifecycle.py`, which also import the daemon one, import it as `scheduler_import_closure as import_closure` where they import the other. `scheduler_import_closure(sources)` takes a mapping of module name to source text and reads no file.
- The hub `tests/integration/test_scheduler.py` keeps `assert_reachable` and every test; `tests/integration/serve_rig.py` and `tests/integration/test_restart_timers.py` are importers of this hub and change only their import lines for `text`, `Time` and `turn`.
- `tests/regress_serve_reoffer_dispatch.py` imports `Rig` from this hub, takes it from `tests.loop_helpers`, and stays green.
- The unit test for `scheduler_import_closure` passes a hand-built in-memory mapping (for example `{"clutch.__main__": "from clutch import a", "clutch": "", "clutch.a": ""}`) and asserts the reached set, never the real package sources. The `Time` test awaits `sleep` and checks that `advance` past the deadline wakes it, with no real sleep.
- In every importer listed in `## Scope fence` (the 16 files that import a moved name from `tests/integration/test_scheduler.py`), change only the import line (also an import line inside a function) so each moved name comes from `tests.loop_helpers`. Names an importer takes from other hubs stay as they are, and a module import (`from tests.integration import <hub>`) is not an import of a name and stays. A file that is both hub and importer here also changes only its import lines.
- The hub `tests/integration/test_scheduler.py` deletes its definition of every moved name it defines and imports the name back from `tests.loop_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line and every name it defines that no other file imports); the hub module keeps each moved name as a module attribute.
- Create or extend `tests/unit/test_loop_helpers.py`: one test per moved name, each running without reading a repo file and calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name this ticket moves is importable from `tests.loop_helpers`.
- `tests/loop_helpers.py` starts no process, runs no real git, and calls no real sleep: grep criterion 4 checks it.
- Record the base-commit and candidate integration pass and skip counts in `run.md` (criterion 5). The run adds no new test to a hot test file: the only edits in `tests/integration/test_cli.py`, `test_drain.py`, `test_daemon_composition.py`, `test_stages.py`, `test_mergequeue.py`, `test_watch.py` or `serve_rig.py` are import lines the move forces.
- - Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.
Scope out:
- Restoring any skipped test file (later batch tickets): a hub file stays skipped and its tests are unchanged; skipped importers may still break semantically and their batch ticket fixes that.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior (except `Time`, which moves unchanged where Scope in says so).
- Defining in `tests/loop_helpers.py` a class that duplicates `tests/fakes.py` or `tests/git_fake.py`, or a copied reply or config helper.
- Names that other hubs own: each of the other four `io-helpers-loop-*` tickets moves its own hub's names, and this ticket leaves their definitions and importers alone.

## Scope fence
- tests/loop_helpers.py
- tests/unit/test_loop_helpers.py
- tests/integration/test_scheduler.py
- tests/integration/serve_rig.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_notify.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_restart_timers.py
- tests/integration/test_serve_admission.py
- tests/integration/test_serve_dispatch.py
- tests/integration/test_serve_driver.py
- tests/integration/test_serve_driver_overlap.py
- tests/integration/test_serve_kill.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_serve_upgrade.py
- tests/integration/test_watchdog.py
- tests/integration/test_watchdog_activation.py
- tests/regress_serve_reoffer_dispatch.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_loop_helpers.py` passes; `tests/unit/test_loop_helpers.py` checks that `Rig` built over `tmp_path` writes only under `tmp_path`, that `Time` wakes an awaited `sleep` when `advance` passes the deadline, that `scheduler_import_closure` returns the reached set of a hand-built mapping, and that `tests.loop_helpers.turn is tests.fakes.turn`.
2. `grep -rPzl "from tests\.integration\.test_scheduler import" tests --include=*.py` lists no file: no file imports a name from the hub.
3. `grep -nE "^(async def|def|class) (Rig|Time|text|turn|import_closure)\b|^(Rig|Time|text|turn|import_closure) =" tests/integration/test_scheduler.py` prints nothing: the hub no longer defines a moved name.
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/loop_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the same number of passed and skipped tests as on the base commit, both recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object).

## Verification
```
./dev.py test tests/unit/test_loop_helpers.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test that runs today fails or is skipped, or a skipped test becomes unskipped.
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/loop_helpers.py` defines a class that duplicates a shared fake or a copied reply or config helper.
- `tests/loop_helpers.py` imports from a `tests/integration/` test file, or a name moved by another of the five tickets is moved here.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 20m
- stuck: 40m
- reason: five names and 16 one-line import edits; `Rig` is the only body that needs a rewrite
