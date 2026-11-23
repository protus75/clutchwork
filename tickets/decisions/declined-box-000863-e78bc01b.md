---
id: declined-box-000863-e78bc01b
kind: declined
link: box-000863-e78bc01b
reopen_after_days: 30
---
The training-eval Implement run, which ended ok, noted that the evaluation description in the planning document docs/training-data-plan.md still says the eval report goes to the engine log. The merged training-eval change made that wording stale, and the run could not fix it because the file was outside its scope fence.

This is a plan-wording mismatch in a planning document. It does not show any wrong runtime behavior. The run ended ok, and nothing shows that an operator or stage acted on the stale sentence. The registry has declined many earlier reports of the same kind, where a planning document went stale after a merge and was outside the ticket's fence: 000447, 000594, 000605, 000811, 000856 and 000861. Reopen if a stage, prompt or operator decision is shown to have used this sentence and acted wrongly, for example a run that looked for the eval report in the engine log and failed.

- message class suggestion, origin training-eval, stage implement, outcome ok
- training-eval is in the merged set
- summary itself says the document is a historical plan and the drift is in its prose only
- prior declines of the same pattern: declined-box-000447-54115f00, declined-box-000594-ac4726ce, declined-box-000861-0b9acb13

Message: box-000863-e78bc01b
