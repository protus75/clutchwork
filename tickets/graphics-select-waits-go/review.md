# Review: approve

The diff adds `resolve_visual_baseline`, which works the same way as `resolve_baseline`. `check_candidates` now returns `visual_undecided` after the `candidate_paths` refusal and before any judge call, unless the visual baseline is GO for the current identity. The unit, integration and doc changes cover every acceptance criterion and stay inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "279c7ad0b5bdb9e3f05681bf9d1cfc817774affa",
  "stem": "graphics-select-waits-go",
  "reviewed_sha": "279c7ad0b5bdb9e3f05681bf9d1cfc817774affa",
  "summary": "The diff adds `resolve_visual_baseline`, which works the same way as `resolve_baseline`. `check_candidates` now returns `visual_undecided` after the `candidate_paths` refusal and before any judge call, unless the visual baseline is GO for the current identity. The unit, integration and doc changes cover every acceptance criterion and stay inside the fence.",
  "findings": [],
  "spec_version": "1.8",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
