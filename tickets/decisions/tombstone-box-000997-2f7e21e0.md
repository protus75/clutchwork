---
id: tombstone-box-000997-2f7e21e0
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 14
---
A requisition-contract-review-comparison Implement run that ended ok saw the integration test test_serve_admission_refusal_keeps_main_green[integration] in tests/integration/test_serve_admission.py time out now and then during a full integration suite run. The report gives no timeout output, traceback or suspected cause, and describes no harm to the run.

This is the same intermittent serve-admission precheck timeout that record 000983 declined. Records 000985, 000988 and 000995 already tombstoned repeats of it, and 000995 came from this same requisition-contract-review-comparison run. The message adds no new evidence: no output, no traceback, no cause, and the run ended ok. Reopen when a report includes the timeout output or traceback, or shows the timeout cost a run a cycle (gate_failed at Check or a spent cap).

- Message: class suggestion, origin requisition-contract-review-comparison, stage implement, outcome ok, no report body
- declined-box-000983-96a0ff93: precheck admission integration test timed out once in a full suite, passed alone; run ended ok
- tombstone-box-000995-4667dbf6: same test [integration] param, same origin run, already linked to 000983
- tombstone-box-000988-23de4fca and tombstone-box-000985-584adc0d: same test, linked to 000983
- Neighbor index unavailable; this match comes from the decision registry alone

Message: box-000997-2f7e21e0
