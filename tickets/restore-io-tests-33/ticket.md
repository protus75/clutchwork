---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- restore-helpers-misc
- restore-io-tests-28
- restore-io-tests-34

## Context
- tests/integration/test_status.py
- tests/integration/test_step_events.py
- tests/integration/test_step_icons.py
- tests/integration/test_storm.py
- tests/fakes.py
- tests/conftest.py
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/vscode_step_icons.js

## On-demand
- tests/integration/test_storm_hold.py
- vscode-clutchwork/extension.js

## Goal / Why
`integration-disk-io-skip` skipped 184 integration test files after one run wrote 975 MB in 119,498 files and 1,531 real git repos. This ticket restores the status, step-event, step-icon and storm test files (98 tests). Each loses its `pytestmark = pytest.mark.disk_io_skip` line and passes under the rules of `clutch/docs/host-authoring.md#Unit and integration tests`, fast (no test above 1.0 s) and on the shared fakes. The storm tests keep their real journal files under `tmp_path` because journal persistence (torn lines, roll, restart) is their subject; the live drain tests in `test_storm_hold.py` build their root on the fake-backed drain helpers. `test_step_icons.py` starts `node` today (a process the I/O guard forbids), so its icon test reads the icon table from `vscode-clutchwork/extension.js` as text instead (see the file entry).

## Boundary contract
none
- reason: tests encoding an existing contract; the production code under test, its callers, outputs, failures and side effects are unchanged and only test files move or change

