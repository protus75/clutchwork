# Review: approve

The diff adds one lint check over the Acceptance criteria text and the joined Verification commands that refuses `git diff --name-only` against `main`, `main..HEAD` and `main HEAD` and points to `main...HEAD`, adds the guide sentence and its parity phrase, and adds unit tests covering both sections, the three refused forms and the merge-base, `--stat` and `mainline` forms, all inside the scope fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "6f8e9c0278f29c4a8050fd7e81b6731032f4a343",
  "stem": "lint-refuses-two-dot-git-diff-main",
  "reviewed_sha": "6f8e9c0278f29c4a8050fd7e81b6731032f4a343",
  "summary": "The diff adds one lint check over the Acceptance criteria text and the joined Verification commands that refuses `git diff --name-only` against `main`, `main..HEAD` and `main HEAD` and points to `main...HEAD`, adds the guide sentence and its parity phrase, and adds unit tests covering both sections, the three refused forms and the merge-base, `--stat` and `mainline` forms, all inside the scope fence.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
