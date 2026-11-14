---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Runs before
- vscode-help-registry
- vscode-help-surfaces
- vscode-help-docs

## Context
- chupa/artifacts.py::Outcome
- chupa/journal.py::TERMINAL_STATES
- chupa/stages.py::ImplementReply
- chupa/stages.py::_short
- chupa/stages.py::implement
- chupa/caps.py::failed_attempt
- chupa/runner.py::drive
- chupa/runner.py::failure_terminal
- chupa/drain.py::parked_blob
- chupa/drain.py::record_reoffer
- tests/unit/test_implement_premise_path.py
- tests/unit/test_drain_reoffer.py
- tests/unit/test_caps_requisition_park.py
- tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs
- tests/integration/test_closed_sets.py::test_artifacts_closed_sets_and_constants
- tests/integration/test_closed_sets.py::test_journal_closed_sets_and_constants
- tests/integration/test_stages.py::implement_reply
- tests/integration/test_stages.py::test_premise_failed_stops_after_implement_with_its_run_record
- tests/integration/test_terminal.py::run
- tests/integration/test_terminal.py::diagnosis_reply
- tests/integration/test_terminal.py::transitions
- tests/integration/test_terminal.py::test_a_premise_failure_journals_its_terminal
- tests/regress_vscode_task_identity.py

## On-demand
- chupa/specs/implement.md
- docs/how-chupa-works.md

## Goal / Why
The Implement reply has three outcomes: `ok`, `already_satisfied`, and `premise_failed`. There is
no outcome for "I stopped before the work was committed and nothing in the ticket is wrong." When
the implementer gives up, the engine rejects its reply as invalid and re-asks it to "fix the
reply's shape and finish the work"; the model then picks `premise_failed` to satisfy the schema.
The engine books that as a ticket defect: it draws `premise_bounce`, runs Diagnose, parks the
ticket in the Reject queue, and tells the operator to edit a ticket that has nothing wrong with it.

Evidence, in `tickets/implement-incomplete-outcome/evidence/`: on 2026-11-13 the `vscode-help`
attempt 3 first reply was `{"outcome": "incomplete", ...}` and was refused as invalid; the second
reply was `premise_failed` with one finding whose message reads "No contradictory premise or
missing scope-fence file was established; this outcome records incomplete work, not a demonstrated
ticket defect." The journal excerpt shows the engine drawing `premise_bounce` and routing the stem
to the Reject queue on that reply. The same shape (an `incomplete` first reply, then a confessed
`premise_failed`) occurred seven times that day across `vscode-help`, `menu-mirrors-verb-admission`,
and `menu-table-run-review-admission`, each costing a bounce, a Diagnose call, and an operator
confirm. `menu-table-run-review-admission` then succeeded on a plain retry, so a quit is a retry
case, not a ticket defect.

When this ticket is done, `incomplete` is a first-class Implement outcome and attempt terminal. An
`incomplete` attempt counts toward `attempts`, draws no `premise_bounce`, is diagnosed like a
`gate_failed` attempt, and is re-offered drawing `retry` under the existing re-offer rule. The
spec tells the model to reply `incomplete` for unfinished work and never to recast it as
`premise_failed`. The journal, the drain report, `status`, and the harvest then say what happened.

## Scope in / Scope out
Scope in:
- `chupa/artifacts.py::Outcome` gains the member `"incomplete"`, placed after `"premise_failed"`.
  `OUTCOMES` and `chupa/journal.py::TERMINAL_STATES` derive from it and change by derivation only;
  the Harvest and Diagnosis artifacts' `terminal` validation accepts it through
  `TERMINAL_STATES` with no edit of their own.
- `chupa/stages.py::ImplementReply`:
  - `outcome` gains `"incomplete"`;
  - the validator treats `incomplete` as it treats `ok`: an `incomplete` reply whose `findings`
    list is not empty raises;
  - the `premise_failed` error message keeps the phrases `naming `path`` and `implement the
    ticket` that `tests/unit/test_implement_premise_path.py` pins, and its closing clause becomes
    "implement the ticket and reply ok, or reply incomplete when you stopped before finishing";
  - the message raised for findings on a non-premise outcome names `incomplete` as the reply for
    unfinished work.
- `chupa/stages.py::implement`: the existing early return for `premise_failed` widens to both
  stopping outcomes, with no new statement, so the coverage floor on `chupa/stages.py` needs no
  new unit test:
  `if reply.outcome in ("premise_failed", "incomplete"): return _short(result, reply.outcome, list(reply.findings))`.
  An `incomplete` reply carries an empty findings list by validation, so it returns outcome
  `incomplete` with no findings and no packing slip. `run_record` already prints the reply's
  outcome under `## Outcome`.
- `chupa/caps.py::failed_attempt` adds `"incomplete"` to its set of failed terminals, so an
  `incomplete` attempt counts toward `attempts`. Nothing else in `chupa/caps.py` changes.
