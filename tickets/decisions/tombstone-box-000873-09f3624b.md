---
id: tombstone-box-000873-09f3624b
kind: tombstone
link: testguard-slowest-order-deterministic
reopen_after_days: 30
---
Retro/61 reports that tests/integration/test_testguard.py::test_budget_and_slowest failed once in the integration gate on meta-schema-and-refresh-r2 attempt 3. The test ranked per-test durations taken from real time.sleep(0.2) and time.sleep(0.1) calls, so under load the order could swap. The proposed fix is to set the durations directly instead of sleeping, so the order assertion always gives the same result.

The merged ticket testguard-slowest-order-deterministic already made this fix. The current test_budget_and_slowest (tests/integration/test_testguard.py:116-140) no longer sleeps for real. A hook sets report.duration to fixed values ({'test_slowest': 2.0, 'test_slower': 1.0}) and then checks the order. The duration still flows through pytest's report, which also covers the overcorrection risk the finding raises. Nothing is left to fix. Reopen if test_budget_and_slowest fails again on the current code.

- tests/integration/test_testguard.py:132 sets report.duration = {"test_slowest": 2.0, "test_slower": 1.0}.get(item.name, 0.0); the test no longer calls time.sleep(0.2)/time.sleep(0.1)
- tests/integration/test_testguard.py:140 asserts the order on those fixed durations
- The merged stems list includes testguard-slowest-order-deterministic, and tickets/testguard-slowest-order-deterministic/ holds its ticket, run.md, checks.json and review.md
- Record declined-box-000869-a380d615 covers the same one-time failure on meta-schema-and-refresh-r2

Message: box-000873-09f3624b
