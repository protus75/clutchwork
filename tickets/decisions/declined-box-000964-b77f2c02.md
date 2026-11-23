---
id: declined-box-000964-b77f2c02
kind: declined
link: box-000964-b77f2c02
reopen_after_days: 30
---
While implementing spools-onto-evidence-store-r2, the agent found that two planning documents outside its scope fence, docs/roadmap.md and docs/training-data-plan.md, still say the per-attempt spools layout is in use. That change moved per-attempt captures onto the evidence store, so this wording is now out of date.

This is a mismatch between plan wording and the code. It does not show reachable incorrect runtime behavior. Planning documents are not read by the engine, and the registry has consistently declined stale planning-document notes filed from Implement runs (for example declined-box-000447, 000594, 000863 and 000870). The related how-clutch-works.md note was tombstoned to spools-evidence-docs. Neither docs/roadmap.md nor docs/training-data-plan.md is shown to cause a run, gate or agent decision to go wrong. Reopen if an agent or gate is shown to act on the stale spools wording in either document and fail a run because of it.

- Message class suggestion from spools-onto-evidence-store-r2 implement; names only docs/roadmap.md and docs/training-data-plan.md, with no runtime failure.
- Registry precedent: declined-box-000447-54115f00, declined-box-000594-ac4726ce and declined-box-000863-e78bc01b decline stale-plan-document notes left by Implement runs.
- tombstone-box-000963-e6daf0c3 links the docs/how-clutch-works.md part of the same change to spools-evidence-docs; the plan documents named here are not that canonical doc.
- Neighbor index unavailable (index_unreadable); not used as grounds either way.

Message: box-000964-b77f2c02
