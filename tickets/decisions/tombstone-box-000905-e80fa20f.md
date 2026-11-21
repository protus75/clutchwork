---
id: tombstone-box-000905-e80fa20f
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
The Check stage for index-box-neighbors-query ended base_red. `uv run clutch meta check` also fails on merge base 18f3accc, so the report asks for main to be fixed instead of the ticket. It does not name the failing files, give a finding count, or include the check output.

This is the same failure that registry record declined-box-000893-4c8a8e81 already decided: `clutch meta check` fails on the base commit because `# clutch:meta` blocks are missing or out of date in files outside the ticket's fence. Records 000894, 000896, 000897, 000899, 000901 and 000902 already tombstoned the same report from other runs and bases. This message adds no new evidence: no failing paths, no finding count and no output. Reopen if a report names the files or check output that make the base-red cause actionable as one bounded repair.

- message class failure_report, stage check, outcome base_red, origin index-box-neighbors-query, merge base 18f3accc
- declined-box-000893-4c8a8e81: `uv run clutch meta check` fails on base because of missing or out-of-date `# clutch:meta` blocks outside the fence; no files, count or output given
- tombstone-box-000894/000896/000897/000899/000901/000902 all link the same meta-check base_red report to declined-box-000893-4c8a8e81
- index-box-neighbors-query is in the merged set

Message: box-000905-e80fa20f
