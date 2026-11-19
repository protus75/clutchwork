---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- chain-order
- parallel-config
- serve-parallel-dispatch-r2
- parallel-dispatch-eligible-r1

## Context
- clutch/scheduler.py::Scheduler.dispatch_next
- clutch/drain.py::parallel_order
- clutch/drain.py::fill_slots
- clutch/drain.py::order_tickets
- clutch/drain.py::write_queue
- clutch/config.py::Parallel
- clutch/tickets.py::fences_overlap
- clutch/daemon.py::daemon_core
- clutch/__main__.py::build_daemon_core
- tests/unit/test_scheduler_write_queue_seams.py
- tests/unit/test_drain_eligible.py
- docs/parallel-tickets-plan.md#3. Ordering: fill free slots by longest chain

## Goal / Why
Roadmap row 164. `parallel_order`, `fill_slots` and `SKIP_LIMIT` exist in `clutch/drain.py` (merged as `chain-order`) but nothing calls them: `Scheduler.dispatch_next` always runs `order_tickets` and dispatches `ordered[0]`. After this ticket, when `scheduler.parallel.enabled` is true, `dispatch_next` orders the eligible tickets with `parallel_order` (P0 first, then longest chain), picks the first one that `fill_slots` accepts against the tickets this scheduler has in flight, and keeps the per-stem overlap-skip counts between calls so a repeatedly skipped ticket becomes a barrier. Each skip goes to the engine log, and `queue.json` lists the order as dispatched. With parallel off nothing changes.

Honest limit, so the criteria do not promise more: `dispatch_next` still holds its single `_slot` lock until the dispatched run returns (row 166, `serve-dispatch-returns-on-slot`), so in production the in-flight set is empty at selection time and the overlap skip fires only after that row lands. This ticket delivers the selection and the in-flight bookkeeping that row 166 needs; tests drive the in-flight set directly through the scheduler's own tracking.

## Boundary contract
### Scheduler dispatch selection
- disposition: extend
- owner: clutch/scheduler.py (`Scheduler.dispatch_next`)
- consumers: `serve.py` dispatch loop, `daemon_core` and `build_daemon_core` composition, and the `Scheduler` tests that call `dispatch_next`
- observable change: with `scheduler.parallel.enabled` true, the dispatched ticket is the first `fill_slots` accepts from the `parallel_order` list, `queue.json` `order` lists the dispatched ticket first and the remaining ordered candidates after it, and `dispatch_next` returns `None` when every candidate overlaps an in-flight ticket or `len(in-flight) >= parallel.max_runs`. With it false, selection, `write_queue` input and return value are exactly as today.
- compatibility: preservation when disabled (the default): the same `order_tickets` call, same list to `write_queue`, same dispatched ticket. A `Scheduler` built without the new attributes behaves as parallel off. The `Parallel` config is read on each call, so a config reload applies at the next dispatch.
- acceptance: the unit tests in the new file below pin parallel-off equality with today's choice and the parallel-on ordering, overlap skip, barrier, slot cap and log cases.
- tests: tests/unit/test_scheduler_parallel_fill.py
- post-merge source of truth: clutch/scheduler.py `Scheduler.dispatch_next`
### Engine log `dispatch_skip` event
- disposition: create
- owner: clutch/scheduler.py (`Scheduler.log` callable, set by serve to `EngineLog.event`)
- consumers: operators reading `engine.log`; no code reads it for a decision
- observable change: one `dispatch_skip` line per overlap skip, with `stem` and the new skip `count`. It is never journaled.
- compatibility: the engine log is diagnostic and non-authoritative (clutch/enginelog.py); no existing event changes.
- acceptance: a skipped candidate produces exactly one `dispatch_skip` call carrying its stem and count, and none when parallel is off.
- tests: tests/unit/test_scheduler_parallel_fill.py
- post-merge source of truth: clutch/scheduler.py
- closest existing: `EngineLog.event` in clutch/enginelog.py, used by `serve.py` for events such as `self_upgrade_off`
- earning reason: `Scheduler` has no logger today and parallel-tickets-plan section 3 requires skips in the engine log. It reuses `EngineLog.event` through an injected callable rather than building a second logger, matching how the scheduler already takes `select` and `continuations` as replaceable attributes.

