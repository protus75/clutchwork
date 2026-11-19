# Review: approve

The diff moves the four shared conditions into `eligible()` in `clutch/drain.py` and both callers now use it, with the held, running, re-offer and `select` checks still in the callers in their original order, so dispatch order, the `write_queue` list and the side effects in the storm, budget and drought checks stay the same; the new unit and integration tests cover acceptance criteria 1-7, and only one copy of the filter remains, inside `eligible`.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e3d8427cad3dcd906139a673abd53d943366a355",
  "stem": "parallel-dispatch-eligible-r1",
  "reviewed_sha": "e3d8427cad3dcd906139a673abd53d943366a355",
  "summary": "The diff moves the four shared conditions into `eligible()` in `clutch/drain.py` and both callers now use it, with the held, running, re-offer and `select` checks still in the callers in their original order, so dispatch order, the `write_queue` list and the side effects in the storm, budget and drought checks stay the same; the new unit and integration tests cover acceptance criteria 1-7, and only one copy of the filter remains, inside `eligible`.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
