# Review: approve

Every listed hub name now lives in tests/misc_helpers.py on the shared fakes (commit_lock returns an asyncio.Lock and requisition_reply re-exports tests/stage_replies.py), every fenced importer imports from tests.misc_helpers except the real-I/O commit_lock users the ticket allows, the hubs no longer define the moved names, and tests/unit/test_misc_helpers.py tests each name without a process, real git, or a write outside tmp_path.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "deaee72905f044fa364d1084b5e0262794957838",
  "stem": "io-helpers-misc",
  "reviewed_sha": "deaee72905f044fa364d1084b5e0262794957838",
  "summary": "Every listed hub name now lives in tests/misc_helpers.py on the shared fakes (commit_lock returns an asyncio.Lock and requisition_reply re-exports tests/stage_replies.py), every fenced importer imports from tests.misc_helpers except the real-I/O commit_lock users the ticket allows, the hubs no longer define the moved names, and tests/unit/test_misc_helpers.py tests each name without a process, real git, or a write outside tmp_path.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
