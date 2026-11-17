---
id: tombstone-box-000665-12eb6f0e
kind: tombstone
link: declined-box-000457-e922cb8b
reopen_after_days: 30
---
During the tests-shared-fakes-b Implement run, the agent saw the kill-scenario integration test time out now and then. It did not reach its scripted boundary within 60 seconds. The note asks for the test's timing or synchronization to be looked at, but gives no test output, traceback or likely cause.

This is the same intermittent timeout already recorded for tests/integration/test_serve_dispatch.py::test_kill_aborts_requested_retro: during a full-suite run, the kill/retro scenario sometimes misses its scripted boundary. Record declined-box-000457-e922cb8b declined it because the reports had no failure output or cause. Tombstones 000529, 000531, 000574 and 000634 already link later sightings to that record. This report adds no timeout output, traceback or suspected cause, so it is another sighting of the same flake. Reopen when a report includes captured timeout output or a reproduction that names the race.

- Message: kill-scenario integration test intermittently failed to reach its scripted boundary within 60 seconds (origin tests-shared-fakes-b, stage implement, outcome ok)
- declined-box-000457-e922cb8b: test_kill_aborts_requested_retro failed once and passed on rerun, with no output or cause
- tombstone-box-000531-54d4b6b6 and tombstone-box-000574-4ff595a0: the same test intermittently timed out waiting for its scripted boundary during a full-suite run
- tombstone-box-000529-fc244696 and tombstone-box-000634-f9ff23e2: further sightings of the same flake linked to 000457

Message: box-000665-12eb6f0e
