# Review: approve

The diff adds the model-visible, read-only `clutch_index_query` tool, which calls `index.query` unchanged with the `self.creator` seam and the filtered `child_env(..., serving=None)` environment; it maps refusal outcomes to the specified remedies, has tests covering schema, routing, read-only connect, the lock-free path, serialization and every refusal, and updates the help text and docs, all inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "326977aed00ecbb064e7e66e668e44a80fa04eb6",
  "stem": "mcp-index-query",
  "reviewed_sha": "326977aed00ecbb064e7e66e668e44a80fa04eb6",
  "summary": "The diff adds the model-visible, read-only `clutch_index_query` tool, which calls `index.query` unchanged with the `self.creator` seam and the filtered `child_env(..., serving=None)` environment; it maps refusal outcomes to the specified remedies, has tests covering schema, routing, read-only connect, the lock-free path, serialization and every refusal, and updates the help text and docs, all inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
