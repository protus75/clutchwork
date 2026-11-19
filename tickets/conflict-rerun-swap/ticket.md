---
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
- conflict-rerun-accounting

## Context
- docs/parallel-tickets-plan.md
- clutch/caps.py
- clutch/mergequeue.py::ConflictHandoff
- clutch/stages.py::lift_prior_diff
- clutch/drain.py::record_reoffer
- clutch/drain.py::awaiting_operator

## On-demand
- clutch/daemon.py
- clutch/runner.py
- clutch/serve.py
- clutch/merge.py
- clutch/rework.py
- clutch/journal.py
- clutch/specs/rework.md

## Goal / Why
This is part 3 of 3 of the conflict discard-and-rerun work (parts 1 and 2 are `conflict-discard-rerun-r1`, which added `lift_prior_diff` and the Prior attempt prompt section, and `conflict-rerun-accounting`, which added `CONFLICT_RERUN_LIMIT`, `conflict_reruns` and `conflict_rerun_spent` in `clutch/caps.py`). After this ticket, when the serve merge queue cannot resolve a rebase conflict by `merge.strategies` or the model step, it no longer hands the conflict to Rework, which rewrites the ticket. It aborts the rebase, lifts a reference copy of the discarded diff with `lift_prior_diff`, retires the branch and worktree through `git.py`, journals a `SIGNAL` event for the stem with body `{"signal": "merge_conflict_rerun", "attempt": n}` for the discarded attempt n, and the ticket is offered again for a fresh Implement from current `main`. A conflict means the code needs merging, not that the ticket is wrong, so a rerun draws no `retry` cap and does not count as a failed attempt. After `CONFLICT_RERUN_LIMIT` reruns the ticket parks in the Reject queue with the paved road "split the ticket, or run it with parallel disabled".

`ConflictHandoff`, `TicketWriter.consume_handoff` and the `handoff` parameter of `rework()` and `apply_rework` are deleted with their tests (no dual path).

## Boundary contract
### Merge queue conflict outcome
- disposition: replace
- owner: clutch/mergequeue.py
- consumers: clutch/daemon.py (`TicketWriter`, `apply_rework`), clutch/merge.py (`AdmissionBoundary`), clutch/serve.py (merge poll), clutch/runner.py (`drive`), clutch/rework.py, clutch/drain.py (`record_reoffer`, `awaiting_operator`), clutch/caps.py (`failed_attempt`), clutch/journal.py (`SIGNAL_NAMES`)
- observable change: a conflict that neither `merge.strategies` nor the model step resolves aborts the rebase and returns a refused `StageResult` whose finding code is `merge_conflict_rerun`, instead of a `ConflictHandoff`. The writer that consumes the delivery (replacing `consume_handoff`, one function) then: if `conflict_rerun_spent` is false, lifts the discarded diff limited to non-conflicted files with `lift_prior_diff(ctx, stem, attempt=n, diff=..., conflicted=...)`, appends the `merge_conflict_rerun` SIGNAL, retires the branch and worktree (`worktree remove` + `prune` through `git.py`), and writes a `gate_failed` terminal whose body carries `conflict_rerun: true`. `merge_conflict_rerun` joins `SIGNAL_NAMES` with that emitter. `drain.record_reoffer` draws no `retry` cap for a body carrying `conflict_rerun`, as it already skips `provider_drought` bodies. `caps.failed_attempt` does not count such a terminal. If `conflict_rerun_spent` is already true, no signal is emitted and the terminal is a `gate_failed` routed to the Reject queue with finding code `merge_conflict_rerun_spent` (also in its `reason`) and paved road `CONFLICT_RERUN_ROAD`, and `drain.awaiting_operator` holds that stem like `ticket_changed` until an operator `reject_verdict` keep. `CONFLICT_FACTS.resolving_rung` becomes `none | mechanical | model | rerun`; the journal fold still accepts a historical `rework`.
- compatibility: the old contract is `ConflictHandoff` consumed into `apply_rework`; every consumer migrates in this change and the old names are removed. Journals holding `resolving_rung: rework` still fold. Terminals without `conflict_rerun` keep today's retry and attempts accounting.
- acceptance: a refused conflict ends in a retired branch, a `merge_conflict_rerun` signal, a `prior.diff` without conflicted paths, and a re-offered ticket with no `retry` draw and an unchanged failed-attempt count; the third conflict parks.
- tests: new tests/unit/test_conflict_rerun_swap.py and tests/integration/test_conflict_rerun_swap.py; the exact `SIGNAL_NAMES` set in tests/integration/test_closed_sets.py
- post-merge source of truth: clutch/mergequeue.py, documented in docs/how-clutch-works.md

