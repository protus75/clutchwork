---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Runs before
- preflight-once-per-session

## Context
- clutch/drain.py::PRIORITY
- clutch/drain.py::sort_key
- clutch/drain.py::chain
- clutch/drain.py::parallel_order
- tests/unit/test_chain_order.py
- tests/unit/test_scheduler_parallel_fill.py
- tests/unit/test_flake_fix_order.py
- docs/parallel-tickets-plan.md#3. Ordering: fill free slots by longest chain
- docs/parallel-tickets-plan.md#Open decisions

## Goal / Why
With parallel dispatch on, `parallel_order` in `clutch/drain.py` sorts eligible tickets by `(priority != "P0", -chain, *sort_key)`. P0 goes first. Below P0, the ticket with the most unsettled work waiting behind it (`chain`) runs first, whatever its priority. A P2 ticket with three tickets behind it runs before a P1 ticket with none. This follows owner decision 2 of 2026-11-13 in `docs/parallel-tickets-plan.md` ("below P0 only"), which `tests/unit/test_chain_order.py::test_parallel_priority_chain_and_soft_edges` pins.

On 2026-11-22 the owner reordered 34 queued tickets with `clutch ticket order`. P1 and P2 ranked as one tier. `extension-provider-update-action` (P2, three extension tickets behind it) would have dispatched ahead of every P1 ticket, including the Check speedups and `check-opens-own-stage`. The only fix was hand-added `## Runs before` links from the last P1 tickets to the first P2 tickets. Those links go stale whenever the queue changes, and the priority field misleads whoever sets it. Owner decision 2026-11-22 replaces decision 2: priority ranks first at every level, and chain length breaks ties only within one priority.

After this ticket `parallel_order` sorts by `(PRIORITY[priority], -chain, *sort_key)`, so a P1 ticket with chain 0 runs before a P2 ticket with chain 3. Within one priority the longest chain still runs first. `runs_before` soft edges still apply after the sort, as today.

## Boundary contract
### Parallel dispatch order
- disposition: replace
- owner: clutch/drain.py `parallel_order`
- consumers: `clutch/scheduler.py` `Scheduler.dispatch_next` (parallel enabled), and through it `queue.json` `order`, `clutch view status` and the extension's queue order
- observable change: the old contract ranks P0 first, then by `-chain` across P1/P2/P3 together, then by priority. The new contract ranks by full priority (P0 < P1 < P2 < P3 via `PRIORITY`), then `-chain`, then the rest of `sort_key`. `runs_before` soft edges are applied after the sort, unchanged.
- compatibility: P0 ordering is unchanged. Within one priority the order is unchanged. Only tickets of different non-P0 priorities change their relative order. The function signature, `chain`, `fill_slots`, `SKIP_LIMIT`, `order_tickets` (serial path) and `queue.json` shape are unchanged. No ticket, journal or config migration.
- acceptance: a P1 ticket with chain 0 is ordered before a P2 ticket with chain 3
- tests: tests/unit/test_parallel_order_priority.py, plus the updated expectations in tests/unit/test_chain_order.py and tests/unit/test_scheduler_parallel_fill.py
- post-merge source of truth: clutch/drain.py `parallel_order`, described in docs/how-clutch-works.md section 7.2 and docs/parallel-tickets-plan.md section 3

