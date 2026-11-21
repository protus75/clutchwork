---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- review-panel-stage-use
- review-panel-dropped-member-findings

## Context
- clutch/stages.py::diagnose
- clutch/stages.py::review
- clutch/stages.py::write_diagnosis
- clutch/panel.py
- clutch/driver.py::Driver.run_panel
- clutch/driver.py::PanelResult
- clutch/providers.py::panel_members
- clutch/artifacts.py::DiagnosisReply
- clutch/artifacts.py::Diagnosis
- clutch/artifacts.py::Cost
- tests/unit/test_review_panel_use.py
- tests/unit/test_panel_combiners.py
- docs/stage-panels-plan.md

## On-demand
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 192 as filed holds two call sites, diagnosis (`clutch/stages.py::diagnose`) and triage (`clutch/triage.py::_settle_pass`), each with its own artifact model, tie order, failure handling and tests. That is more than one 60-minute run, so this ticket takes the first slice, diagnosis, plus the one edit both surfaces need in `clutch/panel.py`: making both tie orders total. The triage half is the rest of row 192: it stays an open roadmap row, is not authored here, and needs only `clutch/triage.py` and its own tests once this merges (it reuses the helper this ticket adds to `clutch/stages.py`).

After this ticket a routing row `{tier, surface: diagnose, panel: {size: N, combine: majority-verdict}}` makes `diagnose` run N member diagnoses through `Driver.run_panel` and write one `diagnosis.json` from the majority verdict. Today `Route.panel`, `majority_verdict`, `run_panel` and `PanelResult.dropped_findings` are merged, `review` uses them (row 179), and a `diagnose` panel row loads and then does nothing.

