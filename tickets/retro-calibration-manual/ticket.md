---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- retro-due-one-owner

## Context
- clutch/serve.py::Serve.check_retro
- clutch/serve.py::Serve.retro_pending
- clutch/serve.py::Serve.run_retro
- clutch/serve.py::Serve.run
- clutch/drain.py::_Drain._run_retro
- clutch/calibration.py
- clutch/retro.py::select_trigger
- clutch/retro.py::project_window
- clutch/doctor.py
- clutch/status.py::project
- clutch/status.py::render
- clutch/config.py::Retro
- clutch/config.py::Calibration
- docs/how-clutch-works.md#9.5 Retro

## On-demand
- tests/integration/serve_rig.py
- tests/integration/test_drain.py
- tests/unit/test_supervise_idle_hooks.py
- tests/unit/test_phase_events.py

## Goal / Why
Owner decision (2026-11-22): retro and estimate calibration stay as features but never run on their own. Today serve and drain start a retro after a settle (`Serve.check_retro`, `_Drain._run_retro(forced=False)`), a due retro holds dispatch through `Serve.retro_pending`, and both engines calibrate at their idle point (`calibrate_when_due`). That spends provider calls and wall time nobody asked for. When done:
- Serve and drain never start a retro or a calibration unprompted, and a due count never holds dispatch. A retro or calibration runs only when an operator runs `clutch engine retro` or `clutch engine calibrate`; an operator-submitted retro request still reaches a running serve or drain and still runs between tickets as today.
- The existing count settings are overdue thresholds. When either feature is overdue, `clutch view status` prints one line for it and `clutch host doctor` adds a WARN row for it, so the operator knows to run the verb. Both are computed from the journal alone (no git read, no provider call).

Automatic trigger sites found by grep (`calibrate_when_due`, `check_retro`, `retro_due`, `run_retro`, `select_trigger`, `retro_pending`, `_run_retro`), all removed except where noted:
- `clutch/serve.py`: `Serve.check_retro` and every call to it wherever it sits (on main today the dispatch wrapper `finally` and `Serve.merge`; after `retro-due-one-owner` the `Serve.run` loop); `retro_due` and `retro_checked` state; `retro_due` inside `retro_pending` (the request clause stays); the `retro_due = False` reset in `run_retro`; `calibrate_when_due(self.checkout)` in the idle `supervise` step and its import.
- `clutch/drain.py`: the unforced `await self._run_retro(forced=False)` branch in the between-tickets block; `retro_terminal_count` and the count dedupe in `_run_retro`; `calibrate_when_due(self.c)` after `supervise_idle` and its import. The forced branch for an operator request stays.
- `clutch/calibration.py`: `calibrate_when_due` has no caller left and is deleted.
- `clutch/retro.py`: `Retro.__call__(forced=False)` keeps its due decision; it now has no engine caller but status and doctor reuse `due_trigger` from `retro-due-one-owner`.

## Boundary contract
### Engine retro and calibration triggers
- disposition: replace
- owner: clutch/serve.py and clutch/drain.py
- consumers: operators running `clutch engine serve`, `clutch engine drain`, `clutch engine retro`, `clutch engine calibrate`; the VS Code extension through the control inbox
- observable change: serve and drain write no retro report, no `estimate_calibration` signal, and no `retro_check` phase events unprompted, and dispatch is never held for a count-due retro; a requested retro (`projection.retro_id`) keeps its path and its hold on admission, because the operator asked for it
- compatibility: old contract is "retro and calibration run automatically at count thresholds"; replacement is "they run when an operator runs the verb". No config key is renamed or removed, so every existing `config.yaml` still loads. `engine retro` and `engine calibrate` behave as today. Consumers migrate by running the verbs when the overdue line or WARN row appears; no alias or flag keeps the old behavior
- acceptance: with the retro and calibration thresholds exceeded, a serve run and a drain run start no retro and no calibration, and a ticket that becomes eligible is admitted while the window is overdue
- tests: tests/unit/test_no_automatic_retro_calibration.py, tests/unit/test_manual_retro_calibration_verbs.py
- post-merge source of truth: clutch/serve.py, clutch/drain.py, docs/how-clutch-works.md

