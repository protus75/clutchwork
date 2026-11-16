# Review: approve

The diff deletes Scheduler.active, TicketWriter.active and Serve.mutating, moves the mutation and idle facts onto DaemonAdmission, adds a selection-lock check to upgrade_idle, rewrites every test that read the old fields to read the admission owner (or record the ticket in the dispatch stub), and adds the required unit tests plus the test for the window between selection and admission, all inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "f1242d0d7df854e84e9a037472f351914bc06adb",
  "stem": "active-slot-single-owner",
  "reviewed_sha": "f1242d0d7df854e84e9a037472f351914bc06adb",
  "summary": "The diff deletes Scheduler.active, TicketWriter.active and Serve.mutating, moves the mutation and idle facts onto DaemonAdmission, adds a selection-lock check to upgrade_idle, rewrites every test that read the old fields to read the admission owner (or record the ticket in the dispatch stub), and adds the required unit tests plus the test for the window between selection and admission, all inside the scope fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
