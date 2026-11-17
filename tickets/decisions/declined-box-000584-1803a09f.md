---
id: declined-box-000584-1803a09f
kind: declined
link: box-000584-1803a09f
reopen_after_days: 30
---
Proposes a host-authoring guide rule that a ticket adding a docs/roadmap.md row names the row by stem and places it as the table's last row, never by a literal row number or 'after row N', with criteria that check the row by stem. Trigger: the closed-sets-single-owner draft pinned row 94, and rows 94-107 were added before it ran. Following it as written would have duplicated row 94, which roadmap.parse refuses. The operator fixed the draft by hand in 2f4a8fe6 before any run.

The defect was found and fixed by hand before any run, so no run failed, no caps were spent, and the roadmap parse never broke. If a ticket did duplicate a row, roadmap.parse (clutch/roadmap.py:91) already refuses with a 'make row unique' paved road. The test suite would make Check fail instead of letting a broken roadmap merge. The request is an authoring-guide rule against a ticket going stale while it waits. Record 000342 declined the same class (a copied block went stale while the ticket waited), and records 000431-000437 declined guide-rule additions without a failed run. Reopen if a ticket run or an Author-stage roadmap_row draft actually fails or parks because a pinned roadmap row number or 'after row N' placement went stale, or if a duplicate row reaches main.

- clutch/roadmap.py:91 parse raises Refusal on a duplicate row number, with a paved road
- clutch/docs/host-authoring.md has no roadmap row rule today (grep 'roadmap' finds nothing)
- Message: the stale row 94 pin in closed-sets-single-owner was repaired by hand in 2f4a8fe6 before any run
- declined-box-000342-ff84bb14: a near-identical 'ticket text goes stale before it runs' authoring-rule proposal was declined

Message: box-000584-1803a09f
