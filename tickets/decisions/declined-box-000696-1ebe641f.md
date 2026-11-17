---
id: declined-box-000696-1ebe641f
kind: declined
link: box-000696-1ebe641f
reopen_after_days: 14
---
The report says `clutch ticket order` writes its priority or runs-before edit to the working tree without committing it. It says the running drain then left the edited P0 ticket drop-closed-sets-follow-up-test out of its queue and dispatched plan-drain-author-in-parallel first, the opposite of the requested order. The proposed fix is for order to commit its edit through intake.

Leaving the edit uncommitted is by design, and the drain already commits pending edits. The order command's help says it edits ordering 'for intake to commit' and writes only the working tree. `clutch/drain.py` calls `intake(..., stems=None)` on every loop (lines 296 and 399). With `stems=None`, `clutch/tickets.py::intake` commits every pending ticket file, modified ones included, unless validation refuses it. So the proposed fix, having order commit through intake, repeats what the drain already does on its next loop. The problem in the report is more likely one of two things: intake refused the edited ticket, or the drain picked its queue before the next intake ran. The report shows neither, so it cannot back one bounded repair. Both stems in the report, drop-closed-sets-follow-up-test and plan-drain-author-in-parallel, have since merged, so nothing is held up now. Reopen if a new incident shows a ticket edited by `clutch ticket order` staying uncommitted through a full drain loop with no intake refusal recorded, or being refused by intake with the refusal never shown.

- clutch/__main__.py:718 order help: 'Edit priority and runs-before ordering for intake to commit.'; writes: 'Ticket in the working tree.'
- clutch/drain.py:296 and :399 call intake(..., stems=None) each loop before dispatch
- clutch/tickets.py:764-802 intake with stems=None commits every pending modified ticket that validates
- drop-closed-sets-follow-up-test and plan-drain-author-in-parallel are both in the merged set

Message: box-000696-1ebe641f
