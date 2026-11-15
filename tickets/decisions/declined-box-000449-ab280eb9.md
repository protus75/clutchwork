---
id: declined-box-000449-ab280eb9
kind: declined
link: box-000449-ab280eb9
reopen_after_days: 30
---
During Check for provider-cli-install, the integration test test_host_loop_drives_supervised_fixture_serve in tests/integration/test_host_loop.py failed once and passed on rerun. The report carries no failure output, assertion, or traceback, and names no cause.

This is a single intermittent failure with no evidence of what went wrong. It does not show a current runtime behavior gap in engine code, and it has no measurable post-change observation to build a ticket around. The test passed on rerun, and the merged flake-detection and flake-check machinery already exists to classify and record intermittent tests. Record declined-box-000395-ea5ac8c5 noted that this test runs a FixtureLoop on the wall clock, real asyncio.sleep, and real timeouts, so it is likely timing-sensitive under load. Making the test deterministic would be a test-only change, which this triage declines unless it is tied to incorrect runtime behavior. The same shape of report was declined in declined-box-000359-1e0f1d0a. Reopen if this test fails again within the window and the report includes the failure output (assertion or traceback), or if flake detection quarantines it. Either would show a reproducible failure or a real-time timeout that is repeatedly costing ticket attempts at Check.

- Message class failure_report, stage check, outcome gate_failed, summary says failed then passed; no report body, no fixed_failure, no proposed paths.
- declined-box-000359-1e0f1d0a declined an identical-shape report (test_daemon_soak_runs_production_serve failed once then passed, no output or cause).
- declined-box-000395-ea5ac8c5 records that this test's failure-path FixtureLoop uses datetime.now(UTC), real asyncio.sleep and real timeouts (test_host_loop.py:112), a plausible timing-sensitivity source in test code only.
- Merged stems flake-detection, flake-check, flake-release and flake-edit-coverage already provide intermittent-failure handling.
- provider-cli-install is in the merged set, so the failure did not block the ticket from landing.

Message: box-000449-ab280eb9
