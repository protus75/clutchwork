---
id: tombstone-box-001040-bbd2205b
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
A regression-command-program-lint Implement run that stopped premise_failed filed a second problem. It says the repo-wide meta check reports empty purposes that were already there in the clutch:meta headers of tests/integration/test_meta_refresh_commit_lock.py and tests/unit/test_training_triage_records.py. The run changed neither file. The note has no check output and does not show that these findings caused the premise failure.

This is the same repeated filing of pre-existing meta findings on untouched files that open ticket implement-spec-meta-untouched-not-reported fixes. That ticket removes the step-5 sentence that sends such findings to second_problems. Record tombstone-box-001037-91379ae2 already linked a report naming these same two files to that ticket. Reopen if the findings still get filed after that ticket merges, or if evidence shows these headers caused a premise failure.

- Open ticket implement-spec-meta-untouched-not-reported covers routing meta findings on untouched files to the Suggestion Box
- tombstone-box-001037-91379ae2 reports the same two files with empty purposes and links to that ticket
- Many earlier tombstones (000982 to 001035) link the empty purpose in tests/unit/test_training_triage_records.py to the same ticket

Message: box-001040-bbd2205b
