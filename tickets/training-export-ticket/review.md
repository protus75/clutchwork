# Review: approve

The diff adds the opt-in `ticket` export kind as specified: it picks the highest-ordered author call for each stem (from `_calls`' sorted order), builds the reply from assistant `message` events (Gemini fragments joined, Claude/Codex last event), maps `source` through the canonical `Source` type (which fixes the prior finding), skips and counts bad calls, applies the `_safe` scrub, holdout and `since` filters, makes `report` read `counts['ticket']` directly, keeps the four-entry default `--kinds`, updates both doc rows, and has tests covering every acceptance criterion inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e3a32a725a14c1477aa00de473beecfe2e7a66f5",
  "stem": "training-export-ticket",
  "reviewed_sha": "e3a32a725a14c1477aa00de473beecfe2e7a66f5",
  "summary": "The diff adds the opt-in `ticket` export kind as specified: it picks the highest-ordered author call for each stem (from `_calls`' sorted order), builds the reply from assistant `message` events (Gemini fragments joined, Claude/Codex last event), maps `source` through the canonical `Source` type (which fixes the prior finding), skips and counts bad calls, applies the `_safe` scrub, holdout and `since` filters, makes `report` read `counts['ticket']` directly, keeps the four-entry default `--kinds`, updates both doc rows, and has tests covering every acceptance criterion inside the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
