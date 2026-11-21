---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- requisition-review-compact-context
- plan-subagents-explicit-sonnet

## Context
- clutch/requisition.py
- clutch/ask.py
- clutch/config.py::Config
- tests/integration/test_requisition.py
- tests/unit/test_requisition_dependents.py
- tests/unit/test_requisition_panel.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_serve.py
- clutch/docs/host-authoring.md
- docs/how-clutch-works.md#3. Tickets

## On-demand
- clutch/specs/requisition_review.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- clutch/specs/ask/author.md
- clutch/specs/ask/review.md

## Goal / Why
Owner decision, November 21: routine tickets receive one short Sonnet check; full buildability investigation and extra auditors run only when explicitly requested. The owner withdrew the proposed cost-comparison study. This stem now delivers that decision instead of an experiment. Current plan prompts require a separate adversarial audit for every authored row, while requisition review directs exhaustive caller/test investigation and repeated full dependent accounting. Stop that blanket cost. Retain mechanical authoring checks, the short ticket check, implemented-code review and existing run gates. Explicit full review uses the existing clutch prompt review STEM procedure; no new command, mode flag, classifier, benchmark or configuration framework is introduced.

## Boundary contract
### Routine ticket check
- disposition: replace
- owner: clutch/requisition.py and clutch/specs/requisition_review.md
- consumers: CLI ticket review, Author, Rework and dispatch through their existing review_ticket calls
- observable change: the automatic requisition check is a concise review of the supplied ticket and declared contracts, criteria and selected Context; it does not launch independent reviewers, perform exhaustive repository closure searches or redo full dependent accounting. The existing verdict vocabulary and JSON reply remain.
- compatibility: preserve ticket parsing/lint, render feasibility, provider failure handling, provisional-review rules and implemented-code review. Existing full-investigation assertions migrate to the explicit audit owner. No automatic fallback to full review is permitted after a short-check snag.
- acceptance: a normal ticket check uses one reviewer invocation with no model-panel fanout or schema-repair model retry inside that invocation; invalid replies return a concrete snag. A routine snag is repaired through the existing authoring process without adding auditors.
- tests: tests/unit/test_requisition_brief_check.py and tests/integration/test_requisition_brief_check.py
- post-merge source of truth: clutch/requisition.py and clutch/specs/requisition_review.md

### Explicit full investigation
- disposition: reuse
- owner: clutch/specs/ask/review.md
- consumers: an operator explicitly requesting clutch prompt review STEM
- observable change: the full adversarial procedure remains available on request; routine plan-ticket-drain and plan-ticket-serve workflows no longer invoke it for every row
- compatibility: preserve its read-only checks and report-to-owner behavior, and preserve Sonnet selection for any Claude children an explicitly requested audit launches; no automatic size/tier/risk classifier chooses a full investigation
- acceptance: rendered plan prompts require one short check and do not require a separate per-ticket audit; the explicit audit still exposes the detailed checks
- tests: tests/integration/test_requisition_brief_check.py and tests/integration/test_ask_plan_brief_review.py
- post-merge source of truth: clutch/specs/ask/review.md and the two shipped plan prompts

