---
state: draft
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
- clutch/stages.py::prior_attempts
- clutch/stages.py::lift_outbox

## Goal / Why
This is part 1 of 3 of roadmap row 47 (docs/roadmap.md), the inputs a conflict rerun reads. The earlier single-ticket attempts stopped as incomplete after a partial edit, because the 28-file fence used up the per-attempt budget on reading. Parts 2 (`conflict-rerun-accounting`) and 3 (`conflict-rerun-swap`) are follow-up rows added by this ticket.

After this ticket, Implement's prompt can carry a "Prior attempt (discarded on merge conflict); re-derive against current main; do not copy blindly" section. It holds the discarded attempt's `run.md` and its review approval findings. It also holds a reference copy of the discarded diff, limited to files that did not conflict, lifted to `attempts/<n>/prior.diff` as a new lift kind `prior-diff`. The section appears only after a conflict-rerun marker exists, and it is inert until part 3 emits that marker. Without it, a rerun would start blind and repeat the discarded work.

The marker is one journal event: type `SIGNAL`, `ticket` equal to the stem, body `{"signal": "merge_conflict_rerun", "attempt": n}`, where n is the discarded attempt number. This ticket defines it; part 3 emits it.

## Boundary contract
### Prompt prior_attempts input
- disposition: extend
- owner: clutch/stages.py
- consumers: the Implement stage prompt builder
- observable change: `prior_attempts` reads the latest `SIGNAL` event for the stem whose body signal is `merge_conflict_rerun`. When one exists it appends a `conflict_rerun` section holding `tickets/<stem>/run.md` text, the approval findings from `tickets/<stem>/review.md`, and the text of `tickets/<stem>/attempts/<n>/prior.diff`, with n taken from the event body. The marker is read independently of `run_terminals`: a discarded run that never reached a terminal still renders the section, and when `run_terminals` is empty `prior_attempts` returns only that section instead of None.
- compatibility: with no such event, `prior_attempts` output is byte-identical to today. A missing `prior.diff`, `run.md` or `review.md` omits that part and does not raise.
- acceptance: the section is present when the event exists and absent otherwise.
- tests: new unit test in tests/unit/test_stages_conflict_rerun_inputs.py appends exactly the event above to the journal
- post-merge source of truth: clutch/stages.py

### prior-diff lift
- disposition: extend
- owner: clutch/stages.py
- consumers: part 3's rerun path, which calls it with the discarded branch diff
- observable change: new function `lift_prior_diff(ctx, stem, *, attempt, diff, conflicted)` in clutch/stages.py. `diff` is the discarded branch's unified diff text and `conflicted` is the list of conflicted repo paths. It drops every per-file section of `diff` whose path is in `conflicted` (header and hunks), writes the remainder to `tickets/<stem>/attempts/<attempt>/prior.diff`, and commits it as one ticket-plane commit through `ctx.driver.effects.run` keyed `ticket-plane/<stem>/<seq>/prior-diff`, as `lift_outbox` does. It returns the commit sha, or None when nothing remains. It does not use the worktree outbox, because the diff is not an agent-written file.
- compatibility: `lift_outbox` and existing lift kinds and paths are unchanged.
- acceptance: a conflicted file's header and hunks never appear in `prior.diff`.
- tests: new unit test in tests/unit/test_stages_conflict_rerun_inputs.py
- post-merge source of truth: clutch/stages.py

### Implement prompt spec
- disposition: extend
- owner: clutch/specs/implement.md
- consumers: the Implement stage and the spec pin tests
- observable change: wording that tells the agent to re-derive against current main and not copy the prior diff blindly; `version` becomes the next minor above the version on main.
- compatibility: existing rules are unchanged.
- acceptance: spec pin tests pass at the new version.
- tests: tests/unit/test_specs.py and the integration spec pin tests
- post-merge source of truth: clutch/specs/implement.md

## Scope in / Scope out
Scope in:
- Add the `conflict_rerun` section to `prior_attempts` in clutch/stages.py, triggered by the `merge_conflict_rerun` SIGNAL event described above.
- Add `lift_prior_diff` with the signature above.
- Add the static Implement wording and bump its version to the next minor above main.
- Update only the version pin or expected text that changes in tests/unit/test_specs.py, tests/integration/test_specs_delimiter_note.py, tests/integration/test_implement_spec_mutation_check.py and tests/integration/test_stages.py.
- Update docs/how-clutch-works.md section 7.2.1 only where it describes the Implement prompt inputs.
- In docs/roadmap.md, add follow-up rows for part 2 `conflict-rerun-accounting` and part 3 `conflict-rerun-swap`, each depending on the one before it. Part 3's Content names the exact `merge_conflict_rerun` SIGNAL event (body `signal`, `attempt`) as what the rerun outcome must emit, and the call to `lift_prior_diff`.

Scope out:
- drain.py, caps.py, mergequeue.py, daemon.py, merge.py, serve.py, runner.py, rework.py and rework.md, which are parts 2 and 3.
- Deleting ConflictHandoff.
- Any caller that emits the marker or calls `lift_prior_diff`.

## Scope fence
- clutch/stages.py
- clutch/specs/implement.md
- tests/unit/test_stages_conflict_rerun_inputs.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py
- docs/how-clutch-works.md
- docs/roadmap.md

## Acceptance criteria
1. After the test appends `SIGNAL {signal: merge_conflict_rerun, attempt: 0}` for the stem, `prior_attempts` contains the `conflict_rerun` section with the `run.md` text and the `prior.diff` text, and returns that section rather than None when there are no run terminals; a journal without the event yields no such section and the section is not an empty heading; checked by `./dev.py test tests/unit/test_stages_conflict_rerun_inputs.py`.
2. `lift_prior_diff` called with a two-file diff where one path is in `conflicted` writes a `prior.diff` containing the other file's hunks and none of the conflicted file's header or hunks, not the whole diff; checked by `./dev.py test tests/unit/test_stages_conflict_rerun_inputs.py`.
3. A missing `prior.diff` renders the section without raising, not a `FileNotFoundError`; checked by `./dev.py test tests/unit/test_stages_conflict_rerun_inputs.py`.
4. The Implement spec carries the re-derive wording and a bumped `version`; checked by `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py`.
5. The whole suite passes; checked by `./dev.py test`.
6. docs/roadmap.md still parses after the edit; checked by `./dev.py test tests/integration/test_roadmap_table.py`. The two follow-up rows exist: a one-time review check, not a standing test pinning roadmap text.

## Verification
```
./dev.py test tests/unit/test_stages_conflict_rerun_inputs.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
The branch edits drain.py, caps.py, mergequeue.py, daemon.py or rework.md, or changes any prompt that is not a conflict rerun.

## Time budget
- expected: 20m
- stuck: 40m
