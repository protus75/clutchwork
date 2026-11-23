---
id: declined-box-001021-44ec8a54
kind: declined
link: box-001021-44ec8a54
reopen_after_days: 30
---
The serve-merge-off-exclusive Implement run, which ended ok, reports that the planning document docs/engine-state-db-plan.md still says serve's merge polling enters the admission exclusive section. That change took merge polling out of the exclusive section, so the plan's wording is now stale. The run could not edit the document because it was outside the ticket's scope fence.

This is only a mismatch between a planning document and merged code. The engine does not read docs/engine-state-db-plan.md, so the stale sentence causes no incorrect runtime behavior and no run was harmed. Earlier stale-wording notes about this same plan were declined for the same reason: record 000962 (verdict settlement described as part of merge admission) and record 000986 (scan and watch described as taking the exclusive section). Reopen if a ticket, prompt or gate is shown to read this plan sentence and act wrongly because of it, or if a plan-status sweep ticket for engine-state-db-plan.md is scheduled and needs this line listed.

- message origin serve-merge-off-exclusive, stage implement, outcome ok
- serve-merge-off-exclusive is in the merged set
- declined-box-000986-9d4b6377: same plan doc, stale exclusive-section wording for scan/watch, declined as plan-wording only
- declined-box-000962-55e5afa7: same plan doc, stale verdict-settlement wording, declined
- no runtime reader of docs/engine-state-db-plan.md is cited

Message: box-001021-44ec8a54
