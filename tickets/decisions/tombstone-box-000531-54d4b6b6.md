---
id: tombstone-box-000531-54d4b6b6
kind: tombstone
link: declined-box-000457-e922cb8b
reopen_after_days: 30
---
An Implement run (origin diagnose-spec-first-char-json-reply) saw tests/integration/test_serve_dispatch.py::test_kill_aborts_requested_retro intermittently time out while waiting for its scripted boundary during the full integration suite. The test passed when run on its own. The report gives no timeout output, traceback or suspected cause.

This repeats an intermittent failure of the same test that the registry has already settled. declined-box-000457-e922cb8b declined it: the test failed once, passed on rerun, and the report carried no assertion, output or cause. tombstone-box-000529-fc244696 linked a second report of the same host-check timeout back to that record. This message adds only that the test passes in isolation. That is still not a reproducible cause or a bounded repair. Reopen if a report includes the timeout traceback or captured output that names a cause, or if the test fails often enough to block runs.

- declined-box-000457-e922cb8b: test_kill_aborts_requested_retro failed once during Check and passed on rerun, with no assertion, traceback or cause
- tombstone-box-000529-fc244696: the same test timed out intermittently during the roadmap-table-parser run, with no timeout output or cause, and was linked to 000457
- The current message names the same test and the same timeout on the scripted boundary, and it also has no traceback, output or cause

Message: box-000531-54d4b6b6
