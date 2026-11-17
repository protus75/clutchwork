---
id: tombstone-box-000634-f9ff23e2
kind: tombstone
link: declined-box-000457-e922cb8b
reopen_after_days: 14
---
An Implement run with origin supervisor-effect-scope saw the integration test test_kill_aborts_requested_retro in tests/integration/test_serve_dispatch.py time out now and then during the integration gate. The report includes no timeout output, traceback or suspected cause.

This is the same intermittent test_kill_aborts_requested_retro failure that registry record 000457 already declined. Records 000529, 000531 and 000574 already tombstoned repeat sightings from other Implement runs against that record. This report adds only one more origin and no assertion, traceback, timing data or cause, so it supplies none of the evidence the earlier decision lacked. Reopen if a report includes the timeout output or the boundary the test waited on, or if the failure rate shows the flake is spending caps or blocking merges.

- message summary: test_kill_aborts_requested_retro intermittently timed out during the integration gate; origin supervisor-effect-scope, stage implement, outcome ok
- declined-box-000457-e922cb8b: same test failed once and passed on rerun, no traceback or cause
- tombstone-box-000529-fc244696, tombstone-box-000531-54d4b6b6, tombstone-box-000574-4ff595a0: repeat sightings of the same intermittent timeout, all linked to declined-box-000457-e922cb8b
- the report has no output, traceback or proposed cause

Message: box-000634-f9ff23e2
