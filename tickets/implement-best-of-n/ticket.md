---
state: rejected
source: box:roadmap_row
priority: P3
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- `panel-combiners`
- `serve-parallel-dispatch-r2`

## Context
- clutch/panel.py
- docs/stage-panels-plan.md

## On-demand
- clutch/stages.py
- clutch/driver.py
- clutch/runner.py
- clutch/config.py
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 87 (`implement-best-of-n`, release 0.7.0), from `docs/stage-panels-plan.md` sections 2-4. A routing row for `implement` with `panel: {size: N, combine: best-of-n}` makes the Implement stage run N members. Each member works in its own worktree named `<worktree_root>/<stem>.m<k>`. Check runs on every candidate. The engine keeps the candidate that passes Check, breaking ties by the fewest soft findings and then the smallest inserted-line count. It retires the other worktrees. Today Implement is always one call in one worktree. Panel size stays 1 by default, so existing behavior is unchanged. Decision 19 of `docs/roadmap.md` already chose this selection rule.

## Boundary contract
### Best-of-n selection
- disposition: extend
- owner: clutch/panel.py
- consumers: the Implement stage in clutch/stages.py
- observable change: given candidate results (check passed, soft finding count, inserted lines), the combiner returns the kept candidate index. Order is Check pass, then fewest soft findings, then smallest inserted-line count, then lowest member index. When no candidate passes Check, it returns none.
- compatibility: the review, requisition review, diagnose and triage combiners are unchanged. The function stays pure with no I/O.
- acceptance: unit tests cover each tie-break level and the none case.
- tests: tests/unit/test_implement_best_of_n.py
- post-merge source of truth: clutch/panel.py

### Implement fan-out
- disposition: extend
- owner: clutch/stages.py
- consumers: clutch/runner.py and the journal run record
- observable change: with a best-of-n panel row, Implement creates one worktree per member, runs Check on each candidate, applies the selection, and retires the other worktrees through `git.py` (`worktree remove` plus `prune`). The kept candidate continues as the ticket branch, and the run record names the kept member and the retired members. When no candidate passes Check, the stage fails as a failed Check does today.
- compatibility: size 1, or no panel key, takes today's single-worktree path unchanged.
- acceptance: fake-driven tests show N worktrees created, Check run N times, and N-1 worktrees removed.
- tests: tests/unit/test_implement_best_of_n.py
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
Scope in:
- Add the best-of-n selection function to clutch/panel.py. Use it if `panel-combiners` already added one, otherwise add it.
- Add the Implement fan-out in clutch/stages.py, with per-member worktrees through `clutch/git.py` argv wrappers.
- Update `docs/how-clutch-works.md` section 4.4 to describe best-of-n.
- Update the Status and Roadmap lines in `docs/stage-panels-plan.md` so row 87 counts as merged.

Scope out:
- Review panels, the scorecard and the config surface-fit refusal, which are already merged.
- Side-by-side review of candidates, which the plan lists as a later combiner.
- Any change to the default panel size.

Tests go in a new file and use fakes only. `clutch/driver.py`, `clutch/runner.py` and `clutch/config.py` are fenced only because a forced call-site or config edit may land there; make no edit in them unless the fan-out requires it.

## Scope fence
- clutch/panel.py
- clutch/stages.py
- clutch/driver.py
- clutch/runner.py
- clutch/config.py
- docs/how-clutch-works.md
- docs/stage-panels-plan.md
- tests/unit/test_implement_best_of_n.py

## Acceptance criteria
1. With results (A: check failed, B: passed with 3 soft findings, C: passed with 1 soft finding), the selection returns C, not A or B. Check: `./dev.py test tests/unit/test_implement_best_of_n.py -k fewest_soft`.
2. With equal soft findings, the candidate with the fewer inserted lines is kept, and with those also equal the lowest member index is kept. Check: `./dev.py test tests/unit/test_implement_best_of_n.py -k tie_break`.
3. When every candidate fails Check, the selection returns `None`, not index 0. Check: `./dev.py test tests/unit/test_implement_best_of_n.py -k none_pass`.
4. A fake-driven Implement stage with size 3 creates worktrees `<stem>.m0` to `<stem>.m2`, runs Check 3 times, and removes exactly the 2 unkept worktrees. Check: `./dev.py test tests/unit/test_implement_best_of_n.py -k fanout`.
5. A route without a panel key creates exactly one worktree and takes the pre-existing path. Check: `./dev.py test tests/unit/test_implement_best_of_n.py -k default_single`.

## Verification
```
./dev.py test tests/unit/test_implement_best_of_n.py
```

## Definition of rejected
The branch is rejected if a default (no panel key) Implement run changes behavior. It is also rejected if the selection reads the clock or the disk, or if a non-kept worktree is left behind after the stage.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one pure selection function plus one stage fan-out, tested with fakes; the calibration table shows Implement runs of this size finish well under 15m.
