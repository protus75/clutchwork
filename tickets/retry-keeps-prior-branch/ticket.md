---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- implement-skips-full-suites

## Context
- clutch/stages.py::prepare_worktree
- clutch/stages.py::implement
- clutch/stages.py::prior_attempts
- clutch/journal.py::run_terminals
- clutch/git.py::Git.rebase
- clutch/git.py::Git.worktree_add
- clutch/git.py::RebaseRefused
- tests/fakes.py
- tests/integration/conftest.py
- tests/unit/test_specs.py::test_diagnose_spec_states_attempt_starting_point
- docs/how-clutch-works.md#4.1 Worktree

## On-demand
- clutch/specs/implement.md
- clutch/specs/diagnose.md

## Goal / Why
Every retry throws away the previous attempt's code. `prepare_worktree` deletes the stem's branch and branches again from main, and the Diagnose prompt says "Every attempt starts from the merge base, so no earlier diff survives". When Check or Review fails an attempt whose code was mostly right (a missing test, one doc sentence, one out-of-fence test the rework then fences), the next attempt redoes the whole change: 10–20 minutes of Implement plus a full Check. On 2026-11-21 most Review failures said the code was sound and listed only gaps ("Redo all of that work from the merge base"). After this ticket, a retry that follows a `gate_failed` terminal at stage `check` or `review` starts from the failed branch rebased onto main. Implement then fixes only what the findings name. Every other retry, including Implement failures (`premise_failed`, `incomplete`, `timeout`) and merge-conflict reruns, still starts fresh from main.

## Boundary contract
### Attempt worktree start
- disposition: extend
- owner: clutch/stages.py::prepare_worktree and clutch/stages.py::implement
- consumers: Implement and every retry
- observable change: `prepare_worktree(ctx, stem, *, keep=False)`. When `keep` is true and branch `<stem>` exists, it removes only the old worktree, attaches a worktree to the existing branch with a new `Git.worktree_attach(dir, path, branch)` (`git worktree add <path> <branch>`) and runs `ctx.git.rebase(path, MAIN)`. If the rebase raises `GitError` (which `RebaseRefused` subclasses; `Git.rebase` already runs `rebase --abort` before raising it), it falls back to today's teardown-and-create. `implement` passes `keep=True` only when the stem's latest run terminal (`run_terminals`) has `to == "gate_failed"` and `stage` in `{"check", "review"}` and no `merge_conflict_rerun` signal is newer than it
- compatibility: `keep=False` (the default, and every other caller) is byte-for-byte today's behavior; first attempts, Implement failures and conflict reruns start fresh as today
- acceptance: criteria 1 to 3
- tests: tests/integration/test_retry_keeps_branch.py, tests/integration/test_git.py and tests/unit/test_retry_keep_decision.py
- post-merge source of truth: clutch/stages.py

### Implement and Diagnose prompts on the starting point
- disposition: replace
- owner: clutch/specs/implement.md and clutch/specs/diagnose.md
- consumers: Implement and Diagnose
- observable change: Implement's Task says that when the branch already holds commits from a prior attempt, it keeps what the retry findings don't contradict and changes only what they name, without redoing the change; Diagnose's sentence "Every attempt starts from the merge base, so no earlier diff survives; ..." becomes: after a Check or Review failure the next attempt starts from the failed branch rebased onto main, so lessons name only what to fix or add; after an Implement failure or a merge conflict it starts from main, so lessons restate the work
- compatibility: other rules unchanged; each spec's `version` bumps to the next minor above main
- acceptance: criterion 4
- tests: tests/unit/test_specs.py and tests/integration/test_retry_prompts_starting_point.py
- post-merge source of truth: clutch/specs/implement.md and clutch/specs/diagnose.md

