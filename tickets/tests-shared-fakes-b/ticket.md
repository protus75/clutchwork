---
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
- shared-test-fakes

## Context
- tests/fakes.py
- tests/integration/test_journal.py::FakeClock
- tests/unit/test_suggest_box.py::MemoryFS
- tests/unit/test_suggest_box.py::memory_box
- tests/unit/test_retro_recurrence.py::MemoryJournal

## Goal / Why
Three test modules define their own clock, filesystem or journal fake that `tests/fakes.py` already provides: `tests/integration/test_journal.py` (`FakeClock`), `tests/unit/test_suggest_box.py` (`MemoryFS`) and `tests/unit/test_retro_recurrence.py` (`MemoryJournal`). After this ticket each uses the shared class (`FakeClock`, `FakeFileSystem`, `FakeJournal`), so a fix to a fake lands in one place. This is the second batch of roadmap row 120, after row 119's five modules.

These were chosen because each local fake is a drop-in for the shared one. The other candidates were checked and left out because they are not drop-ins. `test_providers.py`, `test_git.py`, `test_checkpoint.py`, `test_git_commit.py`, `test_git_tree_id.py` and `test_release.py` each script a per-call result list or assert on the exec call arguments. `test_fault_injection.py::Clock` advances one second per call. `test_premise_overruled.py`, `test_supervise_idle_point.py`, `test_runner_dead_dependents.py` and `test_verdict_extension.py` seed their journal with initial events and use their own `ts` or event version. `test_supervise_cap_lineage.py` defines its own `MemoryJournal` and is not an importer of the one deleted here.

Two groups of modules outside the three import these names, so deleting the local classes forces edits there.
- Five modules import `FakeClock` from `tests.integration.test_journal`: `tests/integration/test_storm_producer.py`, `test_storm_hold.py`, `test_storm.py`, `test_storm_notification_activation.py` and `test_journal_roll.py`. Those imports keep working with no change, because `test_journal.py` binds the shared class under its old name (`from tests.fakes import FakeClock`).
- Eleven modules import `MemoryJournal` from `tests.unit.test_retro_recurrence`: `tests/unit/test_author.py` (inside functions, three sites), `test_roadmap_author.py`, `test_roadmap_ship.py`, `test_roadmap_merged.py`, `test_roadmap_gate.py`, `test_roadmap_accept.py`, `test_paved_roads.py`, `test_roadmap_start_gates.py`, `test_author_roadmap_row.py`, `test_driver_hooks.py` and `test_roadmap_drive.py`. Each switches to `FakeJournal` from `tests.fakes`. This is safe because `EVENT_VERSIONS` in `clutch/journal.py` maps every event type to 1, equal to the version the local class hard-coded, and no importer passes `type_=` as a keyword (the shared `append` names that parameter `type`).

## Scope in / Scope out
Scope in:
- `tests/integration/test_journal.py`: delete `class FakeClock`; add `from tests.fakes import FakeClock`. `T0` stays. Every `FakeClock(T0)` call site already passes the start instant positionally, which the shared `now` parameter accepts. Nothing else in the file changes. Remove the `timedelta` import only if nothing else in the file uses it.
- `tests/unit/test_suggest_box.py`: delete `class MemoryFS`; add `from tests.fakes import FakeFileSystem`; `memory_box` builds `FakeFileSystem()`; and in `test_suggest_output` `monkeypatch.setattr(cli, "LocalFileSystem", MemoryFS)` becomes `monkeypatch.setattr(cli, "LocalFileSystem", FakeFileSystem)`. `FakeFileSystem` takes no constructor arguments, the same as `MemoryFS`, and `fs.files` is keyed by `Path` in both. Nothing else changes.
- `tests/unit/test_retro_recurrence.py`: delete `class MemoryJournal`; add `from tests.fakes import FakeJournal`; each `MemoryJournal()` call site becomes `FakeJournal()`. The shared default clock renders `2026-01-01T00:00:00+00:00`, equal to the `ts` the local class hard-coded. Keep the `Event` import if still used. Nothing else changes.
- The eleven importer modules listed in Goal / Why: replace the `MemoryJournal` import with `from tests.fakes import FakeJournal` (in `test_author.py` keep `message` imported from `tests.unit.test_retro_recurrence`, in each of its three function-level imports) and rename each call site, including the `lambda *a: MemoryJournal()` in `test_roadmap_gate.py`, to `FakeJournal()`. Nothing else changes in those files. If any importer relies on a `type_=` keyword, or appends an event type whose `EVENT_VERSIONS` value is not 1, that module stays out of this batch: leave it untouched, keep a re-export is not allowed, and the ticket stops and names it.
- Add `tests/integration/test_shared_fakes_adoption_b.py`, which pins the identities and the absence of the local classes.