- `chupa/specs/implement.md`:
  - the paragraph that begins "Two first-class outcomes replace grinding out a bad
    implementation" says three outcomes and gains a third bullet: `incomplete` -- you stopped
    before finished work was committed and nothing in the ticket is wrong; say in `summary` what
    stopped you, carry an empty `findings` list, and commit nothing further; never report
    unfinished work as `premise_failed`;
  - the `## Output format` object lists `"incomplete"` after `"premise_failed"`, and the sentence
    after it says that `ok`, `already_satisfied`, and `incomplete` carry an empty `findings` list;
  - `## On-failure` gains one sentence: if you stopped before finishing, reply `incomplete`; the
    retry findings never ask you to recast unfinished work as `premise_failed`;
  - every sentence that `tests/unit/test_specs.py` pins verbatim stays as it is;
  - `version` bumps to the next minor above the version on main, and both implement version
    pins in `tests/unit/test_specs.py` follow:
    `test_spec_lint_accepts_the_implement_and_requisition_specs` (the `("implement", ...)` pair)
    and `test_implement_spec_consumer_read` (its `spec.meta.version` assertion).
- `docs/how-chupa-works.md`: the Implement outcome list in section 6.2 gains an `incomplete`
  bullet; the failure-routing step that names which caps each outcome draws says `incomplete`
  draws none; the sentence "Failed attempts are `gate_failed`, `premise_failed`, `infra_error`, and
  `timeout` terminals" gains `incomplete`; the `retry` cap row's exception list is unchanged
  because an `incomplete` re-offer draws `retry`.
- Tests:
  - new `tests/unit/test_implement_incomplete.py` holds criteria 1 and 2 with no disk, clock,
    process, or network use, following `tests/unit/test_implement_premise_path.py` and
    `tests/unit/test_caps_requisition_park.py`;
  - `tests/unit/test_drain_reoffer.py::test_other_reoffer_draws_retry` adds `incomplete` to its
    parametrize list; nothing else in that file changes;
  - `tests/integration/test_closed_sets.py`: the expected `OUTCOMES`, `Outcome`, and
    `TERMINAL_STATES` sets each gain `incomplete`; no other expected set changes;
  - `tests/integration/test_gates.py::test_outcome_vocab_is_closed_and_includes_already_satisfied`:
    its expected `OUTCOMES` set gains `incomplete`; nothing else in that file changes;
  - `tests/integration/test_stages.py` gains the test in criterion 5, mirroring
    `test_premise_failed_stops_after_implement_with_its_run_record`;
  - `tests/integration/test_terminal.py` gains the test in criterion 6, mirroring
    `test_a_premise_failure_journals_its_terminal`;
  - new `tests/regress_implement_incomplete.py` is the `## Regression` reproducer. It follows the
    protocol of `tests/regress_vscode_task_identity.py`: it imports `ImplementReply` from
    `chupa.stages` (an `ImportError` prints `error` and exits 2), validates an `incomplete` reply
    with an empty `findings` list, and prints `defect` with exit 1 when validation raises, `pass`
    with exit 0 when it validates and an `incomplete` reply carrying one finding is refused, and
    `defect` otherwise. It prints exactly one JSON object to stdout.

Scope out:
- `chupa/runner.py` and `chupa/drain.py` stay as they are. `runner.drive` draws `premise_bounce`
  only for `premise_failed` and `infra` only for `infra_error` and `timeout`, so an `incomplete`
  attempt draws neither; `failure_terminal` routes it by the Diagnose verdict as it routes
  `gate_failed`; `parked_blob` parks only premise and diff-budget terminals, so an `incomplete`
  stem is re-offerable while `retry` has budget; `record_reoffer` draws `retry` for every terminal
  it does not except. A second routing path for `incomplete` is accretion.
- No escalation on a single `incomplete`. The existing rules move the rung: a Diagnose
  `escalate` verdict, or the same failure reason three times running.
- `chupa/specs/diagnose.md` stays as it is. Diagnose receives the `incomplete` terminal through
  the harvest and answers with its existing verdicts.
- `chupa/config.py::SpikeKind`, `chupa/retro.py`, and the scorecard stay as they are; an
  `incomplete` terminal is visible in `status`, the drain report, and the journal without a spike
  kind.
- The engine's invalid-artifact retry text stays as it is; the spec change removes the case that
  produced it.
- `vscode-chupa/` stays as it is: the extension draws terminal names from the snapshot and
  enumerates none.

## Scope fence
- chupa/artifacts.py
- chupa/stages.py
- chupa/caps.py
- chupa/specs/implement.md
- docs/how-chupa-works.md
- tests/unit/test_implement_incomplete.py
- tests/unit/test_drain_reoffer.py
- tests/unit/test_specs.py
- tests/integration/test_closed_sets.py
- tests/integration/test_gates.py
- tests/integration/test_stages.py
- tests/integration/test_terminal.py
- tests/regress_implement_incomplete.py

