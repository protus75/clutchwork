---
id: tombstone-box-000914-8a1957d9
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
A context-suggest-author-block Implement run that ended ok says the repo-wide `clutch meta check` fails on its base commit. The check finds missing, drifted or empty-purpose `clutch:meta` blocks in files the ticket does not touch. The note does not name a file, give a finding count, include check output, or say how this harmed the run.

Registry record declined-box-000893-4c8a8e81 already decided this report: base-side meta debt outside the ticket's fence, with no files, counts or harm given. Records 000894 to 000912 tombstoned the same report from other runs, and 000912 came from this same origin. The open ticket implement-spec-meta-headers-from-verbs already tells implementers to send meta findings on files outside their diff to second_problems. Reopen if a report names the failing files and shows that base meta debt caused a run to fail.

- declined-box-000893-4c8a8e81 covers the repo-wide meta check failing on base in files outside the fence
- tombstone-box-000912-5f8a19d7 is the same report from origin context-suggest-author-block
- open ticket implement-spec-meta-headers-from-verbs sends findings on files outside the diff to second_problems
- the message reports outcome ok with no file names, finding count or harm

Message: box-000914-8a1957d9
