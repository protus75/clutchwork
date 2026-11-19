---
id: declined-box-000797-beddc761
kind: declined
link: box-000797-beddc761
reopen_after_days: 30
---
During the journal-duckdb-cache Implement run, the agent noted that the planning document docs/annotations-index-plan.md still calls DuckDB a future dependency that another ticket will add. journal-duckdb-cache has since merged and added DuckDB. The run could not update the plan because the file was outside its scope fence.

This is a wording mismatch in a forward-looking planning document. No code reads docs/annotations-index-plan.md, so the stale sentence causes no incorrect runtime behavior. The registry has already declined the same kind of report many times: stale plan-document wording left behind by a merged change that could not edit the file. Examples are records 000526, 000530, 000594, 000605, 000616, 000621, 000646 and 000652. Reopen if a ticket, prompt or authoring run is shown to act wrongly because this plan still treats DuckDB as unbuilt, for example an Author draft that adds DuckDB again or fences work that already exists.

- Message class suggestion, origin journal-duckdb-cache, stage implement, outcome ok: the run succeeded and the note concerns only a document outside its fence.
- journal-duckdb-cache and snapshot-from-duckdb-cache are both in the merged set, so DuckDB is already a dependency in the code.
- Decision records 000526, 000530, 000594, 000605, 000616, 000621, 000646 and 000652 declined the same pattern of stale plan wording outside a run's fence.

Message: box-000797-beddc761
