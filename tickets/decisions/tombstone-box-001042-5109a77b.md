---
id: tombstone-box-001042-5109a77b
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
After the check-rerun-failed-only Implement run ended ok, it filed a second problem. The repo-wide metadata check reports empty purposes in the clutch:meta headers of tests/integration/test_meta_refresh_commit_lock.py and tests/unit/test_training_triage_records.py. The run did not change either file. The note includes no check output and describes no harm to the run.

This is the same repeated filing of pre-existing meta findings on untouched files that open ticket implement-spec-meta-untouched-not-reported fixes. That ticket changes how step 5 of the Implement spec routes such findings. Records 001037, 001040 and 001041 already tombstoned the same two files to that ticket. Reopen if these filings continue after that ticket merges.

- Open ticket implement-spec-meta-untouched-not-reported covers sending meta findings on untouched files to the Suggestion Box as second problems
- tombstone-box-001037-91379ae2, tombstone-box-001040-bbd2205b and tombstone-box-001041-8ec0ae01 name the same two files and point to the same ticket
- The message has origin check-rerun-failed-only, outcome ok, and names no harm to the run

Message: box-001042-5109a77b
