---
state: confirmed
source: human
priority: P1
kind: bug
---

## Depends on
- none

## Context
- clutch/status.py::project
- clutch/status.py::Status
- clutch/status.py::last_states
- clutch/status.py::reject_queue
- clutch/status.py::SETTLED
- clutch/status.py::render
- clutch/control.py::ControlInbox.consume
- clutch/observe.py::snapshot
- tests/unit/test_status_verdict_decisions.py
- tickets/verdict-decisions-retire-on-resolution/evidence/evidence.txt

## Goal / Why
`project` folds every non-accepted `control_decision` event in the whole journal into `Status.verdict_decisions` with no retirement rule, so a dead confirm/reject request is reported forever. `vscode-clutchwork/media/view.js` prepends those rows above the ticket rows in the tickets view, and `render` prints them as the `Verdict decisions:` block, so both surfaces show the same growing pile.

Observed 2026-11-15 in this repo (`evidence/`): twelve decisions journaled between 2026-11-06 and 2026-11-12 fill the top of the tickets view and the tail of `clutch status`. Every one of the twelve names a stem whose verdict has since been applied: a later `draft_confirmed` or `reject_verdict` signal for that stem exists in the journal for all nine distinct stems (`evidence/evidence.txt` lists each with its superseding signal and timestamp). None is actionable, and there is no verb that clears one.

These twelve are residue, not a live fault: the `known` bug that made the requests go stale was fixed by the merged tickets `drain-settles-admissions` and `control-inbox-known-required`, and no stale decision has been journaled since 2026-11-12.

Done means a non-accepted decision stops being reported once a verdict for its stem has been applied, so the row lives exactly as long as it is actionable, and this repo's twelve dead rows disappear from both surfaces without touching the journal.

## Scope in / Scope out
In:
- Add one pure retirement rule to `project` in `clutch/status.py` (no clock, no I/O): a non-accepted `control_decision` event naming a stem is dropped from `verdict_decisions` when a later event for that stem is a `draft_confirmed` signal or a `reject_verdict` signal. Those two signals are journaled exactly when a verdict was applied: `clutch/runner.py` appends `draft_confirmed` on a confirmed draft, `reject_verdict` with `verdict: keep` or `verdict: kill` on an operator verdict, and `clutch/drain.py` appends `reject_verdict` with `verdict: keep`, `actor: machine` on a machine re-offer. Order is by journal position, so a verdict applied before the decision does not retire it.
- Keep `verdict_decisions`'s shape, order, and the five-field rows; only membership changes. `render` and the snapshot keep reading the same projection, so no separate fix is needed in either, and `render` already omits the `Verdict decisions:` block when the tuple is empty.
- `tests/unit/test_status_verdict_decisions.py` gains the retirement cases in Acceptance criteria 1-5 and is the guard that stops this class returning: it pins both directions, so a later change that drops the rule or over-filters fails.

Out:
- `vscode-clutchwork/`: it draws what the snapshot sends.
- `clutch/observe.py` and `render`: they must not gain a filter of their own; the projection is the single place the rule lives.
- The journal: no compaction, rewrite, deletion, or new "clear" verb. The twelve events stay; only the projection retires them.
- `ControlInbox.consume` and the `known` check that decides staleness; that cause is already merged.
- `Status.verdict_refusals`, `Status.intake`, and `Status.reopens`, which fold the whole journal the same way. They are a second problem; file them, do not fold them in.
- `tests/integration/test_status.py` is not fenced and must keep passing unchanged: its fixture journals a stale decision with no superseding signal, so it proves a live row still shows.

## Scope fence
- clutch/status.py
- tests/unit/test_status_verdict_decisions.py
- tests/regress_verdict_decisions_retire_on_resolution.py

## Acceptance criteria
1. `tests/unit/test_status_verdict_decisions.py` asserts that a stale `confirm` decision naming stem `draft`, followed by a `draft_confirmed` signal for `draft`, gives `project(...).verdict_decisions == ()`, not a one-row tuple, and that `render(status)` contains no `Verdict decisions:`.
2. `tests/unit/test_status_verdict_decisions.py` asserts the same retirement for a stale `reject` decision followed by a `reject_verdict` signal with `verdict: kill`, and for a stale `confirm` decision followed by a `reject_verdict` signal with `verdict: keep` and `actor: machine`.
3. `tests/unit/test_status_verdict_decisions.py` asserts that a stale decision for a stem with no later `draft_confirmed` or `reject_verdict` signal is kept: `verdict_decisions` is the one-row tuple, not `()`. A stale decision whose stem has only a later `state_transition` to `merged` and neither signal is also kept.
4. `tests/unit/test_status_verdict_decisions.py` asserts order: a `draft_confirmed` signal for stem `draft` appearing *before* a stale `confirm` decision for `draft` leaves that decision in `verdict_decisions` as a one-row tuple, not `()`.
5. `tests/unit/test_status_verdict_decisions.py` asserts a `rejected` decision carrying no stem (`verb` `None`, no `stem` key) is kept whatever signals follow, since no stem can supersede it, and renders with an empty verb and stem as it does today.
6. `grep -n "draft_confirmed" clutch/observe.py vscode-clutchwork/media/view.js` finds no match: the rule lives only in `clutch/status.py`.
7. `uv run python tests/regress_verdict_decisions_retire_on_resolution.py` prints `{"regression_result": "pass"}` and exits 0 on the branch head, and `{"regression_result": "defect"}` with a non-zero exit at the merge base.
8. `./dev.py test` exits 0.

## Verification
```
./dev.py test
```

## Definition of rejected
- The retirement is implemented in `vscode-clutchwork/`, in `clutch/observe.py`, or in `render` instead of in `project`.
- Journal files are edited, compacted, deleted, or rewritten, or a verb is added that clears decisions.
- A row is aged out by a clock, a row-count cap, a config knob, or the control lifecycle id instead of an applied verdict for its stem.
- A stale decision with no applied verdict for its stem stops being reported.
- `project` gains I/O, a clock, or a dependency on ticket files.

## Time budget
- expected: 25m
- stuck: 60m

## Regression
```
uv run python tests/regress_verdict_decisions_retire_on_resolution.py
```
- carries: tests/regress_verdict_decisions_retire_on_resolution.py
