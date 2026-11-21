---
id: tombstone-box-000908-e8b592cb
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
An Implement run that ended ok says the repo-wide `clutch meta check` reports 29 metadata findings (missing, drifted or empty) that were already on the base, all in files outside the ticket's fence. It does not name any file, show any finding, or say what harm this caused the run.

This is the same report that registry record 000893 already decided: `clutch meta check` fails on the base commit because of `# clutch:meta` debt outside the fence. Records 000894 through 000905 already tombstoned repeats of it. The only new detail here is a count of 29. The report still names no file, gives no finding text, and shows no harm, since the run ended ok. The open ticket implement-spec-meta-headers-from-verbs also already tells implementers to fix meta findings only on files in their diff and to put findings on untouched files in `second_problems`. Reopen when a report names the failing files and the check output, or shows that this base-red meta debt cost a run an attempt or a Check.

- Message: class suggestion, origin context-suggest, stage implement, outcome ok, with a count of 29 pre-existing meta findings outside the fence
- declined-box-000893-4c8a8e81: same report that `clutch meta check` fails on the base commit outside the fence, with no files named
- tombstone-box-000894 through tombstone-box-000905 already link repeats of this report to record 000893
- Open ticket implement-spec-meta-headers-from-verbs sends meta findings on files the diff does not touch to second_problems

Message: box-000908-e8b592cb
