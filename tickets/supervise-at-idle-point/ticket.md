---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
- supervise-every-route
- supervisor-effect-scope

## Context
- clutch/runner.py::failure_terminal
- clutch/daemon.py::apply_rework
- clutch/status.py::reject_queue
- clutch/caps.py
- clutch/drain.py::awaiting_operator
- docs/roadmap-driver-plan.md#Target design

## Goal / Why
Today the supervisor step runs only inside `failure_terminal`, so a Reject-queue stem that arrives another way (a drain `reject_arrival`, whose terminal lacks `routed: reject_queue`) is never supervised and waits for a person. After this ticket, at the serve idle point after each settle and between drain tickets, every Reject-queue stem with no `supervisor_attempt` after its last operator keep gets the supervisor step once, in a detached worktree from main's HEAD at that point, under a key scope, and the attempt is journaled. The worktree is removed through `git.py` on approve and on escalate. This moves the roadmap driver toward running unattended (`docs/roadmap-driver-plan.md` section 6 step 1).

## Scope in / Scope out
Scope in:
- `clutch/runner.py`: move the step body (the `supervisor_attempt` signal, `apply_rework`, the `rework.md` lift on a refused or escalated result) out of `failure_terminal` into one helper `supervise_step(ctx, ticket, findings, *, attempt, trigger, lessons, key_scope=None)` that returns the committed ticket blob sha on an approved update and `None` otherwise. The helper never journals a state transition. A second helper `record_supervisor_keep(ctx, stem, sha)` holds the `consume(..., "supervise", sha)` call and the `reject_verdict keep actor: supervisor` signal. `failure_terminal` calls both in the current order (terminal first, then keep) with no key scope; its behavior is unchanged and existing tests need no edit.
- New `clutch/supervise_idle.py`: `async supervise_idle(checkout, make_ctx)` selects stems and runs the step for each. `make_ctx` is an async callable returning a `StageContext` or `None`; it is awaited only when at least one stem is eligible, and a `None` result means the step is skipped with no `supervisor_attempt` and no git call. A stem is eligible when it is in `reject_queue(events)`, has no `supervisor_attempt` signal after its last operator keep (`lineage(events, stem, actors=("operator",))`), `supervise_draws(events, stem) < config.caps.supervise`, and its last terminal is `premise_failed` or `gate_failed` with a spent cap. It skips a stem whose terminal has a `ticket_changed` reason or is `abandoned`. Decision on the documented exclusions: the idle step deliberately supervises merge-conflict-handoff terminals and stems that already requested Rework, because the `sup` key scope keeps their Effect keys from replaying; the two doc statements that say otherwise are updated (see the `docs/how-clutch-works.md` item). For each eligible stem, it adds a detached worktree at `ctx.worktree(stem)` from `main` with `git.worktree_add_detached`, calls `supervise_step` with `key_scope="sup"` and an attempt number equal to the count of that stem's `supervisor_attempt` signals, calls `record_supervisor_keep` on an approved result, and in `finally` calls `git.worktree_remove` then `git.worktree_prune`. It journals no terminal. Findings come from one `Finding` built from the last terminal's `reason`.
- `clutch/serve.py`: in the dispatch loop, when `upgrade_idle()` is true and the engine is not stopping or paused, call `supervise_idle` under `self.mutations()` before `dispatch_next`. `make_ctx` is a lazy async callable that returns `(await self.prepare(replace(self.checkout, config=snapshot_config(self.control.load_config())))).ctx`, as `run_retro` does; it runs only when `supervise_idle` finds an eligible stem, so provider preflight does not run on idle polls with nothing to supervise.
- `clutch/drain.py`: in `Drain.run`, call `supervise_idle` after the retro and driver steps when `_between_tickets()` is true. `make_ctx` is a lazy async callable that returns `None` when the dispatch has no `prepare` attribute, and otherwise runs `await self.dispatch.prepare()` and returns `self.dispatch.callback.ctx`. Existing drain tests pass dispatches with no `prepare`, so for them the hook skips supervision.
- `docs/how-clutch-works.md`: update section 6.6 and the roadmap-driver loop paragraph that says the supervisor runs only inside `runner.drive` and merge-route `TicketWriter.consume_result`, to add the idle-point hook. In section 6.4 (line 413), drop the clause "and a conflict handoff never does" from the `routed` sentence and say the idle-point hook supervises a conflict-handoff stem. In the section 6.6 Supervisor keep bullet (line 446), drop the "attempts that already requested Rework (whose Effect keys would replay)" exclusion and say the idle step runs under a key scope so those keys do not replay; the other exclusions stay.
- New tests `tests/unit/test_supervise_idle_point.py` and `tests/unit/test_supervise_idle_hooks.py`, fakes and `tmp_path` only.

