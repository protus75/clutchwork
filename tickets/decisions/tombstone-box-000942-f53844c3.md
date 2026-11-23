---
id: tombstone-box-000942-f53844c3
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 30
---
A panel-scorecard Implement run that ended ok repeats that the repository-wide metadata check reports findings in files the change did not touch. The message points back to its own earlier filing, box-000929. It names no file, gives no finding count, includes no check output and describes no harm to the run.

This is the same report as registry record 000893, which declined repo-wide `clutch meta check` debt in untouched files because the report named no files, gave no counts and showed no harm. Record 000929, filed earlier from the same panel-scorecard run, was already tombstoned to 000893. This message adds no new evidence. Reopen when a report names the flagged files and shows a run failing or a gate going red because of that base-side metadata debt.

- message summary: findings 'were previously recorded as box-000929-3c6a17f6'
- tombstone-box-000929-3c6a17f6 links to declined-box-000893-4c8a8e81 for the same panel-scorecard report
- declined-box-000893-4c8a8e81: repo-wide meta check failures with no files, count or output
- message outcome is ok, so no run was harmed

Message: box-000942-f53844c3
