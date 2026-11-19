---
id: tombstone-box-000838-0328f75a
kind: tombstone
link: declined-box-000836-f2068ed4
reopen_after_days: 30
---
After image-embed-presence merged, an Implement note says docs/gemini-graphics-refactor-plan.md still describes the old presence-check design: no model call and a crop at the expected location. The run could not fix the plan document because it was outside the ticket's scope fence.

This repeats record declined-box-000836-f2068ed4, which declined a stale description in the same planning document (docs/gemini-graphics-refactor-plan.md) left behind by a sibling graphics change. Records 000595, 000811 and others declined the same kind of out-of-fence planning-doc wording as well. A planning document is not runtime behavior, so the stale text causes no incorrect engine behavior. Reopen if a ticket or Author run is misled by this document's presence-check description.

- Message class is suggestion, origin image-embed-presence, stage implement, outcome ok
- declined-box-000836-f2068ed4 covers stale design text in docs/gemini-graphics-refactor-plan.md after a merged graphics change
- declined-box-000595-5cb94fad declined stale kind definitions in the same plan document
- image-embed-presence is in the merged set

Message: box-000838-0328f75a
