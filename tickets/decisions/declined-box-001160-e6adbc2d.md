---
id: declined-box-001160-e6adbc2d
kind: declined
link: box-001160-e6adbc2d
reopen_after_days: 30
---
Proposes an authoring and requisition-review rule for tickets that move helper functions out of clutch/__main__.py into a domain module. Such a ticket would have to fence any test that checks which module owns or calls a function by reading the source tree (for example tests/integration/test_main_verb_groups.py). The trigger was a fence gap on mcp-control-and-tickets.

This is a class-prevention authoring rule drawn from one fence gap, and the ticket that hit it (mcp-control-and-tickets) has since merged. The message shows no runtime behavior that is wrong today. Its only cost was authoring or Implement friction on that one ticket, and it reports no measured repeat across other tickets. The registry has already declined several narrow fence-closure rules of the same kind: unfenced importers of a changed test module (001094), unfenced callers of deleted symbols (000555), tests that pin removed journal records (000619), and consumers of the step-kind vocabulary (000773). Reopen if, within the window, a second ticket that moves helpers out of clutch/__main__.py is parked premise_failed or fails Check because an AST call-ownership test it did not fence fails, with run evidence attached.

- mcp-control-and-tickets is in the merged set, so the triggering ticket landed
- Message class is suggestion from a session; it gives no stage, outcome or measured recurrence
- Same-shape fence-closure authoring rules were declined in declined-box-001094-9d305e08, declined-box-000555-2528178b, declined-box-000619-29321b17 and declined-box-000773-2d21b8d4
- Neighbor index unavailable (index_unreadable); no neighbor evidence either way

Message: box-001160-e6adbc2d
