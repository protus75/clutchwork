# Review: approve

The diff adds one per-instance asyncio.Lock behind Git.main_write(); merge_squash, _write_row, ship and dirty_overlap each take it once, outside CommitLock, and none of them calls another while holding it; the new tests fail if any caller drops the lock, the existing fakes gain main_write, and no out-of-fence consumer reaches the four functions through a fake that lacks it.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "0c2eb649de521d6e2cb14b603425ad4525c59445",
  "stem": "dispatch-during-driver-pass-gate",
  "reviewed_sha": "0c2eb649de521d6e2cb14b603425ad4525c59445",
  "summary": "The diff adds one per-instance asyncio.Lock behind Git.main_write(); merge_squash, _write_row, ship and dirty_overlap each take it once, outside CommitLock, and none of them calls another while holding it; the new tests fail if any caller drops the lock, the existing fakes gain main_write, and no out-of-fence consumer reaches the four functions through a fake that lacks it.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
