---
id: tombstone-box-000995-4667dbf6
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 30
---
During the requisition-contract-review-comparison Implement run, which ended ok, the integration test test_serve_admission_refusal_keeps_main_green[integration] timed out once in a full suite run. It passed when run alone on both the base commit and the candidate, and it passed in the final full suite. The report has no timeout output, traceback or suspected cause.

This repeats the intermittent timeout in test_serve_admission_refusal_keeps_main_green that record 000983 declined. Record 000988 already tombstoned the same [integration] parameter against that record, and record 000985 did the same for the [host-red] parameter. Like those reports, this one has no timeout output, traceback or cause, the run ended ok, and the test passed when run alone and in the final suite. Reopen if a report brings a captured timeout traceback or a failure that can be reproduced in isolation.

- message: stage implement, outcome ok, the test passed alone on base and candidate and in the final full suite
- tombstone-box-000988-23de4fca: the same test_serve_admission_refusal_keeps_main_green[integration] intermittent timeout, linked to declined-box-000983-96a0ff93
- tombstone-box-000985-584adc0d: the [host-red] variant of the same test, linked to declined-box-000983-96a0ff93
- declined-box-000983-96a0ff93: a one-off timeout of the precheck admission integration test with no traceback; the run ended ok

Message: box-000995-4667dbf6
