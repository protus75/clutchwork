---
id: tombstone-box-000959-46d6716b
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 30
---
An Implement run of engine-state-duckdb-plan that ended ok reports again that the repository-wide metadata check finds missing, drifted or empty-purpose metadata blocks in existing files outside the ticket's fence. It names no file, gives no finding count, includes no check output and describes no harm to the run.

This repeats the pre-existing repo-wide `clutch meta check` debt that registry record 000893 declined, and dozens of later tombstones (000894 to 000957) point to the same record. Open ticket implement-spec-meta-untouched-not-reported already deals with why these reports keep coming back: Implement's step 5 routes findings on untouched files to second_problems. Reopen if a run shows the meta findings on untouched files caused a failed gate or a wrong outcome, or if those findings keep getting filed after implement-spec-meta-untouched-not-reported merges.

- registry record declined-box-000893-4c8a8e81 covers the same repo-wide meta check findings on files outside the fence
- tombstones box-000894 through box-000957 link the same repeated report to 000893
- open ticket implement-spec-meta-untouched-not-reported targets the Implement step 5 routing that files these repeats
- message outcome is ok and it names no file, count, output or harm

Message: box-000959-46d6716b
