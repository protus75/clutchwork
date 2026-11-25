---
id: tombstone-box-001158-ad277c83
kind: tombstone
link: review-internal-contradictions
reopen_after_days: 30
---
Proposes that requisition review check each concrete input/output example in a ticket's Scope in and Acceptance criteria against the ticket's own stated formula, after a roadmap-align-pypi-versions-r2 draft said minor+1 maps 1.9.0 to 2.0.0 instead of 1.10.0.

The merged ticket review-internal-contradictions already makes requisition review snag any two statements in a ticket that cannot both hold. Its own example is 'a named fixture and the result a criterion expects from it', which covers a stated formula that disagrees with a worked example. The originating ticket, roadmap-align-pypi-versions-r2, has merged, and the message reports no run or park caused by a missed formula/example mismatch after that rule landed. Reopen if a requisition review approves a ticket whose worked example contradicts its own stated formula and that defect costs an Implement or Check cycle.

- tickets/review-internal-contradictions/ticket.md:25 adds the snag bullet 'Two statements anywhere in the ticket cannot both hold, for example a declared signature and a call to it, or a named fixture and the result a criterion expects from it.'
- roadmap-align-pypi-versions-r2 is in the merged set
- declined-box-001152-4815a7b2 declined a similar class-prevention request for the earlier roadmap-align-pypi-versions premise failure

Message: box-001158-ad277c83
