# Review: snag

Four of the five Status rewrites match the roadmap's strike-throughs, but the evidence-trail plan's list of merged rows leaves out row 149 (`evidence-record-doc-section`), which is merged and owned by evidence.

## Findings

- [acceptance] docs/evidence-trail-plan.md:19 Acceptance criterion 2 requires each Status to name its merged rows by number and stem. The new evidence-trail Status lists merged rows 28-31, 33, 62-64, 123, 183-186, 189, 190, 194 and 195. It leaves out row 149 (`evidence-record-doc-section`), which is struck through in the roadmap master table (docs/roadmap.md line 377) with Owner `evidence`. The boundary-contract Status does include row 163, which is owned by `boundary` and has no plan number, so the evidence list is not built the same way. (do instead: Add `149 (\`evidence-record-doc-section\`)` to the merged rows in docs/evidence-trail-plan.md#Status, then rerun `uv run clutch meta refresh docs/evidence-trail-plan.md`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "86913fc9cc28bbd6027d088895328dffeb92e0d2",
  "stem": "plan-status-after-050",
  "reviewed_sha": "86913fc9cc28bbd6027d088895328dffeb92e0d2",
  "summary": "Four of the five Status rewrites match the roadmap's strike-throughs, but the evidence-trail plan's list of merged rows leaves out row 149 (`evidence-record-doc-section`), which is merged and owned by evidence.",
  "findings": [
    {
      "code": "acceptance",
      "path": "docs/evidence-trail-plan.md",
      "line": 19,
      "message": "Acceptance criterion 2 requires each Status to name its merged rows by number and stem. The new evidence-trail Status lists merged rows 28-31, 33, 62-64, 123, 183-186, 189, 190, 194 and 195. It leaves out row 149 (`evidence-record-doc-section`), which is struck through in the roadmap master table (docs/roadmap.md line 377) with Owner `evidence`. The boundary-contract Status does include row 163, which is owned by `boundary` and has no plan number, so the evidence list is not built the same way.",
      "paved_road": "Add `149 (\\`evidence-record-doc-section\\`)` to the merged rows in docs/evidence-trail-plan.md#Status, then rerun `uv run clutch meta refresh docs/evidence-trail-plan.md`.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
