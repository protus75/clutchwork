---
id: tombstone-box-001055-d2562a00
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 14
---
During the check-rerun-failed-only Implement run, which ended ok, the safety case of the serve-admission refusal integration test timed out on both the candidate and the base commit. The note gives no timeout output, traceback, failure rate or suspected cause, and describes no harm to the run.

This repeats the intermittent timeout in test_serve_admission_refusal_keeps_main_green that registry record 000983 already declined. Many later reports were tombstoned to that record, including safety-case timeouts from the same ticket (001043) and from check-owns-meta-headers (001050). The test also timed out on the base commit, so the candidate did not cause it. The run ended ok. The note has no output, rate or cause. Merged serve-flaky-tests-deterministic already replaced the wall-clock wait in the precheck case of this test. Reopen if a run is failed or sent to the Reject queue by the safety case after that merge, and the report includes the timeout output or a failure rate.

- message origin check-rerun-failed-only, stage implement, outcome ok
- summary says the test timed out on both candidate and base commit
- declined-box-000983-96a0ff93 covers intermittent serve-admission refusal test timeouts
- tombstone-box-001043-63bd4b02 and tombstone-box-001050-a5c8f914 link safety-case timeouts to 000983
- merged serve-flaky-tests-deterministic addressed the wall-clock wait in this test family

Message: box-001055-d2562a00
