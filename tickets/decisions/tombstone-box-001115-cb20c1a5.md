---
id: tombstone-box-001115-cb20c1a5
kind: tombstone
link: serve-dispatch-fresh-ticket
reopen_after_days: 14
---
Check's scope_fence gate on io-helpers-config attempts 3 and 4 flagged tests/integration/test_shared_fakes_guard.py as outside the fence. The committed ticket.md (lines 24 and 82) fenced that file after attempt 2's finding, so Check was judging a stale, pre-edit Ticket object and not the edited ticket.

This is the same stale-ticket defect the open tickets already cover. In serve-dispatch-fresh-ticket, dispatch runs an in-memory Ticket parsed before the operator's fence edit, and gather_safety_evidence takes scope_fence from that stale object. Its sibling, daemon-continuation-fresh-ticket, covers TicketWriter replacing the offered Ticket with a held continuation's prior.ticket. The io-helpers-config diagnosis itself calls this an engine defect in the fence source, not an implementer error. io-helpers-config has since merged, so the only remaining harm is the class defect, and those tickets own it. Reopen if Check still judges a pre-edit fence after both tickets merge.

- tickets/io-helpers-config/ticket.md:24 and :82 list tests/integration/test_shared_fakes_guard.py in the fence
- tickets/io-helpers-config/attempts/3/harvest.json and attempts/4/harvest.json: 'tests/integration/test_shared_fakes_guard.py is outside `## Scope fence`'
- tickets/io-helpers-config/diagnosis.json: 'Engine defect, not implementer ... ScopeFenceGate (artifact.scope_fence) flagged it as outside the fence in attempts 3 and 4 alike'
- open ticket serve-dispatch-fresh-ticket: stale in-memory Ticket gives a scope_fence failure on newly fenced paths (shared-git-fake-unit-5)
- open ticket daemon-continuation-fresh-ticket: held continuation replaces the edited Ticket and Check keeps judging the pre-edit fence
- tombstone-box-001098-53333552 already linked a similar report to serve-dispatch-fresh-ticket

Message: box-001115-cb20c1a5
