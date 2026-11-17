---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Context
- clutch/control.py
- clutch/triage.py
- clutch/supervise_idle.py

## On-demand
- clutch/__main__.py
- clutch/drain.py
- clutch/serve.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md

## Goal / Why
While `clutch engine drain` or `clutch engine serve` holds the writer lock, `clutch box triage [<id>...]` exits 2 with a `LockHeld` refusal. Under the plan-ticket-drain process a drain runs for hours, so Suggestion Box messages pile up untriaged. `review-alongside-drain` and `serve-live-verdicts` closed the same gap for review and for confirm/reject. After this ticket, `clutch box triage` with a running engine holding the lock publishes a triage request to that engine's control inbox and prints `triage submitted: <request_id>`. The running drain or serve runs one `triage.triage_pass` for the requested ids (all pending when none are named) at its next idle point, and each message then moves from pending to a verdict. The operator still triggers every pass, so the owner decision in `serve-no-auto-triage` (2026-11-06: nothing triages unless the operator runs triage) holds. No engine triages on its own.

The repeated filings of one flaky test (box-000706, 712, 717, 719, 724, 725) are a separate dedup problem and are not part of this ticket.

## Scope in / Scope out
- In `clutch/control.py`: add a third request kind with shape `{request_id, lifecycle_id, verb: "triage", ids, actor}`, where `ids` is a list of box id strings (possibly empty). The request carries no `hold_id`. A new `_TRIAGE_SHAPE` is the shape road `consume()` picks for a malformed triage request. `consume` journals the decision body `{kind, request_id, lifecycle_id, verb: "triage", hold_id: null, ids, actor, decision, reason}`; the `hold_id: null` is the seed `consume` gives every body. `decisions()` keeps `hold_id` in its required fields and adds `{ids, actor}` as the extra fields for verb `triage`, so re-validation of a triage body does not raise `invalid control decision`. `_fold` skips verb `triage` exactly as it skips confirm and reject: no `accepted=True`, no `apply()`, no change to pause, kill, stop or retro state. A stale decision for a wrong lifecycle follows the existing pattern.
- In `clutch/control.py`: add `ControlInbox.settle_triage(run)`, mirroring `settle_admissions`. `run` is an injected callable taking the tuple of ids and wrapping `triage.triage_pass`. Each accepted, unapplied triage request is applied once under an `Effects` key `triage/<request_id>`, so a repeated settle or a restart never runs it twice. A `run` that raises `triage.validate_ids` refusal completes the effect and records the refusal in the engine log; it does not raise out of settle.
- In `clutch/drain.py` and `clutch/serve.py`: at the idle point where `supervise_idle` already runs, call `settle_triage` with a `run` that calls `triage.triage_pass(checkout, llm, frozenset(ids))` through the engine's own provider session. Add no triage call that runs without a request.
- In `clutch/__main__.py` `handle_triage`: follow the retro/confirm `try` pattern. On `LockHeld`, call `_require_engine(exc)`, which checks that the holder's verb is in `ENGINE_VERBS` and otherwise raises `runner.Refusal('writer lock held by <verb>')`; then read the lifecycle with `control.read_active`, the way `_submit_engine` does, publish the request, and print `triage submitted: <request_id>`. A non-engine holder (for example `release`) therefore gets the `writer lock held by <verb>` refusal, exit 2, and no request is published, even when a stale `control/active.json` from a crashed drain is still parseable. With the lock free the behavior is unchanged. Update the `box triage` command help to match.
- Docs: in `docs/how-clutch-works.md` section 2 update the `box triage` row (lock becomes `try`, text says the request goes to a running engine and runs at its idle point) and fix any section 9.2 prose that says triage refuses while an engine runs. In `clutch/docs/host-running.md` change the `box triage` row's "Works while serve runs?" cell from No to Yes, and remove `box triage` from the "Stop serve before ..." sentence that says each listed verb takes the writer lock outright and refuses while it is held.
- Out: any automatic or scheduled triage, dedup of repeated filings, `box dismiss`, changing `triage.py` rules, and a new help-registry surface.
- Simpler approach rejected: automatic idle triage; it reverses `serve-no-auto-triage`.

