---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- conflict-discard-rerun-r1

## Context
- clutch/caps.py
- docs/parallel-tickets-plan.md

## Goal / Why
This is part 2 of 3 of roadmap row 47 (docs/roadmap.md, plan docs/parallel-tickets-plan.md section 5 step 3). After this ticket, `clutch/caps.py` counts conflict reruns separately from the `retry` cap and says when the rerun limit is spent. A conflict is not the ticket's fault, so a rerun draws no `retry`, and `CONFLICT_RERUN_LIMIT = 2` caps reruns. Part 3 (`conflict-rerun-swap`) calls this accounting when it replaces the Rework handoff, so the limit is enforced from the first rerun it emits.

A rerun is counted from the `SIGNAL` event with body `{"signal": "merge_conflict_rerun", "attempt": n}` that part 1 (`conflict-discard-rerun-r1`) defined. Part 3 emits it and adds the name to `SIGNAL_NAMES` with its emitter, so this ticket does not touch `clutch/journal.py`.

## Boundary contract
### Cap accounting
- disposition: extend
- owner: clutch/caps.py
- consumers: part 3 `conflict-rerun-swap` (the merge queue rerun path); existing cap callers are unchanged
- observable change: new constant `CONFLICT_RERUN_LIMIT = 2`; new `conflict_reruns(events, stem) -> int` counting `SIGNAL` events for the stem with body signal `merge_conflict_rerun` inside the same `lineage` window as `draws`; new `conflict_rerun_spent(events, stem) -> bool`, true when that count is at least `CONFLICT_RERUN_LIMIT`; new constant `CONFLICT_RERUN_ROAD` carrying the paved road text "split the ticket, or run it with parallel disabled". `CAPS`, `DECLARED_CAPS`, `draws`, `remaining`, `spent` and `failed_attempts` keep their current results: a rerun marker adds no `CAP_CONSUMED` event and no failed attempt.
- compatibility: preserves every existing cap result; with no rerun events all existing outputs are identical.
- acceptance: two rerun events spend the limit and leave `retry` remaining unchanged; an operator or supervisor `keep` resets the rerun count like other cap draws.
- tests: new tests/unit/test_caps_conflict_rerun.py
- post-merge source of truth: clutch/caps.py

## Scope in / Scope out
Scope in:
- Add the constant, the two functions and the road string to clutch/caps.py, reusing `lineage`.
- In docs/how-clutch-works.md, edit only the part of the caps description that states what counts against caps, adding that conflict reruns are counted separately with a limit of 2 and never draw `retry`.

Scope out:
- Emitting the `merge_conflict_rerun` event, adding it to `SIGNAL_NAMES`, parking a ticket, and any change to mergequeue.py, daemon.py, drain.py, runner.py, rework.py: all part 3, `conflict-rerun-swap`.
- Making the limit a config option; it is an engine constant.

## Scope fence
- clutch/caps.py
- tests/unit/test_caps_conflict_rerun.py
- docs/how-clutch-works.md

## Acceptance criteria
1. With two `merge_conflict_rerun` SIGNAL events for a stem, `conflict_rerun_spent` returns True; with one it returns False, not True; checked by `./dev.py test tests/unit/test_caps_conflict_rerun.py`.
2. After two rerun events, `remaining(caps, events, stem, "retry")` equals the value with no rerun events, and `spent(...)` returns None, not `"retry"`; checked by `./dev.py test tests/unit/test_caps_conflict_rerun.py`.
3. Rerun events for another stem are not counted: `conflict_reruns` returns 0 for a stem with none, not the other stem's count; checked by `./dev.py test tests/unit/test_caps_conflict_rerun.py`.
4. A `reject_verdict` keep event by the operator after two reruns makes `conflict_reruns` return 0, not 2; checked by `./dev.py test tests/unit/test_caps_conflict_rerun.py`.
5. `CONFLICT_RERUN_LIMIT` equals 2 and `CONFLICT_RERUN_ROAD` is non-empty; checked by `./dev.py test tests/unit/test_caps_conflict_rerun.py`.
6. The existing cap tests and the whole suite still pass; checked by `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_caps_conflict_rerun.py tests/integration/test_caps.py
```

## Definition of rejected
The branch emits the rerun event, edits clutch/journal.py, mergequeue.py or daemon.py, adds a config knob for the limit, or makes a rerun draw the `retry` cap.

## Time budget
- expected: 15m
- stuck: 30m
