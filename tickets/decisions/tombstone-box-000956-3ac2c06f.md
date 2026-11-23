---
id: tombstone-box-000956-3ac2c06f
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 30
---
A plan-prompts-read-queue-each-tick Implement run that ended ok reports again that the repository-wide metadata check flags existing missing-header and drifted-metadata findings in files the run did not touch. It names no file, gives no finding count, includes no check output and describes no harm to the run.

This is the same report that registry record declined-box-000893-4c8a8e81 already decided. Records 000894 through 000954 tombstoned the same report many times from other runs. This message adds no file names, no counts, no output and no harm to the run, so nothing about the earlier decision changes. Reopen if a report names the failing files and shows that this existing metadata debt caused a run to fail or be misjudged.

- message class suggestion, stage implement, outcome ok; summary describes existing findings in untouched files
- declined-box-000893-4c8a8e81 settles the same repo-wide meta check debt report
- tombstone records 000894-000954 link the same report to declined-box-000893-4c8a8e81
- merged check-owns-meta-headers makes Check refresh headers on changed files, so drift outside the diff does not block runs

Message: box-000956-3ac2c06f
