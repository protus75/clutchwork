---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- fence-overlap

## Context
- clutch/drain.py::PRIORITY
- clutch/drain.py::sort_key
- clutch/drain.py::order_tickets
- clutch/tickets.py::Ticket
- clutch/tickets.py::fences_overlap
- docs/parallel-tickets-plan.md#Parallel ticket runs: plan

## Goal / Why
Roadmap row 44, parallel plan ticket 5. After this ticket `clutch/drain.py` holds the pure ordering logic that parallel dispatch will call: `chain()` counts the unsettled tickets waiting behind a ticket, `parallel_order()` orders eligible tickets as (P0 first, longest chain, priority, age, stem) while still applying `runs_before` soft edges, `fill_slots()` walks that order and picks every candidate that does not overlap anything in flight until the free slots are full, and a starvation guard makes a candidate skipped for overlap `SKIP_LIMIT` (3) times a barrier that stops further dispatch. Nothing calls these yet; `serve-parallel-dispatch` will. Landing them pure and tested first gives dispatch one tested owner for ordering and slot filling, and long dependency chains start early so slots stay full.

## Boundary contract
### Parallel dispatch ordering
- disposition: extend
- owner: clutch/drain.py
- consumers: none yet; `serve-parallel-dispatch` calls `parallel_order` and `fill_slots`. `order_tickets` keeps its single-flight caller.
- observable change: new pure functions `chain`, `parallel_order`, `fill_slots` and constant `SKIP_LIMIT = 3`. No journal, config, queue file or CLI output changes. `order_tickets` returns what it returned before; its soft-edge loop is shared with `parallel_order` rather than copied.
- compatibility: `order_tickets` and `sort_key` behave identically for every input, so single-flight dispatch is unchanged. Fence overlap is decided only by `clutch.tickets.fences_overlap`; no second fence grammar is added.
- acceptance: unit tests pin chain counts, the order key, runs_before edges, slot filling, the barrier, and the unchanged `order_tickets` result.
- tests: new `tests/unit/test_chain_order.py`.
- post-merge source of truth: clutch/drain.py

## Scope in / Scope out
In, all in `clutch/drain.py`:
- `chain(stem, unsettled)`: `unsettled` maps stem to Ticket. Returns the number of distinct tickets reachable from `stem` by following dependents: a ticket `u` is a dependent of `t` when `t.stem` is in `u.depends` or `u.stem` is in `t.runs_before`. The start ticket is not counted, and a cycle terminates.
- `parallel_order(eligible, authored, unsettled)`: sorts by `(priority != P0, -chain, *sort_key)` then applies the same `runs_before` soft-edge selection `order_tickets` uses. To share that loop, move it into one private helper called by both functions; `order_tickets` behavior stays byte-for-byte the same.
- `SKIP_LIMIT = 3` and `fill_slots(ordered, in_flight, free, shared, skips)`: `skips` maps stem to its prior overlap-skip count. Returns `(dispatch, skips)` where `dispatch` is a list of tickets and `skips` is a new dict (the input is not mutated). A candidate that overlaps (by `fences_overlap`) any in-flight ticket or any ticket already chosen this walk is skipped and its count increases by one. A skipped candidate whose count before this walk was already `SKIP_LIMIT` or more is a barrier: the walk stops and nothing after it is chosen. Dispatched stems are dropped from `skips`. Stop when `free` tickets are chosen.

Out: any caller or wiring; `scheduler.parallel` config; `write_queue`; the engine-log line for each skip (the caller logs from the returned counts); run-alone after a conflict rerun; docs (ticket `serve-parallel-dispatch` documents the behavior when it wires it); `clutch/graph.py`.

## Scope fence
- clutch/drain.py
- tests/unit/test_chain_order.py

## Acceptance criteria
1. For a diamond where B and C depend on A and D depends on B and C, `chain('A', ...)` returns 3 (not 4: D is counted once and A itself is not), checked by `./dev.py test tests/unit/test_chain_order.py`.
2. A ticket with no dependents has `chain` 0, and a ticket whose `runs_before` names an unsettled stem counts that stem, not 0, checked by `./dev.py test tests/unit/test_chain_order.py`.
3. A two-ticket `depends` cycle makes `chain` return a finite count instead of looping, checked by `./dev.py test tests/unit/test_chain_order.py`.
4. `parallel_order` puts a P0 ticket with chain 0 before a P1 ticket with chain 5, and puts a P2 ticket with chain 3 before a P1 ticket with chain 0 (not priority-first), checked by `./dev.py test tests/unit/test_chain_order.py`.
5. With Y a P0 ticket (chain 0) and X a P1 ticket whose `runs_before` names Y (so chain(X) = 1 and the sort key alone puts Y first), `parallel_order` returns X before Y, not Y before X; this fails if the soft-edge helper is not applied. Checked by `./dev.py test tests/unit/test_chain_order.py`.
6. `order_tickets` returns the same list as before for a fixed input covering priorities, ages and a `runs_before` edge, checked by `./dev.py test tests/unit/test_chain_order.py` and the existing `./dev.py test tests/integration/test_drain.py`.
7. `fill_slots` with `free=2` and three non-overlapping candidates returns the first two in order, not three, checked by `./dev.py test tests/unit/test_chain_order.py`.
8. `fill_slots` skips a candidate overlapping an in-flight ticket and still dispatches a later non-overlapping one while its count is below `SKIP_LIMIT`; the skipped stem's count is 1 in the returned dict and the input dict is unchanged, checked by `./dev.py test tests/unit/test_chain_order.py`.
9. A candidate with prior count `SKIP_LIMIT` that still overlaps stops the walk, so a later non-overlapping candidate is not dispatched (returns `[]`, not that candidate), checked by `./dev.py test tests/unit/test_chain_order.py`.
10. A candidate overlapping only on a `shared` path is dispatched, and a candidate whose ticket has `gate_bypass` naming `scope_fence` is skipped when it overlaps without the shared allowance, checked by `./dev.py test tests/unit/test_chain_order.py`.

## Verification
```
./dev.py test tests/unit/test_chain_order.py tests/integration/test_drain.py
```

## Definition of rejected
The branch changes the order or result of `order_tickets`, adds a second path-matching rule instead of calling `fences_overlap`, wires the functions into dispatch, config, or any caller, or adds tests to `tests/integration/test_drain.py`.

## Time budget
- expected: 20m
- stuck: 40m
