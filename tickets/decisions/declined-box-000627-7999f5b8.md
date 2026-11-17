---
id: declined-box-000627-7999f5b8
kind: declined
link: box-000627-7999f5b8
reopen_after_days: 30
---
After core-template-supervisor-verdicts merged, the implementing run reported that two planning documents, docs/roadmap.md and docs/roadmap-driver-plan.md, still describe the old restriction on what a supervising session may do. The run could not update them because both files were outside its scope fence.

This is stale wording in forward-looking planning documents. The engine does not read these passages at runtime, so no wrong runtime behavior follows from them. The registry has declined the same class many times: out-of-fence planning-doc text left stale by a merged change (000526, 000530, 000533, 000594, 000605, 000621, 000622, 000624). The roadmap driver or the next ticket that edits these documents can refresh the wording. Reopen if a roadmap or driver component is shown to parse or act on this supervisor-restriction text and make a wrong decision because of it.

- Message class suggestion from the core-template-supervisor-verdicts implement stage, outcome ok; core-template-supervisor-verdicts is in the merged set
- The two named files are planning documents; the message cites no runtime path that reads the stale passage
- Prior same-class declines: declined-box-000526-6842d927, declined-box-000530-c9630ad6, declined-box-000621-b11145f0, declined-box-000622-dfa19f13, declined-box-000624-9eb8a90f

Message: box-000627-7999f5b8
