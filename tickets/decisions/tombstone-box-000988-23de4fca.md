---
id: tombstone-box-000988-23de4fca
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 14
---
A plan-prompts-priority-order Implement run that ended ok reports that the integration test test_serve_admission_refusal_keeps_main_green[integration] sometimes timed out during a full integration suite run. The report gives no timeout output, traceback, failing assertion or suspected cause, and describes no harm to the run.

Registry record 000983 already declined this report: the serve admission refusal integration test timing out once during a full suite run, with no output or cause. Record 000985 tombstoned the [host-red] variant to 000983. This message reports the [integration] parameter of the same test with the same lack of evidence, and its run ended ok. Reopen if a report includes timeout output or a traceback, or if the test blocks a run at Check, so that a bounded repair can be named.

- message class suggestion, stage implement, outcome ok, origin plan-prompts-priority-order
- declined-box-000983-96a0ff93: precheck admission integration test timed out once during a full integration run, passed alone; run ended ok
- tombstone-box-000985-584adc0d: test_serve_admission_refusal_keeps_main_green[host-red] timed out once, linked to 000983
- the message carries no traceback, timeout output or cause

Message: box-000988-23de4fca
