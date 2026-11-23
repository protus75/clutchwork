---
state: draft
source: box:suggestion
priority: P0
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/serve.py::Serve.__init__
- clutch/stages.py::gather_safety_evidence
- tests/unit/test_serve_scan_head.py

## Goal / Why
Serve's dispatch callback (`prepared` -> `dispatch` in `clutch/serve.py`) resolves `main:tickets/<stem>/ticket.md` to a sha, journals it with `runner.mark_running`, and then runs the in-memory `Ticket` it was handed. It re-parses from the committed blob only when `published[0] is ticket` and the sha differs. A Ticket parsed before an edit to main, but not the object last published, runs under a journaled sha it does not match. Observed: `shared-git-fake-unit-5` attempt 1 ran with ticket_sha 9533446d, whose fence includes `tests/unit/test_serve_scan_head.py` and `tests/unit/test_supervise_idle_hooks.py` after an operator edit. Its scope_fence check failed exactly those two paths, because `gather_safety_evidence` (`clutch/stages.py`) takes `scope_fence=list(ticket.scope_fence)` from the stale object. That burned one attempt. The box message guessed the cause was the retry branch's ticket.md; the code read shows the stale in-memory Ticket instead. The implementer first reproduces the stale-object case in a test, which confirms or refutes this cause, and only then changes code.

After this ticket, the Ticket handed to the callback was parsed from the same blob whose sha is journaled.

## Boundary contract
### Serve dispatch ticket identity
- disposition: extend
- owner: clutch/serve.py
- consumers: Implement and Check stages, which read `ticket.scope_fence` and the other ticket fields through the dispatched Ticket
- observable change: dispatch hands the callback a Ticket parsed from the blob at the journaled sha; if that blob differs from the offered Ticket, the fresh parse is used
- compatibility: restores the invariant that the journaled ticket sha and the judged ticket content agree; when the offered Ticket already matches the blob, behavior is unchanged, and the existing republish path for a changed sha on the published Ticket stays
- acceptance: a fence widened on main between scheduling and dispatch is the fence Check judges
- tests: new unit test with fakes that widens the fence between scheduling and dispatch
- post-merge source of truth: clutch/serve.py

## Scope in / Scope out
Scope in: in the `dispatch` closure in `clutch/serve.py`, make the Ticket passed to `callback(ticket)` equal to the parse of the committed blob already read (`committed`) whenever the offered Ticket's content differs from it, without requiring `published[0] is ticket`. An unparseable blob (`TicketInvalid`) keeps the existing `return "running"` behavior. Add a new unit test file `tests/unit/test_serve_dispatch_fresh_ticket.py` that first demonstrates the stale case against the unfixed code.
Scope out: `clutch/stages.py`, retry-branch handling (`retry-keeps-prior-branch`), mid-run edits (`ticket-changed-midrun`), and the drain path. A drain-path equivalent, if any, goes to the Suggestion Box.

## Scope fence
- clutch/serve.py
- tests/unit/test_serve_dispatch_fresh_ticket.py

## Acceptance criteria
1. With a Ticket parsed before main's ticket.md widened its fence, and no published entry identical to it, dispatch passes the callback a Ticket whose `scope_fence` includes the widened paths, not the old fence; checked by `./dev.py test tests/unit/test_serve_dispatch_fresh_ticket.py`.
2. When main's blob is unchanged, the callback receives a Ticket equal to the offered one; checked by `./dev.py test tests/unit/test_serve_dispatch_fresh_ticket.py`.
3. When main's blob does not parse, dispatch returns `"running"` and never calls the callback; checked by `./dev.py test tests/unit/test_serve_dispatch_fresh_ticket.py`.
4. Existing serve dispatch and scan tests still pass: `./dev.py test tests/unit/test_serve_scan_head.py tests/unit/test_serve_dispatch_containment.py`.

## Verification
```
./dev.py test tests/unit/test_serve_dispatch_fresh_ticket.py tests/unit/test_serve_scan_head.py tests/unit/test_serve_dispatch_containment.py
```

## Definition of rejected
The branch changes how Check reads the fence in `clutch/stages.py` instead of fixing the dispatched Ticket, or the new test passes on the unfixed code, or any other serve behavior changes.

## Time budget
- expected: 20m
- stuck: 40m
