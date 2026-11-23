---
id: tombstone-box-000993-a6cec97c
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
The requisition-review-approval-reuse Implement run ended ok and filed a second problem: tests/unit/test_training_triage_records.py has a clutch:meta header with an empty purpose on the base commit. The run did not touch that file. The note includes no check output and describes no harm to the run.

This is another repeat filing of a pre-existing meta finding on a file the run did not touch. The open ticket implement-spec-meta-untouched-not-reported covers exactly this. It stops Implement from sending meta findings on untouched files to second_problems. Records 000982, 000984, 000987 and 000989 already tombstoned this same empty-purpose finding on this file to that ticket. Reopen if the finding is still filed after that ticket merges.

- message class suggestion, origin requisition-review-approval-reuse, stage implement, outcome ok
- open ticket implement-spec-meta-untouched-not-reported covers repeat filing of meta findings on untouched files
- tombstone-box-000982-54d9aac7 names the same empty purpose in tests/unit/test_training_triage_records.py
- tombstone-box-000984-64d4b65f, tombstone-box-000987-32be8c75 and tombstone-box-000989-f97e5fe7 repeat it

Message: box-000993-a6cec97c
