# Review: approve

The diff gives each piece of shared plumbing one definition (lock wrapper, engine-submit helper, observe context builder, config reloader, error printer), moves verbs into grouped handlers behind a dispatch table, keeps the admission order, output text, exit codes and preserved names unchanged, resolves Lockfile from module globals at call time, and adds unit and integration tests that cover every acceptance criterion inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "00565f520715446df747175e0e3e496ed2fbdd8f",
  "stem": "main-verb-groups",
  "reviewed_sha": "00565f520715446df747175e0e3e496ed2fbdd8f",
  "summary": "The diff gives each piece of shared plumbing one definition (lock wrapper, engine-submit helper, observe context builder, config reloader, error printer), moves verbs into grouped handlers behind a dispatch table, keeps the admission order, output text, exit codes and preserved names unchanged, resolves Lockfile from module globals at call time, and adds unit and integration tests that cover every acceptance criterion inside the fence.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
