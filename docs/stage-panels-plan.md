<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Stage panels: plan
relates: [clutch/driver.py]
owner: clutch/driver.py
verified: 62a64dee
hash: 8627e22035d002923bbe85a3b965d5c5388c2823bc2ec7a118dd777759f7bb29
-->
# Stage panels: plan

Run a ticket lifecycle stage as several independent model calls at once and combine their results before the next stage sees them. Two reviewers instead of one, with every finding either of them raised; three diagnoses with the majority verdict; several implementations with the best one kept. One mechanism, declared per routing row, with a closed set of combiners, used by both ticket stages and the document agent's review lenses.

## Status

Merged roadmap rows: 65 (`panel-combiners`), 66 (`panel-routing-config`), 67 (`review-panel-r2`), 68 (`panel-scorecard`), 179 (`review-panel-stage-use`), 192 (`review-panel-stage-use-majority`), 193 (`review-panel-stage-use-requisition`), 199 (`review-panel-stage-use-triage`). Open roadmap rows: 87. Written 2026-11-14 at commit `0ef95269` for `docs/roadmap.md`.

Owner decision, 2026-11-21 (`requisition-contract-review-comparison`, commit `3636bf88`): requisition review is one short model call with no panel. Row 193 merged the requisition panel and that change then removed it; requisition review is no longer a panel surface. `config.py` still accepts `findings-union` on `requisition_review`, but nothing reads it.

## Roadmap

Release 0.6.0 for the combiners, the routing key, review and diagnosis panels, and the scorecard (`docs/roadmap.md` rows 65-68); 0.8.0 for best-of-N implementation (row 87), which needs the parallel plan's run slots. Needs from other plans: `route-kinds-filter` (0.5.0) lands first because both add an optional key to `Route`; `evidence-envelope` (0.4.0) so each panel member's call has its own record. What needs this plan: the document agent's `doc-review-runner` depends on `panel-combiners` instead of building its own panel (roadmap decision 19); the graphics plan's judge majority (`visual-review-surface`, `graphics.judge_samples`) is the same `majority-verdict` combiner applied per rubric row and moves onto it when this lands. Shared budgets: none. Cost is the budget: a panel of N multiplies that surface's spend by N, so the key is per routing row and off by default.

## Current state

- Every stage is one model call with a re-prompt loop (`clutch/driver.py::Driver._run`; up to `caps.retry` re-prompts on an invalid reply). `resolve()` (`clutch/providers.py:101-108`) picks the first candidate of the `(tier, surface)` row; later candidates serve only on pressure or failover (`clutch/thresh.py`).
- `Route` (`clutch/config.py:99-102`) is `tier`, `surface`, `candidates`. The graphics plan adds `kinds`.
- Review replies carry a verdict and findings (`clutch/specs/review.md`); the engine gates the reply shape and journals `review.md`. Requisition review, diagnosis, and triage reply with a verdict each.
- The scorecard (`clutch/scorecard.py`) counts catches, escapes, and bypasses per gate and surface, for one reviewer.
- `docs/document-agent/plan.md` §4 designs three isolated reviewers and a synthesis with an accounting gate for document lenses; `docs/gemini-graphics-refactor-plan.md` B5-B6 design a per-row majority judge and best-of-N image candidates. Both are panels; neither has an engine mechanism to stand on yet.
- The owner's review prompts (`CutReview.md` and the others) already run as three isolated agents plus a synthesis, by hand.

## Departures from the design record

| Record says | This plan | Why |
|---|---|---|
| D2: a concurrent worker pool "multiplies the review surface and the conflict surface faster than any other knob, so it is never a default" | Panels multiply the review surface on purpose, per row, never by default | The owner asked for it on 2026-11-14 after the document-agent and graphics plans each needed the same mechanism. Default panel size stays 1 everywhere; the scorecard (section 5) is the measurement that says whether a second reviewer earns its cost |

## Target design

### 1. Declaration

A routing row gains an optional `panel`:

```yaml
routing:
  - tier: high
    surface: review
    candidates: [{provider: claude, model: claude-opus-5-5}, {provider: codex}]
    panel: {size: 2, combine: findings-union}
  - {tier: medium, surface: diagnose, candidates: [{provider: claude}], panel: {size: 3, combine: majority-verdict}}
```

