---
id: tombstone-box-000468-7fc958d7
kind: tombstone
link: declined-box-000465-624173ac
reopen_after_days: 30
---
A note from the verdict-decisions-retire-on-resolution Implement run says three status projections keep events from the whole journal without ever dropping old ones: verdict refusals, intake, and reopens. It suggests each may need its own retirement rule, like the one just added for verdict decisions.

Registry record declined-box-000465-624173ac already decided the same observation from the same origin run. That record names `Status.verdict_refusals`, `Status.intake` and `Status.reopens` in `clutch/status.py` `project` as whole-journal retention that may need retirement rules like the one for `verdict_decisions`. This message adds no new evidence: no wrong runtime output, no stale row shown to an operator, and no measured cost. Reopen if a run or operator report shows one of these projections displaying a resolved item as still actionable, or measurably slowing status or snapshot.

- Message origin is verdict-decisions-retire-on-resolution, stage implement, outcome ok, class suggestion, with no report or proposed paths.
- declined-box-000465-624173ac records the same finding from that run: Status.verdict_refusals, Status.intake and Status.reopens keep whole-journal history and may need retirement rules.
- verdict-decisions-retire-on-resolution is in the merged set; no open ticket covers retiring these three projections.

Message: box-000468-7fc958d7
