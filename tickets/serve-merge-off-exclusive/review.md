# Review: approve

The diff adds a `merging()` admission section that waits only for exclusive holders, sets `mutating`, and keeps `busy()` true while held; it moves `Serve.merge` onto that section, takes the commit lock in `dirty_overlap`, updates section 7.2 of the docs, gives the four stand-in fixtures reusable locks and changes only the confirm-during-check wait. The new unit, integration and regression tests can fail on the defects they target, and every acceptance criterion is met inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "fd62a5ac04db343eb3778d93ca6ac893edaf4cbf",
  "stem": "serve-merge-off-exclusive",
  "reviewed_sha": "fd62a5ac04db343eb3778d93ca6ac893edaf4cbf",
  "summary": "The diff adds a `merging()` admission section that waits only for exclusive holders, sets `mutating`, and keeps `busy()` true while held; it moves `Serve.merge` onto that section, takes the commit lock in `dirty_overlap`, updates section 7.2 of the docs, gives the four stand-in fixtures reusable locks and changes only the confirm-during-check wait. The new unit, integration and regression tests can fail on the defects they target, and every acceptance criterion is met inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
