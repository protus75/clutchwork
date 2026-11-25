# Review: snag

The `--check`/`--verify` code, gate block, docs rows and tests are correct, but the sections 2-4 audit removes two duplication items that are still true at the base commit, which violates acceptance criterion 5.

## Findings

- [acceptance] docs/roadmap.md:79 The 'Ask kinds' row was removed from section 2.2, but only half of it was fixed. `__main__.py` now derives its descriptions from `ask.DESCRIPTIONS`, but `clutch/observe.py:731-735` still hand-lists the prompt menu argv (`askDiagnose: ["prompt", "diagnose"]`, `askReview`, `askDrafts`, `askDrainLoop`, `askBox`), which the row also named. Criterion 5 forbids removing an item unless merged work fixed it. (do instead: Restore the 'Ask kinds' row. Drop only the fixed `__main__.py` description clause, keep the `observe.py` prompt-menu argv clause with its current line numbers, and mark it `(recurred in 0.7.0)`.)
- [acceptance] docs/roadmap.md:71 The 'Failed-attempt terminals' row drops the scorecard home, but `clutch/scorecard.py:139` still hand-lists the terminal set `{"merged", "gate_failed", "abandoned", "rejected"}`. No merged change removed that duplicate, so the item was removed without a fix. (do instead: Put scorecard back in the row with its current line (`scorecard.py:139`) next to the caps, journal and stats homes, marked `(recurred in 0.7.0)`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "41b5d3a5b3ddc8561870df1415b7ee385c5055be",
  "stem": "release-audit-070",
  "reviewed_sha": "41b5d3a5b3ddc8561870df1415b7ee385c5055be",
  "summary": "The `--check`/`--verify` code, gate block, docs rows and tests are correct, but the sections 2-4 audit removes two duplication items that are still true at the base commit, which violates acceptance criterion 5.",
  "findings": [
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": 79,
      "message": "The 'Ask kinds' row was removed from section 2.2, but only half of it was fixed. `__main__.py` now derives its descriptions from `ask.DESCRIPTIONS`, but `clutch/observe.py:731-735` still hand-lists the prompt menu argv (`askDiagnose: [\"prompt\", \"diagnose\"]`, `askReview`, `askDrafts`, `askDrainLoop`, `askBox`), which the row also named. Criterion 5 forbids removing an item unless merged work fixed it.",
      "paved_road": "Restore the 'Ask kinds' row. Drop only the fixed `__main__.py` description clause, keep the `observe.py` prompt-menu argv clause with its current line numbers, and mark it `(recurred in 0.7.0)`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": 71,
      "message": "The 'Failed-attempt terminals' row drops the scorecard home, but `clutch/scorecard.py:139` still hand-lists the terminal set `{\"merged\", \"gate_failed\", \"abandoned\", \"rejected\"}`. No merged change removed that duplicate, so the item was removed without a fix.",
      "paved_road": "Put scorecard back in the row with its current line (`scorecard.py:139`) next to the caps, journal and stats homes, marked `(recurred in 0.7.0)`.",
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
