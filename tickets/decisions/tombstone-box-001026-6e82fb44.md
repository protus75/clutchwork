---
id: tombstone-box-001026-6e82fb44
kind: tombstone
link: declined-box-000703-ccb1d10f
reopen_after_days: 30
---
During the serve-merge-off-exclusive Implement run, which ended ok, three host-loop integration tests hit setup errors in one base-commit integration run, while the same tests passed on the candidate. The note blames an abandoned escape, but it names no test and gives no error text, traceback or reproduction.

This is the same intermittent host-loop fixture setup failure that registry record 000703 already declined. Record 001018 tombstoned the same failure from this same serve-merge-off-exclusive run, which also ended ok. The report adds no assertion, traceback, error output, failure rate or code path, and it describes no harm to the run. Reopen if a host-loop setup failure is reported with its error output and a reproducible cause.

- message: class suggestion, origin serve-merge-off-exclusive, stage implement, outcome ok
- tombstone-box-001018-5184bf51 links to declined-box-000703-ccb1d10f: three host-loop integration tests hit shared setup errors during the same serve-merge-off-exclusive run
- declined-box-000703-ccb1d10f: intermittent host-loop fixture failure reported with no failing test, traceback or cause
- neighbors unavailable: index_unreadable

Message: box-001026-6e82fb44
