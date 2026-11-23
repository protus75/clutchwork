---
id: tombstone-box-001018-5184bf51
kind: tombstone
link: declined-box-000703-ccb1d10f
reopen_after_days: 30
---
During the serve-merge-off-exclusive Implement run, which ended ok, three host-loop integration tests hit shared setup errors in one full integration suite run. They passed when run alone and in the next full run. The report names no test, error text, traceback or cause.

This repeats the intermittent host-loop fixture report that record 000703 declined. Records 000805, 000807, 000809 and 000826 tombstoned later copies of it, and 001014 is related. All of them describe host-loop integration tests that failed once in a full-suite run and then passed alone and on the next full run, with no traceback, assertion or cause. This message adds no new evidence and shows no harm to the run. Reopen if a report includes the setup error text or traceback, or shows a host-loop failure that cost a run a cycle.

- message: three host-loop tests had shared setup errors in one full integration run and passed alone and in the next full run; stage implement, outcome ok
- declined-box-000703-ccb1d10f: intermittent host-loop fixture failure that passed alone and in the final full run, with no traceback
- tombstone-box-000805-a4e4c3d2: three host-loop integration tests failed once in a full-suite run and then passed, tombstoned to 000703
- tombstone-box-001014-42751784: host-loop fixture failures under suite load that passed when run alone

Message: box-001018-5184bf51
