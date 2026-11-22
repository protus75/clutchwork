# Review: approve

The diff puts the ticket's exact new rule text in implement.md, retro.md and host-authoring.md, bumps the implement version to 2.26 and retro to 1.7, and updates every pinning test that held the old text or versions; nothing else under tests/ pins them, every changed file is inside the scope fence, and test_stages.py changes only the version string plus its clutch:meta header (Check fills those headers, not the implementer).

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "523ad540417423370e7f5210e8dd27ec0980bd95",
  "stem": "test-io-rules",
  "reviewed_sha": "523ad540417423370e7f5210e8dd27ec0980bd95",
  "summary": "The diff puts the ticket's exact new rule text in implement.md, retro.md and host-authoring.md, bumps the implement version to 2.26 and retro to 1.7, and updates every pinning test that held the old text or versions; nothing else under tests/ pins them, every changed file is inside the scope fence, and test_stages.py changes only the version string plus its clutch:meta header (Check fills those headers, not the implementer).",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
