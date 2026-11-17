---
id: tombstone-box-000604-57447cda
kind: tombstone
link: declined-box-000443-db18b23e
reopen_after_days: 14
---
Codex at its medium Implement tier keeps giving up on wide tickets within minutes. It replies `incomplete` with an empty diff, and each give-up spends a retry or escalation unit plus a Diagnose call. On 2026-11-17 this happened five times across evidence-envelope and supervise-every-route. evidence-envelope merged only once it was escalated to the high rung, and supervise-every-route went to the Reject queue. The message asks the engine to send the next attempt straight to the high rung after a fast, empty `incomplete`. It also asks Implement to answer `premise_failed` naming a split boundary when a ticket is too wide, instead of `incomplete`.

Record declined-box-000443-db18b23e already covers this. It found that codex quits Implement with no diff on large or wide renders and replies `incomplete`. It proposed routing those renders to a higher tier, which is the first half of this proposal. This message adds two more stems as examples, but the behavior and the fix are the same. The second half contradicts a rule in `clutch/specs/implement.md`, set after box-000399/000408: never report unfinished work as `premise_failed`, and use `incomplete` when you stopped early and nothing in the ticket is wrong. It would bring back the premise bounces that earlier sent buildable tickets to the Reject queue. The current behavior also has a working recovery path. `caps.failed_attempt` counts `incomplete` as a failed attempt, `caps.capability` reads the next attempt's tier and effort from the retry rung, and evidence-envelope merged once it reached the high rung. supervise-every-route went to the Reject queue because its Diagnose verdicts disagreed, and `confirm` can still release it. Reopen when either of these holds: a ticket whose `incomplete` attempts with empty diffs never reach the high rung before its caps run out, or such quits keep sending buildable tickets to the Reject queue after the escalation ladder has applied.

- declined-box-000443-db18b23e: on 2026-11-13 codex quit Implement with no diff on 7 of 15 renders of 80 KB or more, and on none of 16 smaller ones. It proposed sending large renders to a higher tier.
- clutch/specs/implement.md:84-86: `incomplete` means you stopped before finished work was committed and nothing in the ticket is wrong; never report unfinished work as `premise_failed`.
- declined-box-000399-63c8360a / tombstone-box-000408-fdc36464: premise_failed replies for unfinished work spent premise_bounce and sent a buildable ticket to the Reject queue.
- clutch/caps.py:51-56: `incomplete` counts as a failed attempt; clutch/caps.py:82-89: the next attempt's tier and effort come from the latest retry rung.
- Message: evidence-envelope merged once escalated to the high rung on attempt 2; supervise-every-route went to the Reject queue because Diagnose verdicts disagreed.

Message: box-000604-57447cda
