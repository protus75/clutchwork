---
id: tombstone-box-001141-8467ba1c
kind: tombstone
link: declined-box-001130-6d860266
reopen_after_days: 30
---
The retro-calibration-manual run reported that docs/roadmap.md and docs/roadmap-driver-plan.md still say retros and calibration run automatically, even though that change made both manual. The run could not fix either planning document because both were outside its scope fence.

This repeats records 001130 (docs/roadmap-driver-plan.md, automatic retros) and 001131 (docs/roadmap.md, automatic calibration), which already declined the same stale wording from the same run. Tombstones 001134, 001135, 001138 and 001139 also point to those records. The wording is in forward-looking planning documents, so it causes no wrong behavior at runtime. Reopen if code or a gate begins reading these planning documents as authority.

- declined-box-001130-6d860266 covers docs/roadmap-driver-plan.md describing retros as automatic after retro-calibration-manual
- declined-box-001131-43b6d880 covers docs/roadmap.md describing calibration as automatic at the idle point
- tombstones 001134, 001135, 001138 and 001139 already redirect repeat filings from the same run to these records
- message origin is retro-calibration-manual, implement stage, outcome ok

Message: box-001141-8467ba1c
