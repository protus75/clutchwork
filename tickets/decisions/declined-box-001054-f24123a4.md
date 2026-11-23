---
id: declined-box-001054-f24123a4
kind: declined
link: box-001054-f24123a4
reopen_after_days: 30
---
The note asks the host authoring guide and the requisition review spec to add a grep recipe for tickets that remove or change a function's behavior, such as a timeout, error path, raise or return value. Authors would grep tests/ for every caller of the changed function and fence each test that asserts the old behavior, and review would check that this was done. The trigger was serve-flaky-tests-deterministic, which ended premise_failed on 2026-11-22. The unfenced test test_serve_rig_fakes.py::test_until_translates_timeout asserted the 60s deadline that the ticket removed.

The rule this incident broke already exists. The Scope fence bullet in clutch/docs/host-authoring.md (lines 105-107) says to fence every file the criteria force to change, 'including existing tests whose assertions flip', and to 'grep the repo for each changed name or value'. A removed 60s deadline is a changed value, so the existing grep step covers this case. The message admits the guide already requires this. The cost was one premise_failed bounce on one ticket, and no repeated pattern is shown for behavior changes beyond what the existing bullet covers. Earlier per-case grep-recipe proposals were declined for the same reason: 000619 (removed journal record keys), 000800 (read-only verbs that start writing) and 000555 (deleted symbols). Merged set-membership-fence-closure already added a behavior-change closure to review. Adding another narrow recipe for each kind of change would grow the guide without closing the class. Reopen if two or more further tickets within the window end premise_failed or are Review-snagged because a test pinning a changed value or behavior was left out of the fence, despite the existing changed-name-or-value grep. That would show the current wording does not work and justify a generic caller-closure rule with a lint or review check.

- clutch/docs/host-authoring.md:105-107 already requires fencing 'existing tests whose assertions flip' and grepping 'for each changed name or value'
- Message states 'the guide already says to fence tests whose assertions flip'
- Single incident: serve-flaky-tests-deterministic premise_failed 2026-11-22 (ticket since merged)
- Similar narrow grep-recipe proposals declined: declined-box-000619-dfa19f13, declined-box-000800-3d88a6b2, declined-box-000555-2528178b
- Merged set-membership-fence-closure added a behavior closure for removed or changed runtime behavior (tombstone-box-000328-77e80e58)

Message: box-001054-f24123a4
