---
id: tombstone-box-001036-f367e6f4
kind: tombstone
link: declined-box-000703-ccb1d10f
reopen_after_days: 14
---
During the training-export-ship-gate Implement run, which ended ok, the host-loop integration fixture abandoned a fixture ticket when it should have merged it. That caused setup errors in three host-loop tests on both the candidate and the base commit. The note names no test and gives no error text, traceback, failure rate or reproduction.

This repeats an issue already in the registry. Record 001026 tombstoned an almost identical report: three host-loop integration tests hit setup errors on the base commit, blamed on an abandoned escape. Record 001018 tombstoned shared setup errors in the same three host-loop tests. Both point to declined-box-000703, the host-loop fixture's intermittent misbehavior. This message adds no test name, error output, traceback or cause beyond those records. The run ended ok, so it shows no harm. Reopen once a report names the failing host-loop test, includes the setup error text or traceback, and shows the abandon path reproduces deterministically.

- message class suggestion, origin training-export-ship-gate, stage implement, outcome ok
- tombstone-box-001026-6e82fb44: three host-loop integration tests had setup errors on the base, blamed on an abandoned escape, linked to declined-box-000703-ccb1d10f
- tombstone-box-001018-5184bf51: shared setup errors in three host-loop integration tests, linked to declined-box-000703-ccb1d10f
- tombstone-box-001030-fc7045e8: the host-loop fixture dropped its escape scenario once
- the message gives no test name, error text, traceback or reproduction

Message: box-001036-f367e6f4
