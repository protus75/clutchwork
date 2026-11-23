---
id: tombstone-box-001065-fc96f8c2
kind: tombstone
link: declined-box-000598-4be912da
reopen_after_days: 14
---
During Check for implement-skips-full-suites, the whole parallel integration suite run also failed on merge base 52b3101c, so the outcome was recorded as base_red and the report asks for main to be fixed instead of the ticket. It names no failing test and includes no assertion, traceback or output. implement-skips-full-suites has since merged.

This is the same base_red report that registry record 000598 declined: the whole integration suite fails on the merge base, and no failing test or output is given. Records 000602, 001013 and 001033 handled the same report from other runs in the same way. The known intermittent integration failures on the base are already covered. Record 000983 holds the serve-admission timeouts, record 000703 holds the host-loop fixture failures, and the open or merged tickets serve-flaky-tests-deterministic and serve-live-keep-single-verdict address them. implement-skips-full-suites is in the merged set, so this ticket is no longer blocked. Reopen if a base_red report names a failing integration test that no ticket or registry record covers and includes its assertion or traceback.

- message: class failure_report, stage check, outcome base_red, origin implement-skips-full-suites, merge base 52b3101c, no failing test named, no output
- registry declined-box-000598-4be912da: same whole-integration-suite base_red report with no failing test named
- registry declined-box-000602-8ec884ea, declined-box-001013-d4549bb5 and tombstone-box-001033-88380fca: repeats of the same report handled the same way
- registry declined-box-000983-96a0ff93 and declined-box-000703-ccb1d10f: hold the known intermittent serve-admission and host-loop integration failures
- merged: implement-skips-full-suites, serve-flaky-tests-deterministic, serve-live-keep-single-verdict

Message: box-001065-fc96f8c2
