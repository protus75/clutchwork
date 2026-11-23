---
id: tombstone-box-001022-fa59fd81
kind: tombstone
link: declined-box-001021-44ec8a54
reopen_after_days: 30
---
The serve-merge-off-exclusive Implement run reported that docs/engine-state-db-plan.md, a planning document outside its scope fence, still describes merge admission as running inside the admission exclusive section. That change took merge polling out of the exclusive section, so the plan's wording is now stale. The run could not edit the document.

Registry record declined-box-001021-44ec8a54 already covers this: the same serve-merge-off-exclusive run reported that docs/engine-state-db-plan.md still describes merge polling under the exclusive section, and that record was declined as a stale-plan wording issue. This message reports the same stale document from the same origin, so it is a duplicate. A planning document out of step with merged code causes no wrong runtime behavior. Reopen if a stage or prompt reads docs/engine-state-db-plan.md as authority and acts wrongly because of this wording.

- Message origin serve-merge-off-exclusive, stage implement, summary names docs/engine-state-db-plan.md merge admission exclusion outside the fence
- Registry declined-box-001021-44ec8a54: same run, same document, same stale merge-polling exclusive wording
- Similar stale engine-state-db-plan notes declined-box-000962-55e5afa7 and declined-box-000986-9d4b6377 were also declined as plan-wording only
- serve-merge-off-exclusive is in the merged set

Message: box-001022-fa59fd81
