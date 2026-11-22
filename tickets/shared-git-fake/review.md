# Review: approve

Approve: `GitFake` matches every public `Git` member and signature, does what the Goal describes for overrides, defaults and call recording, and the 9 files are migrated with the same names and assertions. The adoption test's `PENDING` list holds 69 files, not the 64 the ticket counts; the scan forces this, and five of them (`tests/unit/test_check_meta_fill.py`, `tests/integration/test_retry_keeps_branch.py`, `tests/integration/test_serve_verdict_orphan_sweep.py`, `tests/unit/test_runner_verdict_reread.py`, `tests/unit/test_serve_verdict_owned.py`) are in no sibling ticket's fence, so the chain will not empty `PENDING` on its own.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "7324a59239fed17185649f14cb2494ddb64ec07f",
  "stem": "shared-git-fake",
  "reviewed_sha": "7324a59239fed17185649f14cb2494ddb64ec07f",
  "summary": "Approve: `GitFake` matches every public `Git` member and signature, does what the Goal describes for overrides, defaults and call recording, and the 9 files are migrated with the same names and assertions. The adoption test's `PENDING` list holds 69 files, not the 64 the ticket counts; the scan forces this, and five of them (`tests/unit/test_check_meta_fill.py`, `tests/integration/test_retry_keeps_branch.py`, `tests/integration/test_serve_verdict_orphan_sweep.py`, `tests/unit/test_runner_verdict_reread.py`, `tests/unit/test_serve_verdict_owned.py`) are in no sibling ticket's fence, so the chain will not empty `PENDING` on its own.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
