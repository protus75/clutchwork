---
state: draft
priority: P2
kind: feature
source: human
---

## Depends on
none

## Context
- clutch/stages.py::review
- clutch/stages.py::review_stage
- clutch/panel.py
- clutch/driver.py::Driver.run_panel
- clutch/driver.py::PanelResult
- clutch/providers.py::panel_members
- clutch/artifacts.py::Cost
- tests/unit/test_driver_panel_fanout.py
- tests/unit/test_route_kinds_filter.py
- docs/stage-panels-plan.md

## On-demand
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 179 as filed holds four call sites (review, diagnosis, triage, requisition review), each with its own artifact model, tie order and tests. That is more than one run, so this ticket takes the first slice, the `review` stage, the surface `docs/stage-panels-plan.md` section 4 names first. After it, a routing row `{tier, surface: review, panel: {size: N, combine: findings-union}}` makes Review run N member reviews through `Driver.run_panel` and use the `findings-union` result as the one `review.md`. Today `Route.panel`, `clutch/panel.py` and `run_panel` are merged but no stage calls them, so a configured panel does nothing. The rest of row 179 moves to two follow-up roadmap rows that already exist (rows 192 and 193): `review-panel-stage-use-majority` (diagnosis and triage, `majority-verdict`, with the full tie order) and `review-panel-stage-use-requisition` (requisition review, `findings-union`, member keys around its own `llm_call`).

Design, read from the merged code:
- Size comes from `len(providers.panel_members(ctx.config, tier, "review", kind))`: it is `Route.panel.size` for a row whose surface is `review`, and 1 otherwise. Config load already refuses any combiner but `findings-union` on a `review` row, so Review never reads `combine`; there is one combiner for this surface.
- `panel_members` raises `ProviderSetupError` when no routing row resolves or a candidate still carries the placeholder. Review treats that as size 1 and calls `Driver.run`, which raises the identical error as today, so a failing route is not changed by this ticket.
- Size 1 calls `Driver.run`, never `run_panel`. Reason: `run_panel` returns a dropped member as a bare `DroppedMember`, losing the `infra_error` result's findings (a `quota_exhausted` finding stops the run in `clutch/runner.py`), so routing size 1 through it would change today's behavior.

Outcomes, each by name:
- **Unset panel**: no `Route.panel` (or `size: 1`) gives `driver.run` called once with today's arguments; the `review.md` bytes, `StageResult` and effect keys equal today's; no `panel_facts` event is written.
- **All members ok**: every member's artifact is a `ReviewVerdict`; `panel.findings_union(replies, members, dropped)` combines them.
- **Member failing**: a member whose provider call fails is in `PanelResult.dropped`; the surviving members are combined. `panel_facts.dropped` records it (`index` is the member's original index, `failure_class` `infra_error`).
- **One member left**: a size-2 panel with one dropped member combines one reply. The verdict, summary and findings equal that member's, `agreement` reads `1/1`, `member_count` is 2.
- **All members failing, or the stuck budget exhausted before any member finished** (`run_panel` stops silently when the budget runs out, so `PanelResult.members` holds fewer members than `size`, and none when it ran out at the start): `PanelResult.members` is empty; Review returns `StageResult(outcome="infra_error", artifact=None, findings=[], cost=Cost())`. The `quota_exhausted` finding of the dropped calls is not carried (`PanelResult` has no findings); the driver's own notification still fires. This is the dropped-findings gap filed to the Suggestion Box, not fixed here.
- **Member not ok**: if any member in `PanelResult.members` has an outcome other than `ok` (a `timeout`, a `budget_exceeded`, a `ProviderDroughtResult`), Review returns the first such result unchanged, as the single call does today, and writes no `review.md`.
- **Tie**: `findings_union` has no tie; the verdict is the worst any member gave (`rma` over `snag` over `approve`). A two-member `snag`/`approve` panel is `snag`; `approve`/`approve` is `approve` with no findings.
- **Over-bound render**: `RenderOverBound` raised while rendering returns `premise_failed` exactly as today, for either path (render happens before the first member call).

Stored values.
`review.md` stays the single combined artifact: `produced_at_sha` and `reviewed_sha` are the one reviewed head, `summary` is the members' summaries joined by newline in member order, `findings` is the merged list (a finding two members raised on the same `(code, path, line)` appears once, its messages joined by newline), and `provider`/`model` are those of the first member in `PanelResult.members` (a member's `cost.provider` and `cost.model`). Worked example, panel size 2, members m0 (claude) replies `snag` with `Finding(code="logic", path="a.py", line=3, message="off by one")`, summary `bad loop`; m1 (codex) replies `approve`, summary `fine`. Combined: verdict `snag`, summary `bad loop\nfine`, findings `[logic a.py:3 "off by one"]`, `provider` `claude`. The stage cost is the sum over members: `tokens` the sum (`None` when any member's is `None`), `seconds`, `attempts` and `usd` the sums, `provider` and `model` the first member's.
`panel_facts` is one engine-log event (`ctx.driver.log.event`, never the journal, which is not a debug log), written only when size is above 1 and a combined result exists: `event="panel_facts"`, `stem`, `attempt`, `surface="review"`, and the `PanelFacts.model_dump()` fields. For the example: `combiner "findings-union"`, `member_count 2`, `members [{provider claude, model <m0 model>, verdict snag}, {provider codex, model <m1 model>, verdict approve}]`, `verdict_counts {"snag": 1, "approve": 1}`, `dropped []`, `merged [{finding logic a.py:3, agreement "1/2", members [0]}]`, `kept_index null`, `agreement_kind "models"`. Member provider and model come from each member's `cost.provider` and `cost.model`, and from `panel_members(...)[k]` (`provider.name`, `model`) only when the cost carries `None` (a fake LLM), where k is the member's original index: the j-th surviving member's k is the j-th index in `range(size)` that is not in `dropped`. `members` and `merged[].members` index the surviving members in order; `dropped[].index` is the original member index, so with m0 dropped and m1 surviving, a finding m1 raised reads `members [0]` and `dropped [{index 0, ...}]`.

## Boundary contract
### Review stage panel use
- disposition: extend
- owner: clutch/stages.py
- consumers: `run_stages` and `clutch/runner.py` (read `StageResult` outcome, findings, cost), `clutch/rework.py`, `clutch/scorecard.py`, `clutch/retro.py` and `clutch/training.py` (read `review.md` and `llm/` keys, unchanged shapes), tests/integration/serve_rig.py (calls `review`)
- observable change: `review` reads the panel size for its tier and kind and, above 1, calls `driver.run_panel(..., size=N)` and combines the members' `ReviewVerdict`s with `panel.findings_union` into one `review.md`, writing one `panel_facts` log event; size 1 or a route error calls `driver.run` exactly as today. Inputs: the same stage, invoice and arguments; outputs: the same `StageResult` shape (`ok` on approve, `gate_failed` with the merged findings on snag or rma, `infra_error`, or a member's non-ok result); failure: each outcome in Goal; side effect: one `panel_facts` log line; ordering: reviewed SHA read before the calls; persistence: `review.md` only, no new file
- compatibility: no `Route.panel` gives byte-identical behavior (criterion 1); member effect keys are `llm/<stem>/m<k>-<run_seq>/review/<attempt>/<call>` as `review-panel-r2` merged, six parts, so every six-part reader accepts them; the review prompt spec is unchanged, so no spec version bump
- acceptance: criteria 1 to 9
- tests: tests/unit/test_review_panel_use.py
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
The implementer creates the new test file's meta header with `uv run clutch meta refresh tests/unit/test_review_panel_use.py` and then edits only the `# purpose:` line to a non-empty one-line statement; the header is never written by hand.

