---
id: tombstone-box-001043-63bd4b02
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 30
---
A check-rerun-failed-only Implement run that ended ok saw the safety case of test_serve_admission_refusal_keeps_main_green time out now and then while waiting for the next merge boundary. The report gives no timeout output, traceback, failure rate or suspected cause, and describes no harm to the run.

This is the same intermittent serve-admission refusal timeout that registry record 000983 declined. Tombstones 000985, 000988, 000995, 000997, 001010, 001014, 001017, 001019, 001024, 001032 and 001034 already link the same report about other cases of this test to that record. This message adds no traceback, failure rate or cause. Reopen if a report brings timeout output or a reproduction that ties the timeout to a specific cause, or if the quarantine release path (open ticket flake-release-declined-resolution) changes how these flakes are handled.

- message: suggestion from check-rerun-failed-only, stage implement, outcome ok, test_serve_admission_refusal_keeps_main_green[safety] intermittently times out waiting for the next merge boundary
- declined-box-000983-96a0ff93: precheck admission integration test timed out once in a full suite run, passed alone, and the run ended ok
- tombstone-box-001017-ced5da4b: the same [safety] case failed once at Check and was linked to 000983
- tombstone-box-001024-dcda882f: the host-red case timed out waiting for the next merge and was linked to 000983

Message: box-001043-63bd4b02