Scope out:
- `tests/fakes.py`, every module that imports `FakeClock` from `test_journal.py`, `tests/unit/test_supervise_cap_lineage.py`, `tests/unit/test_premise_overruled.py`, `tests/unit/test_supervisor_trigger.py`, and every other test file.
- The first-batch modules (roadmap row 119, `tests-shared-fakes-a`).
- Scripted or seeded fakes listed in Goal / Why, and the shared helpers `turn` and `until`.
- If a call site in the changed modules cannot use the shared class unchanged, the ticket stops and names that call site; it does not edit `tests/fakes.py`.

## Scope fence
- tests/integration/test_journal.py
- tests/unit/test_suggest_box.py
- tests/unit/test_retro_recurrence.py
- tests/unit/test_author.py
- tests/unit/test_roadmap_author.py
- tests/unit/test_roadmap_ship.py
- tests/unit/test_roadmap_merged.py
- tests/unit/test_roadmap_gate.py
- tests/unit/test_roadmap_accept.py
- tests/unit/test_paved_roads.py
- tests/unit/test_roadmap_start_gates.py
- tests/unit/test_author_roadmap_row.py
- tests/unit/test_driver_hooks.py
- tests/unit/test_roadmap_drive.py
- tests/integration/test_shared_fakes_adoption_b.py

## Acceptance criteria
1. `tests.integration.test_journal.FakeClock is tests.fakes.FakeClock`, not a local class of the same name. Checked by `./dev.py test tests/integration/test_shared_fakes_adoption_b.py`.
2. The names `MemoryFS` and `MemoryJournal` no longer exist as attributes of `tests.unit.test_suggest_box` and `tests.unit.test_retro_recurrence`, and `tests.unit.test_suggest_box.FakeFileSystem is tests.fakes.FakeFileSystem` and `tests.unit.test_retro_recurrence.FakeJournal is tests.fakes.FakeJournal` (a leftover local class would fail this). Checked by `./dev.py test tests/integration/test_shared_fakes_adoption_b.py`.
3. A `FakeClock(T0)` from `test_journal` returns `T0` (2026-08-04 12:00 UTC), not the shared default 2026-01-01, and `advance(5)` moves it by exactly 5 seconds, not zero. Checked by `./dev.py test tests/integration/test_shared_fakes_adoption_b.py`.
4. The three changed modules, the eleven `MemoryJournal` importers and the five `FakeClock` importers keep their prior results, including `test_suggest_output` in `tests/unit/test_suggest_box.py` (which fails with `NameError` if `MemoryFS` is left referenced) and every importer of `MemoryJournal` (which fails with `ImportError` if one is left on the deleted name). Checked by `./dev.py test tests/integration/test_journal.py tests/unit/test_suggest_box.py tests/unit/test_retro_recurrence.py tests/unit/test_author.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_ship.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_accept.py tests/unit/test_paved_roads.py tests/unit/test_roadmap_start_gates.py tests/unit/test_author_roadmap_row.py tests/unit/test_driver_hooks.py tests/unit/test_roadmap_drive.py tests/integration/test_storm.py tests/integration/test_storm_hold.py tests/integration/test_storm_producer.py tests/integration/test_storm_notification_activation.py tests/integration/test_journal_roll.py`.

## Verification
```
./dev.py test tests/integration/test_shared_fakes_adoption_b.py
./dev.py test tests/integration/test_journal.py tests/unit/test_suggest_box.py tests/unit/test_retro_recurrence.py tests/unit/test_author.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_ship.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_accept.py tests/unit/test_paved_roads.py tests/unit/test_roadmap_start_gates.py tests/unit/test_author_roadmap_row.py tests/unit/test_driver_hooks.py tests/unit/test_roadmap_drive.py tests/integration/test_storm.py tests/integration/test_storm_hold.py tests/integration/test_storm_producer.py tests/integration/test_storm_notification_activation.py tests/integration/test_journal_roll.py
./dev.py test tests/unit
```

## Definition of rejected
The branch is rejected if any importer of `FakeClock` from `test_journal.py` changes, if `tests/fakes.py` changes, if a test's expected value or timestamp changes to make it pass, if a local clock, filesystem or journal class of the replaced names remains in the three modules, or if any file outside the fence changes.

## Time budget
- expected: 35m
- stuck: 70m
- reason: not split because the fourteen edits are mechanical one-line renames of one shared fake, and splitting would leave a deleted class with importers between tickets.
