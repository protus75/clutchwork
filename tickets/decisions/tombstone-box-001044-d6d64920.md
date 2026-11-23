---
id: tombstone-box-001044-d6d64920
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
An Implement run of check-rerun-failed-only filed a second problem again: the repo-wide metadata check reports empty purposes that were already in the clutch:meta headers of tests/integration/test_meta_refresh_commit_lock.py and tests/unit/test_training_triage_records.py. The run changed neither file. The note has no check output and describes no harm to the run.

This is the same repeated filing of pre-existing meta findings on untouched files that open ticket implement-spec-meta-untouched-not-reported covers. Registry records 001037, 001040, 001041 and 001042 already tombstoned the same two files and the same finding to that ticket, and 001041 and 001042 came from this same origin, check-rerun-failed-only. Reopen if the files are still flagged after that ticket merges and a run shows real harm from the findings.

- message origin check-rerun-failed-only, stage implement, outcome ok, names the same two empty-purpose files
- tombstone-box-001042-5109a77b: same origin, same two files, linked to implement-spec-meta-untouched-not-reported
- tombstone-box-001037-91379ae2 and tombstone-box-001040-bbd2205b: same findings, same link
- open ticket implement-spec-meta-untouched-not-reported covers routing meta findings on untouched files to second_problems

Message: box-001044-d6d64920