Scope out: `ticket_changed` and `abandoned` stems, the key-scope plumbing (merged in `supervisor-effect-scope`), `caps.py`, `rework.py`, `daemon.py`, `clutch/specs/`, the extension, and `clutch/help.py`.

## Scope fence
- clutch/runner.py
- clutch/supervise_idle.py
- clutch/serve.py
- clutch/drain.py
- docs/how-clutch-works.md
- tests/unit/test_supervise_idle_point.py
- tests/unit/test_supervise_idle_hooks.py

## Acceptance criteria
1. With a fake `ctx`, a Reject-queue stem whose terminal carries no `routed` field (a drain `reject_arrival`) is supervised exactly once by `supervise_idle`, and a second call journals no second `supervisor_attempt`; checked by `./dev.py test tests/unit/test_supervise_idle_point.py`.
2. `supervise_idle` appends no `state_transition` event on approve, refuse, or escalate, while `failure_terminal` still appends exactly one; checked by `./dev.py test tests/unit/test_supervise_idle_point.py`.
3. A stem with a `supervisor_attempt` before its last operator keep is supervised again, and one with it after is not; checked by `./dev.py test tests/unit/test_supervise_idle_point.py`.
4. A stem whose reason is `ticket_changed`, one whose last terminal is `abandoned`, and one with `supervise_draws` equal to `caps.supervise` each get no `supervisor_attempt` and no worktree, not a refused attempt; checked by `./dev.py test tests/unit/test_supervise_idle_point.py`.
5. The fake git records `worktree_add_detached` from `main`, then `worktree_remove`, then `worktree_prune`, on an approved update, and the same removal and prune on an escalation; no bare filesystem delete of the worktree occurs; checked by `./dev.py test tests/unit/test_supervise_idle_point.py`.
6. The recorded effect keys of the idle step contain `sup-` in the sequence position and none equals an unscoped key; checked by `./dev.py test tests/unit/test_supervise_idle_point.py`.
7. An approved idle step journals `cap_consumed` with `cap: supervise` and `reject_verdict keep actor: supervisor` after the `supervisor_attempt`; checked by `./dev.py test tests/unit/test_supervise_idle_point.py`.
8. With fakes, the serve dispatch loop calls `supervise_idle` when `upgrade_idle()` is true and does not call it when it is false or the engine is stopping; checked by `./dev.py test tests/unit/test_supervise_idle_hooks.py`.
9. With fakes, `Drain.run` calls `supervise_idle` after a settle when `_between_tickets()` is true, and not while a ticket's retry cycle is still open; checked by `./dev.py test tests/unit/test_supervise_idle_hooks.py`.
10. Every existing test passes unedited, including `tests/unit/test_supervisor_trigger.py` and `tests/unit/test_supervise_merge_route.py`; checked by `./dev.py test`.
11. With a dispatch that has no `prepare`, `Drain.run` with an otherwise eligible Reject-queue stem journals no `supervisor_attempt` and makes no git call, and `prepare` is not called when no stem is eligible; checked by `./dev.py test tests/unit/test_supervise_idle_hooks.py`.
12. In serve, the fake `prepare` is called zero times when no Reject-queue stem is eligible and once when one is, and `make_ctx` is not awaited in the first case; checked by `./dev.py test tests/unit/test_supervise_idle_hooks.py`.
13. A Reject-queue stem from a merge-conflict handoff (no `supervised` marker) and a stem that already requested Rework each get exactly one `supervisor_attempt` from `supervise_idle`, not zero; checked by `./dev.py test tests/unit/test_supervise_idle_point.py`.

## Verification
```
./dev.py test tests/unit/test_supervise_idle_point.py tests/unit/test_supervise_idle_hooks.py
./dev.py test
```

## Definition of rejected
`supervise_idle` or the shared helper journals a terminal; the step body is copied instead of moved; `failure_terminal` behavior or event order changes; a stem is supervised twice in one lineage; a worktree is removed other than through `git.py`; an unscoped effect key is used at the idle point.

## Time budget
- expected: 45m
- stuck: 90m
- reason: the helper move, the new selector module and the two hooks share one contract and one set of fakes, so splitting would leave an unused helper or hook
