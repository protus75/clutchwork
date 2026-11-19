# Review: approve

The diff adds the DuckDB rule as the last `## Engine conduct` bullet, starting with `When you add or change code,`. It shortens other bullets without changing their meaning or touching any pinned phrase, the `clutch box issue` sentence, or `--kind feature|bug|chore`, which leaves the template at about 8178 bytes by hand count (limit 8179). All three managed blocks match the template and GOLDEN was regenerated. The new unit test checks the in-memory bytes for one matching line after the `## Engine conduct` heading and for the 8192-byte cap.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "d524fef9aee824c98c4ef3ca0d0a3fdc50e9850e",
  "stem": "core-rule-duckdb-not-sqlite",
  "reviewed_sha": "d524fef9aee824c98c4ef3ca0d0a3fdc50e9850e",
  "summary": "The diff adds the DuckDB rule as the last `## Engine conduct` bullet, starting with `When you add or change code,`. It shortens other bullets without changing their meaning or touching any pinned phrase, the `clutch box issue` sentence, or `--kind feature|bug|chore`, which leaves the template at about 8178 bytes by hand count (limit 8179). All three managed blocks match the template and GOLDEN was regenerated. The new unit test checks the in-memory bytes for one matching line after the `## Engine conduct` heading and for the 8192-byte cap.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
