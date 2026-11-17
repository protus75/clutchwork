---
id: declined-box-000622-dfa19f13
kind: declined
link: box-000622-dfa19f13
reopen_after_days: 30
---
An Implement run of checkpoint-counts-settled noted that row 100 of docs/roadmap.md still describes CHECKPOINT_INTERVAL as a live checkpoint trigger. The merged cadences-count-runs and checkpoint-counts-settled changes removed that wall-clock trigger, so the row's wording is now stale.

This is a wording mismatch in a planning document. It is not a runtime behavior gap. docs/roadmap.md is a forward-looking roadmap, and no engine path reads the row's prose. The roadmap parser uses the row's stem and status, not its description of checkpoint triggers, so the stale sentence cannot cause incorrect runtime behavior. The registry has declined the same class of note several times: stale roadmap or plan prose reported by an Implement run whose fence excluded the doc (000613 for a stale coverage-floor line in docs/roadmap.md, 000621 for the stale retro elapsed trigger in the same file after cadences-count-runs, plus 000447, 000526, 000616). Reopen if the roadmap driver or an Author draft is shown to act on this row's CHECKPOINT_INTERVAL wording, for example by authoring a ticket that restores or depends on the removed timer.

- Message class suggestion, origin checkpoint-counts-settled, stage implement, outcome ok: no failure was reported.
- checkpoint-counts-settled and cadences-count-runs are both in the merged set; the code change that made the row stale has landed.
- declined-box-000621-b11145f0 declined a stale docs/roadmap.md description of the replaced retro elapsed trigger after cadences-count-runs.
- declined-box-000613-0126575c declined a stale docs/roadmap.md line made out of date by a merged ticket.
- declined-box-000501-39826928 records that CHECKPOINT_INTERVAL in clutch/checkpoint.py was the wall-clock checkpoint cadence that the run-count work replaced.

Message: box-000622-dfa19f13
