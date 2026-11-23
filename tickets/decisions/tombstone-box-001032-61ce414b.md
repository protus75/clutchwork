---
id: tombstone-box-001032-61ce414b
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 14
---
During Check for roadmap-meta-resync, the precheck case of the serve-admission refusal integration test (tests/integration/test_serve_admission.py::test_serve_admission_refusal_keeps_main_green[precheck]) failed once and passed on rerun, so the run was recorded as gate_failed at check. The report has no assertion, traceback, timeout output, failure rate or suspected cause.

Registry record 000983 already decided this intermittent failure of test_serve_admission_refusal_keeps_main_green, and its precheck case is the one named there. Records 000985, 000988, 000995, 000997, 001010, 001017, 001019 and 001024 tombstoned the same flake for its other parameter cases (host-red, integration, safety). This report adds nothing new: no traceback, no assertion and no cause. The open ticket flake-release-declined-resolution covers the quarantine release path for flakes whose reports were declined. Reopen if a report includes timeout output or a traceback that identifies a cause in serve admission.

- Message origin: tests/integration/test_serve_admission.py::test_serve_admission_refusal_keeps_main_green[precheck], stage check, outcome gate_failed, report null
- declined-box-000983-96a0ff93: the precheck admission integration test timed out once in a full suite run and passed alone
- tombstone-box-001017-ced5da4b: the [safety] case failed once at Check and passed on rerun; tombstoned to 000983
- tombstone-box-001024-dcda882f and tombstone-box-001010-220843ef: further timeouts in the serve-admission refusal cases
- roadmap-meta-resync is in the merged set

Message: box-001032-61ce414b
