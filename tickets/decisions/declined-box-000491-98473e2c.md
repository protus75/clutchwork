---
id: declined-box-000491-98473e2c
kind: declined
link: box-000491-98473e2c
reopen_after_days: 30
---
Proposes that `clutch/status.py::Admission` reject a `refuse` outcome with a blank `paved_road` when it is built. It also proposes that `triage.validate_ids` pass the admission's road through `UnknownBoxId`, so the CLI prints that road and stops using the suffix hard-coded in `clutch/__main__.py::main`.

Nothing is broken at runtime today. The empty road in `_box_admission` was the actual bug, and the merged ticket paved-roads-name-verbs fixed it. Line 149 now returns the road ``name ids that `clutch status` lists``, and `tests/unit/test_paved_roads.py` pins it. Every other `Admission("refuse", ...)` in `clutch/status.py` either passes a road or splats a (message, road) tuple. The operator also always sees a road: the `UnknownBoxId` handler prints `-- name ids that clutch status lists`, which says the same thing. The road living in two places is duplication with matching output. The construction-time check guards against a defect that does not exist yet. Both are prevention and cleanup, not a repair of harmful behavior. Reopen if any refuse admission reaches an operator with a blank road, or if the CLI's unknown-id suffix and `_box_admission`'s road come to say different things.

- clutch/status.py:149 `_box_admission` returns Admission("refuse", f"unknown box id {id}", "name ids that `clutch status` lists")
- clutch/status.py:80-184: every refuse Admission passes a road or splats a (message, road) tuple from verdict_refusal
- clutch/__main__.py:710-711 UnknownBoxId handler prints `-- name ids that clutch status lists`, the same text without backticks
- tests/unit/test_paved_roads.py:32 pins the box admission road; tests/integration/test_triage.py:605 and tests/integration/test_ask.py:75 pin the CLI suffix
- tickets/paved-roads-name-verbs/ticket.md:43 shows the instance fix merged

Message: box-000491-98473e2c
