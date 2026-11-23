---
id: tombstone-box-001023-bab020a9
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 14
---
Second problem filed after the serve-merge-off-exclusive Implement run: the repo-wide metadata check reports existing drift in docs/roadmap.md and an empty purpose in tests/unit/test_training_triage_records.py. The run changed neither file, so both findings were already on main. This is another repeat of the routing that sends meta findings on untouched files to the Suggestion Box.

This is the same repeat filing that open ticket implement-spec-meta-untouched-not-reported covers. That ticket removes the step 5 routing sentence in clutch/specs/implement.md that sends meta findings on untouched files to second_problems. Tombstones 000979-001020 already link the same two files to that ticket, and 001020 comes from this same origin run. Reopen if the ticket merges and Implement keeps filing these findings.

- Open ticket implement-spec-meta-untouched-not-reported names repeat filing of pre-existing repo-wide meta findings on untouched files
- tombstone-box-001020-44d979f0 is the same finding from the same serve-merge-off-exclusive run, linked to that ticket
- tombstone-box-000984, 000987, 000989, 000996, 000999, 001008, 001012 and 001016 report the same two files

Message: box-001023-bab020a9
