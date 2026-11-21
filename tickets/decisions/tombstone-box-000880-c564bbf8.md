---
id: tombstone-box-000880-c564bbf8
kind: tombstone
link: serve-polls-block-parallel-runs
reopen_after_days: 14
---
With scheduler.parallel enabled and max_runs 2, serve never ran two implementations at once. On 2026-11-21, index-config-touches waited while meta-fill-surface implemented alone, no dispatch_skip events were logged, and a confirm submitted mid-run was not applied until the run ended. The note's hypothesis is that serve's scan, merge and box-intake polls enter admission.mutations() -> exclusive() every 0.1 s. Each waiting poll then counts as an exclusive waiter, and _acquire_run refuses a second run while one exists.

This is the same defect, with the same cause and evidence, as merged ticket serve-polls-block-parallel-runs. That ticket's Goal cites the same 2026-11-21 incident: index-config-touches queued behind meta-fill-surface, 0 dispatch_skip events, and a confirm held until the run ended. Its Cause names the same mechanism: the poll loops enter mutations()/exclusive() every SERVE_POLL_S, the waiter counter blocks _acquire_run, and dispatch holds its slot for the whole run. Its fix lets an idle poll skip the exclusive section, so a second run can be admitted. Reopen if serve still never runs two non-overlapping confirmed tickets at once with max_runs 2 after that merge, for example if the engine log after the merge shows no overlapping implement stage_start pairs.

- tickets/serve-polls-block-parallel-runs/ticket.md Goal: same 2026-11-21 incident (index-config-touches queued while meta-fill-surface implemented alone, 0 dispatch_skip, confirm not applied until the run ended)
- tickets/serve-polls-block-parallel-runs/ticket.md Cause: exclusive() waiter blocks _acquire_run while the scan, merge and box_intake polls run mutations() every 0.1 s
- serve-polls-block-parallel-runs is in the merged stems list
- clutch/daemon.py:587 _acquire_run waits on `not self._exclusive_waiters`; clutch/daemon.py:596-604 exclusive() raises _exclusive_waiters while it waits for _holding == 0

Message: box-000880-c564bbf8
