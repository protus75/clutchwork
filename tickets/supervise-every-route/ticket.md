---
state: confirmed
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: high
agent_effort: medium
---

## Depends on
none

## Context
- clutch/runner.py::failure_terminal
- clutch/daemon.py::TicketWriter.consume_result
- clutch/caps.py::supervise_draws

## On-demand
- clutch/journal.py
- docs/roadmap-driver-plan.md
- docs/how-clutch-works.md

## Goal / Why
Open decision 2 of the roadmap driver plan supervises every `premise_failed` and spent-cap route. Merged code supervises a spent cap only on the `gate_failed` path that `runner.drive` reaches with `supervised=True` (`clutch/runner.py::failure_terminal`). A serve merge-queue failure (`clutch/daemon.py::TicketWriter.consume_result`) calls `failure_terminal` unsupervised, so a held stem on the merge route waits for a person. Merged code also journals no record of an escalated or refused supervisor attempt (`cap_consumed supervise` is written only on approval), so nothing later can tell an attempted stem from an unattempted one.

The serve and drain idle-point step (plan section 6 step 1) is roadmap row `supervise-idle-point`, which builds on the signal this ticket adds; the Effect-key scope that step needs is roadmap row `supervisor-effect-scope`.

When this is done:
- A spent-cap or `premise_failed` terminal routed to the Reject queue from `TicketWriter.consume_result` gets the supervisor step, bounded by `caps.supervise` as today.
- Every supervisor attempt, on `runner.drive` and on the merge route, journals one `supervisor_attempt` signal with the stem in the body, whether the attempt is approved, refused, or escalated.

## Scope in / Scope out
In:
- `clutch/journal.py`: add `supervisor_attempt` to `SIGNAL_NAMES`.
- `clutch/runner.py`: inside the existing supervisor step in `failure_terminal`, journal `supervisor_attempt` once per attempt, before the `apply_rework` call and before the routed terminal, so the order assertions in `tests/unit/test_supervisor_trigger.py` (the last three events are terminal, draw, keep; no terminal before the lift) stay green. Do not copy the step into a second function.
- `clutch/daemon.py`: `TicketWriter.consume_result` passes `supervised=True` to its `failure_terminal` call for a merge-stage failure. The existing gate in `failure_terminal` (routed terminal, `caps.supervise` bound, not `ticket_changed`, worktree present) decides whether the step runs.
- `tests/integration/test_closed_sets.py`: add `supervisor_attempt` to the expected set at the `SIGNAL_NAMES ==` assertion; no other edit.
- `docs/how-clutch-works.md`: update only the section on the supervisor step (6.4-6.7) to say the merge route is supervised and every attempt journals `supervisor_attempt`, and the last sentence of section 7.5 (Roadmap driver) to say the supervisor runs in `runner.drive` and merge-route `consume_result`. `docs/roadmap-driver-plan.md`: update only sections 2 and 6 to match the built merge-route behavior.

Out: the serve and drain idle-point step, its worktree and Effect keys (roadmap rows `supervisor-effect-scope` and `supervise-idle-point`), `ticket_changed` holds, `abandoned` stems, Diagnose `reject` and `abandon-human` routes, the `rework.md` allowed-edit gate, the `caps.supervise` default, the roadmap driver's authoring and release steps. Any other problem found goes to `clutch suggest`.

## Scope fence
- clutch/runner.py
- clutch/daemon.py
- clutch/journal.py
- tests/integration/test_closed_sets.py
- docs/how-clutch-works.md
- docs/roadmap-driver-plan.md
- tests/unit/test_supervise_merge_route.py

## Acceptance criteria
1. A merge-stage failure delivered to `TicketWriter.consume_result` with a spent cap and a routed terminal runs the supervisor step and journals `reject_verdict keep actor: supervisor` on approval; `./dev.py test tests/unit/test_supervise_merge_route.py -k merge_route` drives `consume_result` with fake git, journal, and rework seams and fails if the stem stays in the Reject queue with no supervisor attempt.
2. Each supervisor attempt journals exactly one `supervisor_attempt` signal naming the stem, on approve, refuse, and escalate, on both `runner.drive` and the merge route; `./dev.py test tests/unit/test_supervise_merge_route.py -k attempt_signal` fails if any of those cases journals zero or two signals.
3. A stem whose `supervise_draws` already equals `caps.supervise` is not supervised on the merge route; `./dev.py test tests/unit/test_supervise_merge_route.py -k cap_spent` fails if a third supervisor keep is journaled with `caps.supervise` set to 2.
4. The supervised `gate_failed` path from `runner.drive` keeps its event order; `./dev.py test tests/unit/test_supervisor_trigger.py tests/integration/test_rework_supervise.py` still exit 0.
5. `supervisor_attempt` is in `journal.SIGNAL_NAMES`, and `./dev.py test tests/integration/test_closed_sets.py` exits 0, failing if the signal is missing from the set or the pinned expectation.

## Verification
```
./dev.py test tests/unit/test_supervise_merge_route.py tests/unit/test_supervisor_trigger.py tests/integration/test_rework_supervise.py tests/integration/test_closed_sets.py
```

## Definition of rejected
The branch is thrown away if the supervisor step is copied into a second code path instead of reused from `failure_terminal`, if `caps.supervise` can be exceeded on the merge route, if an attempt journals no `supervisor_attempt` or more than one, or if it supervises `ticket_changed` or `abandoned` stems.

## Time budget
- expected: 40m
- stuck: 80m
