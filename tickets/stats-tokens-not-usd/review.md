# Review: approve

The diff replaces the USD `spend` section with a per-provider and per-surface `usage` section that never sums tokens across providers, handles null token counts, an `unknown` provider and a null per-merge figure, updates the help entry and the pinned integration key list, and adds unit tests covering criteria 1-4, all inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "14bd6343fa6d25254adf92728832ef132fa31f33",
  "stem": "stats-tokens-not-usd",
  "reviewed_sha": "14bd6343fa6d25254adf92728832ef132fa31f33",
  "summary": "The diff replaces the USD `spend` section with a per-provider and per-surface `usage` section that never sums tokens across providers, handles null token counts, an `unknown` provider and a null per-merge figure, updates the help entry and the pinned integration key list, and adds unit tests covering criteria 1-4, all inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
