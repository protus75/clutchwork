# Review: approve

The diff removes the driver from serve and drain, moves `roadmap.ship` into a gated, locked `clutch release ship` handler, stops re-filing rejected rows (they now appear under `waits:` with their rejection reason), and rewrites the prompts, docs and tests as the ticket's scope requires; it also fixes the prior `clutch release bump --minor` pin.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "69ee0159afaea355fa74d84d0a0e35d77fe34319",
  "stem": "serve-no-roadmap",
  "reviewed_sha": "69ee0159afaea355fa74d84d0a0e35d77fe34319",
  "summary": "The diff removes the driver from serve and drain, moves `roadmap.ship` into a gated, locked `clutch release ship` handler, stops re-filing rejected rows (they now appear under `waits:` with their rejection reason), and rewrites the prompts, docs and tests as the ticket's scope requires; it also fixes the prior `clutch release bump --minor` pin.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
