---
id: tombstone-box-000949-86acd30a
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 30
---
After a review-cost-sonnet-instance Implement run that ended ok, a note says the repo-wide metadata check found existing findings in files outside the ticket's fence and none in the test the run added. It names no file, gives no finding count, includes no check output and describes no harm to the run.

This is the same repeated observation that registry record 000893 declined: the repo-wide `clutch meta check` reports metadata debt that already exists in files outside a ticket's fence. Dozens of later reports were tombstoned to that record, including 000946 from this same review-cost-sonnet-instance run. This message adds no file, count, output or harm. Reopen if a report shows that base-side meta findings caused a run to fail or be misjudged.

- registry declined-box-000893-4c8a8e81 covers base-side meta check findings outside the fence
- tombstone-box-000946-dcc58924 is the same report from the same origin review-cost-sonnet-instance
- message outcome is ok with no named file, count, or harm

Message: box-000949-86acd30a
