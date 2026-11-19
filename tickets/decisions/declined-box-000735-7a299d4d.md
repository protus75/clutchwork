---
id: declined-box-000735-7a299d4d
kind: declined
link: box-000735-7a299d4d
reopen_after_days: 30
---
The merged `engine calibrate` table only counts Implement calls that finished. A killed or timed-out call journals an empty-body `effect_intent` and no `effect_completion`, so its provider and model are never in the journal and it drops out of the table. The note worries that once estimates shrink to calibrated AI minutes, more calls will hit the stuck kill and the table's p90 will drift lower each window. It proposes journaling the provider and model somewhere a killed call can be read, and counting each killed call at its kill time.

The gap is real but its harm is predicted, not shown. The merged estimate-calibration ticket left killed and timed-out calls out on purpose (Scope out). It measured them at 29 intents against 1,444 completions, about 2%, which is too few to move the p90 in a meaningful way. The feedback loop the note describes only starts after calibrated estimates are written into tickets, and that needs estimate-calibration-author plus newly authored budgets. No calibration table or kill rate has yet been observed going wrong. Today stuck budgets are about 20 times the real minutes, so stuck kills are rare. Reopen when, after calibrated estimates are in use, the share of Implement intents with no completion in one `calibration.every` window rises above about 5%, or a calibrated p90 falls below a stuck kill time actually observed for the same provider and model.

- tickets/estimate-calibration/ticket.md Scope out: 'Killed or timed-out Implement calls, which journal no completion and so no model. On 2026-11-17 this repo's journal held 29 such Implement intents against 1,444 completions.'
- clutch/effects.py:35 appends EFFECT_INTENT with an empty body {}, so provider and model appear only on the completion's cost
- tickets/estimate-calibration/ticket.md Goal: actual minutes are about a tenth of the estimates, so stuck (2x estimate) is about 20x the real time and stuck kills are rare today
- estimate-calibration-author (part 3, which feeds calibrated estimates into authoring) is the first point where the predicted downward feedback could begin
- Open ticket exec-seam-unwind-capture keeps the output of killed calls but does not touch the journal or calibration, so it is not a duplicate

Message: box-000735-7a299d4d
