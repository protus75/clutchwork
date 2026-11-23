---
id: tombstone-box-001139-57de75a4
kind: tombstone
link: declined-box-001131-43b6d880
reopen_after_days: 30
---
Once retro-calibration-manual made calibration a manual step, the planning document docs/roadmap.md still says calibration runs automatically at the engine idle point. The statement is stale plan wording and causes no wrong behavior at runtime.

Registry record declined-box-001131-43b6d880 already decided this same report, which came from the same retro-calibration-manual run, and tombstone-box-001135-b9bf357f already pointed a repeat of it at that record. docs/roadmap.md is a forward-looking planning document, so stale wording in it does not lead to incorrect runtime behavior. Reopen if a stage or verb reads that roadmap sentence and acts on it.

- declined-box-001131-43b6d880: same stale roadmap.md calibration-at-idle-point wording from the retro-calibration-manual run
- tombstone-box-001135-b9bf357f: earlier repeat already tombstoned to 001131
- message origin retro-calibration-manual, stage implement, outcome ok; no runtime harm described

Message: box-001139-57de75a4
