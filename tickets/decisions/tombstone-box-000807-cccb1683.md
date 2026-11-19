---
id: tombstone-box-000807-cccb1683
kind: tombstone
link: declined-box-000703-ccb1d10f
reopen_after_days: 14
---
The conflict-rerun-accounting run says the host-loop integration fixture sometimes records journal timestamps out of order. It proposes either fixing how timestamps are ordered or making the fixture deterministic. The report names no failing test and includes no assertion, traceback, example timestamps or cause, and the run itself ended ok.

This is the same intermittent fault already in the registry. Record declined-box-000703-ccb1d10f declined it from the plan-drain-author-in-parallel run, and tombstone-box-000805-a4e4c3d2 linked the snapshot-merged-history-cap sighting to that record. This report adds no new evidence. Reopen it if a report names the failing host-loop test and includes the assertion output or the out-of-order timestamps. A third sighting with that evidence should go to a ticket that fixes the root cause.

- message origin conflict-rerun-accounting, stage implement, outcome ok; no test name, traceback or timestamps
- declined-box-000703-ccb1d10f: host-loop fixture intermittently writes out-of-order journal timestamps, declined for lack of evidence
- tombstone-box-000805-a4e4c3d2: same symptom on snapshot-merged-history-cap, linked to declined-box-000703-ccb1d10f

Message: box-000807-cccb1683
