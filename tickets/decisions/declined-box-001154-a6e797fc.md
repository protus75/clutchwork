---
id: declined-box-001154-a6e797fc
kind: declined
link: box-001154-a6e797fc
reopen_after_days: 30
---
When engine-serve-detach was implemented, the agent found that the historical introduction in the planning document docs/antigravity-plan.md still says `clutch engine serve` has no --detach option. That change has now added the option. The file was outside the ticket's scope fence, so the run left the sentence alone.

This is only a wording mismatch in a forward-looking planning document. It causes no wrong runtime behavior: the CLI, its help and the shipped guides decide what serve does, not this plan text. Earlier registry records turned down the same kind of report, where a plan sentence went stale after a merge and sat outside the fence (for example 000811, 000962 and 001130). Reopen within 30 days if a shipped guide, the command help or an operator prompt is found to rely on this plan text and tells operators that serve cannot detach.

- The message class is suggestion, from engine-serve-detach at the implement stage, with outcome ok.
- engine-serve-detach is in the merged set (commit 5d565dfd1).
- The stale text is in the planning document docs/antigravity-plan.md, not in engine code or a shipped host guide.
- Registry records 000811, 000962, 001021 and 001130 declined the same class: stale plan wording outside the fence.

Message: box-001154-a6e797fc
