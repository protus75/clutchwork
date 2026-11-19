# Review: approve

The diff adds `--allow-build` to the pnpm argv, refuses with exit 2 when a named install's CLI prints no version, updates the help exit text, and adds the required unit test and carried reproducer; it stays inside the fence and fixes the prior finding by patching `Path.is_file`.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "f382715bd0ce231268fac4f464f8b008e887d8b8",
  "stem": "provider-install-verifies-binary",
  "reviewed_sha": "f382715bd0ce231268fac4f464f8b008e887d8b8",
  "summary": "The diff adds `--allow-build` to the pnpm argv, refuses with exit 2 when a named install's CLI prints no version, updates the help exit text, and adds the required unit test and carried reproducer; it stays inside the fence and fixes the prior finding by patching `Path.is_file`.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