## Scope in / Scope out
Scope in:
- `clutch/scheduler.py`: add replaceable attributes `parallel` (a `Callable[[], Parallel]`, default returns `Parallel()`, i.e. disabled), `log` (a `Callable[..., None]`, default no-op), plus `self.flying: dict[str, Ticket]` and `self.skips: dict[str, int]`. `dispatch_next` records the dispatched ticket in `flying` before awaiting `self.dispatch` and removes it in a `finally`. When `parallel().enabled` is false the existing path (`order_tickets`, `ordered[0]`) runs unchanged. When true: return `None` if `len(flying) >= max_runs`; build `unsettled` as the candidate tickets not in `settled` plus `flying`, order `ready` with `parallel_order(ready, authored, unsettled)`, call `fill_slots(ordered, flying.values(), 1, parallel.shared_paths, self.skips)` (free is 1 because `dispatch_next` dispatches one ticket per call), store the returned counts in `self.skips`, call `self.log("dispatch_skip", stem=..., count=...)` once for each stem whose count rose, call `write_queue` with the dispatched ticket first and the other ordered tickets after it, return `None` if nothing was dispatched, else remove it from `pending` and dispatch it as today.
- `clutch/daemon.py::daemon_core`: add a keyword `log: Callable[..., None] | None = None`; after building the scheduler set `scheduler.parallel = lambda: load().scheduler.parallel`, and set `scheduler.log = log` when `log` is given.
- `clutch/__main__.py::build_daemon_core`: add the same `log` keyword and forward it to `daemon_core`.
- `clutch/serve.py`: pass `log=self.log.event` in its `build_daemon_core(...)` call.
- `docs/how-clutch-works.md` section 7.2 Dispatch bullet: replace "the scheduler runs one ticket at a time" and "the scheduler still awaits each dispatch" wording only as needed to say that, with `scheduler.parallel.enabled`, candidates are ordered by `parallel_order`, a candidate whose fence overlaps an in-flight ticket is skipped and logged (`dispatch_skip`), and one skipped `SKIP_LIMIT` times blocks later candidates. Leave the rest of the bullet, and the awaiting-each-dispatch statement, which stays true until row 166.
- New test file `tests/unit/test_scheduler_parallel_fill.py` driving `dispatch_next` with in-memory fakes as `tests/unit/test_scheduler_write_queue_seams.py` does; tickets there carry `scope_fence`, `depends`, `runs_before` and `priority`.

Scope out:
- Waiting for a run to finish versus returning on slot fill (`serve-dispatch-returns-on-slot`, row 166); running more than one ticket at once, the merge queue, and `DaemonAdmission`.
- Run-alone handling after a conflict discard (`conflict-rerun-runs-alone`, row 165); `runs_alone` is used as it is.
- `_Drain._select` and drain ordering; `drain.py`, `tickets.py` and `config.py` are not edited.
- Counting tickets waiting in the merge queue as in flight; in this ticket in-flight means dispatched by this scheduler and not yet returned.
- Roadmap row edits (the driver rewrites rows).

## Scope fence
- clutch/scheduler.py
- clutch/daemon.py
- clutch/__main__.py
- clutch/serve.py
- docs/how-clutch-works.md
- tests/unit/test_scheduler_parallel_fill.py

