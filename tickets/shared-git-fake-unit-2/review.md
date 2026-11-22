# Review: approve

All 19 stand-ins in the 13 named files are migrated onto GitFake with their assertions preserved or translated to equivalent `fake.calls` checks (`assert_awaited_once_with` becomes an exact single-call list match, and `await_count == 2` becomes a count over `commit_edit` calls); the `_commit` gap is bridged by a per-test attribute override, PENDING drops exactly those 13 entries, and the only other header changes are engine-filled meta fields.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ee4b0b2e9ea9f7aec6abf713dd0bbd3c75c5461c",
  "stem": "shared-git-fake-unit-2",
  "reviewed_sha": "ee4b0b2e9ea9f7aec6abf713dd0bbd3c75c5461c",
  "summary": "All 19 stand-ins in the 13 named files are migrated onto GitFake with their assertions preserved or translated to equivalent `fake.calls` checks (`assert_awaited_once_with` becomes an exact single-call list match, and `await_count == 2` becomes a count over `commit_edit` calls); the `_commit` gap is bridged by a per-test attribute override, PENDING drops exactly those 13 entries, and the only other header changes are engine-filled meta fields.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