Scope in:
- clutch/stages.py, in `review` only: compute `size`; build the keyword arguments once in one dict used by both calls; call `ctx.driver.run(stage, invoice, **kwargs)` when size is 1 and `ctx.driver.run_panel(stage, invoice, size=size, **kwargs)` otherwise; combine, build the artifact and cost, write `review.md` once through the one existing write and `lift_outbox` path, and log `panel_facts`. Import `panel_members`, `ProviderSetupError` (if not already imported), `findings_union`, `PanelMember` and `Cost` as needed. `review_stage` and `render_review` are not changed.
- tests/unit/test_route_kinds_filter.py: the one test whose `ctx` stand-in is `SimpleNamespace(driver=..., worktree=..., repo=..., git=...)` (about line 157) gains `config=SimpleNamespace(routing=[], providers=[])`; no other line changes. Review now reads `ctx.config`, and `routing=[]` makes `panel_members` raise `ProviderSetupError`, so the size-1 path runs and `calls == ["bug", "bug", "bug"]` still holds.
- docs/how-clutch-works.md: section 4.4 Review gains one sentence saying a `findings-union` panel on the review route runs N member reviews and writes one combined `review.md`; line 657 drops "no stage fans out yet" and says review fans out and the other surfaces do not yet.
- tests/unit/test_review_panel_use.py: new file holding every new test, built on fakes (`FakeLLM`, `FakeClock`, `FakeFileSystem`, `FakeJournal` as in tests/unit/test_driver_panel_fanout.py).

