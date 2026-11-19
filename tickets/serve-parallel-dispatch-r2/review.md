# Review: snag

The run set, exclusive gate, occupied() probes, cancellation-safe releases, config wiring, tests, docs and roadmap rows match the ticket, but the diff also makes an unrequested change to how serve reports its failure type.

## Findings

- [scope] clutch/serve.py:656 The diff changes the serve lifetime's `except Exception` handler from always setting `failure_type = type(exc).__name__` to doing so only `if failure_type is None:`. This changes which failure type serve reports when a guarded worker has already latched one. The ticket does not ask for this: it covers admission slots, idle checks and watch publication, not serve's failure reporting. (do instead: Revert this hunk so the handler again sets `failure_type = type(exc).__name__` unconditionally. If the reporting order is a real defect, file it with `clutch box suggest` as a separate problem.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "67dde2039927df55f91c2b6ef1026079986db33d",
  "stem": "serve-parallel-dispatch-r2",
  "reviewed_sha": "67dde2039927df55f91c2b6ef1026079986db33d",
  "summary": "The run set, exclusive gate, occupied() probes, cancellation-safe releases, config wiring, tests, docs and roadmap rows match the ticket, but the diff also makes an unrequested change to how serve reports its failure type.",
  "findings": [
    {
      "code": "scope",
      "path": "clutch/serve.py",
      "line": 656,
      "message": "The diff changes the serve lifetime's `except Exception` handler from always setting `failure_type = type(exc).__name__` to doing so only `if failure_type is None:`. This changes which failure type serve reports when a guarded worker has already latched one. The ticket does not ask for this: it covers admission slots, idle checks and watch publication, not serve's failure reporting.",
      "paved_road": "Revert this hunk so the handler again sets `failure_type = type(exc).__name__` unconditionally. If the reporting order is a real defect, file it with `clutch box suggest` as a separate problem.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
