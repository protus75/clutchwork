---
id: tombstone-box-001062-cbf86391
kind: tombstone
link: reconcile-spares-confirming-draft
reopen_after_days: 30
---
This note comes from the serve-flaky-tests-deterministic Implement run. It says startup reconciliation can journal a ticket as abandoned while that ticket's draft confirmation is still running. The sweep sees the confirmation's effect intents with no completion and treats them as an orphaned open run.

This is the same defect as registry record tombstone-box-001057-8010d6da. That record came from the same origin run (serve-flaky-tests-deterministic) and was linked to the merged ticket reconcile-spares-confirming-draft, which stops the orphan sweep from reaping a draft that is still being confirmed. This message brings no new evidence beyond that record. Reopen if a draft is reaped as abandoned during confirmation after reconcile-spares-confirming-draft merged.

- Registry record tombstone-box-001057-8010d6da reports the same race from the same origin run serve-flaky-tests-deterministic and is linked to reconcile-spares-confirming-draft.
- reconcile-spares-confirming-draft is in the merged stems list.
- The message has no reproduction, journal excerpt or new failure after that merge.

Message: box-001062-cbf86391
