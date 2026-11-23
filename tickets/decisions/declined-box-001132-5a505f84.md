---
id: declined-box-001132-5a505f84
kind: declined
link: box-001132-5a505f84
reopen_after_days: 30
---
During the retro-calibration-manual Implement run, which ended ok, the agent found that the ticket's unit Verification command named tests/unit/test_drain_driver_overlap.py and tests/unit/test_driver_hooks.py. Neither file exists on the base commit. Merged serve-no-roadmap had removed the driver, and both tests went with it.

No current harmful behavior remains. retro-calibration-manual is in the merged set and its run ended ok. Its committed ticket.md no longer names either file. No open ticket names them either: every ticket.md that still mentions them belongs to a merged or rejected stem. This was a one-off stale path in one ticket, and that ticket has settled. Nothing here gives one bounded repair with an observable effect. Reopen within 30 days if an open or confirmed ticket's Verification or criteria name a deleted test file and a run loses an attempt because of it. In that case the fix would be a lint rule that refuses Verification test paths missing at the base commit.

- Glob for tests/unit/test_drain_driver_overlap.py and tests/unit/test_driver_hooks.py on main finds no files
- tickets/retro-calibration-manual/ticket.md no longer mentions either file
- retro-calibration-manual is listed among the merged stems and the message reports stage implement, outcome ok
- Tickets naming these files (serve-no-roadmap, driver-loop, box-triage-via-inbox, estimate-calibration-idle, dispatch-during-driver-pass, etc.) are none of them in the open tickets list

Message: box-001132-5a505f84
