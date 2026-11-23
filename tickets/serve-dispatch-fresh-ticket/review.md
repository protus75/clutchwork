# Review: approve

Dispatch now resolves the ticket's blob ID once and reads that exact blob. If the parsed content differs from the selected ticket, it re-offers the fresh ticket through `publish` before any running event. Content that does not parse never reaches the callback. The callback gets the committed parse that matches the journaled sha, and the tests cover every acceptance criterion, including a stale selection that is not the latest publication, a mid-dispatch main move, and fixtures switched to real parsed tickets.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "3bdd8ce916adbf792aacad95bcc0dcabf4f24cbd",
  "stem": "serve-dispatch-fresh-ticket",
  "reviewed_sha": "3bdd8ce916adbf792aacad95bcc0dcabf4f24cbd",
  "summary": "Dispatch now resolves the ticket's blob ID once and reads that exact blob. If the parsed content differs from the selected ticket, it re-offers the fresh ticket through `publish` before any running event. Content that does not parse never reaches the callback. The callback gets the committed parse that matches the journaled sha, and the tests cover every acceptance criterion, including a stale selection that is not the latest publication, a mid-dispatch main move, and fixtures switched to real parsed tickets.",
  "findings": [],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