## Scope fence
- clutch/control.py
- clutch/__main__.py
- clutch/drain.py
- clutch/serve.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/unit/test_control_triage_request.py
- tests/unit/test_drain_serve_triage_idle.py
- tests/integration/test_box_triage_inbox.py
- tests/integration/test_control.py
- tests/unit/test_main_box_group.py

## Acceptance criteria
1. `validate_request` accepts a triage request with `ids: []` and with `ids: ["box-000001"]`, and refuses `ids` that is not a list of strings, naming the `_TRIAGE_SHAPE` road. Checked by `./dev.py test tests/unit/test_control_triage_request.py`.
2. `ControlInbox.consume` journals a triage request from the current lifecycle as `accepted` and one from another lifecycle as `stale`; `decisions()` yields the accepted triage decision with `ids` and `actor` and does not raise `invalid control decision`; a triage decision never sets `pause_id`, `kill_requested`, `stop_requested` or `retro_id` on the folded projection. Checked by `./dev.py test tests/unit/test_control_triage_request.py`.
3. `settle_triage` with a fake `run` calls it exactly once for one accepted request even when settle runs twice, and zero times with no request; a `run` that raises the id refusal completes the effect without raising. Checked by `./dev.py test tests/unit/test_drain_serve_triage_idle.py`.
4. The drain and serve idle points call `settle_triage` with a fake `run` and fake journal, and call it with no triage when no request exists. Checked by `./dev.py test tests/unit/test_drain_serve_triage_idle.py`.
5. With a real drain holding the lock, `clutch box triage <id>` prints `triage submitted:` and exits 0, not a `LockHeld` refusal with exit 2. Checked by `./dev.py test tests/integration/test_box_triage_inbox.py`.
6. With a real drain or serve at its idle point, the pending message gets a verdict after one accepted request and no second pass runs; with no request, `triage_pass` runs zero times. Checked by `./dev.py test tests/integration/test_box_triage_inbox.py`.
7. With a non-engine holder (a lock whose verb is `release`) and a parseable `control/active.json` left by a crashed drain, `clutch box triage` prints the `writer lock held by release` refusal, exits 2, and publishes no request. Checked by `./dev.py test tests/integration/test_box_triage_inbox.py`.
8. With the lock free, `clutch box triage` still runs a pass directly, as before. Checked by `./dev.py test tests/integration/test_box_triage_inbox.py`.
9. A fake-driven `handle_triage` test monkeypatches `entry._locked` to raise `LockHeld` and stubs `control.read_active` and `control.publish_request`. With an engine holder (verb `drain`) it prints `triage submitted:` and exits 0 after one publish; with a `release` holder it exits 2 and publishes nothing. The test starts no git process and no provider. Checked by `./dev.py test tests/unit/test_main_box_group.py`.

## Verification
```
./dev.py test tests/unit/test_control_triage_request.py tests/unit/test_drain_serve_triage_idle.py tests/integration/test_box_triage_inbox.py tests/integration/test_control.py tests/unit/test_main_box_group.py tests/unit/test_main_help.py tests/integration/test_help.py
```

## Definition of rejected
Any path where drain or serve triages without an operator request; a triage request applied twice; two copies of the triage pass logic; `clutch box triage` still exiting 2 with `LockHeld` against a running drain or serve; a request published while a non-engine process holds the lock; docs or command help left describing the old lock behavior, including the "Stop serve before" sentence in `clutch/docs/host-running.md`.

## Time budget
- expected: 45m
- stuck: 90m
- reason: one request kind needs control, CLI, drain and serve edits that share one contract; splitting would leave an unusable half.
