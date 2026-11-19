# Review: snag

The gate, Evidence fields, check reorder, writer, pinned sets and tests match the ticket, but the new roadmap row uses the arbitrary number 999 instead of the next stable identifier.

## Findings

- [logic] docs/roadmap.md:366 The added `image-embed-presence` row is numbered 999. docs/roadmap.md line 225 says "Row numbers are stable identifiers assigned in the order rows were added". The highest existing row is 161, so 999 is not the next identifier and breaks that convention. (do instead: Number the row 162, the next unused identifier after the current maximum of 161, and leave its position and other columns unchanged.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "489837eae8c5221fd2e1486e9a0cac530bd3518c",
  "stem": "image-quality-gate-wiring",
  "reviewed_sha": "489837eae8c5221fd2e1486e9a0cac530bd3518c",
  "summary": "The gate, Evidence fields, check reorder, writer, pinned sets and tests match the ticket, but the new roadmap row uses the arbitrary number 999 instead of the next stable identifier.",
  "findings": [
    {
      "code": "logic",
      "path": "docs/roadmap.md",
      "line": 366,
      "message": "The added `image-embed-presence` row is numbered 999. docs/roadmap.md line 225 says \"Row numbers are stable identifiers assigned in the order rows were added\". The highest existing row is 161, so 999 is not the next identifier and breaks that convention.",
      "paved_road": "Number the row 162, the next unused identifier after the current maximum of 161, and leave its position and other columns unchanged.",
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
