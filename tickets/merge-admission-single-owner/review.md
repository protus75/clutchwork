# Review: approve

The diff turns merge.merge into a thin call to MergeQueue._admit and keeps inline behavior the same: a plain rebase that refuses on any failure, unscoped CHECK_GATES, hard-only host checks spooled to merge/host-NN.txt, no conflict facts, no receipt or tree check, and squash plus retire; it also gathers safety evidence once, adds the single artifacts.refused constructor at every listed site, removes the served_review exception swallow, and adds the required tests and doc line inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "a1d9d8c14329c2b2820e21cc6821eea750adda0a",
  "stem": "merge-admission-single-owner",
  "reviewed_sha": "a1d9d8c14329c2b2820e21cc6821eea750adda0a",
  "summary": "The diff turns merge.merge into a thin call to MergeQueue._admit and keeps inline behavior the same: a plain rebase that refuses on any failure, unscoped CHECK_GATES, hard-only host checks spooled to merge/host-NN.txt, no conflict facts, no receipt or tree check, and squash plus retire; it also gathers safety evidence once, adds the single artifacts.refused constructor at every listed site, removes the served_review exception swallow, and adds the required tests and doc line inside the fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
