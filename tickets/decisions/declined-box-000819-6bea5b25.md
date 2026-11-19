---
id: declined-box-000819-6bea5b25
kind: declined
link: box-000819-6bea5b25
reopen_after_days: 30
---
The conflict-rerun-swap Implement run, which ended ok, reported that line 17 of the planning document docs/parallel-tickets-plan.md still describes the Rework handoff that its change removed. The run could not fix the line because the file was outside its scope fence.

The report is about one stale sentence in a planning document. Planning documents are not read by the engine at runtime, so no current behavior is wrong and nothing reachable is harmed. The registry has repeatedly declined the same kind of out-of-fence planning-doc staleness note: 000811, 000814, 000646, 000652, 000656, 000621 and 000622. Any later ticket that edits docs/parallel-tickets-plan.md, or a release audit, can fix the wording. Reopen if an Author draft, requisition review or Implement run is misled by this stale Rework handoff description into a wrong fence, premise or design and spends a run cycle because of it.

- Message class suggestion, origin conflict-rerun-swap, stage implement, outcome ok: the run itself succeeded.
- conflict-rerun-swap is in the merged set; the note only flags out-of-fence doc wording made stale by that change.
- Prior registry records 000811, 000814, 000646, 000652, 000656, 000621 and 000622 declined the same kind of stale planning-document note.
- No runtime code path reads docs/parallel-tickets-plan.md, so there is no reachable incorrect behavior.

Message: box-000819-6bea5b25
