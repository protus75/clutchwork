---
id: declined-box-000844-eb22bb29
kind: declined
link: box-000844-eb22bb29
reopen_after_days: 30
---
In parallel serve, `Scheduler.dispatch_next` keeps a run in `self.flying` until its whole dispatch task ends, including the time the run waits for merge. It compares `len(flying)` with `parallel.max_runs`. `DaemonAdmission.waiting_for_merge` separately gives up that run's admission hold while it waits. The note reads plan section 4 as saying the scheduler slot should also be refilled during the merge wait. As it stands, a run waiting to merge stops another ticket from being dispatched.

The code is as the note describes: `clutch/scheduler.py:84` returns early when `len(self.flying) >= parallel.max_runs`, and an entry leaves `flying` only in the task's done callback. But nothing shows this is a harmful gap. (1) The `DaemonAdmission.waiting_for_merge` docstring says it 'keep[s] ownership while lending this run's slot to the merge consumer'. The admission hold is given up so the merge and exclusive mutation path can go ahead (`exclusive()` waits for `_holding == 0`), not so another ticket can be dispatched. Plan section 4 says 'releases that run's slot only' about DaemonAdmission, so the note's reading that the scheduler should refill the slot is an interpretation, not a stated contract. (2) The plan already limits finished work waiting to merge with a separate knob, `scheduler.max_unmerged`, so keeping merge-waiting runs out of dispatch fits the design. (3) The note was filed while authoring another ticket. It cites no serve run, journal events or timing showing an idle slot that cost throughput, and nothing that came out wrong. Without that evidence this is a plan-wording mismatch. Reopen if a parallel serve run shows that a run waiting for merge kept a ready, non-overlapping ticket from being dispatched for a measurable time (from `queue.json` or engine-log `dispatch_skip` and merge timestamps), or if the plan is amended to say a merge-waiting run frees its scheduler slot.

- clutch/scheduler.py:84 cap `parallel.enabled and len(self.flying) >= parallel.max_runs`; flying entry removed only in task done callback (scheduler.py:145-147)
- clutch/daemon.py:658-664 `waiting_for_merge` docstring: 'Keep ownership while lending this run's slot to the merge consumer'; exclusive() waits on `_holding == 0` (daemon.py:602)
- docs/parallel-tickets-plan.md:84 'waiting_for_merge releases that run's slot only' is stated for DaemonAdmission, not for the scheduler's flying set
- docs/parallel-tickets-plan.md:27 `scheduler.max_unmerged` already limits dispatch while finished tickets wait to merge
- Message origin is a session note made while authoring; it cites no incident, run, or measurement

Message: box-000844-eb22bb29