Why `panel.py` is touched (read from the merged code): `clutch/panel.py` declares `DIAGNOSIS_ORDER = ("escalate", "retry")` and `TRIAGE_ORDER = ("declined", "author")`, but `DiagnosisVerdictName` has five values (`retry`, `escalate`, `split`, `reject`, `abandon-human`) and `TriageReply.verdict` has three (`author`, `tombstone`, `declined`). `majority_verdict` raises `ValueError("every tied verdict must occur in the safer-first order")` for a tie that includes an unlisted verdict, so a panel of three whose members say `retry`, `split`, `abandon-human` would crash `diagnose`. Both orders become total here (triage's too, so `clutch/panel.py` is edited once):
- `DIAGNOSIS_ORDER = ("escalate", "abandon-human", "split", "reject", "retry")`. `escalate` stays first (the plans-doc decision: `escalate` wins over `retry`, and `reject` is not safer than `escalate`); `abandon-human` holds the ticket for a person; `split` and `reject` spend no run; `retry` spends a run on a verdict nobody agreed on, so it is last. Existing pair `retry` vs `escalate` still resolves to `escalate`.
- `TRIAGE_ORDER = ("declined", "tombstone", "author")`. `declined` stays first; `tombstone` only links an existing decision; `author` creates work, so it is last. Existing pair `author` vs `declined` still resolves to `declined`.
This order is a decision made here; the owner may reorder the tuples in review, and the totality test keeps any order total.

Design of `diagnose`, read from the merged `review`:
- Size is `len(providers.panel_members(ctx.config, ticket.frontmatter.agent_tier, "diagnose", ticket.frontmatter.kind))`; `ProviderSetupError` means size 1. Config load already refuses any combiner but `majority-verdict` on a `diagnose` row, so `diagnose` never reads `combine`. For a config with no `diagnose` row, `panel_members` resolves the `review` row, whose `Route.surface` is not `diagnose`, so the size is 1.
- Size 1 or unset calls `ctx.driver.run`, never `run_panel`; the call and its keyword arguments, the `Diagnosis`, and the written `diagnosis.json` are byte-for-byte today's. Size 2 or 3 calls `ctx.driver.run_panel(stage, material, size=size, **kwargs)` with the same one `kwargs` dict.
- `diagnose` and `review` share one new module-level helper in `clutch/stages.py`, `_panel_combine(panel, selected)`, that returns `(replies, members, cost)` for a non-empty `PanelResult` whose members are all `ok`: `replies` is each member's artifact, `members` a `PanelMember(provider, model, verdict)` per surviving member (provider and model are the member's `cost.provider` and `cost.model`, falling back to `selected[k].provider.name` and `selected[k].model` for the member's original index k when the cost carries `None`; the j-th survivor's k is the j-th index of `range(len(selected))` not in `panel.dropped`), and `cost` the member sum (`tokens` the sum, `None` when any member's is `None`; `seconds`, `attempts`, `usd` sums; `provider` and `model` of the first member). `review` is changed only to call it in place of its inline lines; its behavior is unchanged (criterion 12). Rejected simpler approach: copying `review`'s inline lines into `diagnose`: three call sites (review, diagnose, and the triage half) would carry the same twenty lines.

Outcomes, each by name:
- **Unset panel**: no `Route.panel`, or `size: 1`: one `driver.run`, zero `run_panel`, today's results and `diagnosis.json` bytes, no `panel_facts` event.
- **All members ok**: every artifact is a `DiagnosisReply`; `panel.majority_verdict(replies, DIAGNOSIS_ORDER, members, panel.dropped)` picks the winner; the recorded `lessons` and `trimmed_lessons` are the first reply with the winning verdict; `provider` and `model` are that member's; `cost` is the member sum with that member's provider and model. One `panel_facts` log event is written.
- **Majority**: the verdict most surviving members gave. Example: `retry`, `retry`, `escalate` gives `retry`, with m0's lessons (the first member in the majority), not m1's.
- **Tie**: the verdict earliest in `DIAGNOSIS_ORDER` among those tied for most votes, always exactly one winner. Examples: `retry` vs `escalate` gives `escalate`; `retry`, `split`, `abandon-human` (a three-way tie of one vote each) gives `abandon-human`; `split` vs `reject` gives `split`.
- **Member failing**: a member whose provider call fails (`infra_error`) is in `PanelResult.dropped`; the survivors are combined and `panel_facts.dropped` records `{index, failure_class: "infra_error"}`, `index` being the original member index. A size-2 panel with one survivor has `member_count` 2 and that survivor's verdict, lessons and provider.
- **All members failing, or the stuck budget exhausted before any member finished**: `PanelResult.members` is empty; `diagnose` writes today's failure record, `verdict="abandon-human"`, `lessons=[]`, `mechanical="no schema-valid verdict (infra_error)"`, `cost=Cost()`, no `panel_facts`. This is what size 1 writes for an `infra_error` result. A `quota_exhausted` finding on a dropped member does not change that record: the single-model `diagnose` also never surfaces the findings of its failed call (the runner stops for quota on the failing stage before diagnosis, `clutch/runner.py::drive`), so `PanelResult.dropped_findings` is deliberately not read here, and a test proves the record is identical with and without it. `dropped_findings` stays the data the review and triage surfaces use.
- **Member not ok**: any `PanelResult.members` entry with an outcome other than `ok` (a `timeout`, `invalid_artifact`, a `ProviderDroughtResult`): `diagnose` writes today's record for that outcome, `abandon-human`, `lessons=[]`, `mechanical=f"no schema-valid verdict ({outcome})"`, `cost` that member's cost, using the first such member, and no `panel_facts`; no model verdict is used.
- **Over-bound render**: `RenderOverBound` is not caught in `diagnose` today and is not caught here.

Stored values. `diagnosis.json` stays the one `Diagnosis`: `verdict`, `lessons`, `trimmed_lessons` from the winning reply, `terminal`, `stage`, `mechanical=None`, `provider` and `model` the winning member's, `spec_version`, `produced_at_sha` as today. Worked example, size 2, candidates `codex`/`a` and `claude`/`b`, m0 replies `retry` with lessons `["fix the import"]` (cost tokens 10, seconds 2.0, attempts 1, usd 0.5, provider `codex`, model `a`), m1 replies `escalate` with lessons `["needs a stronger model"]` (cost 20, 3.0, 2, 0.25, `claude`, `b`): tie, `escalate` wins; `Diagnosis.verdict` `escalate`, `lessons` `["needs a stronger model"]`, `provider` `claude`, `model` `b`; the stage cost passed to `write_diagnosis` is `tokens 30, seconds 5.0, attempts 3, usd 0.75`. The `panel_facts` event is one engine-log event (`ctx.driver.log.event`, never the journal): `event="panel_facts"`, `stem`, `attempt`, `surface="diagnose"`, and `PanelFacts.model_dump()`: `combiner "majority-verdict"`, `member_count 2`, `members [{provider codex, model a, verdict retry}, {provider claude, model b, verdict escalate}]`, `verdict_counts {"retry": 1, "escalate": 1}`, `dropped []`, `merged []`, `kept_index null`, `agreement_kind "models"`.

## Boundary contract
### Diagnosis panel use
- disposition: extend
- owner: clutch/stages.py
- consumers: `clutch/runner.py::drive` (calls `diagnose`, reads `Diagnosis.verdict`, `lessons`, `mechanical`; unchanged), `clutch/training.py` and `clutch/scorecard.py` (read `diagnosis.json` and `llm/` keys, unchanged shapes), tests/integration/serve_rig.py (stubs `diagnose`)
- observable change: `diagnose` reads the panel size for its tier and kind and, above 1, calls `driver.run_panel(..., size=N)` and combines the members' `DiagnosisReply`s with `panel.majority_verdict` and `DIAGNOSIS_ORDER` into one `diagnosis.json`, writing one `panel_facts` log event; size 1 or a route error calls `driver.run` exactly as today. Inputs: the same stage, material and arguments; outputs: the same `Diagnosis` shape; failure: each outcome in Goal; side effect: one `panel_facts` log line; ordering: the one `write_diagnosis` path after the calls; persistence: `diagnosis.json` only, no new file
- compatibility: no `Route.panel` gives byte-identical behavior (criterion 1); member effect keys are `llm/<stem>/m<k>-<run_seq>/diagnose/<attempt>/<call>` as `review-panel-r2` merged; the diagnose prompt spec is unchanged, so no version bump
- acceptance: criteria 1 to 12
- tests: tests/unit/test_diagnosis_panel_use.py, tests/integration/test_stage_panel_call_sites.py
- post-merge source of truth: clutch/stages.py

### Panel tie orders
- disposition: extend
- owner: clutch/panel.py
- consumers: `clutch/stages.py::diagnose` (this ticket), `clutch/triage.py` (the triage half of row 192, not yet authored), tests/unit/test_panel_combiners.py (imports both constants)
- observable change: `DIAGNOSIS_ORDER` lists all five `DiagnosisVerdictName` values and `TRIAGE_ORDER` all three `TriageReply.verdict` values, so `majority_verdict` resolves every tie between any two or three of them to one verdict and no longer raises for an unlisted one; `majority_verdict` itself is unchanged
- compatibility: the existing pairs `retry` vs `escalate` and `author` vs `declined` resolve as before; `majority_verdict(replies, ("retry",), ...)` still raises, because the check on a tie outside the supplied order stays
- acceptance: criterion 3
- tests: tests/unit/test_panel_tie_orders.py
- post-merge source of truth: clutch/panel.py

## Scope in / Scope out
The implementer creates each new test file's meta header with `uv run clutch meta refresh <file>` (for `tests/unit/test_diagnosis_panel_use.py`, `tests/unit/test_panel_tie_orders.py` and `tests/integration/test_stage_panel_call_sites.py`) and then edits only the `# purpose:` line to a non-empty one-line statement; the header is never written by hand.

Scope in:
- clutch/panel.py: replace the two tuples `DIAGNOSIS_ORDER` and `TRIAGE_ORDER` with the total orders above; nothing else changes there. This edit is forced: the constants live only there.
- clutch/stages.py: add `_panel_combine`; in `review`, replace the inline replies, members and cost lines with a call to it (behavior unchanged); in `diagnose`, compute `size`, build the keyword arguments once in one dict used by both calls, call `ctx.driver.run(stage, material, **kwargs)` for size 1 and `ctx.driver.run_panel(stage, material, size=size, **kwargs)` otherwise, combine, and write through the one existing `write_diagnosis` call path (the success call and the one failure call keep their shapes). Import `majority_verdict`, `DIAGNOSIS_ORDER` from `clutch.panel` and `Cost`, `DiagnosisReply` if not already imported. `diagnose_stage`, `write_diagnosis` and `DiagnosisMaterial` are not changed.
- tests/unit/test_panel_tie_orders.py: new; totality of both orders (criterion 3); it imports `clutch.triage.TriageReply` and `clutch.artifacts` and reads no repo file.
- tests/unit/test_diagnosis_panel_use.py: new; criteria 1 and 4 to 11, built on fakes (`FakeFileSystem`, a recording driver with `run`, `run_panel` and a `log`, as in tests/unit/test_review_panel_use.py); it builds its config with `config` from tests/unit/test_route_kinds_filter.py and does not edit that file. `tests/unit/test_route_kinds_filter.py` needs no edit: its `ctx` stand-in already carries `config=SimpleNamespace(routing=[], providers=[])`, so `diagnose` takes the size-1 path there.
- tests/integration/test_stage_panel_call_sites.py: new; the single-call-site check (criterion 2), reading `clutch/stages.py` through a `Path(__file__)` anchor.
- docs/how-clutch-works.md: section 6.3 Diagnosis gains one sentence saying a `majority-verdict` panel on the diagnose route runs N member diagnoses, writes one `diagnosis.json` from the majority verdict, and breaks a tie by the fixed order `escalate`, `abandon-human`, `split`, `reject`, `retry`; section 8.2 (the line ending "review fans out, while the other surfaces do not yet") says review and diagnose fan out and the other surfaces do not yet.

Scope out:
- Triage (`clutch/triage.py`, its `TRIAGE_ORDER` use and tests) is the remaining half of roadmap row 192, left for its own ticket; requisition review is row 193 (`review-panel-stage-use-requisition`).
- `clutch/driver.py` and `PanelResult` (read only), `majority_verdict`, `findings_union` and every other line of `clutch/panel.py`, the diagnose prompt spec (unchanged, so no version bump and no spec pin test), per-member scorecard attribution, best-of-n.
- Merge order: `review-panel-stage-use-requisition` (running) also fences `clutch/panel.py`, but edits `findings_union` (an `rma_code` keyword) and its imports, a different region from the two constants here; neither edit changes the other's lines, so either order merges, and its criterion 8 (`./dev.py test tests/unit/test_panel_combiners.py` unedited) still passes with the longer orders (the existing pairs are unchanged). `index-consumers-training-join` (running, `clutch/training.py`, `clutch/__main__.py`, host docs), `panel-scorecard` (queued; `clutch/scorecard.py`, `clutch/retro.py`, `clutch/status.py`) and `spools-tests-via-helper-fake-fs` share no file with this fence. `docs/how-clutch-works.md` is shared; edits touch sections 6.3 and 8.2 only. The not-yet-authored `spools-tests-via-helper-driver` (row 194) will fence `tests/integration/test_triage.py`, which this ticket does not touch.

## Scope fence
- clutch/stages.py
- clutch/panel.py
- tests/unit/test_diagnosis_panel_use.py
- tests/unit/test_panel_tie_orders.py
- tests/integration/test_stage_panel_call_sites.py
- docs/how-clutch-works.md

## Acceptance criteria
1. Unset and size-1 panels are unchanged: with `Route.panel` unset, and again with `panel: {size: 1, combine: majority-verdict}`, `diagnose` on a fake ctx makes exactly one `driver.run` call and zero `run_panel` calls; the keyword arguments equal the hand-written literal (`ticket="item"`, `kind="bug"`, `attempt=1`, `tier="medium"`, `effort="low"`, `stuck_budget=600.0`, `expected_budget=60.0`, `scope_fence=()`, `workspace` the worktree path, no `key_scope`); an `ok` `retry` reply returns the literal expected `Diagnosis` and writes `diagnosis.json` bytes equal to its `model_dump_json(indent=2) + "\n"`; a `timeout` result returns `abandon-human` with `mechanical="no schema-valid verdict (timeout)"` and the result's cost; no `panel_facts` event is logged; checked by `./dev.py test tests/unit/test_diagnosis_panel_use.py`. A test that routes a size-1 panel through `run_panel` fails.
2. Single call sites: `tests/integration/test_stage_panel_call_sites.py` parses `clutch/stages.py` with `ast` and finds exactly one `ctx.driver.run` call and one `ctx.driver.run_panel` call inside `diagnose`, the same inside `review`, exactly one call of `_panel_combine` inside each of `review` and `diagnose` and none elsewhere, and no `sum(` over `.usd` in `review` or `diagnose` (the member sum lives only in `_panel_combine`); no `tests/unit/` file reads `clutch/stages.py`; checked by `./dev.py test tests/integration/test_stage_panel_call_sites.py`.
3. Both tie orders are total and every tie resolves to one verdict: `set(DIAGNOSIS_ORDER) == set(get_args(DiagnosisVerdictName))` with no repeated entry (length 5), and `set(TRIAGE_ORDER) == set(get_args(TriageReply.model_fields["verdict"].annotation))` with no repeated entry (length 3); for every unordered pair of distinct verdicts of each model (10 diagnosis pairs, 3 triage pairs), `majority_verdict` over one reply of each returns the earlier one in the order and does not raise, and for every triple of three distinct diagnosis verdicts (10 triples) it returns the earliest in the order; with the old two-entry tuples the pair `split` vs `retry` raises `ValueError`, which this test rules out; the pairs `retry` vs `escalate` and `author` vs `declined` return `escalate` and `declined`; `majority_verdict(replies, ("retry",), ...)` still raises `ValueError`; checked by `./dev.py test tests/unit/test_panel_tie_orders.py`.
4. Majority and tie worked examples through `diagnose`, each with the member replies built as `DiagnosisReply` and `run_panel` faked: `retry`, `retry`, `escalate` writes `retry` with m0's lessons, not m1's and not `escalate`; the Goal's size-2 example (`retry` vs `escalate`) writes `escalate`, lessons `["needs a stronger model"]`, `provider` `claude`, `model` `b`, and passes `write_diagnosis` the summed cost `tokens 30, seconds 5.0, attempts 3, usd 0.75` carrying the winner's provider and model (not `codex`/`a`); `retry`, `split`, `abandon-human` writes `abandon-human` with m2's lessons, not `retry`; a winning reply's `trimmed_lessons` (for example `[0]`) is recorded, not `[]`; checked by `./dev.py test tests/unit/test_diagnosis_panel_use.py`.
5. The `panel_facts` event for the size-2 example equals the literal in the Goal (`combiner "majority-verdict"`, `member_count 2`, both members, `verdict_counts {"retry": 1, "escalate": 1}`, `dropped []`, `merged []`, `kept_index null`, `agreement_kind "models"`) with `surface="diagnose"`, `stem`, `attempt`, is written through `ctx.driver.log.event`, never the journal, and is absent for size 1 and for every failure outcome below; checked by `./dev.py test tests/unit/test_diagnosis_panel_use.py`.
6. Member failing: size 2, m0's call dropped (`PanelResult.dropped == [DroppedMember(index=0, failure_class="infra_error")]`) and m1 replying `split`: `Diagnosis.verdict` is `split`, with m1's lessons; `panel_facts.dropped == [{"index": 0, "failure_class": "infra_error"}]`, `member_count` 2, `verdict_counts {"split": 1}`; with a fake result whose cost carries `provider=None` and `model=None` and a two-candidate config, `panel_facts.members[0].provider` is the second candidate's provider (m1's), not the first's, and the `Diagnosis.provider` is the same; checked by `./dev.py test tests/unit/test_diagnosis_panel_use.py`.
7. All members failing and quota behaves like the single-model path: size 2 with `PanelResult(members=[], dropped=[both], dropped_findings=[quota_exhausted finding])` writes `verdict="abandon-human"`, `lessons=[]`, `mechanical="no schema-valid verdict (infra_error)"`, `cost == Cost()` and no `panel_facts`; the written record is field-for-field equal to the one a size-1 `diagnose` writes when its `driver.run` returns an `infra_error` result carrying the same `quota_exhausted` finding (with `provider` and `model` `None` in both), and equal to the record with `dropped_findings=[]`, so `dropped_findings` changes nothing; a size-2 `PanelResult` with a quota-dropped m0 and survivor m1 replying `retry` writes `retry`, not `abandon-human`; checked by `./dev.py test tests/unit/test_diagnosis_panel_use.py`.
8. Member not ok: size 2 where m0 is `ok` (`retry`) and m1 returns `timeout`: the record is `abandon-human`, `lessons=[]`, `mechanical="no schema-valid verdict (timeout)"`, `cost` equal to m1's cost, not `retry`, with no `panel_facts`; a `ProviderDroughtResult` member gives the same record with its outcome in `mechanical`; checked by `./dev.py test tests/unit/test_diagnosis_panel_use.py`.
9. Stage cost: for member costs `(tokens 10, usd 0.5, attempts 1, seconds 2.0)` and `(20, 0.25, 2, 3.0)` the summed cost is `tokens 30, usd 0.75, attempts 3, seconds 5.0`; with one member's `tokens` `None` the sum is `None`, not a partial sum; checked by `./dev.py test tests/unit/test_diagnosis_panel_use.py`.
10. Route errors and the size-2 argument set: with a ctx whose `config.routing` is `[]`, `diagnose` calls `driver.run` once and no `run_panel`; with a size-2 row the keyword arguments passed to `run_panel` equal those passed to `run` for size 1 except the added `size=2`; checked by `./dev.py test tests/unit/test_diagnosis_panel_use.py`.
11. Existing size-1 diagnosis behavior and the `kind` pass-through still hold; checked by `./dev.py test tests/unit/test_route_kinds_filter.py tests/unit/test_diagnosis_lesson_trim.py tests/integration/test_diagnose.py tests/unit/test_panel_combiners.py`.
12. `review` is unchanged by the helper: `./dev.py test tests/unit/test_review_panel_use.py tests/unit/test_review_panel_dropped_findings.py tests/unit/test_driver_panel_fanout.py` passes with those files unedited.
13. The new files' headers are valid: `uv run clutch meta check tests/unit/test_diagnosis_panel_use.py tests/unit/test_panel_tie_orders.py tests/integration/test_stage_panel_call_sites.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_diagnosis_panel_use.py tests/unit/test_panel_tie_orders.py tests/integration/test_stage_panel_call_sites.py tests/unit/test_panel_combiners.py tests/unit/test_route_kinds_filter.py tests/unit/test_diagnosis_lesson_trim.py tests/integration/test_diagnose.py tests/unit/test_review_panel_use.py tests/unit/test_review_panel_dropped_findings.py tests/unit/test_driver_panel_fanout.py
uv run clutch meta check tests/unit/test_diagnosis_panel_use.py tests/unit/test_panel_tie_orders.py tests/integration/test_stage_panel_call_sites.py
```

## Definition of rejected
A size-1 or unset panel that calls `run_panel`, or any change to its `diagnosis.json` bytes, `Diagnosis`, call arguments or effect keys; a tie order that omits a verdict of its model or leaves any tie unresolved or raising; a second `write_diagnosis` path or two driver call sites in `diagnose` that build their keyword arguments separately; a second copy of the member cost sum outside `_panel_combine`; a `panel_facts` record written to the journal; reading `dropped_findings` in `diagnose` to change the record; any edit to `clutch/driver.py`, `clutch/triage.py`, a prompt spec, or a line of `clutch/panel.py` other than the two tuples.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one function and one extracted helper in `clutch/stages.py`, two tuples in `clutch/panel.py`, three new test files and two doc sentences; triage, the other half of row 192, is left for its own run, and the merged `run_panel`, `majority_verdict` and `panel_members` carry the mechanism.
