# Review: approve

The diff meets every acceptance criterion and stays inside the scope fence: `due_trigger` is the one pure due decision, `override` can no longer make a retro due, `Retro.__call__` loads production evidence only after a trigger is selected, `check_retro` is called only from the `Serve.run` loop outside the merge lock, and the tests and docs are updated to match.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "9abde9de6dff9db6abb76d72e8847501b3489144",
  "stem": "retro-due-one-owner",
  "reviewed_sha": "9abde9de6dff9db6abb76d72e8847501b3489144",
  "summary": "The diff meets every acceptance criterion and stays inside the scope fence: `due_trigger` is the one pure due decision, `override` can no longer make a retro due, `Retro.__call__` loads production evidence only after a trigger is selected, `check_retro` is called only from the `Serve.run` loop outside the merge lock, and the tests and docs are updated to match.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
