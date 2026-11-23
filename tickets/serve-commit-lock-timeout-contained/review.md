# Review: approve

The diff catches `CommitLockTimeout` only around the real `Serve.scan` intake call. It logs `commit_lock_timeout` with `operation="scan"`, keeps the pending ticket for the next poll and re-raises on ordinary errors or when Serve is stopping, stopping or killing; the tests drive the real `CommitLock` through `intake` → `git.commit`, prove the pending ticket is committed exactly once with another run still active, and confirm that ordinary errors, stop, kill and shutdown are not retried.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "f3fd9236f6648d6cd9ddfa2562e80964052e44f6",
  "stem": "serve-commit-lock-timeout-contained",
  "reviewed_sha": "f3fd9236f6648d6cd9ddfa2562e80964052e44f6",
  "summary": "The diff catches `CommitLockTimeout` only around the real `Serve.scan` intake call. It logs `commit_lock_timeout` with `operation=\"scan\"`, keeps the pending ticket for the next poll and re-raises on ordinary errors or when Serve is stopping, stopping or killing; the tests drive the real `CommitLock` through `intake` → `git.commit`, prove the pending ticket is committed exactly once with another run still active, and confirm that ordinary errors, stop, kill and shutdown are not retried.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
