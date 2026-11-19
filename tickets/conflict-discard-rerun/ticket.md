---
state: rejected
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- merge-model-resolve

## Context
- docs/parallel-tickets-plan.md
- clutch/mergequeue.py::ConflictHandoff
- clutch/rework.py
- clutch/stages.py::_lift_decision
- clutch/stages.py::_lift_files
- clutch/stages.py::prior_attempts

## On-demand
- clutch/daemon.py
- clutch/merge.py
- clutch/serve.py
- clutch/runner.py
- clutch/drain.py
- clutch/caps.py
- clutch/specs/implement.md
- clutch/specs/rework.md
- docs/how-clutch-works.md

## Goal / Why
When the mechanical and model conflict steps both fail, the serve merge queue no longer hands the conflict to Rework, which rewrites the ticket. It aborts the rebase, retires the branch and worktree, journals a `merge_conflict_rerun` signal, and re-offers the ticket for a fresh Implement from current `main`. This is step 3 of `docs/parallel-tickets-plan.md` section 5 plus section 6. A conflict means the code needs merging, not that the ticket is wrong, so a rerun does not draw on the ticket's `retry` cap and does not count toward `caps.attempts`. Reruns are capped by the engine constant `CONFLICT_RERUN_LIMIT = 2`; after that the ticket ends as a `gate_failed` terminal routed to the Reject queue with finding code `merge_conflict_rerun_spent` and the paved road "split the ticket, or run it with parallel disabled".

The rerun's Implement prompt carries a "Prior attempt (discarded on merge conflict); re-derive against current main; do not copy blindly" section. It holds the discarded attempt's `run.md`, its `review.md` approval findings, and a reference diff of the files that did not conflict, lifted as the new kind `prior-diff` at `attempts/<n>/prior.diff`. Code is never applied directly from it, and Review checks the whole new diff.

`ConflictHandoff`, `daemon.consume_handoff`, and the `handoff` parameter of `rework()` are deleted together with their tests (no dual path), and the conflict input and the sentence forbidding conflict-only repair are removed from the Rework spec.

## Boundary contract
### Merge queue conflict outcome
- disposition: replace
- owner: clutch/mergequeue.py
- consumers: clutch/daemon.py, clutch/merge.py (`AdmissionBoundary`), clutch/serve.py, clutch/runner.py (`drive`), clutch/rework.py, clutch/drain.py (`record_reoffer`, `awaiting_operator`), clutch/caps.py
- observable change: a conflict neither `merge.strategies` nor the model step resolves returns a rerun outcome instead of `ConflictHandoff`. The rebase is aborted, the branch and worktree are retired through `git.py` (`worktree remove` + `prune`), a `merge_conflict_rerun` signal is journaled, and the ticket's state transition is a `gate_failed` terminal whose body carries `conflict_rerun: true`. `drain.record_reoffer` skips the `retry` draw for a body with `conflict_rerun`, exactly as it already skips `provider_drought` bodies, and `caps.py` does not count such a terminal toward `caps.attempts`. `serve.py` re-offers through its existing path. `CONFLICT_FACTS.resolving_rung` becomes `none | mechanical | model | rerun`; the journal fold still accepts the historical `rework` value. Once `CONFLICT_RERUN_LIMIT` (2) reruns are spent the ticket ends as a `gate_failed` terminal without `conflict_rerun`, routed to the Reject queue with finding code `merge_conflict_rerun_spent`, a token also carried in its `reason`. `drain.awaiting_operator` holds a Reject-queue stem whose reason carries that token exactly as it holds `ticket_changed`, so the stem is not reofferable and `record_reoffer` is not reached until an operator `reject_verdict` keep (`clutch ticket confirm`). The rerun count is the number of `merge_conflict_rerun` signals for the stem since its last operator `reject_verdict` keep, so a confirm resets it. The paved road is to split the ticket or run it with parallel disabled, then release it with `clutch ticket confirm <stem>` or discard it with `clutch ticket reject <stem>`.
- compatibility: old contract is `ConflictHandoff` consumed by `daemon.consume_handoff` into `apply_rework`; the replacement is the rerun outcome. Every consumer migrates in this change and the old names are removed. Journals holding `resolving_rung: rework` still fold. Terminals without `conflict_rerun` keep today's retry and attempts accounting.
- acceptance: a conflict the earlier steps refuse ends in a retired branch, a `merge_conflict_rerun` signal, and a re-offered ticket with no `cap_consumed` event for cap `retry` after the re-offer and an unchanged attempts count. A third conflict ends in the Reject-queue terminal.
- tests: new `tests/integration/test_conflict_discard_rerun.py` and `tests/unit/test_conflict_rerun.py`.
- post-merge source of truth: clutch/mergequeue.py, documented in docs/how-clutch-works.md section 7.2.1