### Overdue report
- disposition: extend
- owner: clutch/status.py (the pure overdue lines), with `clutch/retro.py` and `clutch/calibration.py` owning the counts
- consumers: `clutch view status` (`_status` in clutch/__main__.py), `clutch host doctor` (clutch/doctor.py)
- observable change: status prints `retro overdue: N tickets settled since the last retro; run `clutch engine retro`` (settled trigger; the merges and spike triggers name merged tickets or the spike kind and count) and `calibration overdue: N Implement calls completed since the last calibration; run `clutch engine calibrate``, one line per overdue feature and none otherwise; doctor adds a `WARN retro` and `WARN calibration` row, which never changes the `doctor: ok` header or the exit code
- compatibility: `Status` gains one defaulted field; existing constructors, the snapshot and every non-overdue output are unchanged. `Check` is reused unchanged (its existing `warn` flag), so `PASS` and `FAIL` rows render as before
- acceptance: status and doctor show the line at or above a threshold and nothing below it, and `retro.enabled: false` shows no retro line
- tests: tests/unit/test_status_overdue.py, tests/unit/test_doctor_overdue.py
- post-merge source of truth: clutch/status.py and docs/how-clutch-works.md

## Scope in / Scope out
Scope in:
- Remove every automatic trigger site listed in Goal / Why. In `clutch/serve.py` drop the unused imports that removal leaves (`calibrate_when_due`, `measurements`, `select_trigger`, `suppressing_failure`, `RetroCheckOutcome`, and `due_trigger` if no caller remains); in `clutch/drain.py` drop the `calibrate_when_due` import. `retro_pending` returns only the request clause. `_Drain._run_retro` takes no `forced` argument (every remaining call is forced), loses `retro_terminal_count` and the count dedupe, and keeps its `retro_check` phase events for the operator request.
- Delete `calibrate_when_due` from `clutch/calibration.py`. Split `due(events, every)` in place: a new `pending(events)` returns the count of Implement completions since the latest `estimate_calibration` signal and `due` returns `pending(events) >= every`; `calibrate` is unchanged.
- In `clutch/retro.py`, extract the settled-ticket count that `select_trigger` computes inline into one named function that `select_trigger` calls and the overdue line reuses; `select_trigger` returns the same values as before.
- In `clutch/status.py`, add a pure `overdue(events, config)` returning a dict keyed `retro` and `calibration` (only overdue features present) whose values are the full lines including the `retro overdue:` or `calibration overdue:` prefix; status renders the values and doctor uses the keys as row names and the whole line as the row detail: the retro line from `project_window(events)`, `due_trigger(window, config.retro, forced=False)` and the counts from `measurements` and the settled-count function, skipped when `config.retro.enabled` is false; the calibration line from `calibration.pending` and `due`. `Status` gets a last field `overdue: tuple[str, ...] = ()` holding the values, `project` takes `overdue=()`, and `render` prints one `- ` free line block named `overdue` only when it is nonempty. `_status` in `clutch/__main__.py` passes `overdue(events, checkout.config)`.
- In `clutch/doctor.py`, reuse the existing `Check.warn` flag (added by `evidence-never-prunes`; `render` already prints `WARN` and keeps `doctor: ok`): the `retro` and `calibration` rows are `Check(name, True, line, warn=True)`. After the journal row, `check` reads the same journal events and adds a `retro` and a `calibration` warning row with the line from `overdue` as detail, only when overdue; an unreadable journal adds none.
- Config fields after this ticket (none removed, none renamed; the shape is unchanged):
  - `retro.enabled`: master overdue switch. False means no retro overdue line or row; `engine retro` still runs.
  - `retro.merges.enabled` and `retro.merges.every`: retro is overdue at `every` merged tickets in the window when enabled.
  - `retro.settled.enabled` and `retro.settled.every`: overdue at `every` settled tickets in the window when enabled.
  - `retro.spikes.enabled`, `retro.spikes.count` and `retro.spikes.kinds`: overdue when one allowlisted kind reaches `count` events (`override` stays excluded, per `retro-due-one-owner`).
  - `retro.test_timing` and `retro.coverage`: unchanged; they shape a report that is run.
  - `calibration.every`: calibration is overdue at `every` Implement calls since the last calibration, and `engine calibrate` still tables the last `every` calls.
