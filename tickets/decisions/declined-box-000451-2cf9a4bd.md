---
id: declined-box-000451-2cf9a4bd
kind: declined
link: box-000451-2cf9a4bd
reopen_after_days: 14
---
During Check for provider-cli-install, the integration test test_host_loop_requires_member_auditor_green in tests/integration/test_host_loop.py failed once and passed when rerun. The report has no assertion, traceback or captured output, and names no cause.

This is a single fail-then-pass during one Check run. It has no failure output, no assertion text and no named cause, so it shows no reproducible runtime defect and gives no measurable repair to build. Two other tests in the same file failed once and passed on rerun during the same provider-cli-install Check (declined-box-000449, declined-box-000450). Those reports also had no evidence, and both were declined. This report is about a different test, so it is not a duplicate of either one. Reopen if this test or another test_host_loop.py test fails again with captured output (assertion, traceback, or timing) that points to a shared cause, such as a real-clock or real-sleep race in the FixtureLoop rig, on more than one ticket's Check.

- Message class failure_report, stage check, outcome gate_failed, origin tests/integration/test_host_loop.py::test_host_loop_requires_member_auditor_green
- The summary says the test failed and then passed. The report field is null and no output or traceback is attached.
- declined-box-000449 and declined-box-000450 declined flaky test_host_loop.py failures from the same provider-cli-install Check for the same lack of evidence
- provider-cli-install is in the merged set, so the run that showed the flake has finished

Message: box-000451-2cf9a4bd
