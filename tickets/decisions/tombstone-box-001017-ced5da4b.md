---
id: tombstone-box-001017-ced5da4b
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 30
---
During Check for merge-dirty-checkout-never-blocks, the safety case of the serve-admission refusal integration test (tests/integration/test_serve_admission.py::test_serve_admission_refusal_keeps_main_green[safety]) failed once and passed on rerun. The run was recorded as gate_failed at check. The report has no assertion, traceback, timeout output or suspected cause.

Registry record declined-box-000983-96a0ff93 already covers this intermittent failure of the serve-admission refusal/precheck tests under full-suite load. Records 000985, 000988, 000995, 000997 and 001010 tombstoned repeats for the host-red, integration, safety and precheck cases of test_serve_admission_refusal_keeps_main_green, and 001010 names this ticket's run and the safety case. This report adds no output, traceback, failure rate or cause, so it is the same report again. merge-dirty-checkout-never-blocks has also merged since. The quarantine-release gap that leaves such declined flake reports unreleasable is already owned by the open ticket flake-release-declined-resolution. Reopen if a report brings the failing assertion or timeout output plus a reproduction rate for this test, or if it blocks a ticket from merging.

- message origin tests/integration/test_serve_admission.py::test_serve_admission_refusal_keeps_main_green[safety], stage check, outcome gate_failed, report null
- declined-box-000983-96a0ff93: precheck admission integration test timed out once in full suite, passed alone
- tombstone-box-001010-220843ef: merge-dirty-checkout-never-blocks run saw serve-admission safety and precheck cases time out, linked to 000983
- tombstone-box-000985/000988/000995/000997: same test's other parameter cases, all linked to 000983
- merge-dirty-checkout-never-blocks is in the merged set
- open ticket flake-release-declined-resolution owns release of quarantined flakes whose reports were declined

Message: box-001017-ced5da4b
