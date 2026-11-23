---
id: tombstone-box-000999-0a8d34ab
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 30
---
A requisition-contract-review-comparison Implement run that ended ok filed another second problem. It says the repo-wide metadata check flags drift in docs/roadmap.md and an empty purpose in tests/unit/test_training_triage_records.py. The run did not touch either file, and both findings were already on main. The note has no check output and describes no harm to the run.

This is the same repeat filing of pre-existing meta findings on untouched files that the open ticket implement-spec-meta-untouched-not-reported covers. That ticket stops Implement from routing those findings to second_problems. Record 000996 already tombstoned the same report from this same run to that ticket. Reopen if the problem continues after that ticket merges.

- Open ticket implement-spec-meta-untouched-not-reported covers Implement filing pre-existing meta findings on untouched files as second problems.
- tombstone-box-000996-d7dc4bc0 covers the same findings from the same origin run (requisition-contract-review-comparison).
- tombstone-box-000984-64d4b65f, 000987 and 000989 name the identical docs/roadmap.md drift and the empty purpose in test_training_triage_records.py.

Message: box-000999-0a8d34ab
