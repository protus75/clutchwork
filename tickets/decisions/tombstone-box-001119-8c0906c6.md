---
id: tombstone-box-001119-8c0906c6
kind: tombstone
link: declined-box-001116-739ec955
reopen_after_days: 30
---
After evidence-never-prunes merged, three planning documents outside its fence (docs/evidence-trail-plan.md, docs/training-data-plan.md, docs/roadmap.md) still describe the evidence store's old evidence.max_gb retention and pruning policy.

Registry record 001116 already decided this same note from the same evidence-never-prunes run: the same three planning documents still describe the old automatic retention or pruning policy. This message adds only the config key name evidence.max_gb. The planning documents are forward-looking plans. Stale wording in them causes no incorrect runtime behavior. Reopen if a stale plan statement leads a ticket or run to reintroduce evidence pruning or to read a removed evidence.max_gb setting.

- message origin evidence-never-prunes, stage implement, outcome ok
- declined-box-001116-739ec955 covers the same three documents and the same retention-policy staleness after evidence-never-prunes
- similar plan-staleness notes were declined in 000447, 000594, 000964 and 000970
- evidence-never-prunes is in the merged set

Message: box-001119-8c0906c6
