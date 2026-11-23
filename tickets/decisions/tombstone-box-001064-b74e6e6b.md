---
id: tombstone-box-001064-b74e6e6b
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 14
---
During Check for implement-skips-full-suites, the integration case of the serve-admission refusal test (tests/integration/test_serve_admission.py::test_serve_admission_refusal_keeps_main_green[integration]) failed once and passed on rerun, so the run was recorded as gate_failed at check. The report has no assertion, traceback, timeout output, failure rate or suspected cause, and implement-skips-full-suites has since merged.

Record 000983 already covers this intermittent serve-admission refusal timeout, and many tombstones point to it for other cases of the same test, including [integration], [safety] and [precheck] (000988, 000995, 000997, 001017, 001032). The deterministic-wait cause fix merged as serve-flaky-tests-deterministic. This report adds no new evidence: no traceback, no failure rate, no cause. The ticket it hit, implement-skips-full-suites, is already merged. Reopen if this test keeps failing after serve-flaky-tests-deterministic with captured output that shows a new cause.

- origin tests/integration/test_serve_admission.py::test_serve_admission_refusal_keeps_main_green[integration], stage check, outcome gate_failed, report null
- declined-box-000983-96a0ff93 and tombstones 000988/000995/000997/001017/001032 cover the same test's intermittent failures
- serve-flaky-tests-deterministic and implement-skips-full-suites are in the merged set

Message: box-001064-b74e6e6b
