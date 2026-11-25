# Review: approve

The diff adds `_resolve_node_modules` with local-first resolution and a worktree `gitdir:` fallback that tolerates `OSError`, and passes `NODE_PATH` only on the fallback path, so existing callers keep the same `run_cmd` arguments; the new unit tests and regression reproducer cover every criterion and stay inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e75f07a34671ad33e68f14b080af1199f310707a",
  "stem": "ui-bundle-worktree-node-modules",
  "reviewed_sha": "e75f07a34671ad33e68f14b080af1199f310707a",
  "summary": "The diff adds `_resolve_node_modules` with local-first resolution and a worktree `gitdir:` fallback that tolerates `OSError`, and passes `NODE_PATH` only on the fallback path, so existing callers keep the same `run_cmd` arguments; the new unit tests and regression reproducer cover every criterion and stay inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
