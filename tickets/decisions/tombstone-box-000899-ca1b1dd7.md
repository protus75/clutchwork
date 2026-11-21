---
id: tombstone-box-000899-ca1b1dd7
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 7
---
The index-merge-hook Check stage ended `base_red` because `uv run clutch meta check` also fails on merge base 8c543cf0. The report asks for main to be fixed instead of the ticket, but it names no failing files, gives no finding count and includes no check output.

This is the same report as registry record declined-box-000893-4c8a8e81: `clutch meta check` is red on the base commit because `# clutch:meta` blocks are missing or out of date in files outside the ticket's fence. Records tombstone-box-000894, tombstone-box-000896 (same merge base 8c543cf0) and tombstone-box-000897 already linked later copies of this report to that record. This message adds no file list, no count and no output that would make the base-red failure a bounded repair. Reopen when a report names the files `clutch meta check` flags on current main and includes the check output, or when base_red on meta check blocks a ticket from merging.

- message: class failure_report, origin index-merge-hook, stage check, outcome base_red, merge base 8c543cf0, command `uv run clutch meta check`
- tombstone-box-000896-b1981640: same command and same merge base 8c543cf0, linked to declined-box-000893-4c8a8e81
- tombstone-box-000897-8fe85623: index-merge-hook Implement reported the same meta check failure on its base, linked to declined-box-000893-4c8a8e81
- declined-box-000893-4c8a8e81: meta check red on base, declined for naming no files, no count and no output
- index-merge-hook is in the merged set, so this base_red did not stop the ticket from landing

Message: box-000899-ca1b1dd7
