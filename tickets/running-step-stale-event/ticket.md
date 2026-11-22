---
state: confirmed
source: human
priority: P2
kind: bug
---

## Depends on
- none

## Context
- clutch/observe.py::current_step
- clutch/observe.py::running_stems
- clutch/observe.py::snapshot
- clutch/observe.py::live_call
- tests/unit/test_observe_step_session.py

## Goal / Why
A running ticket's step and elapsed time come from the stem's stage events that belong to the current run, never from an event logged before that run began. When no stage event exists since the run began, the step reads `Starting` with no elapsed time.

Today `current_step` takes the stem's last `stage_start`/`stage_end` in the engine log with no lower bound. On 2026-11-22 (see `evidence/`) preflight ran a requisition review on `host-prompts` at 13:31, which ended `ok` at 13:31:16. The ticket waited in the queue until the engine journaled it `running` at about 15:18:04. Its own requisition review did not start until 15:18:09. For those seconds the Tickets panel showed `running: Implement for 106m48s`: the stale `requisition_review` `stage_end` was mapped to "next step Implement", and its timestamp was used as the start. The same function feeds the `Now:` line of the status text, so that line was wrong too. The operator could not tell a fresh run from one stuck for almost two hours.

## Boundary contract
### Running step projection
- disposition: extend
- owner: clutch/observe.py
- consumers: the status text `Now:` line and the snapshot `running` row status (Tickets panel)
- observable change: `current_step(log, stem, since)` ignores stage events whose `ts` is earlier than `since`, the `ts` of the stem's last journaled `running` transition; with no event at or after `since` it returns `("Starting", "", None)`
- compatibility: restores the intended contract that a running row describes the current run; return shape and step names are unchanged
- acceptance: a stage event older than the running transition never sets the step or the elapsed time
- tests: new `tests/unit/test_observe_current_step_run_floor.py`, plus the updated existing calls in `tests/integration/test_watch.py` and `tests/unit/test_observe_step_session.py`
- post-merge source of truth: clutch/observe.py

## Scope in / Scope out
Scope in:
- Add a required third parameter `since: str` (an ISO timestamp) to `current_step` in `clutch/observe.py`. Filter stage events to those with `datetime.fromisoformat(e["ts"]) >= datetime.fromisoformat(since)` before taking the last one.
- Both callers in `clutch/observe.py` (the status `Now:` loop and the `snapshot` running-row loop) pass the stem's last journaled running body `ts` (`last_state[stem]["ts"]` and `last[stem]["ts"]`). `running_stems` already guarantees that body is `to: running`.
- Update the four existing `current_step(...)` calls in `tests/integration/test_watch.py` to pass a `since` at or before their first event's `ts`, so their expected values do not change.
- `tests/unit/test_observe_step_session.py::test_snapshot_sessions` monkeypatches `running_stems` and returns an empty `journal`, so `last[stem]` would raise KeyError. Make its `journal` fake return a `state_transition` event with `to: running` and `ts` `2026-01-01T00:00:00+00:00` for each running stem (`active`, `finished`). Its expected session values do not change.
- New unit test `tests/unit/test_observe_current_step_run_floor.py`.
- New carried reproducer `tests/regress_running_step_stale_event.py`. It builds a log holding only a `requisition_review` `stage_end` at T0 and uses a `since` 106 minutes later. It checks `inspect.signature(observe.current_step)`. With fewer than three parameters (base), it calls `current_step(log, stem)`, which returns `("Implement", T0, None)`, so it prints `{"regression_result": "defect"}` and exits 1. Otherwise it calls `current_step(log, stem, since)`. It prints `{"regression_result": "pass"}` and exits 0 when the result is `("Starting", "", None)`, and `defect` with exit 1 otherwise. An import failure prints `{"regression_result": "error"}` and exits 2.

Scope out: `running_stems`, `live_call`, step names, the extension, and the engine log format. No other behavior changes.

## Scope fence
- clutch/observe.py
- tests/integration/test_watch.py
- tests/unit/test_observe_step_session.py
- tests/unit/test_observe_current_step_run_floor.py
- tests/regress_running_step_stale_event.py

## Acceptance criteria
1. Given a log with a `requisition_review` `stage_end` at T0 and `since` = T0 + 106 minutes, `current_step(log, stem, since)` returns `("Starting", "", None)`, not `("Implement", T0, None)`. Checked by `tests/unit/test_observe_current_step_run_floor.py`.
2. Given the same stale event plus a `stage_start` for `requisition_review` at T1 >= `since`, `current_step` returns `("Requisition", T1, "requisition_review")`, not a result carrying T0. Checked by `tests/unit/test_observe_current_step_run_floor.py`.
3. An event whose `ts` equals `since` counts as part of the run (the floor is inclusive). Checked by `tests/unit/test_observe_current_step_run_floor.py`.
4. The existing `current_step` assertions in `tests/integration/test_watch.py` and the session assertions in `tests/unit/test_observe_step_session.py` keep their expected values. Checked by `./dev.py test tests/integration/test_watch.py tests/unit/test_observe_step_session.py`.
5. `uv run python tests/regress_running_step_stale_event.py` prints `{"regression_result": "pass"}` and exits 0 on the branch. On the base it prints `{"regression_result": "defect"}` and exits non-zero.

## Verification
```
./dev.py test tests/unit/test_observe_current_step_run_floor.py tests/unit/test_observe_step_session.py tests/integration/test_watch.py
uv run python tests/regress_running_step_stale_event.py
```

## Definition of rejected
- A running row or `Now:` line can still show a step or elapsed time from an event earlier than the stem's running transition.
- `current_step` keeps a no-floor path, for example an optional `since` that defaults to no filtering.
- Changes outside the fence, or changes to step names or the snapshot shape.

## Time budget
- expected: 10m
- stuck: 20m

## Regression
```
uv run python tests/regress_running_step_stale_event.py
```
- carries: tests/regress_running_step_stale_event.py
