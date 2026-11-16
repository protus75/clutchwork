---
id: tombstone-box-000529-fc244696
kind: tombstone
link: declined-box-000457-e922cb8b
reopen_after_days: 30
---
During the roadmap-table-parser Implement run, the integration test tests/integration/test_serve_dispatch.py::test_kill_aborts_requested_retro sometimes timed out in the host check. The run said the test is unrelated to its change. The report gives no timeout output, traceback or suspected cause.

Registry record declined-box-000457-e922cb8b already covers this: the same test, test_kill_aborts_requested_retro, failed intermittently during Check with no assertion, traceback or cause. This report differs only in calling the failure a timeout and naming a different originating ticket. It adds no evidence, such as a reproduction rate, captured output or suspected cause, that would make it one bounded repair. Reopen if repeated runs show the test failing at a measurable rate with captured output that points to a cause, such as a timeout trace naming the stalled await.

- message class suggestion, origin roadmap-table-parser, stage implement, outcome ok: the run itself succeeded
- declined-box-000457-e922cb8b: test_kill_aborts_requested_retro failed once and passed on rerun, with no assertion, traceback, output or cause
- the message carries no timeout trace, duration, rate, or proposed fix

Message: box-000529-fc244696
