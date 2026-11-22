# Review: approve

The diff adds `worktree_attach`, a `keep` path in `prepare_worktree` that falls back to a fresh branch from main when the rebase fails, and a journal-based keep decision in `implement`; it also updates both prompts, their version pins, docs section 4.1 and the required tests, stays inside the fence and meets criteria 1 to 4.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ab73535e3e9d47b70f47d282534c53967da0bb05",
  "stem": "retry-keeps-prior-branch",
  "reviewed_sha": "ab73535e3e9d47b70f47d282534c53967da0bb05",
  "summary": "The diff adds `worktree_attach`, a `keep` path in `prepare_worktree` that falls back to a fresh branch from main when the rebase fails, and a journal-based keep decision in `implement`; it also updates both prompts, their version pins, docs section 4.1 and the required tests, stays inside the fence and meets criteria 1 to 4.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