### Prior-attempt lift
- disposition: extend
- owner: clutch/stages.py (`prior_attempts`, the existing canonical owner of prior-attempt Implement input, and the new `prior-diff` lift kind)
- consumers: `implement_stage` (its existing splice into the ticket block) and the rerun path in clutch/mergequeue.py
- observable change: a new lift kind `prior-diff` writes the discarded diff, limited to files that did not conflict, to `attempts/<n>/prior.diff`. When the latest terminal body carries `conflict_rerun`, `prior_attempts` returns the "Prior attempt (discarded on merge conflict); re-derive against current main; do not copy blindly" section holding the discarded `run.md`, the review approval findings (once) and the prior diff, instead of the "these findings are this attempt's to clear" text. No new implement.md data block or render input is added, so `implement_inputs` and its callers (`clutch/requisition.py`) are unchanged.
- compatibility: existing lift kinds and their file selection are unchanged. A first run has no prior section.
- acceptance: the stages.py function that builds the prior-attempt input returns the three items for a rerun and `none` for a first run, and the rendered Implement prompt for a rerun contains them and the `do not copy blindly` wording. The diff excludes conflicted paths.
- tests: `tests/unit/test_conflict_rerun.py` (input building with `tmp_path` data) and `tests/integration/test_conflict_discard_rerun.py` (rendered prompt from the real spec)
- post-merge source of truth: clutch/stages.py and clutch/specs/implement.md

### Prompt specs
- disposition: extend
- owner: clutch/specs/implement.md and clutch/specs/rework.md
- consumers: the Implement and Rework stages, `tests/unit/test_specs.py`, `tests/integration/test_specs_delimiter_note.py`, `tests/integration/test_implement_spec_mutation_check.py`, `tests/integration/test_stages.py`
- observable change: implement.md gains static wording on treating a rerun section in the ticket block as reference only (no new placeholder or input) and bumps `version` to the next minor above main's. rework.md drops the `{{conflict}}` input and the sentence forbidding conflict-only repair, and bumps `version` to the next minor above main's.
- compatibility: the Rework stage renders without a conflict input; every other input is unchanged.
- acceptance: rework.md contains no `conflict` placeholder and the spec still loads and renders. The updated version pins pass.
- tests: `tests/unit/test_specs.py`, `tests/integration/test_specs_delimiter_note.py`, `tests/integration/test_implement_spec_mutation_check.py`, `tests/integration/test_stages.py` and `tests/integration/test_conflict_discard_rerun.py`
- post-merge source of truth: the two spec files

