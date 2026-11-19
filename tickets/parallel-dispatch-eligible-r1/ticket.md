---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- serve-parallel-dispatch-r2

## Context
- clutch/scheduler.py::Scheduler.dispatch_next
- clutch/drain.py::_Drain._select
- clutch/drain.py::order_tickets
- clutch/drain.py::sort_key
- clutch/drain.py::reofferable
- tests/unit/test_scheduler_write_queue_seams.py

## Goal / Why
`Scheduler.dispatch_next` and `_Drain._select` each hand-write the same shared candidate filter: the ticket is confirmed, its last state is not in `CLOSED`, it is not in `supersedes_maps`, and `set(t.depends) <= settled`. After this ticket one `eligible()` in `clutch/drain.py` owns that filter and both callers use it, so the parallel-dispatch work edits it once. Dispatch behavior stays identical with parallel off: the same ticket is dispatched, `write_queue` gets the same list, and storm, budget, drought and park side effects fire in the same order for the same tickets.

`eligible()` is only the common prefix, nothing else. The held check, the running/retained rule and the terminal re-offer check stay in each caller, run in today's order. `_Drain._select` runs them after its storm, budget and drought checks, where `held` applies only to re-offers. `Scheduler.dispatch_next` runs them before `self.select`. Moving them into the shared filter would change which tickets reach `over_budget`, `storm_waiting` and `session.park` in drain.

## Boundary contract
### Dispatch eligibility filter
- disposition: create
- owner: clutch/drain.py (`eligible`), beside `order_tickets` and `reofferable`
- consumers: `Scheduler.dispatch_next` in clutch/scheduler.py and `_Drain._select` in clutch/drain.py
- observable change: none. Both callers pick the same ticket, write the same `write_queue` list, and run the same side effects in the same order as before.
- compatibility: this is a refactor and it claims preservation. `eligible()` returns tickets in input order. The scheduler's `self.select` calls stay in `candidates` order (`{**self.pending, **retained}`). `_Drain._select` sorts the result by `sort_key`, so its loop order is unchanged. Each caller still calls `order_tickets` on its own post-predicate set before `write_queue`, so soft edges are applied to the same set as today.
- acceptance: with parallel off, the existing scheduler and drain suites pass unchanged, and the new tests pin the order and side-effect cases above.
- tests: tests/unit/test_drain_eligible.py (`eligible()` and the `Scheduler.dispatch_next` cases, driven with in-memory fakes) and tests/integration/test_drain_eligible_callers.py (the `_Drain._select` case)
- post-merge source of truth: clutch/drain.py `eligible`
- closest existing: the inline filters in `Scheduler.dispatch_next` and `_Drain._select`, and `order_tickets` in clutch/drain.py
- earning reason: two production consumers duplicate the same four-condition filter. `order_tickets` orders a set and does not filter it, and `reofferable` is a per-ticket caller predicate, so neither can own the shared prefix.

## Scope in / Scope out
Scope in:
- Add `eligible(tickets, last, settled, maps) -> list[Ticket]` to clutch/drain.py. It keeps a ticket only when `frontmatter.state == "confirmed"`, `last.get(stem) not in CLOSED`, `stem not in maps` and `set(t.depends) <= settled`, and it preserves input order. It takes no held, running or re-offer arguments.
- `Scheduler.dispatch_next` calls `eligible()` on `candidates.values()`. It then applies, in today's order and over that result, the running/retained rule, the terminal re-offer check (`reofferable`), the held check and finally `self.select(t, self.next_stage(t))`. `select` is still called in `candidates` order, and only for tickets that pass every earlier check. It then calls `order_tickets` on the survivors and `write_queue` as today.
- `_Drain._select` keeps its `open_` map and `depends_cycle` check, then builds `ready` as `sorted(eligible(open_.values(), last, settled, maps), key=sort_key)`. Its loop body (awaiting_operator, storm hold, over_budget, drought park, fresh or re-offer append) and its final `order_tickets` and `write_queue` are unchanged.
- The new `Scheduler.dispatch_next` tests live in tests/unit/test_drain_eligible.py and drive `dispatch_next` with in-memory fakes (a SimpleNamespace journal, fs, async dispatch and ticket_sha), as tests/unit/test_scheduler_write_queue_seams.py does, so the rewritten `dispatch_next` lines run in the unit tier. Only the `_Drain._select` case goes in tests/integration/test_drain_eligible_callers.py.
- Add the new test files in the fence.

