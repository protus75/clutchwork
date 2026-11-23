---
id: tombstone-box-000996-d7dc4bc0
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
The requisition-contract-review-comparison Implement run ended ok. It filed a second problem saying the repo-wide metadata check flags drift in docs/roadmap.md and an empty purpose in tests/unit/test_training_triage_records.py. The run did not touch either file, and both findings were already on main. The note has no check output and names no harm to the run.

This is another case of the repeat filing that open ticket implement-spec-meta-untouched-not-reported fixes. That ticket stops Implement from sending meta findings on untouched files to second_problems. Records 000984, 000987 and 000989 tombstoned the same two findings to that ticket. Reopen if these findings keep arriving after that ticket merges, or if a run is harmed by them.

- Message origin is requisition-contract-review-comparison, stage implement, outcome ok, so the run was not harmed
- Open ticket implement-spec-meta-untouched-not-reported covers Implement filing pre-existing meta findings on untouched files
- tombstone-box-000984-64d4b65f, tombstone-box-000987-32be8c75 and tombstone-box-000989-f97e5fe7 name the same two files and findings and link to the same ticket

Message: box-000996-d7dc4bc0
