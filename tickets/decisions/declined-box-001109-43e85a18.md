---
id: declined-box-001109-43e85a18
kind: declined
link: box-001109-43e85a18
reopen_after_days: 30
---
The suggestion asks ticket lint to flag any test file named in `## Verification` that appears in none of `## Scope fence`, `## Context` or `## On-demand`. It cites retro-due-one-owner, which was parked premise_failed at dispatch on a 'verification-path-unverified' requisition snag about tests/unit/test_serve_dispatch_containment.py, after the same reviewer had approved the ticket at authoring.

The proposed lint would not have caught the incident it cites. In the committed tickets/retro-due-one-owner/ticket.md, tests/unit/test_serve_dispatch_containment.py is listed in `## Scope fence` (line 98) and in `## On-demand` (line 27), and the file exists in the repo. A Verification-path-missing-from-sections check would have passed that ticket, so the reported harm came from something else, most likely reviewer variance or a different defect. retro-due-one-owner has also merged, so nothing is still blocked. Without an incident where a Verification test path really was missing from every one of those sections, this is speculative hardening. Reopen if a run is lost because a `## Verification` test path was absent from Scope fence, Context and On-demand. The report should include that ticket's text showing the absence.

- tickets/retro-due-one-owner/ticket.md:98 lists tests/unit/test_serve_dispatch_containment.py under ## Scope fence
- tickets/retro-due-one-owner/ticket.md:27 lists the same file under ## On-demand
- tests/unit/test_serve_dispatch_containment.py exists on main
- retro-due-one-owner is in the merged set
- clutch/tickets.py has no verification-path rule, but the cited ticket would satisfy the proposed rule anyway

Message: box-001109-43e85a18