## Acceptance criteria
1. `tests/unit/test_implement_incomplete.py::test_incomplete_reply_shape`:
   `ImplementReply.model_validate` accepts `{"outcome": "incomplete", "findings": [], ...}` and
   returns outcome `incomplete`; the same reply with one `premise` finding raises
   `ValidationError`; an `ok` reply with one finding still raises. A schema that accepts
   `incomplete` with findings, or still refuses `incomplete`, fails.
2. `tests/unit/test_implement_incomplete.py::test_incomplete_is_a_failed_attempt`:
   `failed_attempt({"to": "incomplete", "stage": "implement"})` is `True` and
   `failed_attempt({"to": "already_satisfied"})` stays `False`. A set that omits `incomplete`
   fails.
3. `tests/unit/test_drain_reoffer.py::test_other_reoffer_draws_retry[incomplete]`: re-offering a
   stem whose last terminal is `{"to": "incomplete"}` journals exactly one `retry` cap draw. A
   re-offer that draws nothing, as a premise park does, fails.
4. `tests/integration/test_closed_sets.py::test_artifacts_closed_sets_and_constants` and
   `tests/integration/test_closed_sets.py::test_journal_closed_sets_and_constants` pass with
   `incomplete` in the expected `OUTCOMES`, `Outcome`, and `TERMINAL_STATES` sets, and
   `tests/integration/test_gates.py::test_outcome_vocab_is_closed_and_includes_already_satisfied`
   passes with `incomplete` in its expected `OUTCOMES` set. A vocabulary that lacks `incomplete`
   in any of the three fails.
5. `tests/integration/test_stages.py::test_incomplete_stops_after_implement_with_its_run_record`:
   with an `implement_reply("incomplete")` script, `outcomes(result) == {"implement":
   "incomplete"}`, the result carries no findings, no Check or Review call is made, and
   `tickets/<stem>/run.md` contains `## Outcome\n\nincomplete\n`. A stage that maps the reply to
   `ok`, `premise_failed`, or `invalid_artifact` fails.
6. `tests/integration/test_terminal.py::test_an_incomplete_attempt_journals_a_retry_terminal`:
   `run(repo, [implement_reply("incomplete"), diagnosis_reply()])` leaves the last transition
   equal to `{"to": "incomplete", "stage": "implement", "reason": "incomplete", "dispatch":
   "retry"}`, and the journal holds no `cap_consumed` event with cap `premise_bounce` for the stem.
   A terminal that carries `routed: reject_queue`, or any `premise_bounce` draw, fails.
7. `tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs` and
   `tests/unit/test_specs.py::test_implement_spec_consumer_read` pass with both implement pins at
   the bumped version, so a spec edit without a version bump, or a bump without both pins, fails.
8. `chupa/specs/implement.md` and `docs/how-chupa-works.md` name `incomplete` as described in
   Scope in; the first `uv run python -c` command in `## Verification` checks that
   `chupa/specs/implement.md` mentions `incomplete` at least four times and
   `docs/how-chupa-works.md` at least three times.
9. `uv run python tests/regress_implement_incomplete.py` prints `{"regression_result": "pass"}` and
   exits 0 on the branch; Check proves it prints `defect` and exits non-zero on the merge base.
10. `./dev.py test` exits 0.

## Verification
```
uv run python -c "import pathlib; s = pathlib.Path('chupa/specs/implement.md').read_text(); d = pathlib.Path('docs/how-chupa-works.md').read_text(); assert s.count('incomplete') >= 4, s.count('incomplete'); assert d.count('incomplete') >= 3, d.count('incomplete')"
./dev.py test tests/unit/test_implement_incomplete.py tests/unit/test_drain_reoffer.py tests/unit/test_specs.py tests/unit/test_implement_premise_path.py tests/unit/test_caps_requisition_park.py
./dev.py test tests/integration/test_closed_sets.py tests/integration/test_gates.py tests/integration/test_stages.py tests/integration/test_terminal.py
uv run python tests/regress_implement_incomplete.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- an `incomplete` terminal draws `premise_bounce`, parks the stem until its `ticket.md` changes,
  or routes it to the Reject queue while `retry` has budget;
- the engine infers `incomplete` from the text of a `premise_failed` reply instead of the reply
  naming the outcome;
- `chupa/runner.py` or `chupa/drain.py` gains a path that handles `incomplete` by name;
- a sentence that `tests/unit/test_specs.py` pins verbatim changes;
- `chupa/specs/diagnose.md`, `chupa/config.py`, `chupa/retro.py`, or any file under
  `vscode-chupa/` changes.

## Time budget
- expected: 60m
- stuck: 120m

## Regression
```
uv run python tests/regress_implement_incomplete.py
```
- carries: tests/regress_implement_incomplete.py
