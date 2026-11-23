---
id: tombstone-box-000916-dce84ab8
kind: tombstone
link: serve-confirm-during-check
reopen_after_days: 14
---
In parallel serve, an operator confirm or reject waited for the running implementation to finish. On 2026-11-21 a confirm submitted at 07:09Z was applied only at about 07:15Z. The cause was that verdict settlement ran inside a poll that took admission.exclusive()/mutations(). That exclusive section waits for the run slots to empty, and while it waits _acquire_run refuses to admit a second run, so max_runs 2 behaved like 1 whenever a verdict was pending.

The merged ticket serve-confirm-during-check already makes the change this message asks for. It moves control.poll and settle_admissions out of the merge transaction into a separate Serve.verdicts worker that never takes admission.exclusive or mutations. It also removes verdict-only entries from merge_work, so an accepted confirm never holds an exclusive waiter. Current main matches: Serve.verdicts calls control.inbox.settle_admissions(self.apply_verdict) without any exclusive section, and runner.apply_admission writes only ticket-plane commits and journal events. The 2026-11-21 evidence comes from before that change landed. The triage part of the message is a different path: supervise() calls settle_triage only at idle points, which do not run while a run holds a slot, so it does not block admission the way the message describes. Reopen if, with the verdicts worker in place, a confirm or reject applied while a run is in flight is again delayed until a slot empties, or if a second ready ticket is again refused admission while a verdict is pending.

- clutch/serve.py Serve.verdicts (line 483) runs settle_admissions(self.apply_verdict) with no admission.exclusive()/mutations()
- tickets/serve-confirm-during-check/ticket.md: 'accepted verdicts settle in their own owned worker, independently of merge polling and run-slot quiescence'; 'never admission.exclusive or mutations'; 'Remove verdict-only entries from merge_work so an accepted confirmation never reserves an exclusive run waiter'
- clutch/daemon.py exclusive() (598-606) still increments _exclusive_waiters, which _acquire_run (589) checks, but verdict settlement no longer goes through it
- clutch/serve.py supervise(), which calls settle_triage, runs only when admission.busy() is false, so it never waits on a running implementation

Message: box-000916-dce84ab8
