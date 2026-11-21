# Review: approve

The diff adds lock-free work checks to the scan, watch, merge, and box-intake polls; it matches each work condition the ticket specifies (including the mirrored `settle_admissions` predicate, paused-queue exclusion, HEAD- and pending-state-aware scan snapshot, and 30-second failed-arrival retry), moves `check_upgrade` outside `mutations()` as the ticket allows, updates section 7.2 of `docs/how-clutch-works.md`, and adds the required unit, integration, and regression tests inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e9e2c8ccdbbd3a95576506e457444b6429936b7f",
  "stem": "serve-polls-block-parallel-runs",
  "reviewed_sha": "e9e2c8ccdbbd3a95576506e457444b6429936b7f",
  "summary": "The diff adds lock-free work checks to the scan, watch, merge, and box-intake polls; it matches each work condition the ticket specifies (including the mirrored `settle_admissions` predicate, paused-queue exclusion, HEAD- and pending-state-aware scan snapshot, and 30-second failed-arrival retry), moves `check_upgrade` outside `mutations()` as the ticket allows, updates section 7.2 of `docs/how-clutch-works.md`, and adds the required unit, integration, and regression tests inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
