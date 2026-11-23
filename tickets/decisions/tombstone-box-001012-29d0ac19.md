---
id: tombstone-box-001012-29d0ac19
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
The merge-dirty-checkout-never-blocks Implement run ended ok and filed another second problem. It says the repo-wide metadata check reports docs/roadmap.md as drifted and tests/unit/test_training_triage_records.py as having an empty purpose. The run did not change either file, so both findings were already on main. The note has no check output and describes no harm to the run.

This repeats a filing that the open ticket implement-spec-meta-untouched-not-reported already covers. Step 5 of the Implement spec sends pre-existing meta findings on untouched files to second_problems, and that is why these duplicate box messages keep arriving. Registry record tombstone-box-001008-9c3b24c7 already tombstoned the same two findings from this same run, and records 000984 to 001004 tombstoned the same pair from other runs. Reopen if the open ticket merges and Implement replies still file meta findings on untouched files.

- open ticket implement-spec-meta-untouched-not-reported covers Implement filing pre-existing repo-wide meta findings on untouched files as second problems
- tombstone-box-001008-9c3b24c7: same origin (merge-dirty-checkout-never-blocks), same two files and findings, linked to implement-spec-meta-untouched-not-reported
- tombstone-box-000984, 000987, 000989, 000996, 000999: same docs/roadmap.md drift and test_training_triage_records.py empty-purpose pair, from other runs
- message outcome ok; no harm or check output reported

Message: box-001012-29d0ac19
