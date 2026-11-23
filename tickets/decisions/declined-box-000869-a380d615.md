---
id: declined-box-000869-a380d615
kind: declined
link: box-000869-a380d615
reopen_after_days: 14
---
During Check for meta-schema-and-refresh-r2, the integration test tests/integration/test_testguard.py::test_budget_and_slowest failed once and passed on rerun, and the run was recorded as gate_failed. The report has no assertion, traceback, captured output or suspected cause, and meta-schema-and-refresh-r2 has since merged.

This is a single flaky test: it failed once and passed on rerun. The report has no failure output, traceback or cause, so it gives nothing to reproduce and no bounded repair to build. The run it came from, meta-schema-and-refresh-r2, has merged, so no current run is blocked. Earlier one-off flake reports with no evidence were declined the same way (box-000359, 000449, 000450, 000451, 000457). The merged testguard-slowest-order-deterministic already fixed one known cause of nondeterminism in this test. Reopen if test_budget_and_slowest fails again with captured output or a traceback that points to a reproducible cause, or if it fails repeatedly across runs within the window.

- message class failure_report, stage check, outcome gate_failed, origin tests/integration/test_testguard.py::test_budget_and_slowest
- summary says the test failed and then passed, with no output, traceback or cause attached
- meta-schema-and-refresh-r2 is in the merged set
- merged ticket testguard-slowest-order-deterministic already addressed ordering nondeterminism in this test's slowest report
- similar evidence-free flake reports declined: declined-box-000359-7e4514be, declined-box-000449-ab280eb9, declined-box-000457-e922cb8b

Message: box-000869-a380d615
