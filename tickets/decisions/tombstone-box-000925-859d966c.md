---
id: tombstone-box-000925-859d966c
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 30
---
A spools-tests-via-helper-fake-fs Implement run that ended ok repeats that the repo-wide `clutch meta check` flags metadata blocks outside the ticket's fence that were already on the base commit. The run notes the same issue was already filed as box-000924. The report names no file, gives no finding count, includes no check output and does not say how the run was harmed.

This is the same pre-existing repo-wide `clutch:meta` debt report that registry record 000893 declined. Record 000924 already tombstoned it for this same origin, and many other tombstones (000894-000923) link the same report back to 000893. This message adds no new evidence and shows no harm to the run. Reopen if a report names the failing files and the check output, and shows the base-side meta findings causing a run failure.

- Message origin spools-tests-via-helper-fake-fs, stage implement, outcome ok; summary says it was already tracked as box-000924.
- tombstone-box-000924-078b42cc links the same origin's meta-check debt report to declined-box-000893-4c8a8e81.
- declined-box-000893-4c8a8e81 declined the repo-wide meta check base failure because it lacked file names, counts and output.

Message: box-000925-859d966c