## Scope in / Scope out
Scope in, per file (base-commit facts; the implementer re-reads each file first):
- `tests/integration/test_status.py` (297 lines, 9 tests): `make_root` repo, real `Git(SubprocessExec(), commit_lock=commit_lock(...))` (`commit_lock` now from `tests/misc_helpers.py`), `LocalFileSystem` with `write` patched to raise, retro `rig`/`completed`/`merged` and `PROPOSAL` (misc helpers), reads `runner.SPECS_DIR / 'retro.md'` for the spec version and for a rewritten `version: "7.3"` copy: the spec text comes from a `tmp_path` specs directory installed on `SPECS_DIR` (as `tests/unit/test_roadmap_author.py` does), so nothing reads the repo. The tmp spec is a minimal valid retro spec: front matter `llm_surface: retro`, `tier: medium`, `effort: high`, `version: "1.7"` and a short `## Role` body, written once through a `tmp_path` fixture in the file; the expected `spec_version` is computed from it with `load_spec`, as the version-7.3 test at base already does. If the retro stage cannot render from that minimal spec, stop as a premise failure naming what it needs. Several tests compare every file under the root before and after a read-only verb (real files under `tmp_path`, allowed in unit). Git to `GitFake`. `invoice`, `review` and `rows` are imported from `tests.integration.test_scorecard`; `restore-io-tests-28`, a dependency, moves that file to `tests/unit/test_scorecard.py` and repoints this import line. Final path: `tests/unit/test_status.py`.
- `tests/integration/test_step_events.py` (46 lines, 2 tests): `context`/`repo` from the config helpers (formerly `test_merge.py`) and `STEM`, `agent`, `author`, `verdict` from the stages helpers; ticket files and the stage log under `tmp_path`; git to `GitFake`. Final path: `tests/unit/test_step_events.py`.
- `tests/integration/test_step_icons.py` (47 lines, 2 tests): `test_every_step_has_a_distinct_icon` runs `node tests/vscode_step_icons.js` through `subprocess.run`, which the guard forbids. That harness stubs the `vscode` module, activates `vscode-clutchwork/extension.js` and reads `steps.getTreeItem({kind}).iconPath.id` for each kind in `STEP_KINDS` (null when the kind has no entry). In `extension.js`, `StepsTree.getTreeItem` holds one object literal `const icons = { meta_start: ['symbol-file'], meta_ok: ['symbol-file', 'testing.iconPassed'], ... }` keyed by step kind, each value an array whose first item is the icon id (a ThemeIcon id) and whose optional second item is a theme color. Replace the process with a text read of that file (anchored on `Path(__file__)`, a repo read that writes nothing, so the file stays under `tests/integration/`): extract the literal's keys and first array items in Python (quote the keys and `ast.literal_eval` the literal) and build the same `icons` mapping the harness printed (`None` for a kind with no key). Keep all four assertions: every `STEP_KINDS` key has an icon, no icon is empty, kinds of one step share one icon, distinct steps have distinct icons. If the literal's shape differs from this description, stop as a premise failure naming the difference. `test_recent_step_events_use_the_vocabulary` needs no change. Leave `tests/vscode_step_icons.js` and the extension untouched. Final path: `tests/integration/test_step_icons.py`.
- `tests/integration/test_storm.py` (283 lines, 38 tests): `StormLedger` over a real `Journal` and `Box(LocalFileSystem())` under `tmp_path`, with torn-line and corruption cases, roll and restart; it asserts `list(tmp_path.iterdir()) == []` after idle reads. These are real files under `tmp_path` by design (journal persistence is the subject), so only the clock changes to `FakeClock` where a per-file clock remains, and the file moves to `tests/unit/test_storm.py`. It exports `SIG` and `snapshot` to `test_storm_hold.py` (this ticket) and imports `assert_production_reachable` from `test_storm_producer.py` inside one test (`restore-io-tests-34`, a dependency, restores that file at `tests/unit/test_storm_producer.py` and repoints the import). `test_storm_producer.py` and `test_storm_notification_activation.py` import `SIG` and `snapshot` from this file: change those import lines in `tests/unit/test_storm_producer.py` and `tests/unit/test_storm_notification_activation.py` (the paths `restore-io-tests-34` gives them) to `tests.unit.test_storm`, and nothing else in them. Final path: `tests/unit/test_storm.py`.
- `tests/integration/test_storm_hold.py` (677 lines, 47 tests): live-drain tests: `LiveStorm`/`CoreRig` over `make_root` repos with real git, `drain`, `Lockfile`, control-request files under the state dir, journal corruption cases; imports `CoreRig` (daemon helpers), `NoChild` and `Script`, `commit_ticket`, `confirmed`, `make_root`, `pause_checkout` (drain helpers), `SIG`, `snapshot` (from `test_storm`, moving to `tests/unit/test_storm.py`), and `digest`, `occurrences`, `six`, `trips`, `ARRIVAL` from `test_storm_notification_activation.py` and `test_storm_producer.py` (restored by `restore-io-tests-34`, a dependency, which repoints these lines to `tests.unit.`). Git to `GitFake`, processes to `FakeExec`/`NoChild`, journal to `FakeJournal` except in the persistence-corruption tests, control files stay under `tmp_path`. Final path: `tests/unit/test_storm_hold.py`.

