---
id: tombstone-box-000912-5f8a19d7
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
An Implement run stopped with premise_failed, origin context-suggest-author-block. It reports that the repo-wide `clutch meta check` on its base commit finds drifted metadata, missing metadata and empty purposes in files unrelated to the ticket. It names no file, gives no finding count, includes no check output, and does not show that this base-side debt caused the premise failure.

This is the same report that record 000893 already settled: base-side `clutch:meta` debt outside the ticket's fence, with no named files, no count and no shown harm. Records 000894-000911 tombstoned the same report from other runs. The open ticket implement-spec-meta-headers-from-verbs already covers the behavior part: it tells Implement to run `clutch meta check` and to send findings on files outside the diff to second_problems instead of acting on them. That stops Implement from treating base meta debt as a reason to stop. Reopen if a run shows a specific base meta finding that blocked a ticket after that ticket merges.

- message: class suggestion, stage implement, outcome premise_failed, origin context-suggest-author-block; it names no files and gives no count or output
- declined-box-000893-4c8a8e81: repo-wide meta check fails on the base in files outside the fence, with no files or harm named
- tombstone-box-000908, 000909, 000910 and 000911 link the same report to 000893
- open ticket implement-spec-meta-headers-from-verbs: findings on files the diff does not touch go to second_problems

Message: box-000912-5f8a19d7
