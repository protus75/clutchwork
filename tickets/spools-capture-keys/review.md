# Review: approve

The diff meets every acceptance criterion: `capture_key` itself refuses each bad input, the store accepts attempt 0 and the wider stem rule, help names attempt 0 and the `run-<n>/` segment, every changed file is inside the fence, and the prior finding is fixed because refused-key tests now call `capture_key` alone inside `pytest.raises(ValueError)`.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "637150275d8ff71c6f4e0059bbd38a7017f1fa40",
  "stem": "spools-capture-keys",
  "reviewed_sha": "637150275d8ff71c6f4e0059bbd38a7017f1fa40",
  "summary": "The diff meets every acceptance criterion: `capture_key` itself refuses each bad input, the store accepts attempt 0 and the wider stem rule, help names attempt 0 and the `run-<n>/` segment, every changed file is inside the fence, and the prior finding is fixed because refused-key tests now call `capture_key` alone inside `pytest.raises(ValueError)`.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
