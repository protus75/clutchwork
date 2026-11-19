# Review: approve

The diff moves the dependency-done test out of `choose` into a shared `unfinished_dependency` helper without changing what it decides, calls that helper and `depends_on` in the rejected-row loop before the re-file cap check, writes `waits:` lines for unfinished dependencies and for a malformed Depends on cell, and adds a new test file covering the unsettled, settled (journal and struck) and malformed cases, with all changes inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "2fb71d8beaed20dfd35633c27b2bcaad3d4ecbea",
  "stem": "roadmap-refile-waits-for-depends",
  "reviewed_sha": "2fb71d8beaed20dfd35633c27b2bcaad3d4ecbea",
  "summary": "The diff moves the dependency-done test out of `choose` into a shared `unfinished_dependency` helper without changing what it decides, calls that helper and `depends_on` in the rejected-row loop before the re-file cap check, writes `waits:` lines for unfinished dependencies and for a malformed Depends on cell, and adds a new test file covering the unsettled, settled (journal and struck) and malformed cases, with all changes inside the scope fence.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
