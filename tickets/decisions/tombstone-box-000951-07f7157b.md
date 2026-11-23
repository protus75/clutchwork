---
id: tombstone-box-000951-07f7157b
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 30
---
An author-ticket-writes-commit-edit Implement run that ended ok says the repo-wide metadata check reports findings that already exist in files it did not touch, and that the same findings appear on the base commit. It names no file, gives no finding count, includes no check output and describes no harm to the run.

This repeats the report that registry record declined-box-000893-4c8a8e81 already declined: base-side `clutch:meta` findings in untouched files, with no named file, count, output or harm. Records 000894 through 000950 tombstoned many copies of it from other runs. This run ended ok, so the message shows no current harmful behavior. Reopen if a report names the failing files and shows that this base-side debt changed a run's outcome.

- message outcome is ok and the origin is author-ticket-writes-commit-edit, which has merged
- declined-box-000893-4c8a8e81 covers base-side meta check findings in files outside the fence
- tombstones 000894-000950 link the same report to declined-box-000893-4c8a8e81

Message: box-000951-07f7157b
