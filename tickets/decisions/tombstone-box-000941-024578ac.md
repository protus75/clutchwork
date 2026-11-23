---
id: tombstone-box-000941-024578ac
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 30
---
A serve-scan-ignores-head-moves Implement run that ended ok reports that the repo-wide metadata check finds 31 issues in files the ticket did not touch. The same 31 issues appear on the base commit. The report names no file, includes no check output and describes no harm to the run.

This repeats the existing-metadata-debt report that record 000893 declined, and that 000936 and 000940 already tombstoned for this same origin stem. The only new fact is a count of 31, and the note says those findings are identical on the base commit. So the change did not cause them, and the note shows no harm to a run. Reopen if a report names the flagged files and shows that this debt caused a wrong Check outcome or a lost attempt.

- declined-box-000893-4c8a8e81 declined the same repo-wide meta check debt report
- tombstone-box-000936-436455d4 and tombstone-box-000940-9ec2ef88 tombstoned identical reports from origin serve-scan-ignores-head-moves
- Message states the findings are identical on candidate and base, and the run outcome was ok

Message: box-000941-024578ac