- Command help in `clutch/__main__.py` (the `engine` group description and the `retro` and `calibrate` entries, and the `status` and `doctor` entries) states that these run only when invoked and that status and doctor report overdue.
- Docs: `docs/how-clutch-works.md` (section 7 serve paragraphs on retro admission and idle calibration, the serve loop step list near "maybe run a retro", the retro paragraph in 9.5 that says "when due", the `retro` and `calibration` config table rows, and the `view status` and `host doctor` verb rows) and `clutch/docs/host-contract.md` (the `Retro` and `Calibration` config text near the `retro:` example, and the closed-set sentence "disables automatic retros"), and `clutch/docs/host-running.md` (the `engine retro`, `engine calibrate`, `view status` and `host doctor` rows). Edit only the sentences made false.
- Tests: new files `tests/unit/test_no_automatic_retro_calibration.py` (drive `Serve.dispatch` or the serve loop and `_Drain` with fakes over a window past both thresholds; assert no `Retro` construction, no `estimate_calibration` signal, no phase event, and `select` admits while overdue), `tests/unit/test_status_overdue.py`, `tests/unit/test_doctor_overdue.py`, `tests/unit/test_manual_retro_calibration_verbs.py` (`engine calibrate` journals a signal and `engine retro` still commits a report with automatic triggers overdue). Update the fenced existing tests listed below only where an assertion or monkeypatch of a removed name flips: delete `tests/unit/test_serve_retro_check_once.py`, `tests/unit/test_drain_retro_once_per_settle.py`, `tests/unit/test_serve_retro_check_site.py` (its bytecode assertion that `Serve.run` loads `check_retro` pins the removed method), `tests/regress_serve_retro_check_once.py` and `tests/regress_drain_retro_once_per_settle.py` (they pin the removed dedupes); drop only the `serve.calibrate_when_due` monkeypatch in `tests/unit/test_serve_no_roadmap.py` and only the `drain.calibrate_when_due` monkeypatch in `tests/unit/test_drain_no_roadmap.py`, because those imports are deleted; drop the `calibrate_when_due` and `_run_retro(forced=False)` uses in `tests/unit/test_phase_events.py`, `tests/unit/test_calibration_idle.py` (keep its `due` test, add a `pending` test), `tests/unit/test_drain_report_intake.py` and `tests/unit/test_supervise_idle_hooks.py`; drop only the `owner.check_retro` stub in `tests/unit/test_serve_dispatch_containment.py`, because `check_retro` is removed; in `tests/integration/test_drain.py` delete `test_due_retro_waits_for_retry_and_precedes_next_ticket` and the `not-due`, `due` and `phase` automatic scenarios of `_exercise_retro_drain` while keeping the requested and killable cases; in `tests/integration/serve_rig.py` and `tests/integration/test_serve_dispatch.py` keep the `requested` and `kill` modes, delete the `automatic`, `disabled` and `failed` modes and their two tests that only cover the automatic path, and drop the `check_retro` wrapper. The `Retro(forced=False)`, `due_trigger` and `select_trigger` uses in `tests/unit/test_retro.py`, `tests/unit/test_retro_box.py` and `tests/unit/test_retro_due_owner.py` stay valid and are not edited. Create no placeholder test file for a path this list does not name.
- Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.

Scope out:
- No config field is added, removed or renamed; no alias.
- `Retro.__call__`, `due_trigger` and `select_trigger` keep their signatures and `forced` handling.
- No change to what a retro report or calibration table contains, to `retro_check` event names, to the control inbox request format, or to the VS Code extension.
- No automatic action on an overdue warning, and no new verb.
- Roadmap and plan documents are not edited by this ticket.
- The integration test skip policy (`disk_io_skip`, box-001136) is not changed by this ticket.

## Scope fence
- clutch/serve.py
- clutch/drain.py
- clutch/calibration.py
- clutch/retro.py
- clutch/status.py
- clutch/doctor.py
- clutch/__main__.py
- docs/how-clutch-works.md
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- tests/integration/serve_rig.py
- tests/integration/test_serve_dispatch.py
- tests/integration/test_drain.py
- tests/unit/test_no_automatic_retro_calibration.py
- tests/unit/test_status_overdue.py
- tests/unit/test_doctor_overdue.py
- tests/unit/test_manual_retro_calibration_verbs.py
- tests/unit/test_serve_retro_check_once.py
- tests/unit/test_drain_retro_once_per_settle.py
- tests/unit/test_serve_retro_check_site.py
- tests/unit/test_serve_no_roadmap.py
- tests/unit/test_drain_no_roadmap.py
- tests/regress_serve_retro_check_once.py
- tests/regress_drain_retro_once_per_settle.py
- tests/unit/test_phase_events.py
- tests/unit/test_calibration_idle.py
- tests/unit/test_drain_report_intake.py
- tests/unit/test_supervise_idle_hooks.py
- tests/unit/test_serve_dispatch_containment.py

