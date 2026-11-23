---
id: tombstone-box-000987-32be8c75
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
The serve-scan-watch-off-exclusive Implement run ended ok and filed another second problem: the repo-wide metadata check reports drift in docs/roadmap.md and an empty purpose in tests/unit/test_training_triage_records.py. The run did not touch either file, and both findings were already on main. The note includes no check output and describes no harm to the run.

This is the same repeated filing of pre-existing meta findings on untouched files that open ticket implement-spec-meta-untouched-not-reported fixes. That ticket stops Implement from routing such findings to second_problems. Record tombstone-box-000984-64d4b65f already linked an identical report from this same run, with the same two files, to that ticket. Reopen if these findings keep arriving after that ticket merges.

- open ticket implement-spec-meta-untouched-not-reported covers repeat Implement filings of pre-existing repo-wide meta check findings on untouched files
- tombstone-box-000984-64d4b65f: same origin serve-scan-watch-off-exclusive, same docs/roadmap.md drift and test_training_triage_records.py empty purpose
- tombstone-box-000980-890a467d and tombstone-box-000982-54d9aac7 cover the same two files individually

Message: box-000987-32be8c75
