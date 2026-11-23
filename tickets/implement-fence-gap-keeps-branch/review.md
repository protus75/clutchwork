# Review: approve

The diff adds the `fence_gap` marker to `failure_terminal` only under the ticket's exact conditions, extends the Implement keep decision to that terminal (a newer `merge_conflict_rerun` still blocks it), lets `ImplementReply` accept the `fence_gap` code, updates both specs, their version pins and section 4.1 of `docs/how-clutch-works.md`, and covers every acceptance case with tests inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "55684d1b24c4eaa4e670b79780624ddf5a1bb61e",
  "stem": "implement-fence-gap-keeps-branch",
  "reviewed_sha": "55684d1b24c4eaa4e670b79780624ddf5a1bb61e",
  "summary": "The diff adds the `fence_gap` marker to `failure_terminal` only under the ticket's exact conditions, extends the Implement keep decision to that terminal (a newer `merge_conflict_rerun` still blocks it), lets `ImplementReply` accept the `fence_gap` code, updates both specs, their version pins and section 4.1 of `docs/how-clutch-works.md`, and covers every acceptance case with tests inside the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
