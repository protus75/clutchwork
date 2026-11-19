# Review: approve

This change swaps the single `_slot`/`active`/`task` design in `DaemonAdmission` for a run dict capped at `max_runs`, gated by a condition. It adds an exclusive gate used by mutations, startup, the sweep and watch publication, and `occupied()` probes on both admission and scheduler. It moves every caller and test assertion to the new API, passes 1 when parallel is off, adds the two roadmap rows as rows 156 and 157, updates the docs, and drops the out-of-scope serve failure-type hunk from the prior review.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "a3aad31b859e5fb2b2685f5e169b7d26bcdfa890",
  "stem": "serve-parallel-dispatch-r2",
  "reviewed_sha": "a3aad31b859e5fb2b2685f5e169b7d26bcdfa890",
  "summary": "This change swaps the single `_slot`/`active`/`task` design in `DaemonAdmission` for a run dict capped at `max_runs`, gated by a condition. It adds an exclusive gate used by mutations, startup, the sweep and watch publication, and `occupied()` probes on both admission and scheduler. It moves every caller and test assertion to the new API, passes 1 when parallel is off, adds the two roadmap rows as rows 156 and 157, updates the docs, and drops the out-of-scope serve failure-type hunk from the prior review.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