Scope out: the running-set, slot and parallel logic; `fences_overlap` and chain order; any change to `order_tickets`, `_soft_edges` or `sort_key`; docs and the roadmap, which the driver rewrites; existing hot test files.

## Scope fence
- clutch/drain.py
- clutch/scheduler.py
- tests/unit/test_drain_eligible.py
- tests/integration/test_drain_eligible_callers.py

## Acceptance criteria
1. `eligible()` returns exactly the tickets that are confirmed, whose last state is not in `CLOSED`, that are absent from `maps`, and whose depends are all settled. A unit test in `tests/unit/test_drain_eligible.py` gives it one ticket failing each condition plus one passing ticket, and asserts the result is only the passing ticket, not an empty list and not all tickets.
2. `eligible()` returns tickets in input order, not `sort_key` order. A unit test passes a P2 ticket before a P0 ticket and asserts the result is `[P2, P0]`, not `[P0, P2]`.
3. `eligible()` does not drop a ticket whose last state is `running` or terminal. A unit test asserts such a ticket is returned, because the running and re-offer rules belong to the callers.
4. `Scheduler.dispatch_next` calls `select` in `candidates` order. A unit test in `tests/unit/test_drain_eligible.py` uses fakes, has two pending tickets whose `pending` order differs from their `sort_key` order, and a fake `select` that records calls. It asserts the recorded order is the `pending` order, not the `sort_key` order.
5. `Scheduler.dispatch_next` never calls `select` for a held ticket or for a ticket whose last state is `running` and that is not retained. A unit test in `tests/unit/test_drain_eligible.py` asserts the fake `select` records neither stem.
6. Soft edge through a filtered ticket: A is P0, C is P1, and B is P2 with `runs_before: [A]` and held. A unit test in `tests/unit/test_drain_eligible.py` asserts the scheduler dispatches A and `write_queue` receives `[A, C]`, not `[C, A]`.
7. `_Drain._select` still records `over_budget` for a ticket whose `stuck_minutes` exceed the ceiling, that is held and that is not re-offerable. A test in `tests/integration/test_drain_eligible_callers.py` asserts the stem is in `over_budget`, not absent. The test also asserts `session.park` call order and `provider_deadlines` order follow `sort_key` order across two drought-parked tickets.
8. `rg -c "set\(t\.depends\) <=" clutch/drain.py clutch/scheduler.py` prints `clutch/drain.py:1` and no `clutch/scheduler.py` line, and the one `drain.py` match is inside `eligible`. No other copy of the filter remains in either caller.
9. The existing scheduler and drain tests pass unchanged with parallel off: `./dev.py test tests/integration/test_scheduler.py tests/integration/test_drain.py tests/unit/test_drain_reoffer.py tests/unit/test_scheduler_write_queue_seams.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_drain_eligible.py tests/integration/test_drain_eligible_callers.py tests/integration/test_scheduler.py tests/integration/test_drain.py tests/unit/test_drain_reoffer.py tests/unit/test_scheduler_write_queue_seams.py
```

## Definition of rejected
The branch is rejected if a held, running or non-reofferable ticket is filtered before drain's storm, budget, drought or park checks, or if `select` is called in a different order or for a different set of tickets. It is also rejected if `write_queue` receives a different list than today in the soft-edge case, if any existing test file listed in Verification is edited, or if a copy of the shared filter remains in either caller.

## Time budget
- expected: 25m
- stuck: 50m
