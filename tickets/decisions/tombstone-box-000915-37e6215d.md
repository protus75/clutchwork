---
id: tombstone-box-000915-37e6215d
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
The context-suggest-author-block Check stage ended base_red because `uv run clutch meta check` also fails on merge base f05aa75d. The report asks for main to be fixed instead of the ticket. It does not name a failing file, give a finding count, or include the check output.

Registry record 000893 already covers this report: the repo-wide `clutch meta check` fails on the base because files outside the ticket's fence have missing, drifted or empty-purpose `clutch:meta` blocks, and the report has no file names, finding count or check output. Records 000894-000914 already tombstoned the same base_red report from other merge bases, including 000912 and 000914 from this same origin. The open ticket implement-spec-meta-headers-from-verbs sends meta findings on files outside the diff to `second_problems`. The open ticket diagnose-spec-engine-written-failure-abandons covers failures that engine steps write onto a candidate. Reopen if a report names the failing files and check output and shows that this base debt cost a ticket a cap unit or blocked a merge.

- message: class failure_report, stage check, outcome base_red, origin context-suggest-author-block, merge base f05aa75d; no files, no count, no output
- declined-box-000893-4c8a8e81: same repo-wide `clutch meta check` base failure, declined for lack of named files or harm
- tombstone-box-000894/896/899/902/905/910-*: identical base_red Check reports on other merge bases, all linked to 000893
- tombstone-box-000912-5f8a19d7 and tombstone-box-000914-8a1957d9: same origin context-suggest-author-block, same meta check base debt, linked to 000893
- open ticket implement-spec-meta-headers-from-verbs: routes meta findings on files outside the diff to second_problems

Message: box-000915-37e6215d
