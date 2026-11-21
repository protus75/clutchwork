---
id: tombstone-box-000910-d0a219d0
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
A Check stage ended base_red because `uv run clutch meta check` also fails on merge base be8ec7c3. The report asks for main to be fixed rather than the ticket. It names no failing files, gives no finding count and includes no check output.

This is the same repo-wide `clutch meta check` base debt that record declined-box-000893-4c8a8e81 already decided. Records 000894, 000896, 000899, 000902 and 000905 tombstoned the same base_red Check report from other merge bases. The open ticket implement-spec-meta-headers-from-verbs already tells implementers to send meta findings on files outside the diff to second_problems instead of spending calls on them. This report adds only a new merge base sha. Reopen if a report names the failing files and shows that the base meta debt blocked a ticket from merging.

- message: class failure_report, stage check, outcome base_red, base be8ec7c3, no files or output given
- declined-box-000893-4c8a8e81: repo-wide `clutch meta check` fails on base, files unnamed
- tombstone-box-000894/000896/000899/000902/000905: identical base_red meta check reports linked to 000893
- open ticket implement-spec-meta-headers-from-verbs routes base meta findings outside the diff to second_problems

Message: box-000910-d0a219d0
