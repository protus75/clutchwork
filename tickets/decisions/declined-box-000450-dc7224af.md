---
id: declined-box-000450-dc7224af
kind: declined
link: box-000450-dc7224af
reopen_after_days: 14
---
During the Check stage of provider-cli-install, the integration test tests/integration/test_host_loop.py::test_host_loop_report_regression_and_escape failed once and passed when rerun. The report has no assertion, traceback, or captured output, and it names no cause.

One fail-then-pass in Check is not enough to show a current behavior gap that a single bounded ticket could fix. The report has no failure output, no assertion, and no suspected mechanism, so a ticket could not state a measurable result to check after the change. Its subject is a different test from the one in record declined-box-000449-ab280eb9, so this is not a semantic duplicate. That record is a fail-then-pass of test_host_loop_drives_supervised_fixture_serve in the same file during the same provider-cli-install Check, and it was declined for the same lack of evidence. Reopen if this test fails again with captured output (assertion or traceback) or a named nondeterminism source such as a wall clock, real sleep, or ordering race. Also reopen if flake detection finds repeated intermittent failures across tests in tests/integration/test_host_loop.py, because that would support one root-cause ticket for the file's shared FixtureLoop rig.

- Message class failure_report, stage check, outcome gate_failed, origin tests/integration/test_host_loop.py::test_host_loop_report_regression_and_escape
- Message fields test_issue, report, fixed_failure and proposed_paths are all null or empty: no failure output or cause supplied
- declined-box-000449-ab280eb9: a fail-then-pass of a different test in the same file during the same provider-cli-install Check, declined for lack of failure output
- declined-box-000395-70ebe69b: the test_host_loop.py failure-path FixtureLoop uses a wall clock, real asyncio.sleep and real timeouts, a possible but unconfirmed source of timing-dependent flakiness
- provider-cli-install is in the merged set, so the reported Check failure did not block the ticket

Message: box-000450-dc7224af
