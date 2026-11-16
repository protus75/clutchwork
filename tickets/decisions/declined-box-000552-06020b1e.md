---
id: declined-box-000552-06020b1e
kind: declined
link: box-000552-06020b1e
reopen_after_days: 21
---
docs/roadmap.md (section 3.3 trigger table line 150 and the parallel A0 agent-task bullet at line 453) and docs/parallel-tickets-plan.md say the journal holds 13 merge_conflict_facts events. The journal holds none. The 13 matches are 2026-10-06/07 requisition_verdict signals whose prose quotes the signal name. The suggestion asks to correct these doc statements before the merge-model-resolve row is authored.

This is a plan and roadmap wording mismatch, and nothing shows it causing wrong runtime behavior. The statements are stale prose in planning documents, and no engine code reads that count. The harm the note predicts is that the roadmap driver's Author drafts merge-model-resolve on a false premise. That path is already corrected. Roadmap row 46's own content cell (line 381) now says to author 'after its agent capture tickets/merge-model-resolve/evidence/merge-conflict-facts.md'. That capture is committed, and its Answer and finding 5 state that the count is 0, that the 13 are requisition_verdict text matches, and where each stale claim sits. The A0 task the line-453 bullet describes is already done. A doc-truth fix fits better as a ticket the operator chooses to write, or as part of whatever ticket next edits these plan documents. Reopen if an authored or drafted merge-model-resolve ticket (or a requisition review of one) cites the 13 events as real conflict data, or bases its bounds on them.

- docs/roadmap.md:150 trigger table cell: '13 events exist; nobody has read them'
- docs/roadmap.md:453 A0 bullet: 'an agent reads the 13 merge_conflict_facts events'
- docs/roadmap.md:381 row 46 content: 'after its agent capture tickets/merge-model-resolve/evidence/merge-conflict-facts.md'
- tickets/merge-model-resolve/evidence/merge-conflict-facts.md Answer and findings 1 and 5: 0 merge_conflict_facts events; the 13 are requisition_verdict signals; it lists each stale doc location
- No engine code consumes the stated count; the mismatch is prose only

Message: box-000552-06020b1e
