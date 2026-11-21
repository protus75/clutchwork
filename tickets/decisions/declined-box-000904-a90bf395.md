---
id: declined-box-000904-a90bf395
kind: declined
link: box-000904-a90bf395
reopen_after_days: 30
---
The index-box-neighbors-query Implement run (it ended ok) reported that row 187 of the planning document docs/roadmap.md still says open tickets are among the query results. The merged change leaves open tickets out of those results, so the row now disagrees with the code. The run did not fix it because the file was outside its scope fence.

This is a mismatch between a planning document and the code. It causes no incorrect runtime behavior: nothing reads row 187's Content to decide what the neighbors query returns. Registry records 000811, 000822, 000836 and 000903 declined stale roadmap and plan wording for the same reason. Reopen if a roadmap-driven Author draft or a ticket run is shown to build or check the wrong query behavior because of row 187's wording.

- message class suggestion, origin index-box-neighbors-query, stage implement, outcome ok
- index-box-neighbors-query is in the merged set
- declined-box-000811-773ed1cc and declined-box-000822-b85099ea declined similar stale docs/roadmap.md rows reported after a merge

Message: box-000904-a90bf395