## Acceptance criteria
1. With parallel disabled (the default `Parallel()`), a P2 ticket with a long chain and a P1 ticket with no chain: the P1 ticket is dispatched and `queue.json` `order` equals the `order_tickets` result, not the `parallel_order` result. `./dev.py test tests/unit/test_scheduler_parallel_fill.py` and the unchanged `tests/unit/test_scheduler_write_queue_seams.py` and `tests/unit/test_drain_eligible.py` pass.
2. With parallel enabled, a P2 ticket that has two unsettled dependents is dispatched before a P1 ticket with none (chain order), and a P0 ticket with no dependents is dispatched before both; `./dev.py test tests/unit/test_scheduler_parallel_fill.py` rules out priority-only order.
3. With parallel enabled and one in-flight ticket whose fence overlaps the first-ordered candidate, `dispatch_next` dispatches the next non-overlapping candidate, returns that ticket, not `None` and not the overlapping one, and the overlapping stem's count in `scheduler.skips` is 1; `./dev.py test tests/unit/test_scheduler_parallel_fill.py`.
4. A candidate whose count already equals `SKIP_LIMIT` and still overlaps makes `dispatch_next` return `None` with no ticket dispatched, even though a later candidate does not overlap; `./dev.py test tests/unit/test_scheduler_parallel_fill.py`.
5. When `len(flying) >= parallel.max_runs`, `dispatch_next` returns `None` and does not call `dispatch`, and the skip counts are unchanged; `./dev.py test tests/unit/test_scheduler_parallel_fill.py`.
6. Each overlap skip calls `scheduler.log` once with `"dispatch_skip"`, the stem and the new count, and a parallel-off run never calls it; `./dev.py test tests/unit/test_scheduler_parallel_fill.py`.
7. `queue.json` written by a parallel dispatch lists the dispatched ticket first, then the remaining ordered candidates in order, with a skipped ticket after it, not before; `./dev.py test tests/unit/test_scheduler_parallel_fill.py`.
8. With an in-flight ticket that overlaps the candidate only under a `parallel.shared_paths` entry, the candidate is dispatched and no skip is counted; `./dev.py test tests/unit/test_scheduler_parallel_fill.py`.
9. After `dispatch_next` returns, including when `dispatch` raises, `flying` holds exactly the entries it held before the call (empty when it started empty); `./dev.py test tests/unit/test_scheduler_parallel_fill.py`.
10. A unit test in the same file calls `daemon_core` with in-memory fakes (journal, fs, a `load` returning a `Config` whose `scheduler.parallel` is enabled with `max_runs` 3, stub `bind`, `read` and `ticket_sha`) and a recording `log`; `core.scheduler.parallel()` equals that loaded `Parallel` (not the disabled default) and `core.scheduler.log` is the recording callable; `./dev.py test tests/unit/test_scheduler_parallel_fill.py`.
11. The existing scheduler, daemon and serve tests pass unchanged: `./dev.py test tests/integration/test_scheduler.py tests/integration/test_serve_upgrade.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_admission_running_set.py tests/integration/test_requisition_gate.py tests/integration/test_daemon_core_queue_seams.py`.
12. `docs/how-clutch-works.md` section 7.2 states the parallel ordering and the logged skip, and still says the scheduler awaits each dispatch; checked by review, with no standing doc test.

## Verification
```
./dev.py test tests/unit/test_scheduler_parallel_fill.py tests/unit/test_scheduler_write_queue_seams.py tests/unit/test_drain_eligible.py tests/unit/test_chain_order.py tests/integration/test_scheduler.py tests/integration/test_serve_upgrade.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_admission_running_set.py tests/integration/test_requisition_gate.py tests/integration/test_daemon_core_queue_seams.py
```

## Definition of rejected
The branch is rejected if parallel off changes the dispatched ticket, the list passed to `write_queue`, or the return value; if `dispatch_next` awaits less than today or dispatches more than one ticket per call; if a skip is journaled instead of engine-logged; if `drain.py`, `tickets.py` or `config.py` are edited; or if skip counts are kept anywhere but the scheduler instance.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one selection change in one file plus a two-line wiring and one doc paragraph; the wiring cannot go in a separate ticket without leaving the new attributes unset
