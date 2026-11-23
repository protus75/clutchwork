---
id: tombstone-box-000968-859c0e5c
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
The spools-evidence-docs Implement run ended ok and filed one more note. It says the repo-wide metadata check still reports drifted and missing headers that already exist in files the run did not touch. The note names no file, gives no finding count, includes no check output and describes no harm to the run.

This is the same repeated filing that the open ticket implement-spec-meta-untouched-not-reported covers. That ticket removes the step-5 sentence in clutch/specs/implement.md that sends meta findings on untouched files to second_problems, and that sentence is what produces these repeat Box notes. Records 000960 and 000965 already tombstoned the same report to that ticket. Reopen if the note keeps arriving after that ticket merges.

- Message: class suggestion, origin spools-evidence-docs, stage implement, outcome ok; it names no file, finding count or harm
- Open ticket implement-spec-meta-untouched-not-reported covers routing meta findings on untouched files to second_problems
- Prior tombstones 000960 and 000965 point to the same ticket
- Record declined-box-000893-4c8a8e81 and its many tombstones cover the same repo-wide meta check debt

Message: box-000968-859c0e5c
