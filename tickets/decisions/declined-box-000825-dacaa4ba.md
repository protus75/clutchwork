---
id: declined-box-000825-dacaa4ba
kind: declined
link: box-000825-dacaa4ba
reopen_after_days: 30
---
`DiffBudgetGate` in `clutch/stages.py` counts every inserted line, including a generated `uv.lock` refresh, toward the 1500-line limit. On 2026-11-19 the first image-quality-gate attempt failed Check only on this budget: 1617 lines, of which `uv.lock` was 1268 and hand-written code about 350. The suggestion is to leave lock files out of the count or count them separately, and to add an authoring rule that a dependency refresh gets its own ticket.

The gate is doing what it was built to do. Its purpose, stated in its docstring, is to keep the diff small enough for the review prompt. The Review stage reviews the `uv.lock` change too: image-quality-gate-r1's review.md comments on the lock resolution. So leaving lock lines out of the count only would let a diff through that is larger than Review can take. A correct fix would also have to change what Review sees, which is a design decision, not a small repair. There is one incident, and it is already fixed. Diagnose split the work: image-quality-gate-r1 is a lock-only diff of 1277 lines that passed diff_budget and merged, and image-quality-checks merged. image-quality-gate-wiring is open with no lock change in it. The suggestion shows no current failure that this workaround does not handle. Reopen if a second dependency-adding ticket fails diff_budget mainly because of `uv.lock`, or if a lock-only refresh goes over the budget by itself, which splitting cannot fix. Then file one ticket that changes both the budget count and the Review diff rendering for generated lock files.

- clutch/stages.py:1465-1483 DiffBudgetGate compares artifact.inserted_lines with DIFF_BUDGET_INSERTED; its docstring says the cap exists so the review prompt fits its bound
- tickets/image-quality-gate-r1/ticket.md:23 records the first attempt: 1617 inserted lines, uv.lock 1268, hand-written about 350
- tickets/image-quality-gate-r1/checks.json: lock-only split diff of 1277 inserted lines; diff_budget verdict pass
- tickets/image-quality-gate-r1/review.md:3 shows Review checking the uv.lock resolution, so lock lines are part of the reviewed diff
- image-quality-gate-r1 and image-quality-checks are in the merged set; image-quality-gate-wiring is open

Message: box-000825-dacaa4ba
