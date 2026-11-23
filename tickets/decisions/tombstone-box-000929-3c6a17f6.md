---
id: tombstone-box-000929-3c6a17f6
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
A panel-scorecard suggestion, filed after an Implement run that ended ok, says the repository-wide `clutch meta check` flags metadata findings that already exist in files the change did not touch. It names no file, gives no finding count, includes no check output and does not say how the run was harmed.

Record 000893 already covers this: the repo-wide `clutch meta check` reports `clutch:meta` findings that existed before the run, in files outside the ticket's fence. Records 000894-000927 tombstoned the same report from many other runs. This message adds no file names, no finding count, no output and no harm to its run. Reopen if a report names the failing files and shows a run that failed or was blocked because of findings outside its fence.

- message class suggestion, origin panel-scorecard, stage implement, outcome ok, no report or paths
- declined-box-000893-4c8a8e81 covers repo-wide meta check findings in files outside the fence
- tombstones 000894-000927 link the same repeated report to declined-box-000893-4c8a8e81

Message: box-000929-3c6a17f6
