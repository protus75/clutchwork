---
state: confirmed
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
- clutch/scheduler.py::Scheduler.dispatch_next
- tests/unit/test_serve_dispatch_containment.py

## Goal / Why
A ticket selected before an edit can reach Serve's ordinary dispatch carrying an earlier edit fence. `shared-git-fake-unit-5` was checked with a stale fence despite the wider committed revision. The ordinary dispatch has a separate gap from continuation replacement: it only notices a changed blob if the offered object is the last published object, and it reads mutable `main:tickets/<stem>/ticket.md` twice. Reproduce the ordinary dispatch race independently of the continuation incident.

Bind selection, callback content and the journaled blob to one revision. If the committed ticket no longer matches the selected ticket, re-offer it through selection before any stage runs. This allows the scheduler to apply parallel conflict checks to the new fence.

## Boundary contract
### Ordinary Serve dispatch ticket identity
- disposition: extend
- owner: clutch/serve.py
- consumers: Serve's scheduler and callback, the run journal, Implement and Check
- observable change: dispatch reads by exact blob ID and re-offers altered ticket content through scheduling before starting a run
- compatibility: unchanged selected tickets continue through the existing dispatch, and an invalid revision is never run
- acceptance: a widened edit fence cannot run alongside another ticket now overlapping it, and the eventual running event identifies the blob passed to the callback
- tests: tests/unit/test_serve_dispatch_fresh_ticket.py and existing dispatch tests
- post-merge source of truth: the exact committed ticket blob used for publication, selection and journal identity

## Scope in / Scope out
Scope in:
- In the prepared dispatch closure in `clutch/serve.py`, resolve the current main ticket blob ID once and read that exact object by ID. The selected revision must match the committed parse and published identity before journal and callback. When it differs, publish the valid revision back through the scheduler and return without starting work. Revalidate through the ordinary selection path, including overlaps. Keep unparseable content out of the callback.
- Add the new fake-driven test and update the existing dispatch fixture in `tests/unit/test_serve_dispatch_containment.py` only where the exact blob read or valid parsed tickets force it. Confirm the basic race with a test that fails on main.

Scope out: continuation ownership, covered by `daemon-continuation-fresh-ticket`; branch retry policy and edits after a run starts.

## Scope fence
- clutch/serve.py
- tests/unit/test_serve_dispatch_fresh_ticket.py
- tests/unit/test_serve_dispatch_containment.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_serve_dispatch_fresh_ticket.py` simulates a widened fence between selection and dispatch, including an offered object other than the most recent publication. The first dispatch republishes and records no running event. The scheduler conflicts with the newly overlapping live run until its slot clears.
2. `./dev.py test tests/unit/test_serve_dispatch_fresh_ticket.py` moves main between ID resolution and content read. The read uses the resolved ID. When a selected revision runs, the callback's parsed ticket and the running event identify the same blob. A second lookup against mutable main fails this criterion.
3. The same test shows an unchanged revision runs and an invalid one never reaches the callback. Existing scan and exception containment behavior passes `./dev.py test tests/unit/test_serve_scan_head.py tests/unit/test_serve_dispatch_containment.py`.

## Verification
```
./dev.py test tests/unit/test_serve_dispatch_fresh_ticket.py tests/unit/test_serve_scan_head.py tests/unit/test_serve_dispatch_containment.py
```

## Definition of rejected
A branch that invokes the callback on changed content using the old selection, reads a different blob than the one journaled, depends on the selected object still being the most recent publication, or changes Check's fence handling.

## Time budget
- expected: 20m
- stuck: 40m
