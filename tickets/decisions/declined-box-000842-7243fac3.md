---
id: declined-box-000842-7243fac3
kind: declined
link: box-000842-7243fac3
reopen_after_days: 30
---
The visual baseline harness writes eval/visual_report.json with only case_count, overall, per-row rates and verdict. The judge's provider, model and review_visual spec major are not in that file. The note asks for the report to carry that identity, and for every eval or baseline report to record which models produced its labels and verdicts.

The report really does leave out the judge identity: `agreement` in eval/visual_harness.py builds the report without it. But no runtime behavior goes wrong because of this. `run_baseline` writes the full `identity` (the review_visual routing rows and the spec major) into the `visual_baseline` journal signal. The graphics gate in clutch/stages.py decides through `resolve_visual_baseline` in clutch/baseline.py, which reads that journal signal and never reads the committed report. So a GO cannot bind to the wrong judge, and a stale identity is still caught. What remains is a gap in how the committed file records its source. visual-baseline-fixtures already covers that by naming the identity in run.md. The broader rule that every eval report records model identity is class hardening, not a fix for a demonstrated harm. Reopen if an engine or release decision starts reading visual_report.json, or eval reports generally, as its source of truth. Also reopen if a committed report is shown to have been misattributed to the wrong judge in a way that changed a decision.

- eval/visual_harness.py:86-99 `agreement` returns case_count, overall, rows and verdict, with no identity
- eval/visual_harness.py:153-157 the journal signal body includes `identity`, and the report file is `json.dumps(report)` without it
- clutch/stages.py:1782 the graphics gate binds on `resolve_visual_baseline` over journal events, not the report file
- clutch/baseline.py:81 `resolve_visual_baseline` reads events, so the identity check runs against the journal signal
- Merged visual-baseline-fixtures records the judge identity in run.md as a workaround

Message: box-000842-7243fac3
