# Review: approve

The diff moves the supervisor step into `supervise_step` and `record_supervisor_keep` without changing `failure_terminal` order, adds the `sup`-scoped idle selector with git-only worktree cleanup and lazy prepare in both the serve and drain hooks, updates the named doc statements, and the new tests cover each acceptance criterion with fakes and `tmp_path` only.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "460a4a6402891c771f8d5886b79dcba718a2edfa",
  "stem": "supervise-at-idle-point",
  "reviewed_sha": "460a4a6402891c771f8d5886b79dcba718a2edfa",
  "summary": "The diff moves the supervisor step into `supervise_step` and `record_supervisor_keep` without changing `failure_terminal` order, adds the `sup`-scoped idle selector with git-only worktree cleanup and lazy prepare in both the serve and drain hooks, updates the named doc statements, and the new tests cover each acceptance criterion with fakes and `tmp_path` only.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
