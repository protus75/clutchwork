---
id: tombstone-box-001071-979fce43
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 30
---
A serve-flaky-tests-deterministic Implement run that ended ok reports that the precheck case of the serve-admission refusal integration test runs past its wall-clock deadline when the test suite is under concurrent load. The report has no timeout output, traceback, failure rate or suspected cause.

This is the same intermittent timeout in the serve-admission refusal test that registry record 000983 declined. Many later records already tombstone repeats of it: 000985, 000995, 001010, 001017, 001032, 001064 and others. The precheck-case flake itself was the subject of merged ticket serve-flaky-tests-deterministic, which is where this report comes from. The report adds no new evidence: no timeout output, traceback, failure rate or harm to the run, which ended ok. Reopen if the precheck case keeps timing out on main after serve-flaky-tests-deterministic merged, with captured timeout output and a failure rate.

- message class suggestion, origin serve-flaky-tests-deterministic, stage implement, outcome ok
- declined-box-000983-96a0ff93: the precheck admission integration test timed out once under a full suite run
- tombstone-box-001032-61ce414b and tombstone-box-001045-593d2531 cover the precheck case of test_serve_admission_refusal_keeps_main_green
- serve-flaky-tests-deterministic is in the merged set
- the report includes no timeout output, traceback, failure rate or harm

Message: box-001071-979fce43
