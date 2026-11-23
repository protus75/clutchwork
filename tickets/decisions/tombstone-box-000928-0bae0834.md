---
id: tombstone-box-000928-0bae0834
kind: tombstone
link: declined-box-000917-8fe3d529
reopen_after_days: 30
---
When requisition review runs as a panel, each member gets its own stuck budget instead of sharing one. The review-panel-stage-use-requisition ticket knowingly left this gap and filed it here.

This is the same gap as registry record declined-box-000917-8fe3d529. That record covers requisition panel members each getting a full REQUISITION_STUCK_S through driver.race, when docs/stage-panels-plan.md says they share one budget. It also notes that the panel ticket chose not to share the budget and sent the gap to the Suggestion Box. This message is that same filing from the same origin ticket. It adds no new incident, such as a panel run that hit a stuck kill, and no measurement. Reopen only if a requisition panel run is shown to exceed the drain ceiling or burn caps because members do not share a budget.

- Message origin review-panel-stage-use-requisition, class suggestion, outcome ok, no report or failure attached
- declined-box-000917-8fe3d529 describes requisition panel members each receiving a full REQUISITION_STUCK_S rather than sharing one budget as docs/stage-panels-plan.md states, and says the panel ticket deferred this to the Suggestion Box
- review-panel-stage-use-requisition is in the merged set

Message: box-000928-0bae0834