- `size` is 1 to 3 (1 is today's behavior and the default when the key is absent). `combine` is one of the closed set in section 2, and config load refuses a combiner that does not fit the surface (`best-of-n` only on `implement`; `findings-union` only on `review` and `requisition_review`; `majority-verdict` on `diagnose`, `triage`, `review_visual`).
- Members take distinct candidates in row order when the row has at least `size` candidates; otherwise the first candidate repeats (same model, independent samples). The journal records which, because agreement between two models and agreement between two samples of one model are different signals.
- `Route` gains the key beside `kinds`; the strict loader refuses it on an older engine, as the host contract already states for a newer config.

### 2. Combiners (`clutch/panel.py`, pure)

| Combiner | Surfaces | Rule |
|---|---|---|
| `findings-union` | `review`, `requisition_review` | Verdict is the worst any member gave (`rma` > `snag` > `approve`). Findings are merged on `(code, path, line)`; each carries `agreement: k/N` and the members that raised it; messages from several members are kept, not averaged. Summary lists each member's summary in member order. |
| `majority-verdict` | `diagnose`, `triage`, `review_visual` | The verdict most members gave; the findings, lessons, or per-row results come from the first member in that majority. A tie falls to the safer verdict: `escalate` over `retry` for diagnosis, `declined` over `author` for triage, `unsure` for a visual row. |
| `best-of-n` | `implement` | Each member implements in its own worktree; Check runs on every candidate; the kept candidate is the one that passes Check with the fewest soft findings, then the smallest inserted-line count; the others are retired. Needs the parallel plan's slots; 0.8.0. |

Combiners take and return the existing artifact models (`ReviewArtifact`, `Diagnosis`, and so on) so every downstream gate is unchanged. A combined review is one `review.md` with the merged findings; `reviewed_sha` is the same for every member because they judged the same branch head.

### 3. Execution

- The driver runs `size` members in turn under one stuck budget. Each has its own effect key (`llm/<stem>/m<k>-<run_seq>/review/<attempt>/<call>`), spool, evidence record and re-prompt loop; provider concurrency limits still apply.
- A member whose call fails with a `ProviderCallError` is dropped when at least one member survives; the combined result records the dropped member and its failure class. When every member fails, the stage result is `infra_error`, as one failed call is today.
- One `panel_facts` signal per combined stage: members' provider and model, each verdict, the agreement counts, and the dropped members. The journal is otherwise unchanged; `review.md` and `diagnosis.json` are the combined artifacts.
- A crash mid-panel replays through the effect keys: completed members are not re-called.

### 4. Which stages, in which release

- 0.6.0: `review`, `diagnose`, `triage` (`requisition_review` was dropped on 2026-11-21; see Status). All read-only, one worktree, no new git.
- 0.8.0: `implement` best-of-N, after `serve-parallel-dispatch` gives the engine run slots and a per-candidate worktree name (`<worktree_root>/<stem>.m<k>`).
- The document agent's lenses and the graphics judge are consumers from the day they land: their plans point here.

### 5. Measurement

The scorecard attributes each catch to the members that raised it. A finding only the second member raised, which review later confirmed (the implementer fixed it, or the merged code was later blamed for it), is a unique catch. The scorecard reports, per panel row, unique catches per 100 reviews and the cost multiplier. The plan sets no threshold; whether a panel row stays on is settled from that number by a recorded AI design panel (`docs/roadmap.md` §6, decision 19). The scorecard's existing prune rule (25+ evaluations, no catch, no escape) applies to a member slot the same way.

## Where each piece lives

| Piece | Home |
|---|---|
| Combiners | new `clutch/panel.py` (pure; no I/O) |
| `Route.panel` and the surface-fit refusal | `clutch/config.py`; `clutch/docs/host-contract.md` inventory |
| Fan-out, member effect keys, `panel_facts` | `clutch/driver.py` |
| Review use | `clutch/stages.py` (review); `clutch/requisition.py` makes one call, no panel (2026-11-21) |
| Diagnosis and triage use | `clutch/runner.py` (diagnosis), `clutch/triage.py` |
| Scorecard attribution | `clutch/scorecard.py`, `clutch/retro.py` (report) |
| Best-of-N worktrees | `clutch/stages.py` (implement), `clutch/runner.py` |
| Docs | `docs/how-clutch-works.md` §4.4, §6.3, §8.2, §9.6; the config table |

## Ticket breakdown

Each ticket puts its tests in new files (`docs/parallel-tickets-plan.md` §7).

| # | Stem | Kind | P | Depends on | Content |
|---|---|---|---|---|---|
| 1 | `panel-combiners` | feature | P2 | | `clutch/panel.py` with the three combiners over the existing artifact models; `panel_facts` body model. Pure, unit-tested. Release 0.6.0. |
| 2 | `panel-routing-config` | feature | P2 | `route-kinds-filter` | `Route.panel`, surface-fit refusal, distinct-candidate assignment, `doctor` warning for single-slot providers, host-contract inventory. Release 0.6.0. |
| 3 | `review-panel` | feature | P2 | 1, 2 | Driver fan-out with member effect keys and records; review, requisition review, diagnosis, and triage use the combined result. how-clutch-works updates. Release 0.6.0. |
| 4 | `panel-scorecard` | feature | P3 | 3 | Per-member catch attribution; unique catches per 100 reviews and the cost multiplier in the retro report. Release 0.6.0. |
| 5 | `implement-best-of-n` | feature | P3 | 1, `serve-parallel-dispatch` | Per-member worktrees, Check on every candidate, selection, retirement of the rest. Release 0.8.0. |

`Runs before`: `contention-authoring-rules` (roadmap row 13) before every ticket here. Ticket 1 before `doc-review-runner` (`docs/document-agent/plan.md`), which consumes it.

## Risks

- **Correlated members.** Two samples of one model agree with each other more than two models do. The `panel_facts` record says which kind of agreement a report carries, and the scorecard keeps them apart.
- **Cost.** N times the spend on a paneled surface. The key is per row and per tier, so a host can panel only `review` at `high`.
- **Double counting.** A finding two members raised is one finding with `agreement: 2/2`, never two findings; the merge key is `(code, path, line)`, and a member that cites no line merges on `(code, path)`.
- **Re-prompt loops inside a panel.** Each member has its own invalid-reply re-prompts under the shared stuck budget; a slow member can starve the others of budget. The budget is the ticket's, as today; the risk is bounded by `size <= 3`.

## Open decisions

Decided 2026-11-16 (`docs/roadmap.md` §6, decision 19): items 1-3 take their Proposed option.

1. **Tie rule for `majority-verdict` on `diagnose`.** Proposed: the safer verdict (`escalate` over `retry`, `reject` over `escalate` is not safer, so `escalate` wins over both).
2. **Members on one candidate.** Proposed: allowed (independent samples), recorded as such. The alternative, refusing a panel on a single-candidate row, forces hosts to configure a second provider before they can measure whether a second reviewer helps.
3. **Best-of-N selection.** Proposed: Check pass, then fewest soft findings, then smallest diff. Review could instead judge the candidates side by side; that is a fourth combiner for later.
