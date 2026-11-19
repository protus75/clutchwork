---
id: declined-box-000836-f2068ed4
kind: declined
link: box-000836-f2068ed4
reopen_after_days: 30
---
During the image-candidates-select-r1 Implement run, which ended ok, the agent noted that the planning document docs/gemini-graphics-refactor-plan.md still describes the earlier design for where image candidates live and how a park is released. The merged change made that description out of date. The run could not update the plan because the file was outside its scope fence.

This is wording drift in a forward-looking planning document. No engine code reads that document, so the stale text causes no incorrect runtime behavior. The registry has declined every similar stale-plan note, including declined-box-000595-5cb94fad about this same document. Planning documents are corrected when a ticket next touches their subject. Reopen if a ticket or Author draft is built from the stale design in docs/gemini-graphics-refactor-plan.md and wrong behavior or a premise failure follows, within 30 days.

- Message class suggestion, origin image-candidates-select-r1, stage implement, outcome ok
- image-candidates-select-r1 is in the merged set
- declined-box-000595-5cb94fad declined a stale-description note for the same plan document
- Registry records 000526, 000530, 000594, 000605, 000646, 000811 and 000814 declined stale planning-doc notes left outside a scope fence

Message: box-000836-f2068ed4
