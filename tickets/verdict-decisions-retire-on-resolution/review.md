# Review: approve

The diff adds the retirement rule to `project` and nowhere else; a non-accepted decision is dropped only when a `draft_confirmed` or `reject_verdict` signal for its stem appears later in the journal (journal order); the row shape and order stay the same, stemless decisions are kept, tests cover acceptance criteria 1-5, the regression script passes on the branch head and reports a defect at the merge base, and no doc describes the old behavior.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "4927c31d2fe46d58e59537e5e693997138204b0a",
  "stem": "verdict-decisions-retire-on-resolution",
  "reviewed_sha": "4927c31d2fe46d58e59537e5e693997138204b0a",
  "summary": "The diff adds the retirement rule to `project` and nowhere else; a non-accepted decision is dropped only when a `draft_confirmed` or `reject_verdict` signal for its stem appears later in the journal (journal order); the row shape and order stay the same, stemless decisions are kept, tests cover acceptance criteria 1-5, the regression script passes on the branch head and reports a defect at the merge base, and no doc describes the old behavior.",
  "findings": [],
  "spec_version": "1.5",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
