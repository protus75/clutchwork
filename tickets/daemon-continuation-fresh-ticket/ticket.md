---
state: confirmed
source: box:suggestion
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- none

## Runs before
- `serve-dispatch-fresh-ticket`

## Context
- clutch/daemon.py::TicketWriter
- clutch/daemon.py::Continuation
- clutch/tickets.py::Ticket

## Goal / Why
When a stem has a held continuation and the operator edits and confirms the ticket (for example a new `## Scope fence` path), the resumed stages must run against the edited ticket. Today `TicketWriter.__call__` in `clutch/daemon.py` looks up `self.continuations.get(ticket.stem)` and, if one exists, replaces the offered Ticket with `prior.ticket`. The replacement stays until a later `drive` returns with no `next_stage`. Check's `scope_fence` then keeps judging the pre-edit fence. This cost `shared-git-fake-unit-5` attempts 1 and 2 (box-001095). This is the in-callback sibling of open ticket `serve-dispatch-fresh-ticket`, which fixes only the `dispatch` closure in `clutch/serve.py`. Without this fix, the fresh Ticket that ticket produces is thrown away whenever a continuation exists. Both are needed and neither re-solves the other.

After this ticket, a continuation is resumed only when the offered Ticket equals the continuation's Ticket. When they differ, the continuation is dropped and the offered Ticket is driven from the start.

## Boundary contract
### TicketWriter continuation resume
- disposition: extend
- owner: clutch/daemon.py
- consumers: serve dispatch and the drain path that call `TicketWriter`; `runner.drive`
- observable change: an offered Ticket that differs from the held continuation's Ticket discards that continuation, and the offered Ticket is driven fresh. An equal Ticket resumes exactly as before.
- compatibility: the resume path for an unchanged ticket is preserved. No new parameter, field or knob. The `Continuation` fields do not change.
- acceptance: a unit test with fakes holds a continuation, offers a Ticket whose `scope_fence` has an extra path, and asserts that the stages receive the new fence and that the old continuation is gone.
- tests: `tests/unit/test_daemon_ticket_writer_continuation.py`
- post-merge source of truth: clutch/daemon.py

## Scope in / Scope out
Scope in: in `TicketWriter.__call__`, take the `prior.ticket` and `prior.run` branch only when `prior.ticket == ticket`. Otherwise `self.continuations.pop(ticket.stem)` and drive the offered Ticket with no prior run. Add one new unit test file using fakes, with no disk, process or network use. Rejected simpler approach: always ignoring the continuation would lose resume for unchanged tickets. Comparing for equality is the smallest change that keeps resume and honors edits.

Scope out: `clutch/serve.py` (covered by `serve-dispatch-fresh-ticket`), the `Continuation` dataclass, docs, and the shared hot test files.

## Scope fence
- clutch/daemon.py
- tests/unit/test_daemon_ticket_writer_continuation.py

## Acceptance criteria
1. With a held continuation whose Ticket differs from the offered Ticket in `scope_fence`, `./dev.py test tests/unit/test_daemon_ticket_writer_continuation.py` asserts that the stages receive the offered Ticket's fence, not `prior.ticket`'s fence.
2. The same test file asserts that after that call `TicketWriter.continuations` holds no entry for the stem carrying the old Ticket, and that the boundary's `run` is not the old continuation's run.
3. The same test file asserts that an offered Ticket equal to the continuation's Ticket still resumes with `prior.run`, so resume is not regressed (a driver that always starts fresh fails this).
4. `./dev.py test tests/unit/test_serve_dispatch_containment.py tests/unit/test_serve_scheduler_lifecycle.py tests/unit/test_conflict_rerun_swap.py` passes unchanged.

## Verification
```
./dev.py test tests/unit/test_daemon_ticket_writer_continuation.py tests/unit/test_serve_dispatch_containment.py tests/unit/test_serve_scheduler_lifecycle.py tests/unit/test_conflict_rerun_swap.py
```

## Definition of rejected
The branch is rejected if the continuation still replaces a differing offered Ticket, if resume of an unchanged Ticket is lost, or if it edits `clutch/serve.py` or any file outside the fence.

## Time budget
- expected: 15m
- stuck: 30m
