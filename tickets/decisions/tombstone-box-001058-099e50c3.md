---
id: tombstone-box-001058-099e50c3
kind: tombstone
link: declined-box-000983-96a0ff93
reopen_after_days: 14
---
During the serve-flaky-tests-deterministic Implement run, which ended ok, two admission integration cases hit the global test timeout in the first combined run. Both passed when run alone and in the required full rerun. The note names no test, timeout output, traceback, failure rate or suspected cause.

This is the same intermittent serve-admission integration timeout that registry record 000983 declined, and records 000985, 000988, 000995, 000997, 001010, 001017, 001019, 001024, 001032, 001034, 001043, 001050 and 001055 tombstoned to it. The run ended ok, and the merged ticket serve-flaky-tests-deterministic already targeted these admission timeouts. The note adds no assertion, traceback, failure rate or cause. Reopen if a timeout in a serve-admission case is captured with output after serve-flaky-tests-deterministic merged and it fails a Check gate or costs a run an attempt.

- message origin serve-flaky-tests-deterministic, stage implement, outcome ok
- the cases passed when run alone and on the required full rerun
- declined-box-000983-96a0ff93 and 13 tombstones linked to it cover intermittent timeouts in serve-admission integration cases
- serve-flaky-tests-deterministic is in the merged set
- the report has no test names, traceback, timeout output or cause

Message: box-001058-099e50c3
