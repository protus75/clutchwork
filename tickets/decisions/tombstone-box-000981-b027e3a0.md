---
id: tombstone-box-000981-b027e3a0
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 30
---
An Implement run from requisition-review-input-identity ended ok and reported that docs/roadmap.md, a file the change did not touch, has drifted metadata. The drift was already on main. The note includes no check output and describes no harm to the run.

This is another case of Implement sending pre-existing meta check findings on untouched files to the Suggestion Box. Open ticket implement-spec-meta-untouched-not-reported covers exactly that routing, and registry records 000960 to 000980 already tombstoned the same report, including two about the drifted docs/roadmap.md header (000979, 000980).

- message origin requisition-review-input-identity, stage implement, outcome ok
- open ticket implement-spec-meta-untouched-not-reported covers repeat filing of meta findings on untouched files
- tombstone-box-000979-6ebda3c6 and tombstone-box-000980-890a467d report the same docs/roadmap.md drift
- neighbors box-000992, box-001000, box-001003 repeat the same docs/roadmap.md drift note

Message: box-000981-b027e3a0
