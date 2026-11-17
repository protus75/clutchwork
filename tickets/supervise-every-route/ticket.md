---
state: confirmed
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/runner.py::failure_terminal
- clutch/daemon.py::TicketWriter.consume_result
- clutch/caps.py::supervise_draws

## On-demand
- clutch/drain.py
- clutch/serve.py
- clutch/journal.py
- docs/roadmap-driver-plan.md
- docs/how-clutch-works.md

## Goal / Why
Open decision 2 of the roadmap driver plan supervises every `premise_failed` and spent-cap route. Merged code supervises a spent cap only on the `gate_failed` path that `runner.drive` reaches with `supervised=True` (`clutch/runner.py::failure_terminal`). Two routes never get the supervisor step: a serve merge-queue failure (`clutch/daemon.py::TicketWriter.consume_result`, which calls `failure_terminal` unsupervised) and a drain `reject_arrival` (`clutch/drain.py::_settle`, which only journals the arrival). Section 6 step 1 of the plan is not built at all.

When this is done:
- A spent-cap terminal on every route gets the supervisor step, bounded by `caps.supervise` as today.
- At the serve idle point and between drain tickets, each Reject-queue stem that has no `supervisor_attempt` signal in its operator lineage runs the supervisor step in a fresh worktree created from main's HEAD commit at that idle point (`ctx.git.rev_parse(ctx.repo, MAIN)`). Its Effect keys are its own, never the keys of the original run. Plan sections 2 and 6 name that worktree and those keys; this closes the gap declined-box-000537 asked the plan to close.
- Each idle-point attempt journals a new `supervisor_attempt` signal, whether the attempt is approved, refused, or escalated. Merged code journals no record of an escalated or refused attempt (`cap_consumed supervise` is written only on approval; `rework_order` is skipped when rework returns non-ok), so without this signal the idle point would re-run the LLM call for an escalated stem on every idle point.

Without this a held stem on the merge-queue or drain route waits for a person, and the unattended driver cannot tell it from a stem that is just not ready.

## Scope in / Scope out
In:
- `clutch/runner.py`: let the existing supervisor step in `failure_terminal` run for any caller that routes to the Reject queue, not only the `drive` caller. Reuse its gate and `caps.supervise` bound. Do not copy the step into a second function.
- `clutch/daemon.py`: `TicketWriter.consume_result` supervises a merge-stage failure whose terminal is routed.
- `clutch/drain.py`: after `_settle` journals a `reject_arrival`, the drain idle point runs the supervisor step for each unsupervised Reject-queue stem.
- `clutch/serve.py`: the same idle-point call after each settle, beside the retro hook.
- `clutch/journal.py`: add `supervisor_attempt` to `SIGNAL_NAMES`. The shared supervisor step in `clutch/runner.py::failure_terminal` journals it once per attempt, on every route (`runner.drive`, merge-route `consume_result`, and the idle point), with the stem in the body. It journals it before the `apply_rework` call and before the routed terminal, so the order assertions in `tests/unit/test_supervisor_trigger.py` (the last three events are terminal, draw, keep; no terminal before the lift) stay green. A stem is unsupervised when it has no `supervisor_attempt` after its last `reject_verdict keep actor: operator`.
- `tests/integration/test_closed_sets.py`: add `supervisor_attempt` to the expected set at the `SIGNAL_NAMES ==` assertion; no other edit.
- A fresh worktree from main's HEAD commit at the idle point, removed through `git.py` (`worktree remove` and `prune`), with Effect keys under their own name.
- `docs/how-clutch-works.md`: update only the section on the supervisor step (6.4-6.7) to say every spent-cap route is supervised and when step 1 runs, and the last sentence of section 7.5 (Roadmap driver), which says the supervisor runs inside `runner.drive` only, to say it runs in `runner.drive`, merge-route `consume_result`, and the idle-point step after each settle. `docs/roadmap-driver-plan.md`: update only sections 2 and 6 to match the built behavior.