## Scope in / Scope out
In:
- Delete `ConflictHandoff`, `consume_handoff`, the `handoff` parameter of `rework()` and `apply_rework`, and every caller in `daemon.py`, `merge.py`, `serve.py`, `runner.py` and `rework.py`.
- Implement the retire and re-offer step in `mergequeue.py`, the `merge_conflict_rerun` signal, and `CONFLICT_RERUN_LIMIT = 2`. The retire and the signal happen after `MergeQueue._admit` returns its refused-conflict result (in `process` or its caller), so `tests/unit/test_merge_admission_params.py` keeps its git fake and its event order unchanged.
- No-retry mechanism: the rerun journals a `gate_failed` state transition whose body carries `conflict_rerun: true`. In `clutch/drain.py::record_reoffer`, add `"conflict_rerun" not in body` to the existing skip conditions beside `provider_drought`, so no `retry` cap is drawn. In `clutch/caps.py`, a terminal whose body carries `conflict_rerun` is not counted by the attempts count. `serve.py` needs no new branch: its existing re-offer path (terminal then `record_reoffer`) handles the rerun. The pinning of these two edits lives in the new test files, not in existing drain or caps tests.
- The spent-limit park is an existing terminal: a `gate_failed` terminal (without `conflict_rerun`) routed to the Reject queue with finding code `merge_conflict_rerun_spent` and that token in its `reason`. In `clutch/drain.py::awaiting_operator`, hold a Reject-queue stem whose reason carries `merge_conflict_rerun_spent` beside the existing `ticket_changed` check. Count reruns as `merge_conflict_rerun` signals since the stem's last operator `reject_verdict` keep. Its paved road names the existing verbs: split or edit the ticket then `clutch ticket confirm <stem>`, or `clutch ticket reject <stem>`, or run with parallel disabled.
- Add the `prior-diff` lift kind. Extend `clutch/stages.py::prior_attempts` (no parallel builder) so that, on a `conflict_rerun` terminal, it returns the rerun section built from the discarded run.md, review findings and prior.diff, in place of the gate_failed findings text. Its output for every other terminal is unchanged. The section reaches the prompt through the existing `_in_criteria_position` splice. implement.md gets static wording only, so `implement_inputs`, `clutch/requisition.py` and `tests/integration/test_requisition.py` need no change.
- Update the two specs as above. Each version is stated as the next minor above the one on main, never a literal target. `tests/unit/test_specs.py`, `tests/integration/test_specs_delimiter_note.py`, `tests/integration/test_implement_spec_mutation_check.py` and `tests/integration/test_stages.py` are edited only for the implement version pin (and the rework pin where one exists); `tests/integration/test_stages.py` is a do-not-grow file, and this forced edit changes one asserted version string and adds no test. Before finishing, grep `tests/` for the old implement and rework version strings and update every pin.
- `tests/integration/test_serve_admission.py`: its unresolved-conflict case flips from the Rework handoff (the `handoff` kwargs, `resolving_rung` `rework`, the `('work', 'gate_failed')` return and the rendered rework request) to the rerun outcome, `resolving_rung` `rerun`, and a `merge_conflict_rerun` signal.
- `tests/integration/test_daemon_soak_runner.py`: its conflict-rungs test flips from the handoff/rework evidence (`resolving_rung` `rework`, `member.handoffs`, the `handoff` and `rework` evidence fields, the `['gate_failed', 'merged']` sequence) to the rerun evidence, together with the `tests/harness/daemon_soak.py` change.
- Update docs/how-clutch-works.md section 7.2.1, and section 7.2 only where it describes the handoff: replace the Rework handoff with the rerun and list the `resolving_rung` values.
- Remove the existing tests that name `ConflictHandoff`, `consume_handoff` or `handoff=`. Rewrite the ones that exercise queue conflict behavior in the new files. Existing test files are edited only to delete or flip those references.
- Exception: `tests/integration/test_daemon_composition.py::test_production_applies_reviewed_rework_orders` and `::test_production_refuses_failed_rework_publication` use `writer.consume_handoff` only as a way into production Rework publication, which stays live. Re-point both at `runner.drive`'s Diagnose-then-Rework path, without a handoff. Keep every update, split and escalate publication assertion and every refusal assertion. Only the handoff-specific assertions change: the stage `merge` / reason `post_rebase_regate` terminal and the no-`CAP_CONSUMED` checks become that path's real terminal and its diagnosis cap draw. Add no new test to that file.

Out:
- The run-alone marking and dispatch overlap logic (the parallel dispatch tickets).
- Any change to the model resolve step or its bounds.
- Cherry-picking unconflicted files onto the new branch (rejected alternative in plan section 6).
- Editing docs/roadmap.md or CLUTCH_PLAN.md.