## Scope in / Scope out
Scope in:
- Replace the routine requisition instructions with a short supplied-material check for clear contradictions, missing declared interface decisions, scope/criteria mismatches and impossible named verification. Treat a declared contract as the design input to check for contradictions, not permission to re-design it. Do not instruct the routine model to browse every caller, importer, test, sibling or dependent. Keep the existing reply schema; routine dependents is an empty list and no exhaustive dependents-accounting gate may force an investigation or another model call.
- Keep mechanical lint and full Implement render feasibility checks. Remove coverage-dependent discovery/accounting from the automatic check; keep explicit full-audit checks in their existing ask/review.md owner. Delete private helpers that become production-callerless rather than maintaining a dormant second path. Keep sibling information only as the already bounded supplied overlap summary, not an instruction to investigate every sibling.
- Run the routine requisition check as one member and one invocation, using the existing route and current Sonnet routing. Preserve provider drought/auth failure handling; malformed model output yields a snag instead of another automatic model call. Do not change the provider request schema or add a second LLM call site. Full review is the already-existing operator audit procedure, not a hidden engine escalation.
- In both plan prompts remove the mandatory separate adversarial agent and any unconditional full re-audit before confirmation. Keep authoring, lint, one short ticket review and confirmation, plus existing release-phase acceptance. In ask/author.md describe the short check and preserve the existing bounded repair procedure. Explicit full audit requires an owner request; ticket size, a snag, the implementing model tier and agent preference do not authorize it.
- Bump requisition_review.md to the next minor above main. Migrate existing assertions that pin exhaustive checks to the explicit ask/review.md owner, retaining their substantive checks there. Adjust direct full-investigation fixtures and panel/dependent tests to the new routine semantics; add new tests in separate files. Keep contract/criterion checks in the brief prompt, and verify the moved full checks remain available explicitly.
- Update the authoring guide workflow and review descriptions in README, the host-running verb row, how-clutch-works, CLI help and the extension's existing review help to state the brief default and explicitly requested full audit. Preserve the mandatory ticket-review command in the managed conduct rules; this ticket changes its default depth, not that HARD rule. Do not edit the managed conduct block or its template.
- The dependency's new context-pack tests that assert unchanged full dependent-accounting policy must now assert brief behavior; preserve their lossless material and no-duplicate-ticket assertions. The dependency's shared review identity continues to bind the selected brief spec and actual supplied inputs.
Scope out:
- No study, synthetic corpus, live evaluation calls, new training command, experiment report, automatic policy promotion, extra subagents, risk score, new config knob or removal of implemented-code review/tests.

## Scope fence
- clutch/requisition.py
- clutch/specs/requisition_review.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- clutch/specs/ask/author.md
- clutch/specs/ask/review.md
- clutch/__main__.py
- clutch/help.py
- clutch/docs/host-authoring.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_requisition_brief_check.py
- tests/integration/test_requisition_brief_check.py
- tests/integration/test_ask_plan_brief_review.py
- tests/integration/test_requisition.py
- tests/unit/test_requisition_panel.py
- tests/unit/test_requisition_dependents.py
- tests/unit/test_requisition_context_pack.py
- tests/integration/test_requisition_context_pack.py
- tests/unit/test_requisition_sibling_tickets.py
- tests/unit/test_requisition_stage_events.py
- tests/unit/test_key_scope.py
- tests/unit/test_callerless_code_removed.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_authoring_document_test_rule.py
- tests/integration/test_requisition_review_whole_value_closure.py
- tests/integration/test_requisition_review_tool_output_evidence.py
- tests/integration/test_requisition_review_stand_in_closure.py
- tests/integration/test_spec_unit_io_seam.py
- tests/integration/test_precondition_rules.py
- tests/integration/test_fence_closure_registries.py
- tests/integration/test_spec_sibling_tickets.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_requisition_brief_check.py tests/integration/test_requisition_brief_check.py` proves routine review performs one short reviewer invocation and no panel or schema-repair invocation; malformed replies snag without fallback to full investigation, and mechanical lint/render failures still use no model.
2. `./dev.py test tests/integration/test_ask_plan_brief_review.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py` proves both workflows retain lint, short review and confirmation while requiring an explicit owner request for a full audit or extra reviewer; phase acceptance remains.
3. `./dev.py test tests/integration/test_requisition_brief_check.py` proves the brief prompt omits exhaustive closure and repeated dependent-accounting obligations while the explicit ask/review.md audit retains those detailed checks; no tier, ticket size or model preference silently selects full review.
4. `./dev.py test tests/unit/test_requisition_context_pack.py tests/integration/test_requisition_context_pack.py tests/integration/test_requisition.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py` proves the dependency's lossless context/no-duplication behavior and the existing verdict and feasibility contracts remain after switching default review depth.

## Verification
```
./dev.py test tests/unit/test_requisition_brief_check.py tests/integration/test_requisition_brief_check.py tests/integration/test_ask_plan_brief_review.py tests/integration/test_requisition.py tests/unit/test_requisition_panel.py tests/unit/test_requisition_dependents.py tests/unit/test_requisition_context_pack.py tests/integration/test_requisition_context_pack.py tests/unit/test_requisition_sibling_tickets.py tests/unit/test_requisition_stage_events.py tests/unit/test_key_scope.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py
```

## Definition of rejected
A routine check silently runs full investigation or adds an auditor; a comparison study or new review framework is built; required mechanical checks or implemented-code review disappear; or an owner request is replaced by an automatic risk classifier.

## Time budget
- expected: 30m
- stuck: 60m
