# Review: snag

Review finished: the rename, the table move, the gate cell and the test key are correct, but section 3.3 of docs/roadmap.md still uses the old release names, so some releases have two names, which the ticket's Definition of rejected forbids.

## Findings

- [acceptance] docs/roadmap.md:- Section 3.3 (Deferred items whose trigger has fired) still uses the old name for the journal window. The DuckDB analytics row reads "re-measure; 0.4.0 is conditional on it", but after this diff 0.4.0 is parallel runs and the graphics kind, and the journal window is 0.6.0. The release now has two names, which the ticket's Definition of rejected forbids. (do instead: Change only the release name in that cell to "0.6.0 is conditional on it".)
- [acceptance] docs/roadmap.md:- Section 3.3, Triage-dedup real-model eval row, still reads "`training-eval` (0.6.0) covers triage records". The diff renames `training-eval` to 0.5.0 in decision 11 and in the section 1 table, so the training release now has two names. (do instead: Change only the version in that cell to `training-eval` (0.5.0).)
- [acceptance] docs/roadmap.md:- Section 3.3, Concurrent worker pool row, still reads "0.5.0, declared in `docs/parallel-tickets-plan.md`". The diff moves the parallel plan to 0.4.0 in the section 1 table and in that plan's Roadmap section, so the parallel release now has two names. (do instead: Change only the version in that cell to "0.4.0, declared in `docs/parallel-tickets-plan.md`".)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "64120cdf900507bf16c8e543867c3401e14c61c0",
  "stem": "defer-journal-window",
  "reviewed_sha": "64120cdf900507bf16c8e543867c3401e14c61c0",
  "summary": "Review finished: the rename, the table move, the gate cell and the test key are correct, but section 3.3 of docs/roadmap.md still uses the old release names, so some releases have two names, which the ticket's Definition of rejected forbids.",
  "findings": [
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": null,
      "message": "Section 3.3 (Deferred items whose trigger has fired) still uses the old name for the journal window. The DuckDB analytics row reads \"re-measure; 0.4.0 is conditional on it\", but after this diff 0.4.0 is parallel runs and the graphics kind, and the journal window is 0.6.0. The release now has two names, which the ticket's Definition of rejected forbids.",
      "paved_road": "Change only the release name in that cell to \"0.6.0 is conditional on it\".",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": null,
      "message": "Section 3.3, Triage-dedup real-model eval row, still reads \"`training-eval` (0.6.0) covers triage records\". The diff renames `training-eval` to 0.5.0 in decision 11 and in the section 1 table, so the training release now has two names.",
      "paved_road": "Change only the version in that cell to `training-eval` (0.5.0).",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": null,
      "message": "Section 3.3, Concurrent worker pool row, still reads \"0.5.0, declared in `docs/parallel-tickets-plan.md`\". The diff moves the parallel plan to 0.4.0 in the section 1 table and in that plan's Roadmap section, so the parallel release now has two names.",
      "paved_road": "Change only the version in that cell to \"0.4.0, declared in `docs/parallel-tickets-plan.md`\".",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
