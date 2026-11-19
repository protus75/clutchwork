---
id: tombstone-box-000759-eaccf383
kind: tombstone
link: declined-box-000733-053679e0
reopen_after_days: 30
---
During the Check stage of boundary-contract-authoring, the integration test test_serve_admission_holds_and_cleanup[tree-mismatch] in tests/integration/test_serve_admission.py failed once and then passed on rerun. The report gives no assertion, traceback, captured output or suspected cause. boundary-contract-authoring has since merged.

This is the same intermittent failure of the same parametrized test (test_serve_admission_holds_and_cleanup[tree-mismatch]) that registry record declined-box-000733-053679e0 already decided. That record covers a one-time worker crash in this test that did not reproduce in isolation or in the next suite run. This report adds nothing new. It has no failure output, assertion, traceback or cause, and the ticket it hit (boundary-contract-authoring) is merged, so no run is blocked. Reopen if a report of this test's flake includes the failing assertion or traceback, or if it fails a run that does not pass on rerun.

- message.origin: tests/integration/test_serve_admission.py::test_serve_admission_holds_and_cleanup[tree-mismatch], stage check, outcome gate_failed, failed then passed
- message carries no report, assertion, traceback, or suspected cause
- registry declined-box-000733-053679e0: the same test parameter [tree-mismatch] crashed once in an integration worker and did not reproduce, with no traceback or cause
- boundary-contract-authoring is in the merged stems list

Message: box-000759-eaccf383
