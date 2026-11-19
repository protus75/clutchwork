---
id: declined-box-000832-4ba0215c
kind: declined
link: box-000832-4ba0215c
reopen_after_days: 30
---
A retro/58 finding says hand-built SimpleNamespace stand-ins for Route, the engine config and Ticket in several unit and integration tests no longer match the real types. Because of that drift, route-kinds-filter-r1, projection-leftovers and status-hot-paths each passed their focused Verification and then failed the full unit suite when production code began reading a field the stand-in lacked. The proposed fix replaces those stand-ins with shared in-memory builders that create real Route, config and Ticket objects.

The proposal only changes test fixtures. The stand-ins do not cause wrong runtime behavior in the shipped engine. The harm was wasted pipeline cycles: Implement runs, premise_bounce units and reject diagnoses on three tickets. Open ticket requisition-review-stand-in-closure was filed from the same retro/58 window, cites the same three tickets and the same test files, and fixes that harm at the review stage. Its review rule finds stand-ins that reach a newly read attribute so the ticket can fence them, and it sets a measurable aim of no more stand-in premise_bounces. A second ticket rewriting fixtures across hot test files (test_watch.py) would overlap that fix and collide with parallel tickets, as the finding's own overcorrection risk warns. Reopen if a premise_bounce or full-suite failure from a stand-in missing a newly read field happens again within 30 days after requisition-review-stand-in-closure merges. That would show the review rule is not enough and a shared real-type builder is needed.

- Message test_issue is 'drift' and proposed_paths are all under tests/; no production path is proposed.
- tickets/requisition-review-stand-in-closure/ticket.md Goal names the same incidents: route-kinds-filter-r1 (route.kinds vs SimpleNamespace in test_gemini_adapter.py/test_qwen_adapter.py), projection-leftovers (Redactor.from_config vs SimpleNamespace configs in test_drain_driver_overlap.py/test_driver_hooks.py), status-hot-paths (Ticket.scope_fence vs ticket stand-ins).
- That ticket's measurable aim is that later retro windows show no premise_bounce from a stand-in missing an attribute newly read under Scope in.
- The finding's overcorrection_risk warns that replacing stand-ins broadly crosses hot files (test_watch.py, test_daemon_composition.py) and collides with parallel tickets.

Message: box-000832-4ba0215c
