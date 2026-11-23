<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Plan for assigning planning, review, implementation and chores to providers by cost and quality, listing the current routing, failover, panel and training machinery and breaking the remaining gaps into roadmap tickets.
relates: [clutch/box.py, clutch/providers.py, clutch/training.py]
owner: engine
verified: 8f1c29c2
hash: b3dd28dd836f2c68bc96709633b4767e5c97a5e69a1cb890da2291f7b9e469f4
-->
# Provider roles: plan

Use each provider where it pays for itself. A host with Anthropic, OpenAI (codex) and Google (Gemini) subscriptions, plus a local open-weight model (qwen through Ollama), should spend its scarce, expensive quota on the decisions that matter most (planning, review), its high-volume quota on implementation, and its free local capacity on high-volume chores and measured narrow surfaces. Most of the machinery for this already exists; this plan records what exists so no ticket rebuilds it, sets the principles a host's routing follows, and breaks the remaining gaps into tickets.

## Status

No roadmap rows yet. Written 2026-11-22 at commit `dd8796d8c` from an owner chat session on provider roles and qwen; every current-state fact below was checked in code at that commit.

## Roadmap

No rows admitted. Every breakdown row builds on merged 0.5.0 work (panels, training export and eval, the project index), so the earliest fit is the next open release. Rows 1-3 are independent of each other and of the parallel plan; row 4 needs the index's `index.embed` command configured; row 6 waits on the evidence rows 1-2 produce. Shared budgets: none (no CORE_TEMPLATE text).

## Current state

- **Roles are routing config.** Each stage is a surface (`author`, `implement`, `review`, `diagnose`, `triage`, ...). Routing rows map `(tier, surface)`, optionally restricted by ticket `kinds`, to an ordered list of provider candidates (`clutch/providers.py::candidates`; `clutch/docs/host-contract.md`). Which vendor plans, authors, implements or reviews is therefore a host's `config.yaml`, not engine code.
- **Failover on quota exists.** A provider call classified `quota_exhausted` holds that provider for its `limits.quota_window_minutes` (default 60), and the next routing candidate serves; `auth_error` excludes the provider until login; `outage` and `unclassified` failures count toward a journal-backed breaker (`clutch/thresh.py`). When every candidate of a route is unavailable, the ticket parks as `infra_error` with reason `provider_drought`. `rate_limited` is classified but opens no hold.
- **Panels exist.** A routing row's `panel` runs a surface as 1-3 members with a closed combiner: `findings-union` (review), `majority-verdict` (diagnose, triage, review_visual), `best-of-n` (implement) (`docs/stage-panels-plan.md`). Each combined stage journals `panel_facts`, so the panel scorecard separates distinct-model agreement from repeated samples of one model (`docs/how-clutch-works.md` §9.6).
- **A local provider exists.** `clutch/docs/host-qwen.md` routes Ollama's `qwen3-coder:30b` through Qwen Code to `implement`, probed by `clutch provider probe qwen`.
- **Training data and eval exist.** `clutch training export` emits `implement`, `preference`, `review`, `diagnosis`, `ticket`, `conflict` and `triage` records (`clutch/training.py`). A triage record is labelled `merged` when the box message's resolution kind matches the triage verdict, `negative` when it does not, and `neutral` while unresolved. `clutch training eval` replays only the `review` surface: `evaluate` hard-codes `surface="review"` and the `approve`/`snag`/`rma` verdicts.
- **Embeddings are host-supplied.** The project index (`docs/annotations-index-plan.md`) calls a host-declared `index.embed` argv for vectors; clutch ships no embedding model.
- **Box verdicts are free text.** A triage verdict is `author`, `tombstone` or `declined` with a free-text `rationale` (`clutch/box.py::Verdict`); a resolution is `ticket`, `tombstone` or `declined` with a link (`clutch/box.py::Resolution`). At `dd8796d8c` this repo held 1,144 box messages and 1,021 tickets.
- **No vendor separation for review.** Nothing compares a ticket's review provider with its implement provider.

## Principles

These guide a host's routing and the tickets below. They are deliberately vendor-neutral: model rankings change every few months, so no model name or benchmark goes into engine code, prompt specs or shipped guides. A host records its current choices in its own routing rows.

1. **Spend by volume and weight.** Implementation uses the most tokens by far; it goes to the cheapest strong model. Planning and review are low volume and high consequence; they go to the strongest model. Ticket authoring sits between: medium volume, structured output, needs enough code knowledge for accurate criteria.
2. **Prepaid credit is free at the margin.** While paid quota remains, a cheaper but weaker model saves nothing; the local model earns a main role only when its measured quality is good enough or the paid candidates are held. Failover (above) already makes the local model the last candidate rather than a stall.
3. **Review from another vendor when one is available.** Models from one vendor share blind spots, so a reviewer from a different vendor than the implementer catches more. This is a preference, never a hold: it applies only while another provider is routed for review and not held by quota. Otherwise review runs on the same vendor and the fact is journaled (owner, 2026-11-22).
4. **Local models do duplicate checking, not duplicate implementation.** An extra cheap reviewer, a dedup pass, or a triage pre-score is cheap to compare. A second full implementation is not: someone must read both diffs. `best-of-n` pays only where tests pick the winner without a reader, that is, small tickets with discriminating checks.
5. **Retrieval before training.** A model tuned on the codebase goes stale with every commit; the project index gives current context at run time. Tuning pays for narrow format and decision tasks (triage, a tier router, ticket format), where the host's conventions matter more than general skill (`docs/training-data-plan.md` §4).
6. **Measure before routing.** No surface moves to a local or tuned model until `training eval` scores it against held-out records and it meets the GO baseline.
7. **Set triage thresholds for recall.** Discarding a good idea costs more than sending a weak one to a stronger model, so a pre-score's cutoff is chosen to keep about 95% of suggestions that became merged tickets on held-out history, not for accuracy.

