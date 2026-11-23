---
id: tombstone-box-001050-a5c8f914
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 14
---
The safety case of the serve-admission refusal integration test (tests/integration/test_serve_admission.py::test_serve_admission_refusal_keeps_main_green[safety]) timed out once in a base integration run during a check-owns-meta-headers Implement run that ended ok. The report has no timeout output, traceback, failure rate or suspected cause.

This is the same intermittent serve-admission refusal timeout that registry record 000983 already declined. Records 001010, 001017 and 001043 already tombstoned the safety case of this same test to that record, and the run that filed this report ended ok. The merged serve-flaky-tests-deterministic ticket made the precheck case of this test deterministic. This report adds no new evidence. Reopen only if a report shows the safety case failing a Check gate, with timeout output or a traceback that points to a cause.

- Registry record declined-box-000983-96a0ff93 declined an intermittent timeout of the serve-admission refusal integration test.
- Records tombstone-box-001010-220843ef, tombstone-box-001017-ced5da4b and tombstone-box-001043-63bd4b02 tombstoned reports of the safety case of the same test to record 000983.
- The message says the run had stage implement and outcome ok, and gives no traceback, timeout output or cause.
- The merged ticket serve-flaky-tests-deterministic (tombstone-box-001045-593d2531) covers the timeout in the test's precheck case.

Message: box-001050-a5c8f914
