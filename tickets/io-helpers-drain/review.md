# Review: approve

The diff moves every listed helper into tests/drain_helpers.py on top of the shared fakes, points all 57 importers and both hubs at the new module with only import-line edits (plus the engine-written meta headers that the ticket puts in scope), keeps the hub's `Clock` attribute, avoids the test_stages import cycle with a function-level import, and adds the required unit tests.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "0b2c681c5454c9c2a97d1094143421d2d1e31b06",
  "stem": "io-helpers-drain",
  "reviewed_sha": "0b2c681c5454c9c2a97d1094143421d2d1e31b06",
  "summary": "The diff moves every listed helper into tests/drain_helpers.py on top of the shared fakes, points all 57 importers and both hubs at the new module with only import-line edits (plus the engine-written meta headers that the ticket puts in scope), keeps the hub's `Clock` attribute, avoids the test_stages import cycle with a function-level import, and adds the required unit tests.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
