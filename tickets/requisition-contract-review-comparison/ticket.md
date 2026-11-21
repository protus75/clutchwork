---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/requisition.py
- clutch/driver.py::Driver.panel_members
- clutch/stages.py::implement_inputs
- tests/integration/test_requisition.py
- tests/unit/test_requisition_stage_events.py
- tests/unit/test_callerless_code_removed.py
- docs/how-clutch-works.md#8. AI providers and prompts

## On-demand
- clutch/specs/requisition_review.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md

## Goal / Why
Owner decision, 2026-11-21: normal ticket review is one short Sonnet check. Today `review_ticket` sends the ticket plus the whole Implement prompt, tells the model to trace callers, importers and every test, makes it account for every coverage dependent (and fails a sound ticket on "extra dependent", box-000955), fans out to a panel, and re-prompts on a bad reply. The plan prompts also launch a separate adversarial audit agent per row. After this ticket a normal review is one model call over the ticket, its selected Context and the prior review, checking only the ticket's own statements; the per-row audit agent is gone. The full audit stays available as `clutch prompt review <stem>` when the owner asks for it. This ticket supersedes `requisition-review-compact-context` and `requisition-review-approval-reuse`; the owner rejects both, so no sibling edits these files.

## Boundary contract
### Routine ticket check
- disposition: replace
- owner: clutch/requisition.py::review_ticket and clutch/specs/requisition_review.md
- consumers: CLI `ticket review`, Author, Rework and dispatch, all through `review_with_identity`
- observable change: one model call per review with prompt inputs `ticket`, `context` and `prior_review`; no coverage-dependent accounting, no panel, no re-prompt; an unparseable reply is a `snag` with `mechanical="invalid reply"`
- compatibility: `RequisitionReply` and `RequisitionVerdict` are unchanged (`dependents` stays in the schema and the spec asks for `[]`); `review_ticket` and `review_with_identity` keep their signatures; ticket-lint and render-headroom snags still spend no model call; provider failure handling and stage events are unchanged
- acceptance: criteria 1 to 3
- tests: tests/unit/test_requisition_brief_check.py and tests/integration/test_requisition_brief_check.py
- post-merge source of truth: clutch/requisition.py and clutch/specs/requisition_review.md

### Driver panel accessor
- disposition: replace
- owner: clutch/driver.py
- consumers: clutch/requisition.py::review_ticket only
- observable change: `Driver.panel_members` is deleted with its only caller; the identity gatherer keeps using `providers.panel_members`
- compatibility: no other production caller exists
- acceptance: criterion 4
- tests: tests/unit/test_callerless_code_removed.py
- post-merge source of truth: clutch/driver.py

### Plan prompts
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/plan-ticket-serve.md
- consumers: operators running `clutch prompt plan-ticket-drain` and `clutch prompt plan-ticket-serve`
- observable change: the per-row "separate agent with `clutch prompt review <stem>` for adversarial audit" step is removed; each prompt says to run `clutch prompt review <stem>` only when the owner asks for a full audit
- compatibility: authoring, lint, `clutch ticket review` and confirm steps stay; the Sonnet subagent rule stays as written
- acceptance: criterion 5
- tests: tests/integration/test_requisition_brief_check.py
- post-merge source of truth: the two plan prompts