### Rework prompt spec
- disposition: extend
- owner: clutch/specs/rework.md
- consumers: clutch/rework.py and the spec pin tests
- observable change: the `conflict` input block and the sentence forbidding conflict-only repair are removed; `version` becomes the next minor above the version on main.
- compatibility: every other Rework input is unchanged; Rework still renders and loads.
- acceptance: rework.md has no `{{conflict}}` placeholder and the spec loads and renders.
- tests: tests/integration/test_specs_delimiter_note.py and tests/integration/test_rework.py
- post-merge source of truth: clutch/specs/rework.md

## Scope in / Scope out
Scope in:
- Add the `merge_conflict_rerun` outcome in `clutch/mergequeue.py` in place of `ConflictHandoff`, with fact rung `rerun`; the retire, lift and signal happen in the consuming writer after `MergeQueue._admit` returns, so the admission git fakes and event order of `tests/unit/test_merge_admission_params.py` are unchanged.
- Replace `TicketWriter.consume_handoff` with the rerun consumer in `clutch/daemon.py`; delete the `handoff` parameter of `apply_rework` and `rework()`, and the `consume_handoff` parameter of `runner.drive`, plus their callers in `merge.py`, `serve.py` and `runner.py`.
- Add `merge_conflict_rerun` to `SIGNAL_NAMES` in `clutch/journal.py`, and add `merge_conflict_rerun` to the exact `SIGNAL_NAMES` set asserted in test_journal_closed_sets_and_constants in tests/integration/test_closed_sets.py; add the `conflict_rerun` skip to `drain.record_reoffer`; hold `merge_conflict_rerun_spent` in `drain.awaiting_operator`; exclude `conflict_rerun` terminals in `caps.failed_attempt`.
- Remove the conflict input and the conflict-only-repair sentence from clutch/specs/rework.md and bump its version to the next minor above main, never a literal target; move only the `("rework", ...)` pin in tests/integration/test_specs_delimiter_note.py to the bumped version. tests/unit/test_specs.py has no rework pin and is not edited; it only runs as the load/render check.
- Flip or delete the existing tests that name `ConflictHandoff`, `consume_handoff`, `handoff=` or `resolving_rung` `rework`: test_rework.py, test_daemon_composition.py, test_caps.py, test_daemon_tasks.py, test_mergequeue.py, test_merge_model_resolve.py, test_retro.py, test_serve_admission.py, test_daemon_soak_runner.py and tests/harness/daemon_soak.py. These are do-not-grow files: edit only to delete or flip references, add no new test. In test_daemon_composition.py, `test_production_applies_reviewed_rework_orders` and `test_production_refuses_failed_rework_publication` use `consume_handoff` only as a way into Rework publication, which stays live; re-point both at `runner.drive`'s Diagnose-then-Rework path and keep every publication and refusal assertion.
- In docs/how-clutch-works.md edit only the statements the change makes false: sections 7.2 and 7.2.1 where they describe the handoff to Rework (describe the rerun, the cap, the park, and the `resolving_rung` values); section 6.4 (the retry-cap table row listing cases that skip a `retry` draw, and the sentence routing merge-conflict handoffs and supervising a conflict-handoff stem), adding the `conflict_rerun` retry exception and removing the conflict-handoff wording; and section 6.6 (the machine-keep bullet and the `awaiting_operator` hold list), adding the `merge_conflict_rerun_spent` operator hold.

Scope out:
- Run-alone dispatch marking for a rerun ticket (the parallel dispatch tickets).
- Any change to the model resolve step or its bounds.
- Cherry-picking unconflicted files onto the new branch.
- Changing `lift_prior_diff`, `prior_attempts` or the Implement spec (part 1) and the cap functions beyond `failed_attempt` (part 2).