## Scope in / Scope out
Scope in:
- clutch/git.py: add `async def worktree_attach(self, dir: Path, path: Path, branch: str) -> None` running `worktree add <path> <branch>` through `_run`, beside `worktree_add`.
- clutch/stages.py: the `keep` keyword and the `implement` decision above.
- clutch/specs/implement.md: add the kept-branch sentence after the existing "For a prior attempt discarded on a merge conflict..." sentence; bump `version` to the next minor above main.
- clutch/specs/diagnose.md: replace the starting-point sentence as stated; bump `version` to the next minor above main.
- tests/unit/test_specs.py: update `test_diagnose_spec_states_attempt_starting_point` to the new sentence and the `implement` and `diagnose` version pins; nothing else changes there. tests/integration/test_specs_delimiter_note.py, tests/integration/test_implement_spec_meta_headers.py and tests/integration/test_implement_spec_mutation_check.py (line 22 and its purpose header): update version pins only. tests/integration/test_stages.py: update only the `spec: implement 2.26` pin at line 350; add nothing else there.
- tests/integration/test_git.py (already in `REAL_IO_TESTS`): add one real-git test that `Git.worktree_attach` checks out an existing branch in a new worktree without moving that branch.
- New tests/integration/test_retry_keeps_branch.py drives `prepare_worktree` with an in-memory fake Git and filesystem (the fakes in tests/fakes.py, or a small async fake Git inside the test file) and asserts the git calls made; it runs no git process and writes no repository, so it stays under the integration I/O guard and is not added to `REAL_IO_TESTS`. New tests/integration/test_retry_prompts_starting_point.py reads the shipped specs through a `Path(__file__)` anchor; new tests/unit/test_retry_keep_decision.py runs the `implement` keep decision with fake journal events.
- docs/how-clutch-works.md section 4.1 Worktree: say a retry after a Check or Review failure reuses the branch rebased onto main, and that every other attempt starts fresh.
Scope out:
- Check, Review, Diagnose verdict logic, rework, the merge queue, conflict-rerun handling, retry caps, and tests/integration/conftest.py (`REAL_IO_TESTS` and `DISK_IO_SKIP` stay unchanged).

## Scope fence
- clutch/git.py
- clutch/stages.py
- clutch/specs/implement.md
- clutch/specs/diagnose.md
- docs/how-clutch-works.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py
- tests/integration/test_git.py
- tests/integration/test_retry_keeps_branch.py
- tests/integration/test_retry_prompts_starting_point.py
- tests/unit/test_retry_keep_decision.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_retry_keeps_branch.py tests/integration/test_git.py` proves `prepare_worktree(ctx, stem, keep=True)`, with a fake Git on which branch `<stem>` exists and the rebase succeeds, removes the old worktree, calls `worktree_attach` on the existing branch and `rebase` onto main, and never calls `branch_delete` or `worktree_add` from main; and proves on a real repo that `Git.worktree_attach` checks out the existing branch head.
2. `./dev.py test tests/integration/test_retry_keeps_branch.py` proves that when the fake Git's `rebase` raises `RebaseRefused`, `prepare_worktree` falls back to removing the attached worktree, deleting the branch and calling `worktree_add` from main, and that `keep=False` still deletes the old branch without calling `worktree_attach` or `rebase`.
3. `./dev.py test tests/unit/test_retry_keep_decision.py` proves `keep` is true after a `gate_failed` terminal at `check` or `review`, and false on a first attempt, after `premise_failed`, `incomplete` or `timeout`, and when a `merge_conflict_rerun` signal is newer than the terminal.
4. `./dev.py test tests/integration/test_retry_prompts_starting_point.py tests/unit/test_specs.py` proves the Implement Task carries the kept-branch sentence and the Diagnose prompt no longer says "no earlier diff survives".

## Verification
```
./dev.py test tests/integration/test_retry_keeps_branch.py tests/integration/test_git.py tests/unit/test_retry_keep_decision.py tests/integration/test_retry_prompts_starting_point.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py
```

## Definition of rejected
Keeping the branch after an Implement failure or a merge conflict, a conflicting rebase left in place, a config knob, a new `REAL_IO_TESTS` entry, or files outside the fence change.

## Time budget
- expected: 20m
- stuck: 40m