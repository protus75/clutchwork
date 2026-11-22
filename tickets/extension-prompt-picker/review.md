# Review: approve

The diff adds `prompt_pick` built from `ask.catalog` and merges it into the snapshot through an unconditional `load_config`; it registers `clutch.askPrompt` in package.json, help.py and extension.js using only snapshot fields, updates the docs paragraph, gives each snapshot fixture a readable config, and adds a unit test that covers every acceptance criterion, all inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "4624b2d10ea2528e6a7913490e25928d31834fe7",
  "stem": "extension-prompt-picker",
  "reviewed_sha": "4624b2d10ea2528e6a7913490e25928d31834fe7",
  "summary": "The diff adds `prompt_pick` built from `ask.catalog` and merges it into the snapshot through an unconditional `load_config`; it registers `clutch.askPrompt` in package.json, help.py and extension.js using only snapshot fields, updates the docs paragraph, gives each snapshot fixture a readable config, and adds a unit test that covers every acceptance criterion, all inside the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
