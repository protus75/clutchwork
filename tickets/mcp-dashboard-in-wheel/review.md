# Review: approve

The diff adds `Release.pre_build` as an optional field that defaults to empty and validates each command, runs the commands in order with a cleaned environment after tag verification and before `uv build`, refuses with a fix-it hint on a non-zero exit, `TimeoutError`, or `ExecutableNotFound`, declares the ui-bundle command in `config.yaml`, updates every doc the ticket names, and its unit and real-I/O tests cover each acceptance criterion and stay inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "c9b69b78820c08f7f9cd13410491cf6b9f11592a",
  "stem": "mcp-dashboard-in-wheel",
  "reviewed_sha": "c9b69b78820c08f7f9cd13410491cf6b9f11592a",
  "summary": "The diff adds `Release.pre_build` as an optional field that defaults to empty and validates each command, runs the commands in order with a cleaned environment after tag verification and before `uv build`, refuses with a fix-it hint on a non-zero exit, `TimeoutError`, or `ExecutableNotFound`, declares the ui-bundle command in `config.yaml`, updates every doc the ticket names, and its unit and real-I/O tests cover each acceptance criterion and stay inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
