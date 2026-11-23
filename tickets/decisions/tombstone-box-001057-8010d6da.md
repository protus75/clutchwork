---
id: tombstone-box-001057-8010d6da
kind: tombstone
link: reconcile-spares-confirming-draft
reopen_after_days: 30
---
The serve-flaky-tests-deterministic Implement run reports a race: an orphan sweep runs while a draft is being confirmed, sees the confirmation's effect intents with no completion, treats them as an open run and journals the ticket abandoned. In that run the host-loop fixture member was abandoned mid-confirmation.

Merged ticket reconcile-spares-confirming-draft fixes this exact defect. Its Goal says the move of settlement into the Serve.verdicts worker (99c9d7ec) let the idle orphan sweep read apply_admission's open effect intents as orphans and journal `abandoned`. It cites the same serve-flaky-tests-deterministic host-loop observation and box-001062. That ticket makes the sweep skip while settle_admissions is running. Reopen if a stem is reaped `abandoned` during a draft confirmation again after that merge, with journal evidence.

- tickets/reconcile-spares-confirming-draft/ticket.md Goal: an idle sweep inside the apply_admission window reaps the stem and journals `abandoned` with recovery_alert `orphaned run`
- The same ticket cites serve-flaky-tests-deterministic attempt 2, where host-loop fixture member `merge-bonus` was abandoned while its draft was being confirmed
- reconcile-spares-confirming-draft is in the merged stems list

Message: box-001057-8010d6da
