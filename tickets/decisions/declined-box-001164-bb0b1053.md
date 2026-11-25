---
id: declined-box-001164-bb0b1053
kind: declined
link: box-001164-bb0b1053
reopen_after_days: 30
---
The session proposes two changes to ticket lint. First, warn when a ticket changes a contract that a docs/ document in its Context describes, while that document is left out of the fence and Scope out forbids editing docs. Second, stop scanning Scope out for mentions of docs that are not fenced. The message cites no ticket, run or lint output.

This is a suggested authoring-time lint with no evidence behind it. It names no ticket that ran into the problem, no stale doc that misled a run, no lint finding that fired wrongly on a Scope out mention, and no attempt or cap it cost. The closest earlier case is declined-box-000756-c97e1d39: a Scope out that barred a plan document was found and fixed by hand before it ran. The many stale plan-doc reports, such as 001161, 001157 and 001130, were each declined as wording mismatches in forward-looking documents with no runtime harm. The second half also asks to remove an existing lint check without showing that the check produced a false refusal. Reopen within 30 days if a run spends an attempt, a review round or a premise bounce because a doc contract was left unfenced while Scope out barred docs, or because the current Scope out scan wrongly refused a sound ticket. Cite the stem, the lint or review output, and the attempt it cost.

- The message has no stage, outcome, report, proposed paths or incident reference.
- declined-box-000756-c97e1d39: a similar Scope out barring a plan doc was fixed by hand before any run and declined as a class rule.
- Records such as declined-box-001161-4ece8026, 001157-4d6a9f8b and 001130-6d860266 decline stale docs outside the fence as wording mismatches with no runtime harm.
- No open ticket or merged stem covers this exact lint rule, so tombstone does not apply.

Message: box-001164-bb0b1053
