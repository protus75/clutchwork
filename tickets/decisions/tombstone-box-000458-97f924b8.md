---
id: tombstone-box-000458-97f924b8
kind: tombstone
link: declined-box-000456-99370dbf
reopen_after_days: 30
---
During its Implement run, the merged dev-py-dev-tasks-only ticket noted that some forward-looking plan documents outside its fence still propose `./dev.py` launcher twins for engine verbs that are not built yet. It asked for a follow-up to bring those documents in line with the new rule.

Registry record declined-box-000456-99370dbf already decided this gap. It covers the same plan documents that propose `./dev.py` twins for planned verbs, such as `./dev.py training-export` in docs/training-data-plan.md and `./dev.py release` in docs/roadmap-driver-plan.md, which conflict with the merged dev-py-dev-tasks-only rule. This message has the same origin and makes the same request. It adds no new evidence of runtime harm, because these are unbuilt plans and not code an agent or operator runs today. Reopen if a ticket built from one of those plans adds a `dev.py` engine-verb twin, or if the record is reopened.

- Message origin is dev-py-dev-tasks-only, stage implement, outcome ok; it reports only out-of-scope plan documents.
- declined-box-000456-99370dbf records the same gap: plan documents (docs/training-data-plan.md, docs/roadmap-driver-plan.md) still propose ./dev.py launcher twins for unbuilt engine verbs, contradicting the merged dev-py-dev-tasks-only rule.
- No open ticket or new incident shows a runtime failure caused by those plan documents.

Message: box-000458-97f924b8
