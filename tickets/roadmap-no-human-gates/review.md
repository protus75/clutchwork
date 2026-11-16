# Review: snag

The diff meets every acceptance criterion, but two of its rewrites delete design facts that the ticket never asked to remove.

## Findings

- [scope] docs/roadmap-driver-plan.md:74 The ticket asked section 4 to drop the word "operator", turn the two operator gates into commands, and add the capture and credential blocks to `roadmap status`. The rewrite also deletes two design facts it had no mandate to touch. One is "Read-only; the extension draws it later.", a constraint on `clutch roadmap status`. The other is the list of existing command gates: "the suite, a `status` query, a `training export` count". The `release-gates-as-commands` ticket is authored from this text, and it would lose both. (do instead: Restore "Read-only; the extension draws it later." and the examples of prose gates that become commands (the suite, a `status` query, a `training export` count). Change only the clauses that name an operator or a person.)
- [scope] docs/gemini-graphics-refactor-plan.md:250 The ticket asked B7 to make `./dev.py visual-baseline` report agreement with the AI label panel's labels. The rewrite also drops "The report is committed like the review baseline's." and narrows "the layer-1 score distributions that separate the labels" to "the layer-1 score distributions". That loses the design requirement that the baseline report is committed, which no part of Scope in removes. (do instead: Keep "The report is committed like the review baseline's." and "that separate the labels" in the B7 `./dev.py visual-baseline` bullet. Change only the source of the labels.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "8343b0c17b328716f7db44877352f6806ee878e7",
  "stem": "roadmap-no-human-gates",
  "reviewed_sha": "8343b0c17b328716f7db44877352f6806ee878e7",
  "summary": "The diff meets every acceptance criterion, but two of its rewrites delete design facts that the ticket never asked to remove.",
  "findings": [
    {
      "code": "scope",
      "path": "docs/roadmap-driver-plan.md",
      "line": 74,
      "message": "The ticket asked section 4 to drop the word \"operator\", turn the two operator gates into commands, and add the capture and credential blocks to `roadmap status`. The rewrite also deletes two design facts it had no mandate to touch. One is \"Read-only; the extension draws it later.\", a constraint on `clutch roadmap status`. The other is the list of existing command gates: \"the suite, a `status` query, a `training export` count\". The `release-gates-as-commands` ticket is authored from this text, and it would lose both.",
      "paved_road": "Restore \"Read-only; the extension draws it later.\" and the examples of prose gates that become commands (the suite, a `status` query, a `training export` count). Change only the clauses that name an operator or a person.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "docs/gemini-graphics-refactor-plan.md",
      "line": 250,
      "message": "The ticket asked B7 to make `./dev.py visual-baseline` report agreement with the AI label panel's labels. The rewrite also drops \"The report is committed like the review baseline's.\" and narrows \"the layer-1 score distributions that separate the labels\" to \"the layer-1 score distributions\". That loses the design requirement that the baseline report is committed, which no part of Scope in removes.",
      "paved_road": "Keep \"The report is committed like the review baseline's.\" and \"that separate the labels\" in the B7 `./dev.py visual-baseline` bullet. Change only the source of the labels.",
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
