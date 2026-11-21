# Review: snag

Most of the audit edit is correct, but it drops the section 3.3 'Triage-dedup real-model eval' row even though no merged work did that eval: `training-eval` accepts only the `review` surface and left the triage lens as a follow-up.

## Findings

- [acceptance] docs/roadmap.md:124 Section 3.3 drops the row 'Triage-dedup real-model eval | daemon-era entry | yes, serve has run since the daemon era | not scheduled; `training-eval` (0.5.0) covers triage records and makes this the first lens to score'. No merged change fixed it. `tickets/training-eval/ticket.md:29` says 'Only surface `review` is accepted in this ticket. Triage, requisition and implement lenses are a follow-up row'. Row 176 (`training-export-kinds`) says 'Triage waits for a real label source.' The triage-dedup eval was never run, so removing the row breaks acceptance criterion 3 and the Definition of rejected ('removes an audit item without a merged change that fixed it'). The other removals are backed by merged work: rows 9 and 10 by `serve-parallel-dispatch-r2` and `storm-producer-one-builder`, section 2.4 by `one-parser-per-provider*`, the worker-pool row by `serve-parallel-dispatch-r2`, and the micro-rework row by `merge-model-resolve`. (do instead: Put the 'Triage-dedup real-model eval' row back in the section 3.3 table and correct its Decision cell to say what is true at the base commit: `training-eval` merged with only the `review` lens, and the triage lens is still a follow-up waiting for a label source. End the row with '(recurred in 0.5.0)'.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "a789f69533e0a882c18da60049fd2d8c5b8797e4",
  "stem": "release-audit-050",
  "reviewed_sha": "a789f69533e0a882c18da60049fd2d8c5b8797e4",
  "summary": "Most of the audit edit is correct, but it drops the section 3.3 'Triage-dedup real-model eval' row even though no merged work did that eval: `training-eval` accepts only the `review` surface and left the triage lens as a follow-up.",
  "findings": [
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": 124,
      "message": "Section 3.3 drops the row 'Triage-dedup real-model eval | daemon-era entry | yes, serve has run since the daemon era | not scheduled; `training-eval` (0.5.0) covers triage records and makes this the first lens to score'. No merged change fixed it. `tickets/training-eval/ticket.md:29` says 'Only surface `review` is accepted in this ticket. Triage, requisition and implement lenses are a follow-up row'. Row 176 (`training-export-kinds`) says 'Triage waits for a real label source.' The triage-dedup eval was never run, so removing the row breaks acceptance criterion 3 and the Definition of rejected ('removes an audit item without a merged change that fixed it'). The other removals are backed by merged work: rows 9 and 10 by `serve-parallel-dispatch-r2` and `storm-producer-one-builder`, section 2.4 by `one-parser-per-provider*`, the worker-pool row by `serve-parallel-dispatch-r2`, and the micro-rework row by `merge-model-resolve`.",
      "paved_road": "Put the 'Triage-dedup real-model eval' row back in the section 3.3 table and correct its Decision cell to say what is true at the base commit: `training-eval` merged with only the `review` lens, and the triage lens is still a follow-up waiting for a label source. End the row with '(recurred in 0.5.0)'.",
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