Scope in, every file above:
- Delete the line `pytestmark = pytest.mark.disk_io_skip` (and `import pytest` only when nothing else in the file uses it).
- Rewrite the test body wiring, keeping every test function, parametrization, name and assertion: git becomes `GitFake` from `tests/git_fake.py` (overrides by member name, `fake.calls`); a process becomes `FakeExec` from `tests/fakes.py` or an in-process `clutch.__main__.main([...])` call (when `main` builds its own `SubprocessExec`, replace that construction point with the `fake_exec` fixture's object through `monkeypatch`); the journal becomes `FakeJournal` unless the test's subject is journal persistence; time becomes `FakeClock` plus `until`/`turn`, never a sleep; code taking the `clutch.seams.FileSystem` seam gets `FakeFileSystem`.
- Reuse only the shared modules: `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` and `tests/{cli,drain,stages,daemon,config,loop,misc}_helpers.py`. The modules created by `restore-helpers-misc` and its chain (`restore-helpers-cli` through `restore-helpers-misc`) and by `shared-git-fake-integration`, `shared-review-script` and `shared-serve-rig-config` are merged before this ticket runs; read them in the worktree before editing. Names the files import from `tests.integration.test_cli`, `test_drain`, `test_stages`, `test_scheduler`, `test_rework` and the other hubs already come from those helper modules; keep each import line that names a helper module as it is.
- Placement by the unit and integration test rules in the host authoring guide (the Context section): a file whose rewritten tests still write real files (only under `tmp_path`), or use only fakes, moves to `tests/unit/` (the final path above; same file name, `_flow` suffix where `tests/unit/` already has that name); a test that reads a repo file anchored on `Path(__file__)` and writes nothing stays under `tests/integration/`; a file needing both is split into the two paths named above, each test function keeping its name. Moving a file means deleting the old path in the same change.
- Update the import lines of every other file that imports a name from a file this ticket moves (the fence lists them); only those import lines change in them.
- If a shared fake lacks a behavior a test needs, stop as a premise failure naming the missing behavior and the test; never edit a shared module and never add a `Fake*`/stand-in class or a copy of a helper to a test file.

Scope out: every file under `tests/` not listed above except the importers named in the fence, `tests/fakes.py`, `tests/git_fake.py`, `tests/conftest.py`, `tests/integration/conftest.py`, `tests/integration/serve_rig.py`, the helper modules, `clutch/`, and `docs/`. No test is deleted, skipped, weakened or given a sleep; assertions keep their meaning.

## Scope fence
- tests/integration/test_status.py
- tests/integration/test_step_events.py
- tests/integration/test_step_icons.py
- tests/integration/test_storm.py
- tests/integration/test_storm_hold.py
- tests/unit/test_status.py
- tests/unit/test_step_events.py
- tests/unit/test_storm.py
- tests/unit/test_storm_hold.py
- vscode-clutchwork/extension.js
- tests/unit/test_storm_producer.py
- tests/unit/test_storm_notification_activation.py

## Acceptance criteria
1. `grep -lx "pytestmark = pytest.mark.disk_io_skip" tests/unit/test_status.py tests/unit/test_step_events.py tests/integration/test_step_icons.py tests/unit/test_storm.py tests/unit/test_storm_hold.py` lists none of the paths (exit 1 with no output; every file still carrying the marker is a rejection).
2. `./dev.py test tests/unit/test_status.py tests/unit/test_step_events.py tests/integration/test_step_icons.py tests/unit/test_storm.py tests/unit/test_storm_hold.py --durations=0` passes, and its durations output (recorded in `run.md`) lists no restored test above 1.0 s.
3. `./dev.py test tests/unit/test_status.py tests/unit/test_step_events.py tests/integration/test_step_icons.py tests/unit/test_storm.py tests/unit/test_storm_hold.py --collect-only -q` collects 98 tests, equal to the count `./dev.py test tests/integration/test_status.py tests/integration/test_step_events.py tests/integration/test_step_icons.py tests/integration/test_storm.py tests/integration/test_storm_hold.py --collect-only -q` gives on the base commit; `run.md` records both counts (fewer collected means a test was deleted).
4. `grep -nE "^\s*class (Fake|Stub|Empty)\w*|time\.sleep|import subprocess|SubprocessExec\(\)" tests/unit/test_status.py tests/unit/test_step_events.py tests/integration/test_step_icons.py tests/unit/test_storm.py tests/unit/test_storm_hold.py` prints nothing (no new fake class, no real sleep, no real process).
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` both exit 0.

## Verification
```
./dev.py test tests/unit/test_status.py tests/unit/test_step_events.py tests/integration/test_step_icons.py tests/unit/test_storm.py tests/unit/test_storm_hold.py --durations=0
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test is deleted, skipped, weakened, or loses an assertion, or the collected-test count differs from the base commit.
- A new `Fake*`/stand-in class or a copy of a shared helper appears in a test file, or a shared module (`tests/fakes.py`, `tests/git_fake.py`, a helper module, `tests/conftest.py`, `tests/integration/conftest.py`, `tests/integration/serve_rig.py`) is edited.
- A restored integration test writes disk, starts a process, or runs git.
- A sleep is added, or a restored test takes more than 1.0 s.

## Time budget
- expected: 30m
- stuck: 60m
- reason: the batch is cut at about 1,400 lines (1350 here) so files sharing fixtures stay together; the files are restored by mechanical edits to import lines and fake wiring.
