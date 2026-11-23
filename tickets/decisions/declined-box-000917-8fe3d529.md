---
id: declined-box-000917-8fe3d529
kind: declined
link: box-000917-8fe3d529
reopen_after_days: 30
---
When requisition review runs as a panel, every member call gets its own full REQUISITION_STUCK_S (600 s) through `driver.race`, so a panel of size 3 could run for up to about 30 minutes. docs/stage-panels-plan.md says panel members share one stuck budget. The panel ticket for this surface chose not to share the budget and said the gap would be filed to the Suggestion Box, which is what this message does.

The gap is real: the code differs from the plan. But nothing shows it causing harm now. No routing row in config.yaml sets a `panel` for requisition_review, so every requisition review today is one call raced against one 600 s budget. The note reports no run that timed out, stalled or spent caps because a panel ran too long. The plan itself says the risk is bounded by size <= 3 (stage-panels-plan.md line 117). The worst case, 3 x 600 s, is a fixed bound, not a runaway. As filed, this is a mismatch with the plan wording plus speculative hardening, not a behavior gap that can happen today. Reopen if a requisition_review panel is configured and a panel review goes past a run or drain deadline, holds the commit lock long enough to block other work, or spends caps through a timeout that one shared budget would have stopped.

- clutch/requisition.py:284 and :295: `begin_watch(stuck_budget=REQUISITION_STUCK_S)` and `driver.race(..., REQUISITION_STUCK_S)` apply the budget to each call
- clutch/requisition.py:26: REQUISITION_STUCK_S = 600.0
- docs/stage-panels-plan.md:70 says members run under one stuck budget; line 117 says the risk is bounded by size <= 3
- tickets/review-panel-stage-use-requisition/ticket.md line 51 leaves the shared stuck budget out of scope on purpose and sends it to the Suggestion Box
- config.yaml has no `panel` entry, so no requisition_review panel is routed today
- The message cites no run, timeout or spent cap caused by a long panel review

Message: box-000917-8fe3d529
