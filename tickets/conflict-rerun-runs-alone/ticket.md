---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- clutch/tickets.py::runs_alone
- clutch/tickets.py::fences_overlap
- clutch/drain.py::fill_slots
- clutch/scheduler.py::Scheduler.dispatch_next
- clutch/caps.py::conflict_reruns
- docs/parallel-tickets-plan.md#Target design

## Goal / Why
Roadmap row 165, replacing merged rows 43 and 159. `docs/parallel-tickets-plan.md` section 2 says a ticket run again after a conflict discard must run alone and ignore `shared_paths`. Today `runs_alone` in `clutch/tickets.py` is true only for a ticket whose frontmatter carries a `scope_fence` `gate_bypass`. The `merge_conflict_rerun` signal that `clutch/daemon.py` journals never reaches `fences_overlap`, so a rerun ticket is admitted beside an in-flight ticket whose fence overlaps it only on a `shared_paths` entry. That is the overlap that already produced the conflict. After this ticket, a ticket with at least one `merge_conflict_rerun` signal in its lineage is treated as run-alone by `fill_slots`, in both directions: it is not admitted beside an overlapping in-flight ticket, no other ticket is admitted beside it when their fences overlap, and `shared_paths` waives nothing for either.

## Boundary contract
### Parallel fence overlap
- disposition: extend
- owner: clutch/tickets.py (`fences_overlap`)
- consumers: `clutch/drain.py::fill_slots`, called only by `clutch/scheduler.py::Scheduler.dispatch_next`
- observable change: with parallel enabled, a ticket that has been rerun after a conflict discard, or an in-flight ticket that has, no longer overlaps-through-`shared_paths` with a candidate. A candidate that overlaps it is skipped and counted by the existing `dispatch_skip` path. A rerun ticket with no overlapping in-flight ticket dispatches as before. With parallel disabled nothing changes.
- compatibility: the `scope_fence` `gate_bypass` rule keeps its meaning. A ticket with no rerun signal and no bypass is checked exactly as today. `fences_overlap` and `fill_slots` gain one required parameter, and every caller is updated in this change; there is no default and no second path.
- acceptance: the unit tests named in the criteria fail on the old overlap rule.
- tests: new unit file for the rerun rule; the two existing unit files that call the changed signatures are updated by the added argument only
- post-merge source of truth: clutch/tickets.py

## Scope in / Scope out
Scope in:
- `fences_overlap(a, b, shared, rerun)` in `clutch/tickets.py`: `rerun` is a collection of stems. The shared-path allowance is empty when `runs_alone(a)`, `runs_alone(b)`, `a.stem in rerun` or `b.stem in rerun`.
- `fill_slots(..., shared, skips, rerun)` in `clutch/drain.py` passes `rerun` through to `fences_overlap`.
- `Scheduler.dispatch_next` in `clutch/scheduler.py` computes `rerun` from the journal events it already reads: every stem in the candidates and in `self.flying` for which `caps.conflict_reruns(events, stem) > 0`. It passes that set to `fill_slots`.
- `tests/unit/test_fence_overlap.py` and `tests/unit/test_chain_order.py`: add the new argument to each existing call to `fences_overlap` and `fill_slots`, and nothing else in them.
- `docs/how-clutch-works.md`: in the sentence at the parallel-dispatch bullet that says candidates overlapping an in-flight fence are skipped, add that a ticket rerun after a conflict discard, and a candidate overlapping one, ignore `shared_paths`. Edit only that sentence.
- A new unit test file for the rule.

Scope out:
- The rerun cap (`CONFLICT_RERUN_LIMIT`), the discard and the `merge_conflict_rerun` signal itself are unchanged.
- No change to `shared_paths` for the model-resolve step; that exclusion waiver is separate.
- No change to the serial (parallel disabled) path.

## Scope fence
- clutch/tickets.py
- clutch/drain.py
- clutch/scheduler.py
- tests/unit/test_fence_overlap.py
- tests/unit/test_chain_order.py
- tests/unit/test_conflict_rerun_runs_alone.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `fences_overlap` returns True for two tickets whose fences overlap only through a `shared_paths` entry when one of them is named in `rerun`, and False when `rerun` is empty (the old result for the same pair), checked by `./dev.py test tests/unit/test_conflict_rerun_runs_alone.py`.
2. The rule is symmetric: the result is True whether the rerun stem is the first or the second argument, checked by `./dev.py test tests/unit/test_conflict_rerun_runs_alone.py`.
3. `fill_slots` skips a candidate named in `rerun` that overlaps an in-flight ticket through `shared_paths` only, and counts the skip in the returned counts. It still dispatches the same candidate when `rerun` is empty, checked by `./dev.py test tests/unit/test_conflict_rerun_runs_alone.py`.
4. `Scheduler.dispatch_next` with parallel enabled and a journal holding one `merge_conflict_rerun` signal for the candidate does not dispatch it beside an in-flight ticket that overlaps it through `shared_paths`, and does dispatch it when the signal is absent, checked by `./dev.py test tests/unit/test_conflict_rerun_runs_alone.py`.
5. The existing `scope_fence` bypass behavior is preserved: the existing assertions in `tests/unit/test_fence_overlap.py` and `tests/unit/test_chain_order.py` pass unchanged apart from the added argument, checked by `./dev.py test tests/unit/test_fence_overlap.py tests/unit/test_chain_order.py tests/unit/test_scheduler_parallel_fill.py`.
6. The full suite passes, checked by `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_conflict_rerun_runs_alone.py tests/unit/test_fence_overlap.py tests/unit/test_chain_order.py tests/unit/test_scheduler_parallel_fill.py
./dev.py test
```

## Definition of rejected
`runs_alone` is changed to read the journal, so a pure function gains I/O. A default value on the new `rerun` parameter leaves a second path. The rerun rule is applied only to the candidate and not to an in-flight rerun ticket. Edits to existing tests beyond the added argument. A rerun ticket is serialized when parallel is disabled.

## Time budget
- expected: 20m
- stuck: 40m
