---
id: tombstone-box-000897-8fe85623
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
The index-merge-hook Implement run, which ended ok, reports that `uv run clutch meta check` fails on its base commit because `# clutch:meta` blocks are missing or out of date in files across the repository. The report does not name the files, give a finding count or include the check output.

This is the same report that registry record declined-box-000893-4c8a8e81 already decided: `clutch meta check` is red on the base commit because of metadata drift outside the ticket's fence. Records tombstone-box-000894-dbc06b81 and tombstone-box-000896-b1981640 already linked two more sightings to that record. This message adds no new evidence: no failing files, no finding count, no check output and no run that the failure cost. Reopen if a report names the failing files and the check output, or shows that a base-red `meta check` cost a ticket a cycle at Check.

- The message is a suggestion from index-merge-hook, stage implement, outcome ok, and it says only that repository-wide metadata drift makes `uv run clutch meta check` fail on the base commit.
- declined-box-000893-4c8a8e81 declined the same report from the index-build-r2 run because it named no files, gave no count and had no check output.
- tombstone-box-000894-dbc06b81 and tombstone-box-000896-b1981640 already linked base-red `meta check` reports from index-build-r2 and index-box-neighbors to declined-box-000893-4c8a8e81.
- The message has empty proposed_paths and a null report, so it carries no evidence beyond the earlier sightings.

Message: box-000897-8fe85623
