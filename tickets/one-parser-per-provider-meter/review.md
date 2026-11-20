# Review: approve

CallMeter now meters only from normalized events: it uses the four token buckets, takes cost from the result event's usd, and counts tool_call/tool_result ids, and the Claude normalizer emits the assistant/usage event bumped to claude-stream/2; all eight criteria are covered, the docs are updated, and every changed file is inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "d104d6e3f727441b109e5f8950e59b9baf6030df",
  "stem": "one-parser-per-provider-meter",
  "reviewed_sha": "d104d6e3f727441b109e5f8950e59b9baf6030df",
  "summary": "CallMeter now meters only from normalized events: it uses the four token buckets, takes cost from the result event's usd, and counts tool_call/tool_result ids, and the Claude normalizer emits the assistant/usage event bumped to claude-stream/2; all eight criteria are covered, the docs are updated, and every changed file is inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