## Scope fence
- clutch/mergequeue.py
- clutch/daemon.py
- clutch/merge.py
- clutch/serve.py
- clutch/runner.py
- clutch/rework.py
- clutch/stages.py
- clutch/drain.py
- clutch/caps.py
- clutch/specs/implement.md
- clutch/specs/rework.md
- docs/how-clutch-works.md
- tests/unit/test_specs.py
- tests/unit/test_conflict_rerun.py
- tests/integration/test_conflict_discard_rerun.py
- tests/integration/test_rework.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_caps.py
- tests/integration/test_daemon_tasks.py
- tests/integration/test_mergequeue.py
- tests/integration/test_merge_model_resolve.py
- tests/integration/test_retro.py
- tests/integration/test_serve_admission.py
- tests/integration/test_daemon_soak_runner.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py
- tests/harness/daemon_soak.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_conflict_rerun.py` shows a conflict refused by both earlier steps returns the rerun outcome and not a `ConflictHandoff`, that `record_reoffer` on the resulting `conflict_rerun` terminal appends no `cap_consumed` event with cap `retry`, and that the attempts count is unchanged, not incremented.
2. `./dev.py test tests/integration/test_conflict_discard_rerun.py` shows the rebase is aborted, the branch and worktree are removed (the worktree path is absent after the step), a `merge_conflict_rerun` signal is journaled, the ticket is offered again for a fresh Implement from current `main`, and no `cap_consumed` event for cap `retry` follows the re-offer.
3. `./dev.py test tests/unit/test_conflict_rerun.py` shows the third conflict for one ticket (after `CONFLICT_RERUN_LIMIT` = 2 reruns) ends as a `gate_failed` terminal routed to the Reject queue with finding code `merge_conflict_rerun_spent`, whose paved road text names a split, running with parallel disabled, `clutch ticket confirm <stem>` and `clutch ticket reject <stem>`, and does not offer a third rerun.
4. `./dev.py test tests/unit/test_conflict_rerun.py` shows the `prior-diff` lift writes `attempts/<n>/prior.diff` containing only non-conflicted files, and a conflicted path never appears in it.
5. `./dev.py test tests/unit/test_conflict_rerun.py` shows the stages.py prior-attempt input builder, given `tmp_path` run.md, review findings and diff data, returns all three items for a rerun and the `none` value for a first run, not an empty section; `./dev.py test tests/integration/test_conflict_discard_rerun.py` shows the Implement prompt rendered from the real `clutch/specs/implement.md` for a rerun contains the discarded `run.md`, the review approval findings, the prior diff and the text `do not copy blindly`, and a first-run prompt contains none of them.
6. `./dev.py test tests/unit/test_conflict_rerun.py` shows a journaled `merge_conflict_facts` event from a rerun carries `resolving_rung` of `rerun`, and the fold still accepts a historical event with `rework`.
7. `grep -rn "ConflictHandoff\|consume_handoff" clutch tests` finds no match, and `grep -n "conflict" clutch/specs/rework.md` finds no input placeholder; `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py` passes with the bumped versions.
8. `./dev.py test` passes for the whole suite, with no remaining test that passes only on the old handoff behavior or the old spec versions.
9. `./dev.py test tests/unit/test_conflict_rerun.py` shows a Reject-queue `gate_failed` terminal whose reason carries `merge_conflict_rerun_spent` is held by `drain.awaiting_operator`, is not `reofferable`, and draws no `retry` cap until an operator `reject_verdict` keep; after that keep the rerun count restarts at zero, so the next conflict reruns instead of parking.
10. `./dev.py test tests/unit/test_conflict_rerun.py` shows `prior_attempts` on a `conflict_rerun` terminal contains the review approval findings exactly once and does not contain "this attempt's to clear"; `./dev.py test tests/integration/test_drain_reentry.py tests/integration/test_harvest.py` passes unchanged, so non-rerun terminals keep today's output.
11. `./dev.py test tests/integration/test_daemon_composition.py -k "applies_reviewed_rework_orders or refuses_failed_rework_publication"` passes with all of its update, split and escalate publication cases and its refusal cases driven through `runner.drive`'s Diagnose-then-Rework path, not deleted or skipped; only the handoff-specific terminal and cap assertions differ from today.

## Verification
```
./dev.py test tests/unit/test_conflict_rerun.py tests/integration/test_conflict_discard_rerun.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py tests/integration/test_rework.py tests/integration/test_mergequeue.py tests/integration/test_merge_model_resolve.py tests/integration/test_caps.py tests/integration/test_daemon_tasks.py tests/integration/test_retro.py tests/integration/test_serve_admission.py tests/integration/test_daemon_soak_runner.py tests/unit/test_merge_admission_params.py tests/unit/test_drain_reoffer.py tests/integration/test_requisition.py tests/integration/test_drain_reentry.py tests/integration/test_harvest.py tests/integration/test_harvest_orphans.py tests/integration/test_supervisor_rework.py tests/unit/test_premise_park_keep.py
./dev.py test
```

## Definition of rejected
The branch is thrown away if any `ConflictHandoff` or `consume_handoff` path remains alongside the rerun (dual path), if a rerun draws on the ticket's `retry` cap, if discarded code is applied to the new branch without Implement re-deriving it, or if a changed spec version is a literal target instead of the next minor above main's.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one deletion and replacement across one conflict path whose pieces cannot land separately without leaving a dual path.
