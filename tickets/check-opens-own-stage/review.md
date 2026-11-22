# Review: approve

The diff moves the `check` stage pair out of `run_stages` and into `stages.check`, so every return path emits it exactly once with the returned outcome; it routes `check_meta`'s existence filter through `ctx.fs.entries`, adds the required unit and integration tests, updates the three stub drivers and fixes both doc sentences, with every change inside the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "91c01f6222622c830e64725e61b405c5e061a007",
  "stem": "check-opens-own-stage",
  "reviewed_sha": "91c01f6222622c830e64725e61b405c5e061a007",
  "summary": "The diff moves the `check` stage pair out of `run_stages` and into `stages.check`, so every return path emits it exactly once with the returned outcome; it routes `check_meta`'s existence filter through `ctx.fs.entries`, adds the required unit and integration tests, updates the three stub drivers and fixes both doc sentences, with every change inside the fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
