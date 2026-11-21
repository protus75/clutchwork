# Review: approve

The diff adds an engine-written-failure rule to the `abandon-human` verdict. The rule requires evidence from the run record or checks, tells Diagnose to name the engine file and defect in the lessons, forbids a pre-emptive `retry`, and keeps the normal verdicts for failures the implementer's diff caused; it also bumps both diagnose version pins to 1.9 and adds a test that checks every clause and fails on the old spec, with all changes inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "1aebfe1c1ba24dd0410204e6e0c0ac7e9b6f9461",
  "stem": "diagnose-spec-engine-written-failure-abandons",
  "reviewed_sha": "1aebfe1c1ba24dd0410204e6e0c0ac7e9b6f9461",
  "summary": "The diff adds an engine-written-failure rule to the `abandon-human` verdict. The rule requires evidence from the run record or checks, tells Diagnose to name the engine file and defect in the lessons, forbids a pre-emptive `retry`, and keeps the normal verdicts for failures the implementer's diff caused; it also bumps both diagnose version pins to 1.9 and adds a test that checks every clause and fails on the old spec, with all changes inside the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
