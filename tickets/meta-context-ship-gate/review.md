# Review: approve

The diff adds a `--require` flag to `context suggest` that makes only an empty result exit 1 and leaves every other exit code unchanged; it extends the 0.5.0 gate block to the six commands in the required order, exempts 0.5.0 from the three-command test, documents the flag in the in-fence docs, and adds a pure unit test covering both outcomes with `require=True`.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "47f5627e613a74448ffd57bb98809426e43bf16b",
  "stem": "meta-context-ship-gate",
  "reviewed_sha": "47f5627e613a74448ffd57bb98809426e43bf16b",
  "summary": "The diff adds a `--require` flag to `context suggest` that makes only an empty result exit 1 and leaves every other exit code unchanged; it extends the 0.5.0 gate block to the six commands in the required order, exempts 0.5.0 from the three-command test, documents the flag in the in-fence docs, and adds a pure unit test covering both outcomes with `require=True`.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
