---
id: declined-box-001052-2a15d17a
kind: declined
link: box-001052-2a15d17a
reopen_after_days: 30
---
The check-owns-meta-headers Implement run, which ended ok, reported that the planning document docs/annotations-index-plan.md still describes how the metadata gate worked before that change. The run could not update the document because it was outside the ticket's scope fence.

This only reports a planning document that no longer matches the code. It names no wrong runtime behavior, and no run was harmed. Registry records 000797, 000870, 000891, 000898 and 000978 declined the same kind of stale-plan wording in docs/annotations-index-plan.md, and many other records declined the same kind of note for other plan documents. A plan-wording mismatch is declined unless it leads to incorrect runtime behavior. Reopen if an agent or a gate acts on the stale description in docs/annotations-index-plan.md and that causes a failed or misrouted run.

- message class suggestion, origin check-owns-meta-headers, stage implement, outcome ok
- declined-box-000797-beddc761, declined-box-000870-94229987, declined-box-000891-0fdf4294, declined-box-000898-9929dabd and declined-box-000978-0f775303 declined stale wording in docs/annotations-index-plan.md
- check-owns-meta-headers is in the merged set

Message: box-001052-2a15d17a