## Scope in / Scope out
Scope in:
- `clutch/drain.py` `parallel_order`: in the sort key, replace the term `t.frontmatter.priority != "P0"` with `PRIORITY[t.frontmatter.priority]`. Keep every other term, and any term another merged ticket has added before it (for example a `fixes` term from `flake-fix-jumps-queue`), as is. Update the docstring if it names P0-only ranking.
- `tests/unit/test_chain_order.py::test_parallel_priority_chain_and_soft_edges`: the first assertion changes from `["zero", "long", "middle", "short"]` to `["zero", "long", "short", "middle"]`. This is the only expectation in the file that changes; the soft-edge assertion (`["x", "y"]`) stays.
- `tests/unit/test_scheduler_parallel_fill.py`: these two tests pin the old cross-priority order (`long` is P2 with chain 2, `short` is P1 with chain 0). In `test_order`, the parallel-enabled parametrize case changes from `(True, "long", ["long", "short"])` to `(True, "short", ["short", "long"])`; the disabled case stays. In `test_p0_precedes_chain`, the queue-order assertion changes from `["urgent", "long", "short"]` to `["urgent", "short", "long"]`; the `urgent` dispatch assertion stays. No other test in the file changes.
- New `tests/unit/test_parallel_order_priority.py` with the criteria-1 to 3 tests, building tickets the way `tests/unit/test_chain_order.py::ticket` does (a local helper in the new file; do not import from the old test module).
- `docs/how-clutch-works.md` section 7.2 Dispatch bullet: replace "`parallel_order` prioritizes P0 then the longest unsettled chain" with wording that says it ranks by priority, then the longest unsettled chain within a priority. Nothing else in that bullet changes.
- `docs/parallel-tickets-plan.md`: in section 3, change the order tuple to `(priority, -chain, age, stem)` and replace the sentence "P0 stays first because ... keep the slots full." with one saying priority ranks first at every level and the longest chain breaks ties within a priority. In "Open decisions" item 2, add that the 2026-11-13 decision was replaced on 2026-11-22: chain order applies within each priority, never across priorities, because a long-chain P2 ticket outranked every P1 ticket.
- `docs/roadmap.md` section 6 decision 5: replace "longest-chain ordering below P0 only (P0 keeps the emergency lane)" with "longest-chain ordering within each priority (replaced the below-P0-only rule on 2026-11-22)". Nothing else in the roadmap changes.

Scope out:
- `order_tickets` and the serial drain order (already priority-first through `sort_key`).
- `chain`, `fill_slots`, `SKIP_LIMIT`, `_soft_edges`, `clutch/scheduler.py`.
- `tests/unit/test_flake_fix_order.py`: its parallel cases compare a P0 ticket with a fix or soft-edge ticket, so they pass unchanged.
- Removing the `## Runs before` links the 2026-11-22 reorder added between P1 and P2 tickets; they stay valid and harmless.
- The extension and snapshot; they draw `queue.json` order as given.

## Scope fence
- clutch/drain.py
- tests/unit/test_chain_order.py
- tests/unit/test_scheduler_parallel_fill.py
- tests/unit/test_parallel_order_priority.py
- docs/how-clutch-works.md
- docs/parallel-tickets-plan.md
- docs/roadmap.md

## Acceptance criteria
1. With eligible tickets `p2_long` (P2, three unsettled tickets depending on it) and `p1_lone` (P1, chain 0), `parallel_order` returns `["p1_lone", "p2_long"]`, not `["p2_long", "p1_lone"]`; checked by `./dev.py test tests/unit/test_parallel_order_priority.py`.
2. Within one priority the longest chain still wins: with `p1_long` (P1, chain 2) and `p1_short` (P1, chain 0), authored in the order short then long, `parallel_order` returns `["p1_long", "p1_short"]`, not the age order `["p1_short", "p1_long"]`; checked by `./dev.py test tests/unit/test_parallel_order_priority.py`.
3. Soft edges still override priority: with `p2_first` (P2) whose `runs_before` names `p1_next` (P1), `parallel_order` returns `["p2_first", "p1_next"]`, not `["p1_next", "p2_first"]`; checked by `./dev.py test tests/unit/test_parallel_order_priority.py`.
4. `tests/unit/test_chain_order.py::test_parallel_priority_chain_and_soft_edges` expects `["zero", "long", "short", "middle"]` and passes; checked by `./dev.py test tests/unit/test_chain_order.py`.
5. With parallel dispatch enabled, the scheduler dispatches the P1 `short` ticket ahead of the P2 long-chain `long` ticket and writes queue order `["short", "long"]`, and with a P0 ticket present writes `["urgent", "short", "long"]`; checked by `./dev.py test tests/unit/test_scheduler_parallel_fill.py`.
6. The full unit suite passes: `./dev.py test tests/unit`.

## Verification
```
./dev.py test tests/unit/test_parallel_order_priority.py tests/unit/test_chain_order.py tests/unit/test_scheduler_parallel_fill.py
./dev.py test tests/unit
```

## Definition of rejected
- P0 tickets no longer rank ahead of all other priorities.
- Within one priority, a shorter chain is ordered before a longer one.
- `runs_before` soft edges stop overriding the sort.
- `order_tickets`, `chain`, `fill_slots` or `clutch/scheduler.py` behavior changes.
- A doc section other than the ones named in Scope in is rewritten.

## Time budget
- expected: 12m
- stuck: 24m