Out: `ticket_changed` holds, `abandoned` stems, Diagnose `reject` and `abandon-human` routes, the `rework.md` allowed-edit gate, the `caps.supervise` default, the roadmap driver's authoring and release steps. Any other problem found goes to `clutch suggest`.

The forced edits in the fenced source files are limited to the call sites, the idle-point hook, the signal name, and the worktree helper named above.

## Scope fence
- clutch/runner.py
- clutch/daemon.py
- clutch/drain.py
- clutch/serve.py
- clutch/journal.py
- tests/integration/test_closed_sets.py
- docs/how-clutch-works.md
- docs/roadmap-driver-plan.md
- tests/unit/test_supervise_every_route.py
- tests/integration/test_supervise_every_route.py

## Acceptance criteria
1. A merge-stage failure delivered to `TicketWriter.consume_result` with a spent cap and a routed terminal runs the supervisor step and journals `reject_verdict keep actor: supervisor`, not a bare Reject-queue entry; `./dev.py test tests/integration/test_supervise_every_route.py -k merge_route` fails if the stem stays in `reject_queue` with no supervisor attempt.
2. A drain `reject_arrival` stem with no `supervisor_attempt` gets the supervisor step at the next idle point; `./dev.py test tests/integration/test_supervise_every_route.py -k drain_idle` fails if the stem is still unsupervised after the idle point.
3. The idle-point step runs in a worktree whose base equals main's HEAD at that idle point, not the stem's old branch head; `./dev.py test tests/unit/test_supervise_every_route.py -k worktree_base` asserts the base sha equals the sha main returns when main has advanced past the stem's branch head, and not the branch head.
4. The idle-point step journals its Effects under keys that differ from the original run's keys, so a replayed original run does not reuse them; `./dev.py test tests/unit/test_supervise_every_route.py -k effect_keys` asserts the key sets are disjoint.
5. A stem whose `supervise_draws` already equals `caps.supervise` is not supervised again on any route and stays in the Reject queue with its `rework.md`; `./dev.py test tests/unit/test_supervise_every_route.py -k cap_spent` fails if a third supervisor keep is journaled with `caps.supervise` set to 2.
6. A stem whose attempt escalated or was refused (no `cap_consumed supervise`, no keep) is not supervised by a later idle point, whichever route made that attempt (`runner.drive`, merge-route `consume_result`, or an earlier idle point): `./dev.py test tests/unit/test_supervise_every_route.py -k idempotent` fails if two idle points journal two `supervisor_attempt` signals for one operator lineage, or if a stem whose `runner.drive` or merge-route attempt escalated gets a second supervisor LLM call at the next idle point.
7. The idle-point worktree is gone after the step on both approve and escalate, and `git worktree list` names no leftover; `./dev.py test tests/integration/test_supervise_every_route.py -k worktree_removed` fails on a leftover.
8. The supervised `gate_failed` path from `runner.drive` is unchanged; `./dev.py test tests/unit/test_supervisor_trigger.py tests/integration/test_rework_supervise.py` still exit 0.
9. `supervisor_attempt` is in `journal.SIGNAL_NAMES`, and `./dev.py test tests/integration/test_closed_sets.py` exits 0, failing if the signal is missing from the set or the pinned expectation.

## Verification
```
./dev.py test tests/unit/test_supervise_every_route.py tests/integration/test_supervise_every_route.py tests/unit/test_supervisor_trigger.py tests/integration/test_rework_supervise.py tests/integration/test_closed_sets.py
```

## Definition of rejected
The branch is thrown away if the supervisor step is copied into a second code path instead of reused from `failure_terminal`, if the idle-point step runs in the stem's existing worktree or from a commit other than main's HEAD at the idle point, if it reuses the original run's Effect keys, if `caps.supervise` can be exceeded on any route, if an escalated stem is supervised again at a later idle point, or if it supervises `ticket_changed` or `abandoned` stems.

## Time budget
- expected: 70m
- stuck: 130m
