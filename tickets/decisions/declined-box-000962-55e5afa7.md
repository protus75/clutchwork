---
id: declined-box-000962-55e5afa7
kind: declined
link: box-000962-55e5afa7
reopen_after_days: 30
---
During the serve-confirm-during-check Implement run, the agent noted that the planning document docs/engine-state-db-plan.md says verdict settlement happens as part of merge admission. That change moves verdict settlement out of the exclusive merge poll, so the plan's wording would no longer match the code. The run could not fix the document because it was outside the ticket's scope fence.

This is a mismatch between a planning document's wording and the code. It shows no wrong runtime behavior. Earlier notes of the same kind were declined: stale planning-document wording reported by an Implement run that could not edit an out-of-fence plan (for example records 000811, 000814, 000836, 000930). serve-confirm-during-check has already merged. Reopen if an engine component or prompt reads docs/engine-state-db-plan.md as authority and acts wrongly because of this stale sentence.

- message class suggestion, origin serve-confirm-during-check, stage implement, outcome premise_failed
- serve-confirm-during-check is in the merged set
- the summary describes only stale wording in docs/engine-state-db-plan.md, a planning document, and names no runtime defect
- precedent: declined-box-000811-773ed1cc, declined-box-000814-434c57c7, declined-box-000930-3932a5d2 declined stale plan-doc wording after a merge

Message: box-000962-55e5afa7
