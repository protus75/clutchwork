# Review: approve

The diff adds a `settling_verdicts` flag that is cleared in a `finally` and checked by `Restart.owned`, so the idle orphan sweep cannot reap a stem while `Serve.verdicts` is settling admissions; the new tests and the self-contained reproducer follow the ticket's scope and the result protocol it requires.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "3ef8cf4c3b4100e83aa3451c91a171f0e0626e98",
  "stem": "reconcile-spares-confirming-draft",
  "reviewed_sha": "3ef8cf4c3b4100e83aa3451c91a171f0e0626e98",
  "summary": "The diff adds a `settling_verdicts` flag that is cleared in a `finally` and checked by `Restart.owned`, so the idle orphan sweep cannot reap a stem while `Serve.verdicts` is settling admissions; the new tests and the self-contained reproducer follow the ticket's scope and the result protocol it requires.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
