---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- estimate-calibration

## Context
- clutch/supervise_idle.py
- clutch/drain.py::_Drain.run
- clutch/serve.py::Serve.dispatch
- tests/unit/test_supervise_idle_hooks.py
- tests/unit/test_drain_report_intake.py
- tests/unit/test_driver_hooks.py::test_drain_runs_driver_between_tickets
- tests/fakes.py
- docs/how-clutch-works.md#7.1
- docs/how-clutch-works.md#7.2

## Goal / Why
Roadmap row 142 (`estimate-calibration`, owner request 2026-11-17), part 2 of 3. Part 1 (`estimate-calibration`) adds `clutch/calibration.py`, the `calibration.every` config key (default 100) and `clutch engine calibrate`. That command journals one `estimate_calibration` signal: per provider and model, the median estimate and the median and 90th-percentile actual minutes of the last `calibration.every` completed Implement calls. The row also asks the engine to run that calibration by itself, every `calibration.every` settled Implement runs at its idle point. Until then the table goes stale unless someone runs the command. A settled Implement run here is a completed Implement call: an `effect_completion` whose key has the Implement shape `llm/<stem>/<run_seq>/implement/<attempt>/<call_seq>`.

The engine's idle point is where drain and serve already supervise held stems (`clutch/supervise_idle.py::supervise_idle`, roadmap row 114). In drain it is the between-tickets block, which never runs inside one ticket's retry cycle. In serve it is the dispatch loop's `supervise()` step: it runs under `self.mutations()`, only when serve is idle and not stopping, paused, stopped or killed, and before the next dispatch.

When this ticket is done, drain and serve each check at that point whether at least `calibration.every` Implement calls have completed since the latest `estimate_calibration` signal. When they have, they run part 1's `calibrate` once, which journals a new signal and so resets the count. Neither loop calibrates while busy or paused, and neither calibrates again before `every` more calls complete.

## Scope in / Scope out
In, `clutch/calibration.py`, which part 1 creates (read it first). Add these two functions before `calibrate`; nothing else in the file changes:
- `due(events, every) -> bool`. Walk events in journal order. A `signal` event whose `signal` is `ESTIMATE_CALIBRATION` resets a count to 0. An `effect_completion` whose key fullmatches the Implement key pattern part 1 uses in `implement_runs` adds 1. Return `count >= every`.
- `calibrate_when_due(checkout) -> None`. Read `every = checkout.config.calibration.every`. When `due(checkout.journal.read(), every)`, call `calibrate(checkout.journal, checkout.fs, checkout.repo, every)`.

In, engine loops. Each gets one import (`from clutch.calibration import calibrate_when_due`) and one call:
- `clutch/drain.py::_Drain.run`: `calibrate_when_due(self.c)` right after `await supervise_idle(self.c, make_ctx)`, inside the same `if await self._between_tickets():` block.
- `clutch/serve.py::Serve.dispatch`: `calibrate_when_due(self.checkout)` right after `await supervise_idle(self.checkout, make_ctx)`, inside `supervise()`, under the same lock and guards.

In, tests:
- New `tests/unit/test_calibration_idle.py` (criteria 1-4). It builds journals with `tests.fakes.FakeJournal`, `FakeClock` and `FakeFileSystem`, using its own small builder for Implement intent and completion events. It reuses `serve_rig`, `drain_rig`, `Checkout` and `EndPoll` from `tests/unit/test_supervise_idle_hooks.py`, and `Journal` and `arrival` from `tests/unit/test_supervise_idle_point.py`, as `test_supervise_idle_hooks.py` already does.
- Existing unit tests drive drain and serve through their idle point with stand-in configs that have no `calibration` field, so the new call raises `AttributeError` there. A prototype failed 9 tests: 7 in `tests/unit/test_supervise_idle_hooks.py`, plus `tests/unit/test_drain_report_intake.py::test_loop_intakes_reports_after_tickets` and `tests/unit/test_driver_hooks.py::test_drain_runs_driver_between_tickets`. The only edit to each is one line that stubs the new hook, the way those tests already stub `intake` and `report_intake`:
  - `test_supervise_idle_hooks.py`: `monkeypatch.setattr(serve, "calibrate_when_due", lambda checkout: None)` at the end of `serve_rig`, and the same for `drain` at the end of `drain_rig`.
  - `test_drain_report_intake.py`: the `drain` line after the `report_intake` patch.
  - `test_driver_hooks.py::test_drain_runs_driver_between_tickets`: the `drain` line after the `report_intake` patch.
  - No assertion in these files changes.

In, `docs/how-clutch-works.md`. Only these sentences change:
- Section 7.1, step 2: after "run the roadmap driver after a settle (section 7.5)," insert "calibrate estimates once `calibration.every` Implement calls have completed since the last calibration (`engine calibrate`, section 2.1),".
- Section 7.2: after the roadmap driver paragraph, a new paragraph: "At each idle dispatch point, after supervising held stems, serve calibrates estimates once `calibration.every` Implement calls have completed since the last calibration (`engine calibrate`, section 2.1)."
- Section 11's `calibration` row, added by part 1, gains "; drain and serve also calibrate at their idle point once that many have completed since the last calibration (section 7)".

