---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/stages.py::implement
- clutch/stages.py::prepare_worktree
- clutch/runner.py::failure_terminal
- clutch/tickets.py::in_fence
- tests/unit/test_retry_keep_decision.py
- tests/unit/test_runner_rework_findings_terminal.py
- tickets/retry-keeps-prior-branch/ticket.md

## On-demand
- clutch/specs/implement.md
- clutch/specs/diagnose.md

## Goal / Why
When Implement replies `premise_failed` and every finding names a file outside `## Scope fence` (a fence gap), the whole candidate diff is thrown away on the retry. Merged `retry-keeps-prior-branch` keeps the branch only after a `gate_failed` terminal at `check` or `review`; its Goal leaves Implement failures starting fresh. On 2026-11-21 `requisition-review-approval-reuse` attempts 0 to 2 each ran Implement and Diagnose for about 18 minutes and discovered about 5 more unfenced failing tests per attempt (15 in all), and `requisition-review-input-reuse` hit 5 unfenced test files. Each missing batch of fence entries cost a full redo even though the rework only added files to the fence. Merged `implement-all-premise-findings` and `implement-skips-full-suites` do not stop this drip, because Implement cannot see every failing out-of-fence test. This ticket does not re-solve those, nor declined record 000795 (which `retry-keeps-prior-branch` later delivered for the review snag).

After this ticket, a retry that follows a `premise_failed` terminal at stage `implement` whose findings are all fence gaps starts from the failed branch rebased onto main, so the next attempt only adds the files the widened fence now allows. A `premise_failed` with any other finding starts fresh as today. Today the Implement spec says to "commit nothing further" on `premise_failed`, so uncommitted work would be lost even with the branch kept; the spec therefore also tells Implement to commit its in-fence work in progress before a fence-gap-only `premise_failed`.

## Boundary contract
### Fence-gap marker on the terminal
- disposition: extend
- owner: clutch/runner.py::failure_terminal
- consumers: clutch/stages.py::implement keep decision
- observable change: the terminal `STATE_TRANSITION` body gains `fence_gap: true` exactly when `outcome == "premise_failed"`, `stage == "implement"`, there is at least one finding, and every finding has a `path` that is not under the ticket's scope fence per `clutch.tickets.in_fence` and does not start with `tickets/`. Otherwise the key is absent
- compatibility: existing terminal keys, dispatch, caps, and premise_bounce accounting are unchanged; readers that ignore the key are unaffected
- acceptance: criteria 1 and 2
- tests: tests/unit/test_runner_fence_gap_terminal.py
- post-merge source of truth: clutch/runner.py

### Attempt start after a fence gap
- disposition: extend
- owner: clutch/stages.py::implement (reusing `prepare_worktree(keep=True)` from `retry-keeps-prior-branch`)
- consumers: Implement retries
- observable change: `keep` is also true when the latest run terminal has `to == "premise_failed"`, `stage == "implement"` and `fence_gap` true, and no `merge_conflict_rerun` signal is newer than it. The rebase-conflict fallback to a fresh branch is the existing one
- compatibility: `premise_failed` without `fence_gap`, `incomplete`, `timeout`, first attempts, and conflict reruns still start fresh; `gate_failed` at check or review is unchanged
- acceptance: criterion 3
- tests: tests/unit/test_retry_keep_fence_gap.py
- post-merge source of truth: clutch/stages.py

### Implement and Diagnose prompts
- disposition: extend
- owner: clutch/specs/implement.md and clutch/specs/diagnose.md
- consumers: Implement and Diagnose
- observable change: Implement's `premise_failed` bullet says that when every finding is a forced file outside `## Scope fence`, it first commits its in-fence work in progress, then replies; otherwise it commits nothing further as today. Diagnose's starting-point sentence also names a fence-gap `premise_failed` as a case where the next attempt starts from the kept branch
- compatibility: other rules unchanged; each spec's `version` bumps to the next minor above main
- acceptance: criterion 4
- tests: tests/integration/test_retry_fence_gap_prompts.py and the pinned spec tests
- post-merge source of truth: clutch/specs/implement.md and clutch/specs/diagnose.md

