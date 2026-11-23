---
id: tombstone-box-000919-dbae1952
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
The Check stage for requisition-review-tool-output-evidence ended base_red because `uv run clutch meta check` also fails on merge base 512e4a26. The report asks for main to be fixed instead of the ticket. It names no failing file, gives no finding count and includes no check output.

This is the same base-side `clutch meta check` failure that registry record 000893 declined. Records 000894, 000896, 000899, 000902, 000905, 000910 and 000915 already tombstoned the same base_red report from other Check stages. Record 000918 tombstoned the Implement-side report from this same origin. This message adds only a new merge-base SHA, with no file, count or output. Reopen if a report names the failing files or gives the check output and shows that the base debt is still present and blocking merges.

- message: class failure_report, stage check, outcome base_red, origin requisition-review-tool-output-evidence, base 512e4a26
- declined-box-000893-4c8a8e81: repo-wide `clutch meta check` fails on base; no files or output given
- tombstone-box-000915-37e6215d and earlier tombstones: same base_red Check report on other bases
- tombstone-box-000918-01a51b53: same origin, Implement-side report of the same meta debt

Message: box-000919-dbae1952
