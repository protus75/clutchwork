---
state: rejected
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Context
- docs/stage-panels-plan.md#Status
- docs/stage-panels-plan.md#Current state
- docs/training-data-plan.md#Status
- docs/training-data-plan.md#4. The flywheel: how a host uses it
- docs/annotations-index-plan.md#7. Config
- clutch/docs/host-qwen.md
- clutch/providers.py::FailureClass
- clutch/providers.py::candidates
- clutch/box.py::Verdict
- clutch/box.py::Resolution
- clutch/training.py::evaluate

## Goal / Why
`docs/provider-roles-plan.md` exists: one plan for using several paid providers (Anthropic, OpenAI codex, Google Gemini) and a local open-weight provider (qwen through Ollama) where each earns its cost. Today the owner's thinking on this lives only in a chat transcript (2026-11-22), and the pieces it needs are spread across the panels, training, and index plans with no document saying which gaps remain. The plan records what already exists so later tickets do not rebuild it, and it names the gaps as a ticket breakdown the roadmap can admit.

Facts the plan must state as current state (each verified in code on 2026-11-22 at `dd8796d8c`):
- Stages already route by `(tier, surface)` with optional `kinds`; the role-to-model mapping (which vendor plans, authors, implements, reviews) is host config in routing rows, not engine code. Model rankings change every few months and never go into engine code or shipped guides.
- Quota failover exists: `quota_exhausted` and `rate_limited` failures (`clutch/providers.py::FailureClass`) hold the provider for `quota_window_minutes` and the next routing candidate serves (`clutch/thresh.py`).
- Panels exist with `findings-union`, `majority-verdict`, and `best-of-n`; `panel_facts` is journaled and says whether members are distinct models or repeated samples of one.
- A local qwen provider is documented for `implement` (`clutch/docs/host-qwen.md`).
- `training export` already emits a `triage` record kind, labelled by whether the box message's resolution kind matches the triage verdict (`clutch/training.py`); `training eval` replays only the `review` surface (`clutch/training.py::evaluate` hard-codes `surface="review"`).
- The project index takes vectors from a host-declared `index.embed` argv; clutch ships no embedding model.
- Box verdicts carry a free-text `rationale` (`clutch/box.py::Verdict`), not a closed reason code.
- Nothing enforces that a ticket's review provider differs from its implement provider.

Gaps the plan must design, each as one ticket-breakdown row with a kind, priority, and dependency:
1. `training eval` lens for `triage`: replay held-out triage records and score agreement, so a local model is measured before routing triage to it.
2. Downstream triage label: a triage `author` verdict whose ticket is later rejected labels negative, not `merged`; today the label stops at the resolution kind.
3. Closed decline reason codes on box verdicts (for example already-covered, not-worth-churn, too-speculative), so labels are usable for training.
4. Duplicate grouping at `box suggest` time using the `index.embed` command: a near-duplicate increments the earlier message's count instead of filing a new message.
5. A cross-vendor review preference (owner, 2026-11-22): review prefers a candidate whose provider differs from the ticket's implement provider, but only while such a candidate is routed for review and not held by a quota or rate-limit breaker. When no other provider is routed, or every other one is quota-held, review runs on the same provider rather than waiting; the plan says how that fallback is journaled so the scorecard can count same-vendor reviews.
6. A learned tier router, gated on rows 1-2 showing a local model meets the GO baseline.

## Boundary contract
none
- reason: documentation only; adds one plan document describing existing behavior and proposed tickets, with no code, config, prompt, or contract change.

## Scope in / Scope out
Scope in: create `docs/provider-roles-plan.md` with the section layout other plans use (`Status`, `Roadmap`, `Current state`, `Departures from the design record`, `Target design`, `Where each piece lives`, `Ticket breakdown`, `Risks`, `Open decisions`), covering the current-state facts and the six gaps in Goal / Why. The `Roadmap` section says the plan has no roadmap rows yet and names the earliest release each breakdown row could fit. `Risks` covers the small number of positive triage labels and the cost of best-of-N against a reviewer's time. Fill its meta block with `uv run clutch meta fill docs/provider-roles-plan.md`.
Scope out: no code, config, test, prompt spec, or guide changes; no edits to the roadmap or other plans; no vendor benchmark numbers or model rankings in the plan.

## Scope fence
- docs/provider-roles-plan.md

## Acceptance criteria
1. `docs/provider-roles-plan.md` exists and `uv run clutch meta check docs/provider-roles-plan.md` exits 0.
2. A one-time review check: `docs/provider-roles-plan.md` has a `Ticket breakdown` table with one row per gap 1-6, each naming a proposed stem, kind, and priority.

## Verification
```
uv run clutch meta check docs/provider-roles-plan.md
```

## Definition of rejected
The plan states a capability as missing that the Goal lists as existing, names a vendor model ranking or benchmark, or edits any file outside the fence.

## Time budget
- expected: 15m
- stuck: 30m
