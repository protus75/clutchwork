# Review: snag

The verbs, views, store methods and docs match the ticket, but `renormalize` stops the whole run with exit 2 when a stored call's stdout or arrival-times blob has been pruned, instead of skipping and counting that call.

## Findings

- [logic] clutch/__main__.py:1635 `renormalize` reads `end.raw.stdout_times` and `end.raw.stdout` through `store.get_blob` without catching the error for a missing blob. `EvidenceStore.prune` deletes exactly these blobs for older calls while keeping their records (docs/how-clutch-works.md section 10), so any store that has been pruned raises FileNotFoundError here. The outer `except OSError` turns that into a refusal: the run exits 2 and stops early. It leaves views written for some calls but not others, does not normalize the remaining calls and prints no `normalized`/`skipped` summary. The handler skips and counts a missing `end.json` but not a missing raw blob, which is the normal state of an old call. (do instead: Wrap the two `get_blob` reads (stdout_times and stdout) for each call in a `try/except FileNotFoundError` that adds 1 to `skipped` and continues. Add a test with a stored call whose stdout blob was deleted that shows `renormalize` exits 0 and reports it as skipped.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "47dc4f826b47d57fb71faf0125c613be24705173",
  "stem": "evidence-verbs",
  "reviewed_sha": "47dc4f826b47d57fb71faf0125c613be24705173",
  "summary": "The verbs, views, store methods and docs match the ticket, but `renormalize` stops the whole run with exit 2 when a stored call's stdout or arrival-times blob has been pruned, instead of skipping and counting that call.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/__main__.py",
      "line": 1635,
      "message": "`renormalize` reads `end.raw.stdout_times` and `end.raw.stdout` through `store.get_blob` without catching the error for a missing blob. `EvidenceStore.prune` deletes exactly these blobs for older calls while keeping their records (docs/how-clutch-works.md section 10), so any store that has been pruned raises FileNotFoundError here. The outer `except OSError` turns that into a refusal: the run exits 2 and stops early. It leaves views written for some calls but not others, does not normalize the remaining calls and prints no `normalized`/`skipped` summary. The handler skips and counts a missing `end.json` but not a missing raw blob, which is the normal state of an old call.",
      "paved_road": "Wrap the two `get_blob` reads (stdout_times and stdout) for each call in a `try/except FileNotFoundError` that adds 1 to `skipped` and continues. Add a test with a stored call whose stdout blob was deleted that shows `renormalize` exits 0 and reports it as skipped.",
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
