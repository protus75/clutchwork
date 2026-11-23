---
id: declined-box-000986-9d4b6377
kind: declined
link: box-000986-9d4b6377
reopen_after_days: 30
---
The serve-scan-watch-off-exclusive Implement run, which ended ok, noted that the planning document docs/engine-state-db-plan.md still says serve's scan and watch publication take the admission exclusive section. That change removed the exclusive section from scan and watch, so the plan wording is now out of date. The run could not fix the document because it was outside the ticket's scope fence.

This is stale wording in a forward-looking planning document. It describes no incorrect runtime behavior and no harm to a run. Registry records declined-box-000962-55e5afa7 (same document, verdict settlement leaving merge admission), 000930, 000978 and many others already declined plan-doc drift reported from out-of-fence Implement runs. Reopen if a ticket, prompt or gate reads docs/engine-state-db-plan.md as authority and acts wrongly because of this sentence, or if a release audit or docs-truth sweep picks up the plan's status sections.

- Message class suggestion, origin serve-scan-watch-off-exclusive, stage implement, outcome ok
- serve-scan-watch-off-exclusive is in the merged set
- declined-box-000962-55e5afa7 declined stale wording in the same docs/engine-state-db-plan.md about admission exclusivity
- declined-box-000930-3932a5d2, declined-box-000978-0f775303 and declined-box-000863-e78bc01b declined the same class of plan-doc staleness

Message: box-000986-9d4b6377
