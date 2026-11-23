---
id: tombstone-box-001009-707a106e
kind: tombstone
link: declined-box-001007-c547823e
reopen_after_days: 30
---
The merge-dirty-checkout-never-blocks Implement run reports that docs/how-clutch-works.md describes how merge handles a dirty checkout and will go out of date after the change, because the ticket left documentation out of scope. Registry record 001007 already covers this same gap from the same run.

This repeats declined record 001007. That record came from the same origin ticket (merge-dirty-checkout-never-blocks) and covers the same gap: docs/how-clutch-works.md does not describe that change's new dirty-checkout behavior, and the run did not edit the doc. That ticket has since merged. A stale design-doc sentence is wording drift with no reachable incorrect runtime behavior. Reopen if a later run or operator decision goes wrong because of that stale description.

- origin merge-dirty-checkout-never-blocks is in the merged set
- declined-box-001007-c547823e: same run, same doc, same dirty-checkout description gap
- message names no runtime failure, only documentation staleness

Message: box-001009-707a106e
