---
id: declined-box-000594-ac4726ce
kind: declined
link: box-000594-ac4726ce
reopen_after_days: 30
---
The evidence-envelope Implement run reported that two planning documents outside its scope fence, docs/training-data-plan.md and docs/evidence-trail-plan.md, still describe the provider capture writer as current behavior. The evidence-envelope change removed that writer.

This is a mismatch between planning-document wording and the code. It does not cause any incorrect runtime behavior: the engine does not read or run these plan documents, so the stale text cannot make a run, gate, or stage misbehave. The registry has declined the same kind of report before. Record 000447 covered the same two plan documents describing provider-capture behavior that a merged ticket had changed, and records 000526, 000530 and 000533 covered other plan documents left stale by fenced Implement runs. Reopen if an authoring or Implement run is shown to follow the stale plan text into a wrong ticket or diff, or if a host guide or engine-rendered prompt starts embedding these documents.

- Message class suggestion, origin evidence-envelope, stage implement, outcome ok: the run finished and only flagged documents outside its fence.
- evidence-envelope is in the merged set, so the plan documents now describe code that has changed.
- declined-box-000447-54115f00 declined the same documents (docs/evidence-trail-plan.md, docs/training-data-plan.md) for stale present-tense descriptions of provider capture.
- declined-box-000526-6842d927 and declined-box-000530-c9630ad6 declined stale plan-document wording that Implement runs reported from outside their fences.

Message: box-000594-ac4726ce
