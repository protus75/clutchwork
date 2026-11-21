---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Runs before
- requisition-contract-review-comparison

## Context
- clutch/ask.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_serve.py
- clutch/docs/host-running.md

## On-demand
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md

## Goal / Why
The plan prompts currently request separate authoring and adversarial-audit agents without selecting their model, allowing them to inherit expensive supervisor models. Make Sonnet an explicit selection for every Claude subagent these two plan workflows launch, including phase-closing review and decision panels, while preserving required different-family judges. This is the recurring process cause paired with the immediate routing instance ticket. The shipped process prompts, not session notes or agent conduct rules, own this policy.

## Boundary contract
### Shipped plan delegation
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/plan-ticket-serve.md
- consumers: operators following clutch prompt plan-ticket-drain and plan-ticket-serve
- observable change: each Claude child is explicitly launched as Sonnet rather than inheriting the parent model, including author, audit, release review and decision-panel children
- compatibility: delegation authority, verdict gates, non-Claude provider selection and different-model-family judge requirements remain intact
- acceptance: rendered prompts require explicit Sonnet for all Claude child roles and never instruct a same-family judge where diversity is required
- tests: tests/integration/test_ask_plan_subagent_models.py
- post-merge source of truth: clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/plan-ticket-serve.md

## Scope in / Scope out
Scope in:
- In both plan prompts, state once that every Claude subagent uses an explicit Sonnet model selection in the host agent facility; an Opus parent never implicitly promotes its children. Non-Claude agents retain their selected provider and model. If explicit model selection is unavailable, report that limitation rather than silently inheriting Opus.
- Apply that rule to row authors, separate adversarial auditors, phase-closing reviewers, and open-decision proposal/judge agents while retaining the existing different-family calibration requirement.
- Update the existing test that forbids all provider-name mentions in these prompts to allow the deliberately introduced Claude/Sonnet model policy while continuing to reject workspace paths, shell commands and session facts. Add new rendered-prompt coverage in its own integration file.
- Update the plan prompt descriptions in the host run guide and command table to mention the model-selection behavior.
Scope out:
- No new enforcement rule, agent conduct edit, config schema, parallelism setting, provider probing, or removal of adversarial audits. The brief-default and explicit-full-audit policy is delivered separately by `requisition-contract-review-comparison`.

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_subagent_models.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py` proves both rendered workflows select Sonnet explicitly for Claude authoring, audit, phase review and decision children and retain different-family judge instructions.
2. `./dev.py test tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py` proves an unsupported child-model selection cannot silently inherit Opus and existing startup, delegation, window and daemon-mode checks still pass.

## Verification
```
./dev.py test tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py
```

## Definition of rejected
Removing required checks without evidence, introducing a second production authority, adding speculative settings, or changing files outside the fence.

## Time budget
- expected: 12m
- stuck: 24m
