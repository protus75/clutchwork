---
id: declined-box-000845-1ad5602c
kind: declined
link: box-000845-1ad5602c
reopen_after_days: 30
---
With parallel serve, `Serve.dispatch` in `clutch/serve.py` runs idle-point work (inbox triage settle and `supervise_idle`) only when `admission.busy()` is false. Meanwhile `scheduler.dispatch_next` keeps refilling slots whenever no exclusive work is pending. The note warns that if a slot is refilled every time one frees, idle supervision and calibration could be put off until something drains the slots (retro, upgrade or stop). It suggests an explicit idle point or pausing refill when either is due.

This is a possible starvation risk, not an observed failure. The message says supervision and calibration 'can starve' and only suggests a fix ('consider'). It cites no run, journal event or Reject-queue stem left unsupervised, and no calibration that was overdue in practice. Running this work only at idle points is the design that merged in supervise-at-idle-point. A stem waiting in the Reject queue is still released when the slots drain or by the supervising loop through `clutch prompt diagnose`, so this does not show reachable incorrect behavior. Reopen if a journal or engine log from a parallel serve shows a Reject-queue arrival left unsupervised, or calibration overdue, for a long stretch while slots kept refilling, for example several merges in a row with no `supervise_idle` pass.

- clutch/serve.py:389-424: `supervise()` (inbox `settle_triage` + `supervise_idle`) runs inside `if not busy`. `dispatch_next` runs when `not busy or not exclusive_pending`, so a busy admission with no exclusive work pending refills slots and skips supervision.
- clutch/serve.py:590: another path gated on `not admission.busy() and not scheduler.occupied()`.
- The message's origin is a session. It contains no stage, outcome, run reference or journal evidence of an actual delay.
- Merged supervise-at-idle-point established idle-point supervision by design. Merged serve-dispatch-returns-on-slot and serve-parallel-fill-slots introduced the continuous refill described.

Message: box-000845-1ad5602c
