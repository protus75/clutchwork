---
id: tombstone-box-000979-6ebda3c6
kind: tombstone
link: implement-spec-meta-untouched-not-reported
reopen_after_days: 30
---
A boundary-contract-outcome-compare Implement run that ended ok reports that the repo-wide metadata check flags docs/roadmap.md as drifted. That file is outside the ticket's scope fence, so the finding was already on main and the change did not cause it. The report gives no check output and describes no harm to the run.

This is the same repeat filing that open ticket implement-spec-meta-untouched-not-reported covers. Step 5 of clutch/specs/implement.md sends meta findings on untouched files to second_problems, so every run files existing repo-wide `clutch meta check` debt to the Box again. Records 000960 through 000977 already tombstoned these repeats against that ticket. This message names one file but is otherwise the same: the drift is in a file the diff did not touch, and the run ended ok. Reopen if a run is shown to fail or be blocked because of this drift in an untouched file.

- message: class suggestion, stage implement, outcome ok, origin boundary-contract-outcome-compare; docs/roadmap.md reported drifted and outside the scope fence
- open ticket implement-spec-meta-untouched-not-reported covers the routing of untouched-file meta findings to second_problems
- tombstone records 000960, 000965, 000968, 000972, 000973, 000976, 000977 link the same repeat filing to that ticket
- check-owns-meta-headers merged: Check refreshes headers on changed files, so drift on untouched files does not affect the run

Message: box-000979-6ebda3c6