A scratch prototype of part 1 plus exactly this change on `6e6d9154` touched part 1's files and these 8. The full unit suite (926 tests), `ruff check`, `ruff format --check` and the full integration suite (3,410 tests) passed. Removing the serve call failed only `test_serve_calibrates_at_its_idle_point[idle]`, and removing the drain call failed only `test_drain_calibrates_between_tickets[True]`.

Merge order. Part 3 (`estimate-calibration-author`) also fences `clutch/calibration.py` and `docs/how-clutch-works.md`. It appends `latest` after `render` and edits section 9.3. This ticket inserts before `calibrate` and edits sections 7.1, 7.2 and 11. Neither touches the other's lines, so either order merges and every criterion holds. No other confirmed, unmerged ticket fences `clutch/drain.py`, `clutch/serve.py` or these tests. `cli-group-provider` and `evidence-record-doc-section` edit sections 2.1, 8.1 and the new 10.4 of `docs/how-clutch-works.md`, none of the lines this ticket changes.

Out:
- `engine calibrate`, the calculation, the signal, and the `calibration` config key (part 1), and Author's prompt and the authoring guide (part 3).
- `engine run`, which runs one ticket and has no idle point, and the retro, driver and supervisor hooks, which keep their order and conditions.
- A separate enable switch or a second config key: `calibration.every` is the only knob the row names.
- `clutch/docs/host-running.md`, whose `engine calibrate` row stays true, and `clutch/docs/host-contract.md`, whose inventory does not change.

## Scope fence
- clutch/calibration.py
- clutch/drain.py
- clutch/serve.py
- docs/how-clutch-works.md
- tests/unit/test_calibration_idle.py
- tests/unit/test_supervise_idle_hooks.py
- tests/unit/test_drain_report_intake.py
- tests/unit/test_driver_hooks.py

## Acceptance criteria
1. `tests/unit/test_calibration_idle.py::test_due_counts_implement_completions_since_the_latest_calibration` journals two Implement calls, an `estimate_calibration` signal, one Implement call and one `review` call. `due(events, 2)` is `False`. After one more Implement call it is `True`. Ruled out: counting calls before the latest signal (`True` too early) and counting the review call.
2. `tests/unit/test_calibration_idle.py::test_calibrate_when_due_journals_only_when_due` uses a checkout with `config.calibration.every == 2`. After one Implement call, `calibrate_when_due` journals no signal. After a second call, two `calibrate_when_due` calls journal exactly one `estimate_calibration` signal. Ruled out: calibrating before `every` calls, and calibrating on every idle poll once due.
3. `tests/unit/test_calibration_idle.py::test_serve_calibrates_at_its_idle_point`, parametrized over idle, busy (`upgrade_idle` false) and paused, with `supervise_idle`, `calibrate_when_due` and `dispatch_next` replaced by recorders. Idle records `supervise` (locked), then `calibrate` (locked, given `s.checkout`), then dispatch (unlocked). Busy records only dispatch. Paused records nothing. Ruled out: calibrating while busy or paused, outside `self.mutations()`, or after dispatch.
4. `tests/unit/test_calibration_idle.py::test_drain_calibrates_between_tickets`, parametrized over a settled last ticket and one inside its retry cycle (last state `gate_failed`, not in the Reject queue). The settled case records `supervise`, then `calibrate` given `self.c`. The retry case records nothing. Ruled out: calibrating inside a ticket's retry cycle, or before supervision.
5. `./dev.py test tests/unit/test_supervise_idle_hooks.py tests/unit/test_drain_report_intake.py tests/unit/test_driver_hooks.py tests/unit/test_supervise_idle_point.py` exits 0. In the first three files only the stub lines named in Scope in are added, and `test_supervise_idle_point.py` is unchanged.
6. `grep -c 'estimates once .calibration.every. Implement calls have completed since the last calibration' docs/how-clutch-works.md` prints `2` (the section 7.1 and 7.2 sentences), and `grep -c 'drain and serve also calibrate at their idle point' docs/how-clutch-works.md` prints `1`.
7. `./dev.py test` exits 0. Check's `unit` (with the coverage gate) and `integration` mechanical checks in `config.yaml` run both full suites. Integration tests that run drain or serve with a real config keep passing, because they complete fewer than 100 Implement calls.

## Verification
```
./dev.py test tests/unit/test_calibration_idle.py tests/unit/test_calibration.py tests/unit/test_supervise_idle_hooks.py tests/unit/test_drain_report_intake.py tests/unit/test_driver_hooks.py tests/unit/test_supervise_idle_point.py
./dev.py test tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- Drain or serve calibrates anywhere but its idle point, during a ticket's retry cycle, while busy, paused or stopping, or outside serve's mutation lock.
- The cadence counts wall-clock time, merges or settled tickets instead of completed Implement calls, or adds a config key or switch.
- An existing assertion in a fenced test is changed, dropped or loosened, or a fenced test gains more than the stub lines.
- `engine calibrate`, `calibrate`'s window or rows, the signal body, Author's prompt, or a file outside the fence changes.

## Time budget
- expected: 15m
- stuck: 30m