Scope out:
- Diagnosis, triage and requisition review (the two follow-up rows above), the `majority-verdict` tie order, `clutch/driver.py` and `PanelResult` (a dropped member's findings stay lost, filed to the Suggestion Box), per-member scorecard attribution (row 68), best-of-N, and any prompt spec.
- The review prompt spec: unchanged, so no version bump and no spec pin test.
- Merge order: this ticket's new test builds a `Driver` the way `rig(script, state_dir)` of `tests/unit/test_driver_panel_fanout.py` does since `spools-test-helper` merged (a real `tmp_path` as `state_dir` and `Spool(state_dir / "spools", redactor, LocalFileSystem())`), and reads a spool file only through `tests/spool_captures.py` (`read_capture`, `list_captures`), never by a `spools/` path; `spools-onto-evidence-store-r2` (draft, reworked after the `spools-test-helper` chain merges) will change how `Spool` is built, so that ticket's author re-greps `Spool(` over `tests/` against main and fences this ticket's test file if it constructs one; this ticket does not depend on it. `spools-test-helper` (running) lists `tests/unit/test_route_kinds_filter.py` as left alone, so no running ticket fences it; the config stand-in edit here is one line. `spools-onto-evidence-store-r2` edits `clutch/stages.py` in `run_host_command` and the regression writer, not `review`.

## Scope fence
- clutch/stages.py
- tests/unit/test_review_panel_use.py
- tests/unit/test_route_kinds_filter.py
- docs/how-clutch-works.md

## Acceptance criteria
1. With `Route.panel` unset for the review route, `review` called on a fake ctx makes exactly one `driver.run` call and zero `run_panel` calls, the written `review.md` text equals the literal expected text for one `snag` reply (hand-written in the test), the returned `StageResult` equals the expected one, the effect key is `llm/<stem>/<seq>/review/<attempt>/1` with no `m<k>` scope, and no `panel_facts` event is logged; the same holds with `panel: {size: 1, combine: findings-union}`; checked by `./dev.py test tests/unit/test_review_panel_use.py`. A test that routes a size-1 panel through `run_panel` fails.
2. Single call site: with a recording fake driver, the keyword arguments `review` passes to `run` for size 1 equal those it passes to `run_panel` for size 2 except `size` (the one shared kwargs dict is thereby proven; the source layout stays a review check); checked by `./dev.py test tests/unit/test_review_panel_use.py`.
3. Size 2, m0 `snag` (`logic a.py:3 "off by one"`, summary `bad loop`) and m1 `approve` (summary `fine`): the written `review.md` is one `SnagList` with verdict `snag`, summary `bad loop\nfine`, the one finding, `provider` the first member's; `StageResult.outcome` is `gate_failed`, not `ok`; checked by `./dev.py test tests/unit/test_review_panel_use.py`.
4. Size 2, both `approve`: outcome `ok`, `review.md` is an `ApprovedInvoice` with no findings, not a `snag`; size 2, m0 `approve` and m1 `rma` (finding code `ticket`): verdict `rma`, not `snag`; checked by `./dev.py test tests/unit/test_review_panel_use.py`.
5. Size 2, both members raise the same finding on `(logic, a.py, 3)` with different messages: `review.md` has one finding whose message is both messages joined by newline, and the `panel_facts` `merged` entry reads `agreement "2/2"`, `members [0, 1]`, not two findings; checked by `./dev.py test tests/unit/test_review_panel_use.py`.
6. Member failing: size 2 with m0's provider call failing with `ProviderCallError` and m1 `snag`: outcome `gate_failed`, the combined verdict equals m1's, `panel_facts.dropped == [{"index": 0, "failure_class": "infra_error"}]`, `member_count` 2, `merged[0].members == [0]`, and with a two-candidate config and a fake LLM whose cost carries `None` provider, `panel_facts.members[0].provider` names the second candidate's provider (m1's), not the first's; size 2 with both failing: outcome `infra_error`, `artifact is None`, `findings == []`, no `review.md` written, and no `panel_facts` event; checked by `./dev.py test tests/unit/test_review_panel_use.py`.
7. Member not ok: size 2 where m0 is `ok` and m1 returns `timeout`: `review` returns m1's `StageResult` object unchanged and writes no `review.md`; a `ProviderDroughtResult` member is returned with its `provider_drought` record intact; checked by `./dev.py test tests/unit/test_review_panel_use.py`.
8. The stage cost is the member sum: for member costs `(tokens 10, usd 0.5, attempts 1, seconds 2.0)` and `(20, 0.25, 2, 3.0)` the cost is `tokens 30, usd 0.75, attempts 3, seconds 5.0`; with one member's `tokens` `None` the sum is `None`, not a partial sum; checked by `./dev.py test tests/unit/test_review_panel_use.py`.
9. Route errors: with a ctx whose `config.routing` is `[]`, `review` calls `driver.run` and the `ProviderSetupError` it raises propagates unchanged, not swallowed and not run as a panel; checked by `./dev.py test tests/unit/test_review_panel_use.py`.
10. The existing size-1 review behavior and the `kind` pass-through still hold; checked by `./dev.py test tests/unit/test_route_kinds_filter.py tests/unit/test_driver_panel_fanout.py tests/integration/test_rework.py`.

## Verification
```
./dev.py test tests/unit/test_review_panel_use.py tests/unit/test_route_kinds_filter.py tests/unit/test_driver_panel_fanout.py tests/unit/test_panel_combiners.py tests/integration/test_rework.py
```

## Definition of rejected
A size-1 or unset panel that calls `run_panel`, or any change to its `review.md` bytes, `StageResult` or effect keys; a second `review.md` write path; two driver call sites that build their keyword arguments separately; a `panel_facts` record written to the journal; any edit to `clutch/driver.py`, `clutch/panel.py`, the review prompt spec or a diagnosis, triage or requisition file.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one function in `clutch/stages.py`, one new test file and three small doc edits; the other three call sites are split into the two follow-up rows, and the merged `run_panel`, `findings_union` and `panel_members` carry the mechanism.