## Acceptance criteria
1. With 25 merges and 100 Implement completions in the journal and `retro.merges.every` 25 and `calibration.every` 100, a serve dispatch pass and a drain between-tickets pass construct no `Retro`, append no `estimate_calibration` signal and log no `retro_check` event, and `Serve.select` admits an eligible ticket, not holding it for a retro (`./dev.py test tests/unit/test_no_automatic_retro_calibration.py`).
2. `Serve` has no `check_retro`, `retro_due` or `retro_checked` attribute, `clutch.calibration` has no `calibrate_when_due`, and `retro_pending()` is false for an overdue window with no request and true for a `retro_id` request not yet served (`./dev.py test tests/unit/test_no_automatic_retro_calibration.py`).
3. `overdue(...)['retro']` is the retro line `retro overdue: 40 tickets settled since the last retro; run `clutch engine retro`` for 40 settled stems with `settled.every` 40, returns no line for 39, returns no retro line with `retro.enabled: false` at 40, and the line count resets after a retro report completes (`./dev.py test tests/unit/test_status_overdue.py`).
4. `overdue(...)['calibration']` is `calibration overdue: 100 Implement calls completed since the last calibration; run `clutch engine calibrate`` at 100 completions and nothing at 99 or after a later `estimate_calibration` signal, and `clutch view status` output contains exactly one overdue line per overdue feature (`./dev.py test tests/unit/test_status_overdue.py`).
5. `doctor.check` over a journal past both thresholds returns a `retro` and a `calibration` row with `warn` true and `passed` true, `render` prints `WARN retro:` and `WARN calibration:`, the first line stays `doctor: ok` (not `doctor: failed`), and a journal below both thresholds renders the same text as before this ticket (`./dev.py test tests/unit/test_doctor_overdue.py tests/integration/test_doctor.py`).
6. The overdue computation reads only the journal: a test passes a git fake that raises on any call and `overdue` still returns its lines (`./dev.py test tests/unit/test_status_overdue.py`).
7. `clutch engine calibrate` with the threshold not reached still journals one `estimate_calibration` signal and prints the table, and `engine retro` with the thresholds not reached still commits a report when a merge exists, not "nothing to do" (`./dev.py test tests/unit/test_manual_retro_calibration_verbs.py tests/unit/test_main_engine_calibrate.py`).
8. A requested retro still holds admission and runs between tickets in serve and in drain: `retro_scenario` modes `requested` and `kill` and the drain requested-retro tests pass (`./dev.py test tests/integration/test_serve_dispatch.py tests/integration/test_drain.py`).
9. `config.py` is unchanged and `Config` still loads a config naming every retro and calibration field above (`./dev.py test tests/integration/test_config.py`).
10. The command help of `engine retro`, `engine calibrate`, `view status` and `host doctor` names the manual-only behavior and the overdue report (`./dev.py test tests/unit/test_main_help.py tests/unit/test_help.py`).

## Verification
```
./dev.py test tests/unit/test_no_automatic_retro_calibration.py tests/unit/test_status_overdue.py tests/unit/test_doctor_overdue.py tests/unit/test_manual_retro_calibration_verbs.py tests/unit/test_main_engine_calibrate.py tests/unit/test_calibration_idle.py tests/unit/test_phase_events.py tests/unit/test_drain_report_intake.py tests/unit/test_supervise_idle_hooks.py tests/unit/test_serve_dispatch_containment.py tests/unit/test_serve_no_roadmap.py tests/unit/test_drain_no_roadmap.py tests/unit/test_main_help.py tests/unit/test_help.py
./dev.py test tests/integration/test_doctor.py tests/integration/test_serve_dispatch.py tests/integration/test_serve_admission.py tests/integration/test_serve_upgrade.py tests/integration/test_drain.py tests/integration/test_config.py tests/integration/test_retro.py
```

## Definition of rejected
- Any remaining call that starts a retro or a calibration from serve or drain without an operator verb or request, or any dispatch hold for a count-due window.
- A config alias, a new flag that restores automatic runs, or a dual path keeping `calibrate_when_due`, `check_retro`, or `_run_retro(forced=...)` alive for old tests.
- The overdue computation reads git, calls a provider, or runs a retro measurement that does.
- A WARN row that changes the doctor exit code or its `doctor: ok` header.
- Edits to a hot test file beyond the removals named in Scope in, or any new test placed in one.
- A placeholder test file created only to make a Verification path exist.

## Time budget
- expected: 60m
- stuck: 120m
- reason: removing the automatic retro and calibration triggers from serve and drain and adding the overdue warnings must land together, or one engine verb would still auto-run while status claims it is manual; the 29-file fence is mostly tests that pin the removed triggers