---
id: tombstone-box-000809-f68239e7
kind: tombstone
link: declined-box-000703-ccb1d10f
reopen_after_days: 30
---
The graphics-kind Implement run reported that the host-loop integration fixture sometimes writes journal timestamps out of order, and suggested deterministic ordering or clock control to stop it recurring. The run ended ok. The report names no failing test and gives no assertion, traceback, example timestamps or suspected cause.

This repeats registry record declined-box-000703-ccb1d10f, which declined the same intermittent journal-timestamp ordering report against the host-loop fixture. Records tombstone-box-000805-a4e4c3d2 and tombstone-box-000807-cccb1683 already tombstoned two later reports of the same thing. This report also has no failing test, no output and no cause, and its run ended ok. Reopen if a report names the failing test and shows the assertion and the non-monotonic timestamps, or if the flake costs a run a gate_failed or base_red outcome.

- message class suggestion, stage implement, outcome ok, origin graphics-kind
- declined-box-000703-ccb1d10f: same host-loop fixture non-monotonic journal timestamp report, declined for lack of evidence
- tombstone-box-000805-a4e4c3d2 and tombstone-box-000807-cccb1683 already tombstoned later reports of the same thing to 000703
- the message names no test, assertion, traceback, timestamps or cause

Message: box-000809-f68239e7
