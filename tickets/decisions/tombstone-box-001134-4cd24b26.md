---
id: tombstone-box-001134-4cd24b26
kind: tombstone
link: declined-box-001130-6d860266
reopen_after_days: 30
---
The retro-calibration-manual Implement run reported that the planning document docs/roadmap-driver-plan.md (line 42) still says serve runs retros automatically, although that change made retros manual. The file was outside the ticket's scope fence, so the run did not edit it.

Registry record declined-box-001130-6d860266 already covers this report. It comes from the same retro-calibration-manual run, names the same file (docs/roadmap-driver-plan.md) and describes the same out-of-date wording about automatic retros. That record was declined because the file is a forward-looking plan, so stale text in it causes no wrong behavior at runtime. This message adds only a line number. Reopen if a runtime surface (a prompt, a gate or an agent) reads this plan text and acts wrongly because of it.

- declined-box-001130-6d860266: same retro-calibration-manual run, same document docs/roadmap-driver-plan.md, same stale description of retros running automatically
- Message class is suggestion with origin retro-calibration-manual, stage implement, outcome ok; it cites no wrong runtime behavior
- Earlier stale-plan-text reports such as declined-box-000526, 000530 and 000646 were declined for the same reason

Message: box-001134-4cd24b26
