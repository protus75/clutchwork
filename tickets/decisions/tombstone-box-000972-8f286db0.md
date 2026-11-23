---
id: tombstone-box-000972-8f286db0
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
A release-audit-050 Implement run that ended ok reports that the repo-wide metadata check still flags missing, drifted or empty-purpose metadata in test files the run did not touch. It names no file, gives no finding count, includes no check output and describes no harm to the run.

This is the same repeated filing about pre-existing meta check findings on untouched files. Open ticket implement-spec-meta-untouched-not-reported stops Implement from sending those findings to second_problems, which is how these notes keep reaching the Box. Records 000960, 000965 and 000968 already tombstoned identical notes to that ticket. Reopen if the repeat filings continue after that ticket merges.

- Open ticket implement-spec-meta-untouched-not-reported covers repeat Box filings of pre-existing repo-wide meta check findings on untouched files
- tombstone-box-000960-0d2c91cf, tombstone-box-000965-8d73b624 and tombstone-box-000968-859c0e5c link the same report to that ticket
- declined-box-000893-4c8a8e81 and its many tombstones record the earlier instances
- The message has origin release-audit-050, stage implement, outcome ok, and no file, count or harm

Message: box-000972-8f286db0
