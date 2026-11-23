---
id: declined-box-000994-d9bb22f7
kind: declined
link: box-000994-d9bb22f7
reopen_after_days: 14
---
The engine filed a depends-stage failure report: requisition-review-compact-context was blocked because its only dependency, requisition-review-approval-reuse, was rejected. Both tickets are now `state: rejected` on main, so nothing is still waiting on this dependency.

This report asks for the dependent to be re-wired, re-scoped or rejected. The dependent, tickets/requisition-review-compact-context/ticket.md, is already `state: rejected`, so the operator has already done the last of those three. Its dependency, requisition-review-approval-reuse, and that ticket's sibling requisition-review-input-reuse are also `state: rejected`. Nothing confirmed is still held by the broken edge, so there is no current runtime gap for a ticket to fix. Records 000321 and 000327 handled earlier depends reports the same way once the block no longer held anything back. The fence-gap rework cost that led to the approval-reuse rejection already has its own open ticket, implement-fence-gap-keeps-branch. Reopen if a successor to requisition-review-compact-context is confirmed with a `## Depends on` entry that names a rejected or abandoned stem.

- tickets/requisition-review-compact-context/ticket.md:2 state: rejected; its ## Depends on lists requisition-review-approval-reuse
- tickets/requisition-review-approval-reuse/ticket.md:2 state: rejected
- tickets/requisition-review-input-reuse/ticket.md:2 state: rejected
- Neither stem is in the open_tickets or merged lists
- Precedent: declined-box-000321-cda44a53 and declined-box-000327-a42c7f27 (depends reports with no remaining block)
- Open ticket implement-fence-gap-keeps-branch covers the approval-reuse fence-gap redo cost

Message: box-000994-d9bb22f7
