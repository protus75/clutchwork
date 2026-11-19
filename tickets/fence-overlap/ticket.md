---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/stages.py::_in_fence
- clutch/tickets.py::Ticket
- clutch/tickets.py::GateBypass
- clutch/policy.py::_path_overlap
- docs/parallel-tickets-plan.md#Target design

## Goal / Why
Roadmap row 43, parallel plan ticket 4. After this ticket `clutch/tickets.py` is the one home of the scope-fence path rule: `_in_fence` moves there from `clutch/stages.py` (public name `in_fence`), and a new pure function `fences_overlap(a, b, shared)` answers whether two tickets' fences collide, using the same path rule (an entry matches a file when it is that path or a directory containing it). The run-alone rule is part of it: a ticket whose `gate_bypass` names `scope_fence` has a fence that no longer bounds its diff, so it overlaps others without the `shared` allowance. Nothing calls `fences_overlap` yet; `serve-parallel-dispatch` will. Landing the pure function and its tests first gives dispatch one tested owner to call and ends the second private copy of the fence grammar that the roadmap's duplicate audit found.

## Boundary contract
### Scope-fence path matching
- disposition: replace
- owner: clutch/tickets.py
- consumers: clutch/stages.py (scope_fence gate, host check triggers, lift file listing), clutch/mergequeue.py (strategy path matching), clutch/requisition.py (dependent and test fence checks)
- observable change: `in_fence(path, prefixes)` in `clutch/tickets.py` replaces private `stages._in_fence` with identical behavior; callers import it from `clutch.tickets`; `stages._in_fence` no longer exists
- compatibility: restoration of existing behavior: same inputs give same results (equal path or path under the prefix as a directory; a string prefix of a name never matches); every call site is updated in this change, no alias is left behind
- acceptance: `in_fence` returns the same results as the old function for exact, directory, trailing-slash and string-prefix cases
- tests: tests/unit/test_fence_overlap.py
- post-merge source of truth: clutch/tickets.py::in_fence

### Fence overlap
- disposition: create
- owner: clutch/tickets.py
- consumers: none in this ticket; `serve-parallel-dispatch` (parallel plan ticket 6) calls it at dispatch
- observable change: new pure `fences_overlap(a, b, shared)` and `runs_alone(ticket)`; no I/O, no clock, no behavior change anywhere else
- compatibility: additive; nothing existing calls it
- acceptance: overlap is true for equal entries and for a directory containing the other entry, false for disjoint entries and for string-prefix names; the ticket's own outbox is ignored; overlap confined to `shared` paths is allowed unless either ticket runs alone
- tests: tests/unit/test_fence_overlap.py
- post-merge source of truth: clutch/tickets.py::fences_overlap
- closest existing: `policy._path_overlap` (string-pair overlap, no outbox, shared or run-alone rules, and private to policy.py) and `stages._in_fence` (path-in-prefixes, not entry-vs-entry)
- earning reason: the dispatch consumer needs entry-vs-entry overlap on tickets with outbox exclusion, shared paths and run-alone, which neither existing helper provides; the new function reuses `in_fence` for matching rather than adding a third path rule

## Scope in / Scope out
Scope in:
- Move `_in_fence` from `clutch/stages.py` to `clutch/tickets.py` as `in_fence`, body unchanged. Update its callers: `clutch/stages.py` (imports it from `clutch.tickets`; all former `_in_fence` uses), `clutch/mergequeue.py` (the `stages._in_fence` uses), `clutch/requisition.py` (the import and uses). Remove the old definition.
- Add to `clutch/tickets.py`: `runs_alone(ticket) -> bool` (true when `ticket.frontmatter.gate_bypass` has an entry with code `scope_fence`) and `fences_overlap(a, b, shared) -> bool` over two `Ticket` values and a sequence of shared path prefixes.
- `fences_overlap` rules: drop from each ticket's fence the entries equal to or under its own outbox `tickets/<stem>/`. Two entries overlap when equal or one is a directory containing the other. An entry that is `tickets` or under `tickets/` after that removal overlaps every other ticket (it reaches the whole ticket plane). An overlap whose deeper path lies in `shared` (by `in_fence`) is ignored, except that `shared` is ignored entirely when either ticket `runs_alone`. A ticket never overlaps itself by stem; comparing two tickets with the same stem is a caller error and not handled.
- New tests in new file `tests/unit/test_fence_overlap.py`, using in-memory `Ticket` values only.

Scope out:
- No dispatch change, no config read, no `merge.strategies` exemption, no chain ordering, no conflict-rerun run-alone marker (those are later parallel-plan tickets).
- The duplicate fence matchers at `clutch/watchdog.py` and `clutch/drain.py` have different semantics and stay as they are; `clutch/policy.py::_path_overlap` stays.
- No documentation change: no document describes `_in_fence` or `fences_overlap`.

## Scope fence
- clutch/tickets.py
- clutch/stages.py
- clutch/mergequeue.py
- clutch/requisition.py
- tests/unit/test_fence_overlap.py

## Acceptance criteria
1. `in_fence("a/b.py", ["a"])` is true, `in_fence("ab.py", ["a"])` is false (a string prefix never matches), `in_fence("a", ["a/"])` is false and `in_fence("a/x", ["a/"])` is true, checked by `./dev.py test tests/unit/test_fence_overlap.py`.
2. `clutch.stages` has no attribute `_in_fence` (`hasattr(clutch.stages, "_in_fence")` is false, not true), checked by `./dev.py test tests/unit/test_fence_overlap.py`.
3. `fences_overlap` is true for fences `["clutch"]` and `["clutch/tickets.py"]`, true for equal entries, and false for `["clutch/tickets.py"]` and `["clutch/tickets_x.py"]`, not true by string prefix, checked by `./dev.py test tests/unit/test_fence_overlap.py`.
4. Two tickets that both fence only their own `tickets/<stem>/ticket.md` do not overlap, while a ticket fencing `tickets` overlaps a ticket fencing `clutch/x.py`, not false, checked by `./dev.py test tests/unit/test_fence_overlap.py`.
5. Fences sharing only `docs/how-clutch-works.md` overlap with `shared=[]` and do not overlap with `shared=["docs/how-clutch-works.md"]`; with a `scope_fence` `gate_bypass` on either ticket they overlap even with that shared list, checked by `./dev.py test tests/unit/test_fence_overlap.py`.
6. `runs_alone` is true for a ticket with a `scope_fence` bypass and false for one with none or with a different gate code, checked by `./dev.py test tests/unit/test_fence_overlap.py`.
7. The existing scope_fence gate, merge strategy and requisition behavior is unchanged: `./dev.py test tests/integration/test_mergequeue.py tests/unit/test_requisition_dependents.py tests/integration/test_requisition.py tests/integration/test_stages.py` passes.

## Verification
```
./dev.py test tests/unit/test_fence_overlap.py tests/integration/test_mergequeue.py tests/unit/test_requisition_dependents.py tests/integration/test_requisition.py tests/integration/test_stages.py
```

## Definition of rejected
A branch that leaves `_in_fence` in `clutch/stages.py` (alias, re-export or copy), changes the matching semantics of the moved function, edits `clutch/watchdog.py`, `clutch/drain.py` or `clutch/policy.py`, wires `fences_overlap` into dispatch, or adds tests to an existing hot test file.

## Time budget
- expected: 20m
- stuck: 40m
