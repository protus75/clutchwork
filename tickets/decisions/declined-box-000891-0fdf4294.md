---
id: declined-box-000891-0fdf4294
kind: declined
link: box-000891-0fdf4294
reopen_after_days: 30
---
The index-build-r2 Implement run, which ended ok, found that docs/annotations-index-plan.md says the index embeds each file's `files.purpose`, while the ticket as built embeds only chunk text. The planning document was outside the ticket's scope fence, so the run left it unchanged.

This is a mismatch between a planning document and the shipped scope. The note shows no wrong runtime behavior: it does not show that leaving `files.purpose` out of the embeddings causes a missed or wrong neighbor in any index consumer. The run ended ok, and nothing shows that a consumer reads embeddings expecting purpose text. Earlier stale-plan-document notes were declined for the same reason (for example declined-box-000797-beddc761 for the same plan, and declined-box-000839-fe115fc6 for a gap between a plan and a ticket). Reopen if an index consumer (box neighbors, the training join, or the implement hint) is shown to return wrong or missing results because purpose text is not embedded, with the query and the expected result.

- Message class suggestion, origin index-build-r2, stage implement, outcome ok
- The message reports only a wording gap between docs/annotations-index-plan.md and the ticket's chunk-text-only embedding, with no failing behavior
- index-build-r2 is in the merged set
- Precedent: declined-box-000797-beddc761 (a stale annotations-index-plan.md statement) and declined-box-000839-fe115fc6 (a gap between a plan and a ticket with no runtime harm)

Message: box-000891-0fdf4294
