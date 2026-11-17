---
id: declined-box-000616-3cc90496
kind: declined
link: box-000616-3cc90496
reopen_after_days: 30
---
During the seams-passed-not-built Implement run, the agent reported that docs/roadmap.md and docs/journal-sql-refactor-plan.md still describe how the scheduler used to read the journal, and that the merged change has made those descriptions out of date.

Only planning documents are stale, and the note names no runtime behavior that is wrong as a result. The registry has declined the same kind of stale-planning-doc note several times (000447, 000526, 000530, 000594, 000595, 000605, 000613). Reopen if an engine stage, prompt or operator decision is shown to have acted on the stale text and produced wrong behavior.

- message class suggestion, origin seams-passed-not-built, stage implement, outcome ok
- seams-passed-not-built is in the merged set
- registry precedent: declined-box-000605-4e62ffe8 and declined-box-000613-0126575c declined stale roadmap/plan doc notes
- no proposed_paths, no fixed_failure, no report describing a runtime fault

Message: box-000616-3cc90496
