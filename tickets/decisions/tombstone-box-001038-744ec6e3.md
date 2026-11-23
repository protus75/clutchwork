---
id: tombstone-box-001038-744ec6e3
kind: tombstone
link: declined-box-001006-72d4f6f6
reopen_after_days: 14
---
During the regression-command-program-lint run, the integration test test_live_keep_dispatches_again_without_restart failed once in the candidate's full suite. It passed on the base commit and when run alone. The report gives no assertion, traceback, failure rate or suspected cause.

Registry record 001006 already declined this same intermittent failure of test_live_keep_dispatches_again_without_restart, seen during the merge-dirty-checkout-never-blocks run. This report adds no assertion, traceback, failure rate, reproduction or cause, so it is a repeat of that record. Reopen if a report includes the failing assertion or traceback, a measured failure rate, or a run that lost a cycle because of this test.

- The message says test_live_keep_dispatches_again_without_restart failed intermittently in the candidate integration run and passed on the base and when run alone.
- Record declined-box-001006-72d4f6f6 covers the same test failing once in a full integration check, with no assertion, traceback, failure rate or cause.
- The message has outcome premise_failed but gives no evidence that this flaky test caused the premise failure.

Message: box-001038-744ec6e3
