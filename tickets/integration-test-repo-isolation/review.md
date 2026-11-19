# Review: approve

The diff adds an autouse fixture that moves each integration test into a fresh empty working directory, changes all 18 grep hits in the fenced files to paths anchored on `__file__` (the `parents` depth is correct for each harness module), keeps every assertion unchanged, and adds the one-line rule outside the managed block of both CLAUDE.md and AGENTS.md.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "be7b3b44031aea9401bdce3314c7fe1d9efedaff",
  "stem": "integration-test-repo-isolation",
  "reviewed_sha": "be7b3b44031aea9401bdce3314c7fe1d9efedaff",
  "summary": "The diff adds an autouse fixture that moves each integration test into a fresh empty working directory, changes all 18 grep hits in the fenced files to paths anchored on `__file__` (the `parents` depth is correct for each harness module), keeps every assertion unchanged, and adds the one-line rule outside the managed block of both CLAUDE.md and AGENTS.md.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