## Scope in / Scope out
Scope in:
- clutch/runner.py: set `fence_gap` in `failure_terminal` as stated, using `in_fence` and the findings' `path`.
- clutch/stages.py: extend the keep expression in `implement` with the fence-gap terminal case. The existing merge_conflict_rerun check applies to it too.
- clutch/specs/implement.md and clutch/specs/diagnose.md: the sentences above; bump each `version` to the next minor above main.
- Update version pins only in the tests that pin those specs: tests/unit/test_specs.py, tests/integration/test_specs_delimiter_note.py, tests/integration/test_implement_spec_meta_headers.py, tests/integration/test_implement_spec_mutation_check.py, and the single implement spec pin in tests/integration/test_stages.py; also update tests/integration/test_retry_prompts_starting_point.py only if it asserts the exact Diagnose sentence this ticket extends.
- docs/how-clutch-works.md section 4.1 Worktree: add that a fence-gap `premise_failed` also keeps the branch.
- New tests: tests/unit/test_runner_fence_gap_terminal.py (drives `failure_terminal` with fakes as the existing runner terminal tests do), tests/unit/test_retry_keep_fence_gap.py (keep decision with fake journal events), tests/integration/test_retry_fence_gap_prompts.py (reads the shipped specs through a `Path(__file__)` anchor). Before replying, grep tests/ for any test that lists the full set of terminal body keys and fence only a hit that now fails.
- Rejected simpler approach: the engine committing the dirty worktree itself on a fence-gap terminal needs a new git commit path in the runner; the prompt sentence needs none, and the keep path already rebases whatever was committed.
Scope out: Check, Review, Diagnose verdict logic, rework, retry caps, premise_bounce accounting, the second option in the box message (listing every failing out-of-fence test in one pass), and tests/unit/test_retry_keep_decision.py.

## Scope fence
- clutch/runner.py
- clutch/stages.py
- clutch/specs/implement.md
- clutch/specs/diagnose.md
- docs/how-clutch-works.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py
- tests/integration/test_retry_prompts_starting_point.py
- tests/unit/test_runner_fence_gap_terminal.py
- tests/unit/test_retry_keep_fence_gap.py
- tests/integration/test_retry_fence_gap_prompts.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_runner_fence_gap_terminal.py` proves `failure_terminal` with outcome `premise_failed`, stage `implement` and findings all naming paths outside the fence writes `fence_gap` true on the terminal body, not an absent key.
2. `./dev.py test tests/unit/test_runner_fence_gap_terminal.py` proves the key is absent when one finding names a path inside the fence, when a finding has no path, when the outcome is `gate_failed`, and when the findings list is empty, not `fence_gap` false or true.
3. `./dev.py test tests/unit/test_retry_keep_fence_gap.py` proves `prepare_worktree` receives `keep=True` after a `premise_failed` implement terminal with `fence_gap` true, and `keep=False` after the same terminal without it, after `incomplete`, after `timeout`, and when a `merge_conflict_rerun` signal is newer than the fence-gap terminal.
4. `./dev.py test tests/integration/test_retry_fence_gap_prompts.py tests/unit/test_specs.py` proves the Implement spec tells Implement to commit in-fence work before a fence-gap-only `premise_failed`, and the Diagnose spec names a fence-gap `premise_failed` as keeping the branch.

## Verification
```
./dev.py test tests/unit/test_runner_fence_gap_terminal.py tests/unit/test_retry_keep_fence_gap.py tests/unit/test_retry_keep_decision.py tests/integration/test_retry_fence_gap_prompts.py tests/integration/test_retry_prompts_starting_point.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_implement_spec_mutation_check.py
```

## Definition of rejected
Keeping the branch after any `premise_failed` that has a non-fence finding, after `incomplete` or `timeout`, or after a merge conflict; a config knob; a new git commit path in the engine; or files outside the fence change.

## Time budget
- expected: 20m
- stuck: 40m
