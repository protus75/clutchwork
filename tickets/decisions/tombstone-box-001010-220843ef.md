---
id: tombstone-box-001010-220843ef
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 30
---
During the merge-dirty-checkout-never-blocks Implement run, which ended ok, the full integration suite timed out in serve-admission test cases. The timeouts hit the safety and precheck cases on the candidate and the integration case on the base. The report gives no traceback, timeout output, failure rate or suspected cause, and the run itself ended ok.

This is the same intermittent serve-admission integration timeout (test_serve_admission_refusal_keeps_main_green and its precheck/integration parameters) that registry record 000983 declined and records 000985, 000988, 000995 and 000997 tombstoned. Like those, it carries no timeout output, traceback or cause, and the run ended ok. One new detail is that the timeout also appeared on the base commit, which suggests a load-sensitive suite issue and not something this ticket caused, but it adds no diagnosable evidence. Reopen when a report includes the timeout output or traceback for a named serve-admission case, or shows the timeout failing Check or blocking a merge.

- message origin merge-dirty-checkout-never-blocks, stage implement, outcome ok
- declined-box-000983-96a0ff93: precheck admission integration test timed out once in a full suite run, then passed
- tombstone-box-000985/000988/000995/000997 link the same serve-admission timeouts to record 000983
- the message has no traceback, timeout output, failure rate or cause

Message: box-001010-220843ef
