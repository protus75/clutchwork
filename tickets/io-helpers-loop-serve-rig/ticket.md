---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- io-helpers-loop-restart

## Context
- tests/fakes.py
- tests/git_fake.py
- tests/config_fixture.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/serve_rig.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in later batch tickets, and most of them import their scaffolding from a few large skipped hub files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is one of five per-hub tickets that replace `io-helpers-loop`, which stopped three runs in a row with an empty diff because 26 names and 48 importers did not fit one run. Each hub's names move together with that hub's importers, so every name still resolves in exactly one place. The five write one module and chain by `## Depends on`: `io-helpers-loop-scheduler` -> `io-helpers-loop-triage` -> `io-helpers-loop-terminal` -> `io-helpers-loop-restart` -> `io-helpers-loop-serve-rig`.

When this ticket is done, `tests/loop_helpers.py` also defines the seven names that another test file imports from `tests/integration/serve_rig.py` and that run real git, a process or the real filesystem, or that those names call (`graph`, `admission_graph`, `admission_config`, `enable_upgrade`, `notify_command`, `terminals`, `UpgradeChild`), and each of the 20 importers takes them from `tests.loop_helpers`. `tests/loop_helpers.py` never imports `serve_rig`, so there is no import cycle.

The helpers follow `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a disk write only under a `tmp_path` the caller passes in. A model-reply helper reuses `tests/stage_replies.py` and config text reuses `tests/config_fixture.py`; a helper never copies either. `tests/loop_helpers.py` imports from no `tests/integration/` test file (it may import `tests/*_helpers.py` modules, `tests/stage_replies.py` and `tests/config_fixture.py`).

## Boundary contract
### Shared serve-rig graph builders
- disposition: extend
- owner: tests/loop_helpers.py
- consumers: the 20 test files listed in `## Scope fence` that import `graph`, `admission_graph`, `admission_config`, `enable_upgrade`, `notify_command`, `terminals`, `UpgradeChild` from `tests/integration/serve_rig.py`, and the later batch tickets that restore the skipped ones
- observable change: `graph`, `admission_graph`, `admission_config`, `enable_upgrade`, `notify_command`, `terminals` and `UpgradeChild` move from `tests/integration/serve_rig.py` into `tests/loop_helpers.py`; `graph`, `admission_graph` and `enable_upgrade` stop using git, a process or `LocalFileSystem`, and `notify_command` stops writing a `sys.executable` script; every importer's import line changes to `tests.loop_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_loop_helpers.py` imports each name this ticket moves from `tests.loop_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_loop_helpers.py
- post-merge source of truth: tests/loop_helpers.py
- ordering: `tests/loop_helpers.py` already exists from the earlier tickets of the chain; this ticket appends to it and to `tests/unit/test_loop_helpers.py` and adds no second module.

## Scope in / Scope out
Scope in:
- Add to `tests/loop_helpers.py` (create it if the earlier ticket of the chain is not merged yet, which `## Depends on` rules out) the names `graph`, `admission_graph`, `admission_config`, `enable_upgrade`, `notify_command`, `terminals`, `UpgradeChild`, each rewritten as described, keeping its signature unless a change is named.
- `terminals` (`serve_rig.py` line ~108, read-only over `rig.journal`) and `UpgradeChild` (line ~335) move with the five named functions because `admission_graph` calls `terminals()` (line ~260) and `enable_upgrade` builds `UpgradeChild` (line ~354); if they stayed, `tests/loop_helpers.py` would have to import from `serve_rig` and form a cycle. `serve_rig.py` re-exports both with `from tests.loop_helpers import terminals, UpgradeChild`, so every importer of them that is not listed in `## Scope fence` keeps working.
- `graph` builds its rig through `repository` (from `io-helpers-loop-restart`) and stops overriding `rig.fs.publish` with `LocalFileSystem().publish`: the `FakeFileSystem` publish stays. It uses `reply("declined")` from `tests.loop_helpers`. Its `serve.Serve(...)` `read` and `stems` callables keep reading ticket files from the `tmp_path` root.
- `admission_graph` (about 79 lines, `SubprocessExec` and git today) and `enable_upgrade` (git and files) use `tests/git_fake.py::GitFake`, `tests.fakes.FakeExec` and `tests.fakes.FakeFileSystem`; `enable_upgrade` keeps its signature `enable_upgrade(rig, engine)` and its writes go through `rig.fs` or under `tmp_path`.
- `admission_config(root, *, command=None, safety=False, strategies=())` moves unchanged, importing `amend_config` from `tests.config_fixture` (never from an integration test file).
- `notify_command(root, *, enabled=True)` keeps its signature so no importer changes. Today it writes a `notify` argv of `sys.executable -c <script>` through `amend_config`; the script appends its last argument to `root/deliveries.jsonl` and exits 1 when `root/notify-fails` exists. It becomes `amend_config(root, notify=["notify-sink"] if enabled else None)` (imported from `tests.config_fixture`), and the in-process command is a branch in the scripted-exec wrapper inside `repository` (in `tests/loop_helpers.py`, delivered by `io-helpers-loop-restart`): when `argv[0] == "notify-sink"` it appends `argv[-1] + "\n"` to `root / "deliveries.jsonl"` and returns `(1, "", "")` if `root / "notify-fails"` exists, else `(0, "", "")`, without starting a process. `deliveries(root)` and `notify_completions` stay in `serve_rig.py` unchanged. Before writing it, read `build_notifications` and `CommandNotifications` (`clutch/seams.py`) to confirm the notification command runs through the checkout's exec seam that `repository` wires; if it uses another exec instance, or config validation rejects an unresolved executable, stop as a premise failure naming it.
- `serve_rig.py` keeps its path and every other name it exports (`until`, `write`, `script`, `request`, `trip`, `finish`, `activated_graph`, `active_graph`, `admission_ticket`, `start_admission`, `deliveries`, `notify_completions`, `escalation_batch`, `HeldLLM`, `retro_scenario`) and imports the moved names back from `tests.loop_helpers`. The seven moved names call none of the stay-behind names. `until` stays defined in `serve_rig.py`: `tests/integration/test_serve_rig_fakes.py` asserts `serve_rig.turn is fakes.turn` and that the source of `serve_rig.until` contains `fakes.until`, and stays green.
- The importers of the other `serve_rig.py` names (`activated_graph`, `finish`, `until` and the rest) are not edited, except a line that also imports a moved name, where only the moved names leave that line.
- In every importer listed in `## Scope fence` (the 20 files that import a moved name from `tests/integration/serve_rig.py`), change only the import line (also an import line inside a function) so each moved name comes from `tests.loop_helpers`. Names an importer takes from other hubs stay as they are, and a module import (`from tests.integration import <hub>`) is not an import of a name and stays. A file that is both hub and importer here also changes only its import lines.
- The hub `tests/integration/serve_rig.py` deletes its definition of every moved name it defines and imports the name back from `tests.loop_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line and every name it defines that no other file imports); the hub module keeps each moved name as a module attribute.
- Create or extend `tests/unit/test_loop_helpers.py`: one test per moved name, each running without reading a repo file and calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name this ticket moves is importable from `tests.loop_helpers`. Append only; the earlier tickets' tests stay as they are.
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
- tests/integration/serve_rig.py
- tests/integration/test_box_triage_inbox.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_hostfiles.py
- tests/integration/test_merge.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_serve_admission.py
- tests/integration/test_serve_confirm_during_check.py
- tests/integration/test_serve_dispatch.py
- tests/integration/test_serve_driver.py
- tests/integration/test_serve_driver_overlap.py
- tests/integration/test_serve_kill.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_serve_merge_overlap.py
- tests/integration/test_serve_notify.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/test_serve_scan_head.py
- tests/integration/test_serve_upgrade.py
- tests/integration/test_serve_upgrade_pending.py
- tests/integration/test_watchdog_activation.py
- tests/regress_reconcile_confirming_draft.py
- tests/integration/test_serve_rig_fakes.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_loop_helpers.py` passes; it checks that `notify_command(tmp_path)` writes `notify: [notify-sink]` into `tmp_path/config.yaml` and `notify_command(tmp_path, enabled=False)` removes the key, that a rig from `repository` answers `notify-sink` by appending to `deliveries.jsonl` under `tmp_path` and returns exit 1 once `notify-fails` exists, that `terminals(rig)` returns only non-`running` state transitions, that `UpgradeChild.replace` records its call, that `graph(...)` and `admission_graph(...)` return rigs whose git is a `GitFake` and leave no `.git` directory, and that `serve_rig.until` and `serve_rig.turn` still resolve (`serve_rig.turn is tests.fakes.turn`).
2. `grep -rPzl "from tests\.integration\.serve_rig import (?:\([^)]*|[^\n(]*)\b(?:graph|admission_graph|admission_config|notify_command|enable_upgrade|terminals|UpgradeChild)\b" tests --include=*.py` lists no file (`activated_graph` and `active_graph` stay in `serve_rig.py`; `\bgraph\b` does not match them).
3. `grep -nE "^(async def|def|class) (graph|admission_graph|admission_config|notify_command|enable_upgrade|terminals|UpgradeChild)\b|^(graph|admission_graph|admission_config|notify_command|enable_upgrade|terminals|UpgradeChild) =" tests/integration/serve_rig.py` prints nothing, and `grep -n "serve_rig" tests/loop_helpers.py` prints nothing (no cycle).
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/loop_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the same number of passed and skipped tests as on the base commit, both recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py tests/integration/test_serve_rig_fakes.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object).

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
- expected: 25m
- stuck: 50m
- reason: seven names, two 80-line rewrites onto the shared fakes and 20 import edits; the notify wiring is read-then-write; over 30m would be split again, and the budget is 25m
