---
id: declined-box-001165-ccdf856a
kind: declined
link: box-001165-ccdf856a
reopen_after_days: 30
---
During Check for mcp-index-query, the integration test tests/integration/test_git.py::test_subprocess_exec_publishes_pgid_for_a_synchronous_group_kill failed once and passed when rerun, so the run was recorded as gate_failed. The report has no assertion, traceback, captured output, failure rate or suspected cause. mcp-index-query has since merged.

This is a single report that a test failed once and then passed. It has no failure output, no reproduction and no cause, and the ticket that hit it (mcp-index-query) is in the merged set, so nothing is blocked now. Earlier one-off flake reports with no evidence were declined the same way (records 000359, 000449, 000457, 000869). No bounded repair can be specified from this evidence. Reopen if the same test fails again with an assertion, traceback or timeout output, or if it fails repeatedly enough to cost a ticket an attempt or send it to the Reject queue.

- message class failure_report, stage check, outcome gate_failed, origin tests/integration/test_git.py::test_subprocess_exec_publishes_pgid_for_a_synchronous_group_kill
- summary says the test failed then passed; report field is null, so there is no output or traceback
- mcp-index-query is in the merged stems list
- records declined-box-000359-7e4514be, declined-box-000449-ab280eb9, declined-box-000869-a380d615 decline the same kind of report: a single failure that passed on rerun, with no evidence

Message: box-001165-ccdf856a
