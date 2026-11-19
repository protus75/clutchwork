# Review: approve

The diff replaces ConflictHandoff with a merge_conflict_rerun refused result whose writer lifts the non-conflicted diff, journals the signal, retires the branch and worktree through git (remove + prune), writes a conflict_rerun gate_failed terminal that is excluded from retry draws and failed attempts, parks after CONFLICT_RERUN_LIMIT with an operator hold, and updates the docs, the rework spec version and the tests within the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "cd2d4a45138df81e579fb2b9fe79b23643e05107",
  "stem": "conflict-rerun-swap",
  "reviewed_sha": "cd2d4a45138df81e579fb2b9fe79b23643e05107",
  "summary": "The diff replaces ConflictHandoff with a merge_conflict_rerun refused result whose writer lifts the non-conflicted diff, journals the signal, retires the branch and worktree through git (remove + prune), writes a conflict_rerun gate_failed terminal that is excluded from retry draws and failed attempts, parks after CONFLICT_RERUN_LIMIT with an operator hold, and updates the docs, the rework spec version and the tests within the fence.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
