---
id: declined-box-001116-739ec955
kind: declined
link: box-001116-739ec955
reopen_after_days: 30
---
After evidence-never-prunes merged, its Implement run noted that three planning documents outside its scope fence (docs/evidence-trail-plan.md, docs/training-data-plan.md, docs/roadmap.md) still describe the evidence store's old automatic retention or pruning policy.

This is stale wording in forward-looking planning documents. The engine does not read these documents at runtime, so no runtime behavior is wrong. The registry has declined many reports of the same kind: 000447 (the same three documents after provider-capture-overwrite), 000594, 000605, 000856, 000964, 000970 and 001112. Reopen if a stage, gate or prompt reads one of these documents and acts on the old retention text, or if a release audit needs these plan statements to be accurate.

- Message class suggestion, origin evidence-never-prunes, stage implement, outcome ok; the run itself succeeded
- evidence-never-prunes is in the merged set
- The named files are planning documents, and staleness in them causes no runtime defect
- Declined precedents for stale plan documents after a merge: 000447, 000594, 000605, 000856, 000964, 000970, 001112

Message: box-001116-739ec955
