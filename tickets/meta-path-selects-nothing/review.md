# Review: approve

The diff adds a refusal at the top of `_run_meta`: when a named path selects no tracked file under a configured root, the verb prints one `_fail` line per path naming it and `git add -N`, then returns 2 before refresh or check work and before fill's spec load or model call; it also adds the unit test and regression probe covering every acceptance case and updates the three doc rows, all inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "00eb8a5e83419cb4626bbf1abaa0c272dc4fb90c",
  "stem": "meta-path-selects-nothing",
  "reviewed_sha": "00eb8a5e83419cb4626bbf1abaa0c272dc4fb90c",
  "summary": "The diff adds a refusal at the top of `_run_meta`: when a named path selects no tracked file under a configured root, the verb prints one `_fail` line per path naming it and `git add -N`, then returns 2 before refresh or check work and before fill's spec load or model call; it also adds the unit test and regression probe covering every acceptance case and updates the three doc rows, all inside the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
