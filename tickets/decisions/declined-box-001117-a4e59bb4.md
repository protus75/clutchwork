---
id: declined-box-001117-a4e59bb4
kind: declined
link: box-001117-a4e59bb4
reopen_after_days: 30
---
The engine filed a depends-stage report saying io-helpers-misc was blocked because its dependency io-helpers-loop had been rejected or abandoned, and asked for the ticket to be re-wired, re-scoped or rejected. io-helpers-misc is now in the merged set. io-helpers-loop was rejected, and its work landed as the merged io-helpers-loop-restart, -scheduler, -serve-rig, -terminal and -triage tickets, so nothing is still blocked.

No current failure is left to repair. The blocked dependent, io-helpers-misc, appears in the merged stems, so its dependency edge to the rejected io-helpers-loop was already resolved. Record 001088 says io-helpers-loop is rejected and its work landed as the split io-helpers-loop-* tickets, all of which are merged. This matches earlier depends-stage reports on dependents that later merged (000321, 000327, 001083, 001089), which were all declined. Reopen if some still-open ticket is found that depends on io-helpers-loop.

- io-helpers-misc is in the merged stems list
- io-helpers-loop-restart, io-helpers-loop-scheduler, io-helpers-loop-serve-rig, io-helpers-loop-terminal and io-helpers-loop-triage are all merged
- declined-box-001088-b0177e83 records that io-helpers-loop is state: rejected and its work landed as the split tickets
- declined-box-001089-577f082d declined an earlier depends report for io-helpers-misc after it merged

Message: box-001117-a4e59bb4
