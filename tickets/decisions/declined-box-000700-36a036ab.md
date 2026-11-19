---
id: declined-box-000700-36a036ab
kind: declined
link: box-000700-36a036ab
reopen_after_days: 30
---
After plan-drain-author-in-parallel merged, the supervising-loop description in docs/how-clutch-works.md may still leave out two things that change added: when drafts are authored, and that roadmap_row drafts are excluded. The Implement run could not update the doc because the file was outside its scope fence.

This only reports documentation wording that a merged change may have made stale. It shows no runtime behavior that is wrong. The registry has repeatedly declined stale-doc notes from runs whose fence left the doc out, for example 000403 (also about docs/how-clutch-works.md), 000526, 000530 and 000646, because they name no harmful behavior gap. The supervising process is defined by the shipped prompts in clutch/specs/ask/, not by this description, so the stale prose does not change how a supervising agent acts. Reopen if a supervising session or ticket run is shown to have acted wrongly because it followed the outdated description in docs/how-clutch-works.md.

- Message class suggestion, origin plan-drain-author-in-parallel, stage implement, outcome ok: the run finished ok and only flagged an out-of-fence doc.
- plan-drain-author-in-parallel is in the merged set.
- Registry precedents declined-box-000403-d925564b, declined-box-000526-6842d927, declined-box-000530-c9630ad6 and declined-box-000646-618509dc declined the same kind of out-of-fence stale-doc report.
- The message cites no run or operator decision that went wrong because of the doc text.

Message: box-000700-36a036ab
