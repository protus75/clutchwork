---
id: tombstone-box-000745-6472cc29
kind: tombstone
link: declined-box-000457-e922cb8b
reopen_after_days: 30
---
The cli-group-release Implement run saw the integration test test_kill_aborts_requested_retro in tests/integration/test_serve_dispatch.py time out now and then during a full integration suite run. The run itself ended ok. The report includes no timeout output, traceback, failing assertion or suspected cause.

This repeats the intermittent timeout of test_kill_aborts_requested_retro that record declined-box-000457-e922cb8b already decided. Records 000529, 000531, 000574, 000634 and 000665 already tombstoned the same report from other runs. This copy adds no new evidence: no timeout output, no traceback and no cause. Reopen if a report includes the captured timeout output, or reproduces the timeout in an isolated run, or names a cause in the test's scripted-boundary synchronization.

- message class suggestion, origin cli-group-release, stage implement, outcome ok
- declined-box-000457-e922cb8b: same test intermittently failing during Check, with no output or cause
- tombstone-box-000529, -000531, -000574, -000634 and -000665 all link the same intermittent timeout to 000457
- the message carries no report, test_issue or fixed_failure detail

Message: box-000745-6472cc29
