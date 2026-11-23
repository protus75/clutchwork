---
id: tombstone-box-001005-ea72dc18
kind: tombstone
link: declined-box-000962-55e5afa7
reopen_after_days: 30
---
A serve-confirm-during-check Implement run that ended ok repeats that docs/engine-state-db-plan.md still says verdict settlement happens under the merge gate. That change moved settlement out of the exclusive merge poll. The message says it repeats box-000962, which registry record 000962 already declined.

This is the same stale planning-document wording that record declined-box-000962-55e5afa7 settled. Record tombstone-box-001002-4d7f7003 already tombstoned an earlier repeat from the same run. It is only a plan-wording mismatch with no reachable incorrect runtime behavior. Reopen if the stale plan text is shown to mislead a ticket or a run into wrong behavior.

- Registry declined-box-000962-55e5afa7 covers the same stale statement in docs/engine-state-db-plan.md about verdict settlement under merge admission.
- Registry tombstone-box-001002-4d7f7003 tombstoned an identical repeat from the serve-confirm-during-check run.
- The message itself states it was previously filed as box-000962.

Message: box-001005-ea72dc18
