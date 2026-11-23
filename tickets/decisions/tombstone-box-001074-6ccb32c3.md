---
id: tombstone-box-001074-6ccb32c3
kind: tombstone
link: declined-box-000598-4be912da
reopen_after_days: 14
---
The Check stage for reconcile-spares-confirming-draft ended base_red. The full parallel integration suite run also failed on merge base a84781db, and the report asks for main to be fixed instead of the ticket. It names no failing test and includes no assertion, traceback or output. reconcile-spares-confirming-draft has since merged.

This duplicates declined record 000598: the whole parallel integration suite was base_red on the merge base, and the report names no failing test and gives no output. Records 001033, 001065 and 001072 already tombstoned the same report from other runs. The ticket that filed it has merged, so no run is still blocked. Reopen if a base_red report names the failing integration test and includes its assertion or traceback, or shows a run still blocked.

- message: class failure_report, stage check, outcome base_red, merge base a84781db, no test named, no output
- declined-box-000598-4be912da: whole integration suite base_red, no failing test or output named
- tombstone-box-001033, -001065 and -001072 send the same report to 000598
- reconcile-spares-confirming-draft is in the merged stems list

Message: box-001074-6ccb32c3
