---
id: tombstone-box-001172-96b8d4e7
kind: tombstone
link: declined-box-000598-4be912da
reopen_after_days: 30
---
The release-audit-070 Check stage ended base_red because the full parallel integration suite run (pytest tests/integration with clutch.testreport, -n auto) also failed on merge base dbc0daaf. The report asks for main to be fixed instead of the ticket. It names no failing test and includes no assertion, traceback or output. release-audit-070 has since merged.

This matches declined record 000598 and its tombstones 001033, 001065, 001072 and 001074. Each is a base_red report from the same whole-suite integration command that names no failing test and gives no output, so this one has no bounded repair either. release-audit-070 is in the merged set, so nothing is still blocked. Reopen if a later base_red report names the failing integration test and includes its assertion or traceback.

- message: class failure_report, stage check, outcome base_red, origin release-audit-070, merge base dbc0daaf, no test name or output
- registry declined-box-000598-4be912da: same whole integration-suite base_red with no failing test named
- registry tombstones 001033, 001065, 001072, 001074 link the same report shape to 000598
- merged stems include release-audit-070

Message: box-001172-96b8d4e7
