---
id: declined-box-001103-75d86b43
kind: declined
link: box-001103-75d86b43
reopen_after_days: 30
---
The training-eval-ship-gate Implement run finished ok. It noted that, in docs/roadmap.md, the prose above the 0.5.0 release gate block still calls the training-eval ship clause unchecked. The ticket only allowed edits to the gate block itself, so the run left that prose alone.

This is a stale sentence in a planning document. No runtime behavior is wrong: the gate block that the engine reads was updated, and the prose next to it does not affect scheduling, gates or merges. The registry has repeatedly declined the same class of report (stale planning-document wording left outside a ticket's fence; for example 000978, 001021 and 000811). Reopen if a reader of that prose, such as a roadmap driver step or a release accept review, is shown to make a wrong decision because of it.

- Message class suggestion, origin training-eval-ship-gate, stage implement, outcome ok
- training-eval-ship-gate is in the merged set
- The stale text is prose in docs/roadmap.md, not the gate block the engine runs
- Same class declined before: declined-box-000978-0f775303, declined-box-001021-44ec8a54, declined-box-000811-773ed1cc

Message: box-001103-75d86b43
