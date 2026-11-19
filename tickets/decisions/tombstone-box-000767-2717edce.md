---
id: tombstone-box-000767-2717edce
kind: tombstone
link: declined-box-000552-06020b1e
reopen_after_days: 30
---
This asks to fix the claim in docs/parallel-tickets-plan.md (lines 29 and 149) that the journal holds 13 merge_conflict_facts events. The merge-model-resolve A0 evidence capture shows there are none; the 13 matches are requisition prose that quotes the signal name.

Record declined-box-000552-06020b1e already covers this: docs/roadmap.md and docs/parallel-tickets-plan.md claim 13 merge_conflict_facts events, the journal holds none, and the matches are requisition_verdict prose. This message adds only a newer base commit and a pointer to the committed A0 evidence file. It is still a plan-document wording mismatch with no runtime effect, because nothing in the engine reads that count. Reopen if a stage, gate, or authoring step is shown to read the stale count and act wrongly on it.

- declined-box-000552-06020b1e: docs/parallel-tickets-plan.md and docs/roadmap.md say the journal holds 13 merge_conflict_facts events; it holds none, and the 13 matches are requisition_verdict prose
- message: docs/parallel-tickets-plan.md:29,149 at base a098b404; tickets/merge-model-resolve/evidence/merge-conflict-facts.md A0 capture shows zero events
- message names no runtime behavior that the stale count changes

Message: box-000767-2717edce