## Scope fence
- clutch/mergequeue.py
- clutch/daemon.py
- clutch/merge.py
- clutch/serve.py
- clutch/runner.py
- clutch/rework.py
- clutch/drain.py
- clutch/caps.py
- clutch/journal.py
- clutch/specs/rework.md
- docs/how-clutch-works.md
- tests/unit/test_conflict_rerun_swap.py
- tests/integration/test_conflict_rerun_swap.py
- tests/integration/test_closed_sets.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_rework.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_caps.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_mergequeue.py
- tests/integration/test_merge_model_resolve.py
- tests/integration/test_retro.py
- tests/integration/test_serve_admission.py
- tests/integration/test_daemon_soak_runner.py
- tests/harness/daemon_soak.py

## Acceptance criteria
1. A conflict refused by both earlier steps yields a `merge_conflict_rerun` refused result and a journaled SIGNAL with body `{"signal": "merge_conflict_rerun", "attempt": n}`, not a `ConflictHandoff`; checked by `./dev.py test tests/unit/test_conflict_rerun_swap.py`.
2. After the rerun terminal, `record_reoffer` appends no `cap_consumed` event for cap `retry`, and `caps.failed_attempts` equals its value before the terminal, not one more; checked by `./dev.py test tests/unit/test_conflict_rerun_swap.py`.
3. The rebase is aborted, the worktree path is absent after the step, `tickets/<stem>/attempts/<n>/prior.diff` exists and contains no conflicted path, and the ticket is offered again; checked by `./dev.py test tests/integration/test_conflict_rerun_swap.py`.
4. After two reruns, a third conflict emits no third `merge_conflict_rerun` signal, ends as a `gate_failed` Reject-queue terminal with finding code `merge_conflict_rerun_spent` and `CONFLICT_RERUN_ROAD`, and `drain.awaiting_operator` is true for the stem, not `reofferable`; after an operator `reject_verdict` keep the next conflict reruns again; checked by `./dev.py test tests/unit/test_conflict_rerun_swap.py`.
5. The journaled `merge_conflict_facts` for a rerun has `resolving_rung` equal to `rerun`, not `rework`, and a historical event with `rework` still folds; checked by `./dev.py test tests/unit/test_conflict_rerun_swap.py`.
6. `grep -rn "ConflictHandoff\|consume_handoff" clutch tests` finds no match, `journal.SIGNAL_NAMES` contains `merge_conflict_rerun`, and clutch/specs/rework.md has no `{{conflict}}` placeholder; checked by `./dev.py test tests/unit/test_specs.py tests/integration/test_rework.py tests/integration/test_specs_delimiter_note.py tests/integration/test_closed_sets.py`.
7. The two re-pointed Rework publication tests keep their update, split, escalate and refusal cases and pass; checked by `./dev.py test tests/integration/test_daemon_composition.py -k "applies_reviewed_rework_orders or refuses_failed_rework_publication"`.
8. The whole suite passes with no remaining test that passes only on the handoff behavior; checked by `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_conflict_rerun_swap.py tests/integration/test_conflict_rerun_swap.py tests/unit/test_specs.py tests/unit/test_stages_conflict_rerun_inputs.py tests/unit/test_caps_conflict_rerun.py tests/unit/test_merge_admission_params.py tests/unit/test_drain_reoffer.py tests/integration/test_rework.py tests/integration/test_closed_sets.py tests/integration/test_specs_delimiter_note.py tests/integration/test_mergequeue.py tests/integration/test_merge_model_resolve.py tests/integration/test_caps.py tests/integration/test_daemon_tasks.py tests/integration/test_retro.py tests/integration/test_serve_admission.py tests/integration/test_daemon_soak_runner.py
./dev.py test
```

## Definition of rejected
The branch is thrown away if any `ConflictHandoff` or `consume_handoff` path remains beside the rerun (dual path), if a rerun draws on the `retry` cap or counts as a failed attempt, if discarded code is applied to the new branch instead of lifted as reference, if the spent-limit park offers a third rerun, or if the rework.md version is a literal target instead of the next minor above main.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one deletion and replacement across a single conflict path; the handoff cannot be removed in pieces without leaving a dual path.