## Scope in / Scope out
Scope in:
- `clutch/specs/requisition_review.md`: bump `version` to the next minor above main. Replace the `## Task` bullet list with only these checks of the ticket's own text: a stated repo-state precondition not delivered by `## Depends on` (keep the existing precondition bullet verbatim); a boundary contract whose meaning or `none`/`create` reason is untrue; a `## Scope fence` or `## Verification` path that does not exist and that Scope in does not create (keep that bullet verbatim); a criterion or Definition-of-rejected clause that contradicts merged behavior, or two criteria that cannot both hold; two statements that cannot both hold; a stated invariant with no test obligation; the `no-reproduction-exit` bullet; the `## Regression` protocol bullet. Keep the graphics paragraph, the delimiter note in `## Role`, the `rma` paragraph and the prior-review paragraph (rule each prior finding `cleared` or `standing`; new findings only against changed text unless a criterion is impossible) verbatim. Delete every other Task bullet (sibling interfaces, tool-output scratch runs, reference-closure tracing, set/registry grep, whole-value grep, stand-in grep, roadmap-pin, dependents accounting, coverage floor, unit-test repo-file and disk placement), the "Redo dependents accounting" sentence and the "invalid requisition review reply ... transitive import" sentence. Add one sentence: judge only the supplied ticket and Context; do not search the repository for callers, importers, tests, siblings or dependents. Inputs become `ticket`, `context` (the ticket's selected Context) and `prior_review`; delete the `render`, `coverage_dependents`, `sibling_tickets` and `retry_findings` blocks. The output format keeps the same JSON keys and says `dependents` is always `[]`. Delete the `## On-failure` retry sentence about `retry_findings`; keep the insufficient-evidence and `rma` sentences.
- `clutch/requisition.py::review_ticket`: keep the lint snag, the `_base_render` headroom snag, and the `review render over bound` snag when rendering the review prompt raises `RenderOverBound`. Rewrite `test_review_render_over_bound_is_mechanical_snag` in tests/integration/test_requisition.py to reach that branch through an oversized `prior` argument to `review_ticket`, asserting `mechanical == "review render over bound"` and zero LLM requests. Take `context` from `implement_inputs(repo, text, ticket, ())["context"]` (the same reader `_base_render` uses; no second Context reader). Delete coverage-map reading, the data-file test scan, `expected_dependents`, the sibling block computation, the panel loop and the schema re-prompt loop. Make exactly one `llm_call` at `call_seq` with `key_scope` as given; on `ValidationError` return the existing `invalid reply` snag; otherwise return the reply's verdict. Keep stage events, watch, spool writes, timeout, drought, `ProviderCallError` re-raise and other-exception snag behavior. Keep the `coverage_map` keyword of `review_ticket`: `review_with_identity` passes it to `review_input_identity`, and removing it would change every caller and about fifteen tests for no behavior gain. Delete `dependent_errors` and `test_sources`, which have no other caller. Keep `sibling_tickets_block`; `review_input_identity` still uses it.
- `clutch/driver.py`: delete `Driver.panel_members`.
- Tests: delete tests/unit/test_requisition_panel.py and tests/unit/test_requisition_dependents.py (they test only the panel and dependent accounting). Delete tests/integration/test_spec_sibling_tickets.py, tests/integration/test_requisition_review_stand_in_closure.py, tests/integration/test_requisition_review_tool_output_evidence.py and tests/integration/test_requisition_review_whole_value_closure.py (each pins only a deleted Task bullet). In tests/integration/test_requisition.py, tests/unit/test_specs.py, tests/integration/test_precondition_rules.py, tests/integration/test_authoring_document_test_rule.py, tests/integration/test_fence_closure_registries.py and tests/integration/test_spec_unit_io_seam.py remove only the assertions or tests that pin deleted spec text or removed behavior (coverage-dependent prompt blocks, invalid coverage map snag, re-prompt then accept, sibling rule, spec `inputs` tuple, which becomes `("ticket", "context", "prior_review")`); keep their host-authoring guide, diagnose-spec and other assertions. Update the `requisition_review` version pin in tests/unit/test_specs.py and tests/integration/test_specs_delimiter_note.py. In tests/unit/test_requisition_sibling_tickets.py keep the `sibling_tickets_block` tests and delete the test asserting siblings reach the review prompt. Give the hand-built tickets in tests/unit/test_key_scope.py, tests/unit/test_requisition_stage_events.py and tests/unit/test_requisition_sibling_tickets.py whatever `context` they need to reach the new `implement_inputs` read (for example `context=()`), and nothing else. Add `(requisition, "dependent_errors")`, `(requisition, "test_sources")` and `(driver.Driver, "panel_members")` to the removed list in tests/unit/test_callerless_code_removed.py.
- Re-ask tests that pin the removed schema re-prompt: in tests/integration/test_author.py rewrite `test_author_reviews_keep_unique_keys_when_one_reasks` so the `"invalid"` requisition reply is one review call that returns the `invalid reply` snag with no second requisition request for that review; adjust its FakeLLM script and expected requisition keys to that flow. In tests/integration/test_rework.py rewrite the `headroom=False` case of `test_split_reviews_keep_unique_keys_when_one_reasks` so the `"invalid"` reply is one review call returning the `invalid reply` snag; drop the re-ask `requisition()` from the script and assert the resulting outcome, requisition keys and request count for that single-call flow. Leave every other test in both files unchanged.
- New tests: tests/unit/test_requisition_brief_check.py drives `review_ticket` with a fake driver and fake LLM under `tmp_path`; tests/integration/test_requisition_brief_check.py reads the shipped spec and plan prompts through a `Path(__file__)` anchor.
- Plan prompts: in both files, replace "then a separate agent with `clutch prompt review <stem>` for adversarial audit; carry out its Recommendation," with nothing, and add one sentence to the same bullet: "Run `clutch prompt review <stem>` for a full audit only when the owner asks for one."
- docs/how-clutch-works.md: in section 8 drop "requisition review" from the surfaces that fan out to a panel, and rewrite the `requisition_review.md` row of the spec table to describe the short check of the ticket and its Context. Nothing else in the document changes.
Scope out:
- Approval reuse, context packing beyond the `context` input above, `review_input_identity` composition, `RequisitionReply`/`RequisitionVerdict` schema, the full-audit and Author prompt specs, the managed conduct block, config, and review of implemented code.

