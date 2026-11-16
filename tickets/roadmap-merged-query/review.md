# Review: approve

The diff adds a read-only `roadmap merged` query that meets every acceptance criterion: it refuses bad arguments before any read, decides settlement only from `row.struck` and `choose`'s strike list, counts de-duplicated first-parent trailer stems with the source and person-verdict filters, takes no lock, and updates both docs.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e6d649858bfc0ed95c63a330ac2b2f569f7ff9b9",
  "stem": "roadmap-merged-query",
  "reviewed_sha": "e6d649858bfc0ed95c63a330ac2b2f569f7ff9b9",
  "summary": "The diff adds a read-only `roadmap merged` query that meets every acceptance criterion: it refuses bad arguments before any read, decides settlement only from `row.struck` and `choose`'s strike list, counts de-duplicated first-parent trailer stems with the source and person-verdict filters, takes no lock, and updates both docs.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
