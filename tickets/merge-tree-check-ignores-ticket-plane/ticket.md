---
state: confirmed
source: box:suggestion
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/mergequeue.py::MergeQueue._finish
- clutch/merge.py::write_squash
- clutch/git.py::Git._run

## Goal / Why
After a correct merge, serve keeps running. Today `MergeQueue._finish` compares the whole `main^{tree}` (or the recovery squash commit's tree) with `checked_tree`, the worktree tree Check validated. Ticket-plane commits (run records, decisions, roadmap links) and other legitimate commits move main between Check and the squash and change `tickets/` in that tree. The comparison then fails, `_finish` journals a TREE_MISMATCH hold and raises `TreeMismatch`, and serve's cleanup handler exits 1. This happened at 2026-11-21 05:21:33Z after `index-box-neighbors` merged (error `checked tree c0c0f72b... differs from main tree 00042d6a...`) and earlier at 03:08:58Z for `evidence-captures`. With `scheduler.parallel` max_runs 2 it repeats whenever two tickets merge close together. After this ticket a difference confined to ticket-plane paths (under `tickets/`, or the roadmap file `docs/roadmap.md`, whose `link`, `strike` and `refile` commits the roadmap driver and operators make as ticket-plane commits; the three crashes above each followed such a roadmap commit) is not a mismatch. A difference in any other path is still a mismatch and is held exactly as before.

This is an orchestration cause: it breaks runs while it sits, hence P0.

## Boundary contract
### Merge-queue tree validation
- disposition: extend
- owner: clutch/mergequeue.py (`MergeQueue._finish`)
- consumers: serve's merge admission, drain's merge admission, the TREE_MISMATCH hold and notification readers
- observable change: when `source^{tree}` differs from `checked_tree`, `_finish` lists the differing paths with `git diff --name-only <checked_tree> <source tree>` through `ctx.git._run`. It treats the trees as matching when every differing path is under `tickets/` (use the `TICKETS_DIR` constant from its owner, not a literal) or is exactly the roadmap file (use `roadmap.ROADMAP` from `clutch/roadmap.py`, not a literal; `clutch.roadmap` leads to `clutch.runner` and then `clutch.merge`, so import it inside the function, not at module level, if a module-level import would be a cycle). Any other differing path, or a git error while listing them (fail closed), keeps the existing behavior: TREE_MISMATCH hold with `checked_tree` and `main_tree` unchanged, then `TreeMismatch` raised.
- compatibility: restoration of the intended invariant (the merged code equals the checked code). Hold body shape, `TreeMismatch` and the recovery-replay `source` choice are unchanged. Tests that fake `main^{tree}` with a non-tree string still get a mismatch via the fail-closed path.
- acceptance: a main that moved only in `tickets/` or `docs/roadmap.md` between Check and squash merges with no hold and no exception; a main that moved in a code path holds and raises.
- tests: new unit test with a fake git seam; new integration test with a real repository
- post-merge source of truth: clutch/mergequeue.py

## Scope in / Scope out
Scope in: the tree comparison in `MergeQueue._finish` as described above, plus a private method only if it is needed to unit-test the comparison through the fake git seam. Two new test files.

Scope out: making a real mismatch stop holding-and-raising (it still raises `TreeMismatch` and still stops serve; changing that is a separate decision and needs its own ticket); `merge.write_squash`; the retro-bridge tree check at `clutch/merge.py` line 356; documentation (no document describes the exact comparison). Existing tests are not edited.

Class prevention: the new integration test is the standing guard that ticket-plane movement never trips the check.

## Scope fence
- clutch/mergequeue.py
- tests/unit/test_mergequeue_tree_check.py
- tests/integration/test_mergequeue_tree_moved.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_mergequeue_tree_check.py` passes. With a fake git whose tree diff lists only `tickets/x/run.md`, and again with one that lists only `docs/roadmap.md`, and once with both together, `_finish` returns an ok StageResult, not a TreeMismatch and no hold signal.
2. The same unit test file asserts that a diff listing `clutch/a.py` raises `TreeMismatch` and journals one TREE_MISMATCH hold, and that a diff call raising `GitError` also raises `TreeMismatch`, not `GitError`.
3. `./dev.py test tests/integration/test_mergequeue_tree_moved.py` passes. A real repository has a ticket ready to merge, then a commit touching only `tickets/other/run.md` lands on main after Check, and a second case where a commit touching only `docs/roadmap.md` does. The test asserts the ticket ends merged, `queue.paused` is False, and no TREE_MISMATCH signal is in the journal. A result of TreeMismatch is the wrong outcome.
4. In the same integration test, a code-path commit landing on main after Check still raises `TreeMismatch` and pauses the queue, not a silent merge.
5. `./dev.py test tests/integration/test_mergequeue.py tests/integration/test_merge.py tests/integration/test_serve_admission.py tests/integration/test_daemon_composition.py` passes with those files unmodified.

## Verification
```
./dev.py test tests/unit/test_mergequeue_tree_check.py tests/integration/test_mergequeue_tree_moved.py tests/integration/test_mergequeue.py tests/integration/test_merge.py tests/integration/test_serve_admission.py
```

## Definition of rejected
A branch that skips the tree check, compares only the squash commit against itself, or ignores differences outside `tickets/` and `docs/roadmap.md` is rejected. So is one that edits an existing test to make it pass.

## Time budget
- expected: 25m
- stuck: 50m
