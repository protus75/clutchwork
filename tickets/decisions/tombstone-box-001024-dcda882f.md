---
id: tombstone-box-001024-dcda882f
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 14
---
The serve-merge-off-exclusive Implement run, which ended ok, reports that the host-red case of test_serve_admission_refusal_keeps_main_green timed out waiting for the next merge on both the candidate and the base commit. The report gives no timeout output, traceback, failure rate or suspected cause.

This repeats the intermittent serve-admission refusal test timeout that registry record 000983 declined. Tombstones 000985, 000988, 000995, 000997, 001010, 001017 and 001019 already linked the same test family to that record, and 000985 named this same host-red case. The run ended ok. The report has no output, traceback or failure rate, and it describes no harm to the run. It also says the timeout happens on the base commit, so the ticket's change did not cause it. Reopen if a report includes the timeout output or traceback, or shows the host-red case failing every time on main or costing a run a cycle.

- message outcome: implement ok, origin serve-merge-off-exclusive
- message says the timeout happened on both candidate and base
- declined-box-000983-96a0ff93: intermittent serve-admission test timeout, declined
- tombstone-box-000985-584adc0d: same test, host-red case, linked to 000983
- tombstone-box-001019-1b30fac9: same test, same origin run, linked to 000983

Message: box-001024-dcda882f
