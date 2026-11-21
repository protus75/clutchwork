---
id: tombstone-box-000894-dbc06b81
kind: tombstone
link: declined-box-000893-4c8a8e81
reopen_after_days: 14
---
The Check stage of index-build-r2 ended base_red because `uv run clutch meta check` also failed on merge base 1ce1e32c. The report asks for main to be fixed rather than the ticket. It does not name the files, the finding count or the check output.

This repeats registry record declined-box-000893-4c8a8e81, which came from the same origin (index-build-r2). That record reported the same `clutch meta check` failure on the base commit, caused by missing or stale `# clutch:meta` blocks outside the ticket's fence, and declined it for lack of detail. This report adds only the stage (check) and the outcome (base_red). It still gives no failing paths or output. index-build-r2 is now merged, so the base-red result no longer blocks that ticket. Reopen if a new ticket run ends base_red on `clutch meta check` and the report names the failing files and the check's printed findings on current main.

- message: class failure_report, origin index-build-r2, stage check, outcome base_red, base 1ce1e32c
- declined-box-000893-4c8a8e81: index-build-r2 reported that `uv run clutch meta check` fails on its base commit because of missing or stale meta blocks outside the fence, with no files or output named
- merged stems include index-build-r2, so the failure is no longer blocking that ticket
- the message names no failing files, finding count or command output

Message: box-000894-dbc06b81
