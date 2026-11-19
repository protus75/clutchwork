---
id: declined-box-000776-d6adbe8e
kind: declined
link: box-000776-d6adbe8e
reopen_after_days: 30
---
The merge-model-resolve Implement run stopped with premise_failed. It reported that the inline merge path, used by drain and run, writes no merge_conflict_facts signal when a rebase conflicts. The conflicting paths are therefore never recorded, so the ticket's evidence about conflict frequency cannot be measured on that path.

This is the same gap that registry record declined-box-000551-06020b1e already decided. Under drain and run, merge.merge calls MergeQueue._admit with conflict_facts=False, so no merge_conflict_facts signal is written. The refusal finding keeps only stderr, which on git 2.43 leaves out the CONFLICT path lines. Only serve journals conflict facts. This message adds only that merge-model-resolve ran into the same gap, which is not a new behavior. Reopen if a run shows that the missing inline conflict facts led to a wrong runtime decision, or if serve also stops recording them.

- message origin merge-model-resolve, stage implement, outcome premise_failed
- registry declined-box-000551-06020b1e: drain/run merge passes conflict_facts=False, so no merge_conflict_facts signal is written and conflict paths are lost
- registry declined-box-000552-06020b1e and tombstone-box-000767-2717edce: the journal holds zero merge_conflict_facts events, the same measurement gap
- unresolvable link: declined-box-000551-06020b1e

Message: box-000776-d6adbe8e
