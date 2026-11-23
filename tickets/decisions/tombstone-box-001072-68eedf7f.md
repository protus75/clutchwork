---
id: tombstone-box-001072-68eedf7f
kind: tombstone
link: declined-box-000598-4be912da
reopen_after_days: 30
---
Check for serve-live-keep-single-verdict ended base_red because the whole parallel integration suite run (`pytest tests/integration -p clutch.testreport ... -n auto`) also failed on merge base a2600ead. The report asks for main to be fixed, not the ticket. It names no failing test and includes no assertion, traceback or output. serve-live-keep-single-verdict has since merged.

This is the same kind of report that record 000598 already declined: a whole-suite integration base_red that names no test and gives no output. Records 001033 and 001065 tombstoned later copies of it against 000598. The known intermittent integration failures on these bases already have registry records or merged fixes: serve-admission timeouts (000983), host-loop fixture ordering (000703), and the duplicate keep verdict fixed by serve-live-keep-single-verdict. The origin ticket has merged, so no run is blocked. Reopen if a base_red report names a specific failing integration test, with output, that is not already covered by those records.

- message: class failure_report, stage check, outcome base_red, merge base a2600ead, no test named, no output
- declined-box-000598-4be912da: the same whole-integration-suite base_red with no failing test named
- tombstone-box-001033-88380fca and tombstone-box-001065-fc96f8c2 tombstoned the same report shape against 000598
- serve-live-keep-single-verdict is in the merged stems

Message: box-001072-68eedf7f
