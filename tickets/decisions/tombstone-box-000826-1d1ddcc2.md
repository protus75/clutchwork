---
id: tombstone-box-000826-1d1ddcc2
kind: tombstone
link: declined-box-000703-ccb1d10f
reopen_after_days: 30
---
The projection-leftovers Implement run, which ended ok, reported again that the host-loop integration fixture sometimes writes journal timestamps out of order. It names no failing test and gives no assertion, traceback, example timestamps or suspected cause.

This is the same report that record declined-box-000703-ccb1d10f already decided: the host-loop fixture sometimes writes journal timestamps out of order, with no failing test, output or cause given. Records 000805, 000807 and 000809 already tombstoned repeats of it from other runs. This message is another repeat, from projection-leftovers, and adds no new evidence. Its run ended ok. Reopen if a report names the failing test and includes the assertion or traceback and example out-of-order timestamps.

- message class suggestion, origin projection-leftovers, stage implement, outcome ok, no report, no proposed paths
- declined-box-000703-ccb1d10f: same host-loop fixture timestamp-ordering note, declined for lack of a failing test, traceback, timestamps or cause
- tombstone-box-000805-a4e4c3d2, tombstone-box-000807-cccb1683, tombstone-box-000809-f68239e7 all link to declined-box-000703-ccb1d10f for the same symptom

Message: box-000826-1d1ddcc2
