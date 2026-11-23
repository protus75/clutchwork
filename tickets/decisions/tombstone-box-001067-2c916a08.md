---
id: tombstone-box-001067-2c916a08
kind: tombstone
link: serve-live-keep-single-verdict
reopen_after_days: 14
---
During Check for serve-flaky-tests-deterministic, the integration test tests/integration/test_serve_dispatch.py::test_live_keep_dispatches_again_without_restart failed once and passed on rerun, and the run was recorded as gate_failed at check. The report has no assertion, traceback, captured output or suspected cause.

This is the same intermittent failure of test_live_keep_dispatches_again_without_restart that earlier records already handled. Record 001046 traced it to the test sometimes journaling two keep verdicts where it expects one, and tombstoned it to the merged ticket serve-live-keep-single-verdict. Records 001006 and 001038 covered the same flake without new evidence. serve-flaky-tests-deterministic has merged, and this report adds no traceback or new cause to show the flake outlived serve-live-keep-single-verdict. Reopen if the test fails on a commit that includes serve-live-keep-single-verdict and the report includes the assertion or journal evidence.

- message origin: tests/integration/test_serve_dispatch.py::test_live_keep_dispatches_again_without_restart, stage check, outcome gate_failed, no report body
- tombstone-box-001046-e2222211 links this test's double keep-verdict flake to merged ticket serve-live-keep-single-verdict
- declined-box-001006-72d4f6f6 and tombstone-box-001038-744ec6e3 cover the same test failing once without traceback
- serve-live-keep-single-verdict and serve-flaky-tests-deterministic are both in the merged set

Message: box-001067-2c916a08
