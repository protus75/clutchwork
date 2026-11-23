---
id: tombstone-box-000985-584adc0d
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 30
---
The serve-scan-watch-off-exclusive Implement run, which ended ok, saw the integration test test_serve_admission_refusal_keeps_main_green[host-red] time out once during a full integration gate run. The test passed on the base commit, when run alone on the candidate, and in the next candidate verification. The report gives no timeout output, traceback or suspected cause.

This is the same one-time intermittent timeout that record declined-box-000983-96a0ff93 already settled. Both come from the same serve-scan-watch-off-exclusive Implement run, and in both the test passed alone and in the later verification while the run ended ok. This message adds no assertion, traceback, timing data or cause, so there is still no reproducible runtime failure to repair. Reopen if this test fails again with captured timeout output or a traceback, or if it fails repeatedly across separate runs.

- message origin serve-scan-watch-off-exclusive, stage implement, outcome ok
- the test passed on the base commit, alone on the candidate, and in the later candidate verification
- declined-box-000983-96a0ff93 records an intermittent precheck admission integration test timeout from the same serve-scan-watch-off-exclusive run, which passed alone and in later verification
- the report includes no traceback, timeout output or suspected cause

Message: box-000985-584adc0d
