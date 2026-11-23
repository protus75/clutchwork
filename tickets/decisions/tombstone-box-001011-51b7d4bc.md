---
id: tombstone-box-001011-51b7d4bc
kind: tombstone
link: declined-box-001007-c547823e
reopen_after_days: 30
---
The merge-dirty-checkout-never-blocks run notes that docs/how-clutch-works.md describes how merge treats a dirty main checkout but leaves out the config.yaml exemption that change added. The document was outside the ticket's scope fence, so the run did not edit it.

This repeats a gap that registry record 001007 already declined. That record came from the same run and covers the same document and the same missing config.yaml exemption. Record 001009 already tombstoned an earlier repeat to 001007. The note shows only that one sentence of the docs is stale. It shows no wrong runtime behavior. Reopen if a later run or operator decision goes wrong because it relied on that docs/how-clutch-works.md passage.

- Registry record declined-box-001007-c547823e: same origin run (merge-dirty-checkout-never-blocks), same file docs/how-clutch-works.md, same missing config.yaml exemption.
- Registry record tombstone-box-001009-707a106e already sends a repeat of this gap to 001007.
- The message is a suggestion from an Implement run that ended ok and names no wrong runtime behavior.

Message: box-001011-51b7d4bc
