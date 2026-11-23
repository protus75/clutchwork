---
id: tombstone-box-001000-3f13802e
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
The serve-confirm-during-check Implement run ended ok and filed a second problem: docs/roadmap.md already had drifted clutch:meta metadata before the run. The run did not touch that file. The note includes no check output and describes no harm to the run.

This repeats a report that has already been tombstoned many times: pre-existing metadata drift in docs/roadmap.md, a file the run did not change, filed as a second problem by an Implement run that ended ok. The open ticket implement-spec-meta-untouched-not-reported covers the cause. Step 5 of the Implement spec sends meta findings on untouched files to second_problems, and that produces exactly this repeat filing. Reopen if that ticket merges and Implement runs still file meta findings on files they did not touch.

- message origin serve-confirm-during-check, stage implement, outcome ok, summary: docs/roadmap.md has pre-existing metadata drift
- open ticket implement-spec-meta-untouched-not-reported covers repeat second_problems filing of pre-existing meta findings on untouched files
- registry tombstones 000979, 000980, 000981, 000984, 000987, 000989, 000992, 000996 and 000999 link the same docs/roadmap.md drift report to implement-spec-meta-untouched-not-reported

Message: box-001000-3f13802e
