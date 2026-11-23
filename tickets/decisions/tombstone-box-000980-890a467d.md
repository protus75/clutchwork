---
id: tombstone-box-000980-890a467d
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 30
---
A training-triage-records Implement run that ended ok reports that the metadata header in docs/roadmap.md is drifted. That file was outside the run's change and the drift was already on main. The report includes no check output and describes no harm to the run.

This is the same repeated filing of existing repo-wide `clutch meta check` findings on files a diff does not touch. The open ticket implement-spec-meta-untouched-not-reported covers it: that ticket stops Implement from sending these findings to second_problems. Record tombstone-box-000979-6ebda3c6 already tombstoned an almost identical docs/roadmap.md drift report to that ticket. Reopen this if the drift on docs/roadmap.md is shown to break a gate or a run after that ticket merges. One case would be the roadmap accept commit path skipping meta refresh, but that is a separate cause.

- Message: class suggestion, stage implement, outcome ok, origin training-triage-records, no report or proposed paths
- Open ticket implement-spec-meta-untouched-not-reported: Implement files existing meta findings on untouched files to second_problems
- tombstone-box-000979-6ebda3c6: same docs/roadmap.md drifted report, linked to implement-spec-meta-untouched-not-reported
- Neighbors box-000981, box-000992 and box-001000 repeat the same docs/roadmap.md drift note

Message: box-000980-890a467d
