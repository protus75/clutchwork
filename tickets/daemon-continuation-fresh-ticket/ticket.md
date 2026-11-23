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
- clutch/scheduler.py::Scheduler.dispatch_next
- clutch/serve.py::Serve.resume
- clutch/runner.py::drive
- clutch/stages.py::StagesRun

## Goal / Why
`shared-git-fake-unit-5` attempts 1 and 2 judged a fence older than the edited ticket. A held `Continuation` carries its original ticket and run. In `Scheduler.dispatch_next`, retained entries overwrite pending entries for the same stem, and `AdmissionBoundary.dispatch` chooses the continuation's writer before the ordinary Serve dispatch closure. The writer then substitutes `prior.ticket`. A comparison made only inside the writer can therefore see the stale ticket on both sides.

Keep continuations bound to the committed blob that produced them. After an operator edit and keep, the scheduler must offer the fresh committed ticket through normal admission. Preserve the current mid-run ticket-change path for a still-running attempt and preserve valid unchanged continuations. The separate `serve-dispatch-fresh-ticket` ticket owns the ordinary Serve dispatch closure.

## Boundary contract
### Continuation admission
- disposition: extend
- owner: clutch/daemon.py, with candidate selection in clutch/scheduler.py and resume wiring in clutch/serve.py
- consumers: the Serve scheduler, admission boundary, stages and run journal
- observable change: a retained continuation resumes with its prior run only for its original committed ticket blob. An edited, kept ticket is scheduled and driven normally after the old attempt is terminal
- compatibility: preserve paused or interrupted live-run handling and the mid-run edit finding. Preserve existing custody and resume for an unchanged blob, including when the run normalized its tier or effort
- acceptance: a scheduler-to-writer regression drives a held continuation, an edit and keep, then an offer with the enlarged fence
- tests: tests/unit/test_daemon_ticket_writer_continuation.py
- post-merge source of truth: the committed ticket blob and the producing run's `ticket_sha`

## Scope in / Scope out
Scope in:
- In `clutch/scheduler.py`, make retained eligibility and pending precedence respect the committed ticket identity and the current journal state. An obsolete terminal continuation must not displace a fresh kept ticket in the candidates or make selection check the old stage or old fence.
- In the resume wiring in `clutch/serve.py` and `clutch/daemon.py`, use the producing run's committed blob ID and the actual offered committed blob identity through the existing publication and stage seams. Whole `Ticket` equality is insufficient because `runner.drive` can normalize its capability fields. Release obsolete continuation custody before fresh admission. Preserve the existing `ticket_changed` reporting path when the older run is still live.
- Add a fake-driven unit test that exercises selection, resume choice and the writer. Use real stages only as needed to verify the stage sees the fresh fence. Run the current Serve scheduler and dispatch tests.

Scope out: the ordinary Serve dispatch blob reads, handled by `serve-dispatch-fresh-ticket`, and new states, flags or retry policy.

## Scope fence
- clutch/daemon.py
- clutch/scheduler.py
- clutch/serve.py
- tests/unit/test_daemon_ticket_writer_continuation.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_daemon_ticket_writer_continuation.py` goes through the normal scheduler, admission and writer interfaces. A changed and explicitly kept ticket with an obsolete terminal continuation is selected with the fresh fence, and starts a fresh run with the fresh committed identity. A writer-only fake supplied the fresh object by hand cannot satisfy this criterion.
2. An unchanged committed blob resumes the original run and stage, even if capability normalization changed the in-memory Ticket fields. A still-live old attempt keeps the existing `ticket_changed` behavior rather than sharing results with the new revision.
3. `./dev.py test tests/unit/test_serve_dispatch_containment.py tests/unit/test_serve_scheduler_lifecycle.py tests/unit/test_conflict_rerun_swap.py` remains green.

## Verification
```
./dev.py test tests/unit/test_daemon_ticket_writer_continuation.py tests/unit/test_serve_dispatch_containment.py tests/unit/test_serve_scheduler_lifecycle.py tests/unit/test_conflict_rerun_swap.py
```

## Definition of rejected
A branch where a retained ticket can override a newer kept revision, stage outputs cross ticket identities, an active old attempt is silently dropped, or unchanged continuations lose their resume behavior.

## Time budget
- expected: 25m
- stuck: 50m
