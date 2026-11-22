# Review: approve

The diff adds `providerInstalls` to `extension_fields` from the sorted `ADAPTERS` names with the update-all entry last, registers `clutch.updateProvider` like `clutch.engine` with no argv or provider names in JavaScript, adds the `package.json` menu entries and the `COMMANDS` help entry, and the tests check the entry count, order and parsing as `provider install` against the real parser, which meets all three acceptance criteria inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "979f1e1243adfd1d0145de2f8b60f9a5378d1a09",
  "stem": "extension-provider-update-action",
  "reviewed_sha": "979f1e1243adfd1d0145de2f8b60f9a5378d1a09",
  "summary": "The diff adds `providerInstalls` to `extension_fields` from the sorted `ADAPTERS` names with the update-all entry last, registers `clutch.updateProvider` like `clutch.engine` with no argv or provider names in JavaScript, adds the `package.json` menu entries and the `COMMANDS` help entry, and the tests check the entry count, order and parsing as `provider install` against the real parser, which meets all three acceptance criteria inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
