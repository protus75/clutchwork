---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Context
- clutch/drain.py::fill_slots
- clutch/drain.py::SKIP_LIMIT
- clutch/tickets.py::fences_overlap
- clutch/scheduler.py::Scheduler.dispatch_next
- tests/unit/test_chain_order.py
- tests/unit/test_scheduler_parallel_fill.py::test_barrier_and_capacity
- docs/parallel-tickets-plan.md#3.
- tests/regress_context_directory.py

## Goal / Why
With `scheduler.parallel` on and `max_runs: 2`, serve ran one ticket while four ready tickets waited (evidence: `evidence/evidence.txt`, 2026-11-22). The top-ranked ready ticket, `io-helpers-loop-scheduler`, overlaps the in-flight `llm-request-subject` on four test files. After `SKIP_LIMIT` (3) overlap skips it became a starvation barrier, and `fill_slots` in `clutch/drain.py` then `break`s. That stops every later candidate, including `serve-no-roadmap`, `stats-tokens-not-usd`, `running-step-stale-event` and `heartbeat-file-removed`, whose fences overlap neither ticket. One slot sat idle for the whole run of the in-flight ticket.

The defect is in the spec: `docs/parallel-tickets-plan.md` section 3 says "Nothing new dispatches until it can start." The barrier exists so that later tickets cannot keep taking the files the barrier ticket needs. A later candidate whose fence overlaps neither anything in flight nor the barrier ticket cannot delay the barrier. When the last in-flight ticket that overlaps the barrier finishes, it frees a slot, and the barrier ticket is first in order for it. After this ticket, a barrier blocks only later candidates that overlap it. Disjoint candidates fill free slots.

## Boundary contract
### Parallel slot filling
- disposition: extend
- owner: clutch/drain.py
- consumers: `Scheduler.dispatch_next` in clutch/scheduler.py (the only caller)
- observable change: once a candidate becomes a barrier (skipped `SKIP_LIMIT` or more times), `fill_slots` keeps walking the order and dispatches a later candidate only when `fences_overlap` is false against every in-flight ticket, every ticket already selected in this call, and every barrier ticket; a later candidate that overlaps a barrier is skipped and counted like any overlap skip
- compatibility: signature, return shape, skip counting, `shared_paths` and run-alone/rerun handling are unchanged; with no barrier the result is identical to today
- acceptance: the barrier ticket still starts before any later candidate that overlaps it; disjoint later candidates are dispatched while the barrier waits
- tests: tests/unit/test_barrier_admits_disjoint.py, updated tests/unit/test_chain_order.py and tests/unit/test_scheduler_parallel_fill.py
- post-merge source of truth: clutch/drain.py::fill_slots

## Scope in / Scope out
Scope in:
- `clutch/drain.py::fill_slots`: when a skipped candidate reaches the barrier condition (`prior >= SKIP_LIMIT`), stop breaking out of the loop. Add the barrier ticket to the tickets later candidates are checked against (the `occupied` list) and keep walking. The function docstring says a barrier blocks only overlapping later candidates.
- New `tests/unit/test_barrier_admits_disjoint.py` with the acceptance cases below.
- `tests/unit/test_chain_order.py::test_skips_barrier_and_input_unchanged`: the second `fill_slots` call has `later` (fence `docs`) disjoint from `blocked` (fence `src/file`), so the expected dispatch changes from `[]` to `["later"]`. Keep `counts == {"blocked": 4}`. This is the only expectation in that file that changes.
- `tests/unit/test_scheduler_parallel_fill.py::test_barrier_and_capacity`: `later` (fence `docs`) is now dispatched beside the barrier. Update the first-call expectations to match: `later` is dispatched, `blocked`'s skip count goes to `SKIP_LIMIT + 1` and is logged once. Keep the capacity half of the test, which uses a full slot set and returns `None`. This is the only test in that file that changes.
- New carried reproducer `tests/regress_barrier_admits_disjoint.py` that follows the shape of `tests/regress_context_directory.py`: in-memory `Ticket`s, a call to `clutch.drain.fill_slots`, and one `regression_result` JSON object on stdout.
- `docs/parallel-tickets-plan.md` section 3, the "Starvation guard" bullet: replace "Nothing new dispatches until it can start" with the overlap-only rule.
- `docs/how-clutch-works.md` section 7.2, the dispatch bullet: replace "a candidate skipped `SKIP_LIMIT` times blocks later candidates" with "...blocks later candidates whose fences overlap it".

Scope out: `SKIP_LIMIT`'s value, `parallel_order`, `fences_overlap`, `Scheduler.dispatch_next` (it still selects one ticket per call), and `max_unmerged`.

## Scope fence
- clutch/drain.py
- tests/unit/test_barrier_admits_disjoint.py
- tests/unit/test_chain_order.py
- tests/unit/test_scheduler_parallel_fill.py
- tests/regress_barrier_admits_disjoint.py
- docs/parallel-tickets-plan.md
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_barrier_admits_disjoint.py` passes and covers these cases:
   - In-flight `busy` has fence `src`, barrier `blocked` has fence `src/file` with skips `{"blocked": SKIP_LIMIT}`, and `later` has fence `docs`. `fill_slots([blocked, later], [busy], 1, [], skips, set())` returns `[later]`, not `[]`.
   - A candidate that overlaps the barrier but nothing in flight is still held. In-flight `busy` has fence `a`, barrier `blocked` has fences `a` and `b` with skips `{"blocked": SKIP_LIMIT}`, and `later` has fence `b`. The result is `[]`, not `[later]`, and the returned counts give `later` a skip count of 1.
   - When the barrier's overlap clears (`in_flight` is empty), `fill_slots([blocked, later], [], 1, [], skips, set())` returns `[blocked]` first, not `[later]`.
2. `./dev.py test tests/unit/test_chain_order.py tests/unit/test_scheduler_parallel_fill.py tests/unit/test_conflict_rerun_runs_alone.py` passes with only the two expectation changes named in Scope in.
3. `uv run python tests/regress_barrier_admits_disjoint.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `defect` and exits non-zero on the base.

## Verification
```
./dev.py test tests/unit/test_barrier_admits_disjoint.py tests/unit/test_chain_order.py tests/unit/test_scheduler_parallel_fill.py tests/unit/test_conflict_rerun_runs_alone.py
```

## Definition of rejected
- A barrier ticket can be passed over for a free slot by a later candidate that overlaps it.
- The change touches `Scheduler.dispatch_next`, `parallel_order`, or `SKIP_LIMIT`, or adds a config knob.

## Time budget
- expected: 15m
- stuck: 30m

## Regression
```
uv run python tests/regress_barrier_admits_disjoint.py
```
- carries: tests/regress_barrier_admits_disjoint.py
