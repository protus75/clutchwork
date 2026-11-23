---
id: tombstone-box-001008-9c3b24c7
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
A merge-dirty-checkout-never-blocks Implement run that ended ok filed a second problem: the repo-wide metadata check reports docs/roadmap.md as drifted and tests/unit/test_training_triage_records.py as having an empty purpose. The run did not touch either file, so both findings were already on main. The note has no check output and describes no harm to the run.

This is the same repeat filing that open ticket implement-spec-meta-untouched-not-reported covers. That ticket removes the Implement spec step 5 sentence that sends pre-existing meta findings on untouched files to second_problems. Records 000984, 000987, 000989, 000996 and 000999 already tombstoned the same two files to that ticket. Reopen if these findings keep arriving after that ticket merges.

- Open ticket implement-spec-meta-untouched-not-reported covers repeat filing of repo-wide meta findings on files the diff does not touch
- Records tombstone-box-000984, 000987, 000989, 000996 and 000999 name the same docs/roadmap.md drift and test_training_triage_records.py empty purpose and link to that ticket
- Message origin merge-dirty-checkout-never-blocks, stage implement, outcome ok: no harm to the run reported

Message: box-001008-9c3b24c7
