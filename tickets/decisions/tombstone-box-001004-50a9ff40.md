---
id: tombstone-box-001004-50a9ff40
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
The serve-confirm-during-check Implement run, which ended ok, filed another second problem: tests/unit/test_training_triage_records.py already had a clutch:meta header with an empty purpose on the base commit. The run did not touch that file. The note includes no check output and describes no harm to the run.

This repeats the pre-existing repo-wide meta finding on an untouched file. Implement keeps filing that finding to the box as a second problem. Open ticket implement-spec-meta-untouched-not-reported covers this class: it stops Implement from routing meta findings on untouched files to second_problems. Records 000982, 000984, 000993, 000996, 000999 and 001001 already tombstoned the same empty-purpose finding on this file, and 001001 came from this same origin.

- Open ticket implement-spec-meta-untouched-not-reported names repeat filing of pre-existing meta findings on untouched files, including empty-purpose headers.
- tombstone-box-001001-7aec85cd: the same file, the same empty-purpose finding and the same origin, serve-confirm-during-check.
- tombstone-box-000982, 000984, 000993, 000996 and 000999: the same finding on tests/unit/test_training_triage_records.py.

Message: box-001004-50a9ff40
