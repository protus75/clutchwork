---
id: declined-box-001152-4815a7b2
kind: declined
link: box-001152-4815a7b2
reopen_after_days: 60
---
Proposes that requisition review or ticket lint check any ticket that claims a fixed set of docs/roadmap.md release sections against the release headings actually in docs/roadmap.md at HEAD. It is offered as class prevention after roadmap-align-pypi-versions ended premise_failed on a false 'five release sections' premise.

This is prevention against a single incident, not a current runtime gap. The failing ticket was already caught: Implement's premise check stopped it with premise_failed, and roadmap-release-slot-shift has replaced it with the correct six sections. Ticket lint cannot reliably tell when free prose 'claims a fixed set' of sections, so the rule would rest on a reviewer's judgement. That makes it an authoring-rule preference, like the roadmap-row placement rule declined in box-000584, and the message names no measurable post-change observation. Reopen if within 60 days a second ticket loses a run cycle (premise_failed, Reject queue, or a rework) because its release-section count or list disagreed with the docs/roadmap.md headings at its base commit.

- Message class suggestion, origin session, cites a single incident: roadmap-align-pypi-versions premise_failed.
- Open ticket roadmap-release-slot-shift already replaces the rejected ticket and states the correct six release sections plus the 0.3.0 last-group heading.
- Implement's existing premise check caught the false premise before any wrong change merged.
- declined-box-000584-1803a09f declined a similar authoring rule about docs/roadmap.md row references after one hand-fixed incident.
- Neighbor index unavailable (index_unreadable); not used as grounds.

Message: box-001152-4815a7b2
