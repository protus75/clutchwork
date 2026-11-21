# Review: snag

The panel fold, the rendering and the tests match the ticket, but the diff also changes the existing spend and token measurement by dropping panel-member completions from it, which the ticket does not ask for.

## Findings

- [scope] clutch/scorecard.py:64 `project_scorecard` now passes `measurements` a filtered window. The filter drops every member-scoped (`m<k>`) completion whose `cost` is not a dict holding a numeric `usd`, and this covers every surface, not just review. For example, a cost dict with `usd: None` or with only token fields is now left out of `spend_usd`, `input_tokens` and `output_tokens`. These are existing `Scorecard` fields, and the ticket's compatibility clause says every existing field stays unchanged. The ticket also says to skip malformed completions only inside the panel fold. The filter only applies when `window.evidence` is empty, so the scorecard's spend can also disagree with the `evidence` that `render_report` is given. (do instead: Remove the `measurement_events` filter and keep `evidence = window.evidence or measurements(window)` as it was. Skip malformed costs only in the panel grouping, which already does so. If a malformed cost crashes `measurements`, that bug was there before this diff: file it with `clutch box suggest` and drop `test_malformed_cost_does_not_break_measurement`, or limit that test to the panel fold.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "675d79c84490549a807a872040ce4ed44f035a29",
  "stem": "panel-scorecard",
  "reviewed_sha": "675d79c84490549a807a872040ce4ed44f035a29",
  "summary": "The panel fold, the rendering and the tests match the ticket, but the diff also changes the existing spend and token measurement by dropping panel-member completions from it, which the ticket does not ask for.",
  "findings": [
    {
      "code": "scope",
      "path": "clutch/scorecard.py",
      "line": 64,
      "message": "`project_scorecard` now passes `measurements` a filtered window. The filter drops every member-scoped (`m<k>`) completion whose `cost` is not a dict holding a numeric `usd`, and this covers every surface, not just review. For example, a cost dict with `usd: None` or with only token fields is now left out of `spend_usd`, `input_tokens` and `output_tokens`. These are existing `Scorecard` fields, and the ticket's compatibility clause says every existing field stays unchanged. The ticket also says to skip malformed completions only inside the panel fold. The filter only applies when `window.evidence` is empty, so the scorecard's spend can also disagree with the `evidence` that `render_report` is given.",
      "paved_road": "Remove the `measurement_events` filter and keep `evidence = window.evidence or measurements(window)` as it was. Skip malformed costs only in the panel grouping, which already does so. If a malformed cost crashes `measurements`, that bug was there before this diff: file it with `clutch box suggest` and drop `test_malformed_cost_does_not_break_measurement`, or limit that test to the panel fold.",
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
