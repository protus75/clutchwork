---
id: tombstone-box-001019-1b30fac9
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 14
---
During the serve-merge-off-exclusive Implement run, which ended ok, the integration case of test_serve_admission_refusal_keeps_main_green timed out once in a later full integration suite run. It passed when run alone and in the ticket's next verification. The report has no timeout output, traceback, failure rate or suspected cause.

This repeats the intermittent serve-admission refusal test timeout that record 000983 already declined. Records 000985, 000988, 000995, 000997, 001010 and 001017 tombstoned the same report from other runs. This message adds no traceback, no timeout output, no failure rate and no cause, and the run ended ok, so it shows no new harmful behavior. Reopen if a report includes the timeout output or a traceback that identifies a cause, or shows the timeout cost a run an attempt.

- message: class suggestion, origin serve-merge-off-exclusive, stage implement, outcome ok
- message: test timed out once in a later full integration run, passed alone and in the next ticket verification
- declined-box-000983-96a0ff93: same test (precheck admission) timed out once in the full suite and passed alone and in later verification
- tombstone-box-000988-23de4fca, 000995, 000997: the same [integration] case timing out now and then in full-suite runs, already tombstoned to 000983
- neighbors unavailable (index_unreadable); not grounds for the verdict

Message: box-001019-1b30fac9