## Scope fence
- clutch/requisition.py
- clutch/driver.py
- clutch/specs/requisition_review.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- docs/how-clutch-works.md
- tests/unit/test_requisition_brief_check.py
- tests/integration/test_requisition_brief_check.py
- tests/integration/test_requisition.py
- tests/unit/test_requisition_panel.py
- tests/unit/test_requisition_dependents.py
- tests/unit/test_requisition_sibling_tickets.py
- tests/unit/test_requisition_stage_events.py
- tests/unit/test_key_scope.py
- tests/unit/test_callerless_code_removed.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_precondition_rules.py
- tests/integration/test_authoring_document_test_rule.py
- tests/integration/test_fence_closure_registries.py
- tests/integration/test_spec_unit_io_seam.py
- tests/integration/test_spec_sibling_tickets.py
- tests/integration/test_requisition_review_stand_in_closure.py
- tests/integration/test_requisition_review_tool_output_evidence.py
- tests/integration/test_requisition_review_whole_value_closure.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_author.py
- tests/integration/test_rework.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_requisition_brief_check.py` proves an approving review makes exactly one LLM request (not two or more), and a reply that is not valid JSON returns `verdict="snag"` with `mechanical="invalid reply"` and `calls == 1`, not a second request.
2. `./dev.py test tests/unit/test_requisition_brief_check.py` proves a reply listing dependents for a ticket with no coverage dependents returns `approve`, not a snag containing `extra dependent` (box-000955), and that the rendered prompt holds the ticket's selected Context bytes once and no `render`, `coverage_dependents`, `sibling_tickets` or `retry_findings` block.
3. `./dev.py test tests/integration/test_requisition.py` proves a ticket failing lint, a ticket over render headroom and an oversized `prior` (`mechanical == "review render over bound"`) each return a snag with zero LLM requests.
4. `./dev.py test tests/unit/test_callerless_code_removed.py` proves `requisition.dependent_errors`, `requisition.test_sources` and `Driver.panel_members` no longer exist, not merely that they are unused.
5. `./dev.py test tests/integration/test_requisition_brief_check.py` proves the shipped `requisition_review.md` Task has no "dependents", "Trace the reference closure" or "grep `tests/`" instruction, and that neither rendered plan prompt contains "for adversarial audit" while both still contain `clutch ticket review` and `clutch prompt review <stem>` tied to an owner request.

## Verification
```
./dev.py test tests/unit/test_requisition_brief_check.py tests/integration/test_requisition_brief_check.py tests/integration/test_requisition.py tests/unit/test_requisition_sibling_tickets.py tests/unit/test_requisition_stage_events.py tests/unit/test_key_scope.py tests/unit/test_callerless_code_removed.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_precondition_rules.py tests/integration/test_authoring_document_test_rule.py tests/integration/test_fence_closure_registries.py tests/integration/test_spec_unit_io_seam.py tests/integration/test_graphics_review_spec_blocks.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_author.py tests/integration/test_rework.py
```

## Definition of rejected
A routine review makes more than one model call, keeps dependent accounting or a panel, adds a fallback to a fuller review, adds a config knob, mode flag or new command, or changes files outside the fence.

## Time budget
- expected: 25m
- stuck: 50m