## Target design

### 1. Triage eval lens

`clutch training eval` gains a `triage` lens: it replays held-out `triage` records through the given route and scores verdict agreement (`author`/`tombstone`/`declined`) with the recorded label, the same report shape as the review lens. This is the measurement principle 6 needs before any model takes over triage, and it closes the triage-dedup eval the roadmap lists as waiting for a label source.

### 2. Downstream triage label

Today a triage `author` verdict whose message resolved as `ticket` is labelled `merged` even if that ticket was later rejected. The export follows the resolution link to the ticket's terminal state: merged stays `merged`, rejected becomes `negative`, still running stays `neutral`. The authored-then-rejected cases are the most valuable labels because they are the ones that fooled triage.

### 3. Decline reason codes

A `declined` or `tombstone` verdict, and a requisition-review rejection of an authored ticket, carries one reason from a closed vocabulary owned by `clutch/box.py` (initial set: `already-covered`, `not-worth-churn`, `too-speculative`, `stale`, `out-of-scope`), alongside the free-text rationale. Reasons make the labels trainable and make the scorecard able to say why the box's yield is low.

### 4. Dedup at filing

`clutch box suggest` embeds the new message through `index.embed` and compares it with pending messages. Above a similarity threshold it shows the nearest messages; a confirmed duplicate increments the earlier message's count and links the new source instead of filing a new message. The count reaches triage as data: a suggestion several runs raised independently is more likely to matter. With no `index.embed` configured, filing behaves as today. A one-time sweep applies the same grouping to the existing backlog.

### 5. Cross-vendor review preference

When review selects a candidate, it orders available candidates whose provider differs from the ticket's implement provider ahead of those that match. Availability is the existing one: routed for the review surface and not held by a quota hold, auth exclusion, or open breaker. When no differing candidate is available, review runs on the matching one without waiting, and a `review_vendor` signal records `distinct` or `same` with the reason (`none_routed`, `held`). The panel scorecard counts the two apart, as it does models and samples.

### 6. Learned tier router

A small classifier (embeddings plus simple features such as fence size, kind, and past attempt counts) proposes a ticket's tier, replacing `routing_default_tier` only for tickets that set none. It is gated: it ships after rows 1-2 exist and a `training eval` run shows the classifier meets the GO baseline on held-out tickets. Until then this row stays unadmitted.

## Where each piece lives

| Piece | Owner |
|---|---|
| Triage lens | `clutch/training.py::evaluate`, `clutch/__main__.py` (`training eval`) |
| Downstream label | `clutch/training.py` (triage records) |
| Reason codes | `clutch/box.py` (vocabulary), `clutch/specs/triage.md`, `clutch/triage.py` |
| Dedup at filing | `clutch/box.py` (`suggest`), `clutch/index.py` (embed call) |
| Review preference | `clutch/providers.py` (candidate order), `clutch/scorecard.py` |
| Tier router | not yet placed; decided when row 6 is admitted |
| Docs | `docs/how-clutch-works.md` (box, training, routing sections), `clutch/docs/host-running.md` |

## Ticket breakdown

| Row | Stem | Kind | Priority | Depends on | Delivers |
|---|---|---|---|---|---|
| 1 | `training-eval-triage-lens` | feature | P2 | none | `training eval` replays and scores triage records |
| 2 | `training-triage-downstream-label` | feature | P2 | none | authored-then-rejected triage records label `negative` |
| 3 | `box-decline-reason-codes` | feature | P2 | none | closed reason vocabulary on decline, tombstone and requisition rejection |
| 4 | `box-suggest-dedup` | feature | P2 | none | near-duplicate detection and counts at `box suggest`, plus a backlog sweep |
| 5 | `review-cross-vendor-preference` | feature | P2 | none | review prefers a different available vendor; `review_vendor` signal and scorecard count |
| 6 | `tier-router` | feature | P3 | rows 1, 2 | learned tier proposal, gated on a GO eval |

## Risks

- **Few positive labels.** If roughly 15% of box messages end as merged tickets, the positive class is small; a classifier may overfit and a tuned LLM is premature. Reason codes (row 3) and downstream labels (row 2) raise label quality before quantity matters. Fine-tuning a local model to explain its triage becomes worth trying around 1-2k labelled messages with reasons.
- **Best-of-N cost.** Each extra implementation multiplies spend and, when tests do not decide, review time. Keep `best-of-n` to small tickets with discriminating checks.
- **Similar text is not the same issue.** Embedding similarity groups near-duplicates that differ in substance; row 4 shows candidates rather than merging silently above the threshold.
- **Data leaves the machine.** Hosted open-weight services see the code; only a local endpoint keeps it local. A host with code-location rules routes only to local qwen for that reason.
- **Subscription terms.** Some vendors allow subscription use only in their own CLIs; clutch already drives those CLIs, but a host adding an API-only provider pays per token.

## Open decisions

1. The similarity threshold and whether a confirmed duplicate needs a model check in row 4.
2. The initial reason-code vocabulary in row 3.
3. Whether row 5's preference also applies to `requisition_review` and `diagnose`, or review only.
4. Where the tier router's model file lives and how a host declares it (row 6).
