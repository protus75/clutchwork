---
id: tombstone-box-000963-e6daf0c3
kind: tombstone
link: spools-evidence-docs
reopen_after_days: 30
---
During an Implement run of spools-onto-evidence-store-r2, the agent noted that docs/how-clutch-works.md still described per-attempt captures as files under spools/. The message itself says the separate spools-evidence-docs ticket was expected to fix this.

The note asks for the same doc change that ticket spools-evidence-docs was created to make, and that ticket is now in the merged set. On current main, docs/how-clutch-works.md has no mention of `spools/`, so the stale description is gone. Reopen if the document starts describing per-attempt captures as spools/ files again.

- The message names spools-evidence-docs as the ticket expected to fix this doc wording
- spools-evidence-docs is in the merged stems list
- A grep for `spools/` in docs/how-clutch-works.md on current main finds no matches

Message: box-000963-e6daf0c3
