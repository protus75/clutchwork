---
id: declined-box-001060-4e50783b
kind: declined
link: box-001060-4e50783b
reopen_after_days: 30
---
While implementing check-meta-fill-nested-stage, the agent reported that docs/how-clutch-works.md describes stage nesting more narrowly than the code now allows. The file was outside the ticket's scope fence, so the run did not change it. The run ended ok.

This is a documentation mismatch in a design document. It does not describe any wrong runtime behavior. The note does not quote the stale sentence, give its section, or say how the code now differs. It names no run that a reader misled by the doc got wrong. Registry records 000403, 000998 and 001007 declined the same kind of out-of-fence doc note from docs/how-clutch-works.md. Reopen if the stale nesting description leads an author, a reviewer or a Diagnose lesson into a wrong decision that costs a run, or if a report quotes the exact sentence and the code behavior it contradicts.

- message class suggestion, origin check-meta-fill-nested-stage, stage implement, outcome ok
- no stale sentence, section or contradicting code path is named
- precedent: declined-box-000403-d925564b, declined-box-000998-620886e1, declined-box-001007-c547823e (out-of-fence docs/how-clutch-works.md wording notes declined)
- neighbors unavailable (index_unreadable); not used as grounds

Message: box-001060-4e50783b
