---
id: declined-box-000806-30b8e6b0
kind: declined
link: box-000806-30b8e6b0
reopen_after_days: 30
---
A session proposes replacing the rejected chore integration-test-time-cap with several tickets. The first would add a MechanicalCheck.max_test_seconds field and a cap check in stages.py, with soak and fault-injection speedups. Next would come one speedup ticket for each integration test that takes more than about 7 s (shakeout, status scorecard, serve-admission red-streak and host-red, host-loop). A final ticket would set max_test_seconds: 10 in config.yaml. It also proposes an authoring rule: refuse any 'whole suite passes under the new cap' criterion unless every test over the cap is fenced or covered by a dependency.

The message is a re-plan for a rejected P1 chore (tickets/integration-test-time-cap/ticket.md, state: rejected, kind: chore), not a report of a current runtime fault. Slow integration tests only make the suite take longer. They cause no wrong engine behavior, and earlier triage declined the same kind of request (records 000392, 000395, 000438). The proposal is also at least seven tickets in sequence, not one buildable ticket. Its class-prevention rule, which checks a criterion's bound against what the check actually measures, overlaps the authoring-review rule declined in record 000802. Reopen if a reachable harmful outcome is shown, for example Check or merge timing out, or caps being spent because of test duration. Or reopen when the owner asks for the per-test cap feature again: author the mechanism ticket on its own through `clutch ticket new`, with each speedup filed as a separate box message.

- tickets/integration-test-time-cap/ticket.md frontmatter: state: rejected, kind: chore, priority: P1
- max_test_seconds appears only in the rejected ticket and a .claude session note, not in engine code or config
- Prior declines of test-speed requests: declined-box-000392-7c3e7668, declined-box-000395-70ebe69b, declined-box-000438-a10669cb
- Overlapping authoring-rule decline: declined-box-000802-cfb6465b
- The proposal spans a mechanism ticket, five or more speedup tickets and a final config ticket, so it is not one bounded ticket

Message: box-000806-30b8e6b0
