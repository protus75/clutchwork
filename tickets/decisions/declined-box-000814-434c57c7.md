---
id: declined-box-000814-434c57c7
kind: declined
link: box-000814-434c57c7
reopen_after_days: 30
---
During the dispatch-during-driver-pass Implement run, the agent found that the planning document docs/roadmap-driver-plan.md still says the roadmap driver attaches only at serve idle points. That change lets dispatch continue during a driver pass, so the description is out of date. The agent could not fix it because the file was outside the ticket's scope fence.

This asks only to fix wording in a planning document. Wrong wording there does not cause any wrong runtime behavior: the engine never reads docs/roadmap-driver-plan.md, and the merged dispatch-during-driver-pass code is what decides behavior. The registry has declined the same kind of stale-plan note several times, including for this same document (box-000526, box-000530, box-000627, box-000630, box-000646) and for this same run against docs/roadmap.md (box-000811). The note does not exactly repeat any one of those records, because it covers a different statement, so it is declined rather than tombstoned. Reopen if an agent or operator acts wrongly because of this stale description, for example a supervising session or Author draft that holds dispatch for a driver pass. Also reopen if the next docs-truth sweep or release audit that covers planning documents leaves the statement in place.

- Message class suggestion, origin dispatch-during-driver-pass, stage implement, outcome ok; proposed_paths is empty
- dispatch-during-driver-pass, dispatch-during-driver-pass-drain and dispatch-during-driver-pass-gate are in the merged set
- declined-box-000811-773ed1cc: the same run's stale-plan note about docs/roadmap.md row 160 was declined
- declined-box-000526/000530/000627/000630/000646: earlier stale-wording notes about docs/roadmap-driver-plan.md were declined

Message: box-000814-434c57c7
