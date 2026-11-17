---
id: declined-box-000632-454bc6f4
kind: declined
link: box-000632-454bc6f4
reopen_after_days: 30
---
The Roadmap section of the planning document docs/upstream-issue-plan.md (line 13) still names graphics-kind as a 0.5.0 row. The defer-journal-window Implement run made that wording stale but could not fix it because the file was outside its fence.

This is stale wording in a forward-looking planning document. The engine does not read it, so it causes no incorrect runtime behavior. It matches the earlier plan-doc staleness notes that were declined (000526, 000530, 000533, 000594, 000605, 000621, 000622, 000627, 000630). The upstream-issue-verb ticket the plan describes has already merged, so the paragraph is historical sequencing text. Reopen if a roadmap or authoring step is shown to read this line and make a wrong scheduling or budget decision from it.

- docs/upstream-issue-plan.md:13 says `graphics-kind` (0.5.0) adds 9 bytes later, as part of CORE_TEMPLATE budget arithmetic.
- upstream-issue-verb is in the merged set, so the plan's sequencing note no longer drives any pending work.
- Registry records 000621, 000622, 000627 and 000630 declined the same class: stale planning-doc wording reported from an Implement run whose fence excluded the doc.

Message: box-000632-454bc6f4
