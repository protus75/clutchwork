---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
none

## Context
- clutch/requisition.py::review_ticket
- clutch/panel.py
- clutch/driver.py::Driver.run_panel
- clutch/driver.py::Driver.from_config
- clutch/providers.py::panel_members
- clutch/llmeffect.py
- clutch/stages.py::review
- tests/unit/test_review_panel_use.py
- tests/unit/test_requisition_stage_events.py
- tests/unit/test_panel_combiners.py
- docs/stage-panels-plan.md

## On-demand
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 193. `Route.panel`, `clutch/panel.py` and `Driver.run_panel` are merged and `review` uses them (row 179), but requisition review (`clutch/requisition.py::review_ticket`) never does: a routing row `{tier, surface: requisition_review, panel: {size: N, combine: findings-union}}` loads (`PANEL_SURFACES` in `clutch/config.py` already allows it) and then does nothing. After this ticket, such a row makes `review_ticket` run N member reviews and return one combined `RequisitionVerdict`.

Why `run_panel` is not used: requisition review does not go through `Driver.run`. It owns its render, spool, retry loop, watch and a direct `llm_call(...)` (read from `clutch/requisition.py`, which also already accepts a `key_scope` argument and passes `scoped_seq(key_scope, run_seq)` to `llm_call`). So the panel is a loop over members inside `review_ticket`, each member's `llm_call` keyed with `scoped_seq(f"m{k}", run_seq)`. Rejected simpler approach: adapting `run_panel` to take a callable; it returns `StageResult`s and loses the requisition verdict fields, so it would grow a second result shape.

Design, read from the merged code:
- Size comes from a new `Driver.panel_members(tier, surface)`: `providers.panel_members(config, tier, surface)` where `config` is the first element of `Driver._notify_config` (set by `Driver.from_config`), and `()` when `_notify_config` is `None` (a `Driver` built directly) or `providers.panel_members` raises `ProviderSetupError`. `review_ticket` uses `size = len(driver.panel_members(tier, "requisition_review")) or 1`. Every production caller (`clutch/runner.py`, `clutch/author.py`, `clutch/__main__.py`) builds its driver with `Driver.from_config`, so none of them changes. `providers.panel_members` returns a size above 1 only for a row whose own `surface` is `requisition_review`; a requisition review that falls back to the `(tier, review)` row has size 1 even when that row carries a panel, so a `review` panel never widens requisition review.
- Where member keys are scoped: only the `scoped_seq(...)` argument of the one `llm_call`, which becomes `scoped_seq(f"m{k}", run_seq)` for member `k` of a size above 1. The effect key is `llm/<stem_slot>/m<k>-<run_seq>/requisition_review/<attempt>/<call_seq>`, six parts, so `member_index` in `clutch/llmeffect.py` reads `k` and `ProviderLLM.admitted_call` assigns member `k`'s candidate; nothing in `clutch/providers.py` changes.
- Each member runs the existing re-prompt loop (render, spool prompt, race, spool output, parse `RequisitionReply`, `dependent_errors`) over `range(call_seq, call_seq + retry_cap + 1)`; every member starts at the caller's `call_seq`, in its own key space. Members run in turn, `k = 0..size-1`. Spool names of member `k` are `requisition_review/m<k>/call-NN/...` (the shape `Driver._run` writes for a member); size 1 keeps `requisition_review/call-NN/...`. The retry-cap test counts calls of the current member, not of the review.
- One watch and one `stage_start`/`stage_end` pair for the whole review as today (`owns_watch` is decided by the first call of the first member); `stage_end`'s `calls` is the total over members, and its outcome is `ok` for a combined `approve` and `gate_failed` for a combined `snag` or `rma`, exactly as the single-call path sets it at each `return` today. `Driver.panel_members` is NOT called when `key_scope` is set (the review short-circuits to size 1 first), so `tests/unit/test_key_scope.py`'s stand-in needs no edit for that path. A member that failed with `quota_exhausted` is dropped like any member failure and does not reach `Driver.provider_failure`: only an all-members failure re-raises, so no quota-storm or cooldown signal fires for a partial failure.
- The combiner is `panel.findings_union`, with one change so it fits this surface. Today it builds `ReviewVerdict` (whose validator refuses requisition finding codes) and, for an `rma` verdict, keeps only findings coded `ticket`. It gains a keyword `rma_code: str | None = "ticket"` and builds `type(replies[0])(...)`: the default keeps every existing call bit-for-bit, and `rma_code=None` keeps every finding of an `rma` result. Requisition review passes `rma_code=None` and `RequisitionReply` replies. This is the one earning caller of the new keyword.

Outcomes, each by name:
- **Unset panel**: `Driver.panel_members` is `()` or one member (no `Route.panel`, or `size: 1`): `review_ticket` makes exactly the calls it makes today: same `llm_call` keyword arguments (`run_seq=scoped_seq(key_scope, run_seq)`), spool writes, `begin_watch` arguments, stage events, and returned `RequisitionVerdict`; no `panel_facts` event; `Driver.panel_members` is not consulted again.
- **Scoped review**: `key_scope` is not `None` (the supervisor's `key_scope="sup"` through `clutch/rework.py`): size 1, whatever the route says, because the six-part key admits one scope (`member_index` reads only `m<k>-<n>`), so a panel cannot nest inside `sup-<n>`. The key stays `llm/<stem_slot>/sup-<run_seq>/...`.
- **All members ok**: every member's validated `RequisitionReply` goes to `findings_union(replies, members, dropped, rma_code=None)`. The result is one `RequisitionVerdict` with `verdict`, `summary` and `findings` from the union (verdict is the worst any member gave: `rma` over `snag` over `approve`), `mechanical=None`, `provider` and `model` of the first surviving member, `calls` the total over members, and the shared `render_chars`, `spec_version` and hashes of the one review.
- **Member failing**: a member whose `llm_call` raises `ProviderCallError` is dropped (`DroppedMember(index=k, failure_class="infra_error")`) and the next member runs; the surviving members are combined.
- **One member left**: a size-2 panel with one dropped member combines one reply: verdict, summary and findings equal that member's, `agreement` reads `1/1`, `member_count` is 2.
- **All members failing**: the last `ProviderCallError` is re-raised, exactly the exception a single failed call raises today, so the callers' existing `provider_failure` handling runs; no `RequisitionVerdict`, no `panel_facts`. (Unlike `review`, no finding is lost, because the exception carries it to the caller.)
- **Drought**: a `ProviderDrought` from any member propagates at once; later members do not run.
- **Member not ok**: a member that ends mechanically (`timeout`, `invalid reply`, `provider error`, a review render over bound) ends the whole review: the first such `RequisitionVerdict` is returned unchanged (with `calls` the total so far), later members do not run, no `panel_facts` is written. Same rule as `review`'s "member not ok".
- **Tie**: none; `findings_union` takes the worst verdict. `approve` plus `snag` is `snag`; `approve` plus `approve` is `approve` with no findings.
- **Lint failure and render over headroom**: decided before any member call, unchanged, no panel.
- **Stuck budget**: not shared. Each call keeps `driver.race(..., REQUISITION_STUCK_S)`, so a size-3 panel can take up to three times today's worst case. The plan's shared stuck budget is the gap, filed to the Suggestion Box, not fixed here.

Stored values and `panel_facts`: `panel_facts` is one engine-log event (`driver.log.event`, never the journal), written only when size is above 1 and at least one member produced a reply: `event="panel_facts"`, `stem`, `attempt`, `run_seq`, `surface="requisition_review"` (the `event_context` fields) and the `PanelFacts.model_dump()` fields. Member `provider` and `model` come from the member's `LLMResult`, and from `driver.panel_members(tier, "requisition_review")[k].provider.name` and `.model` only when the result carries `None` (a fake LLM), where `k` is the member's original index: the j-th surviving member's `k` is the j-th index in `range(size)` not in `dropped`. `members` and `merged[].members` index the surviving members in order; `dropped[].index` is the original index.

Worked example, runner path, stem `demo`, `run_seq` 2, `attempt` 2, `call_seq` 1, `retry_cap` 1, panel size 2. Member 0's first reply is not JSON, so it re-prompts once; member 1 replies at once.
- Keys: `llm/demo/m0-2/requisition_review/2/1`, `llm/demo/m0-2/requisition_review/2/2`, `llm/demo/m1-2/requisition_review/2/1`. Spools: `requisition_review/m0/call-01/prompt.md`, `.../m0/call-02/...`, `requisition_review/m1/call-01/...`. `calls` is 3.
- Size 1 for the same review: `llm/demo/2/requisition_review/2/1` and `requisition_review/call-01/prompt.md`. With `key_scope="sup"`: `llm/demo/sup-2/requisition_review/2/1`.
- Union: m0 (claude) `snag`, summary `fence gap`, finding `Finding(code="requisition_review", path="a.py", line=3, message="fence misses a.py", paved_road="fence it", kind="authoring_error")`; m1 (codex) `approve`, summary `fine`. Combined: `snag`, summary `fence gap\nfine`, that one finding, `provider` claude. `panel_facts`: `combiner "findings-union"`, `member_count 2`, `verdict_counts {"snag": 1, "approve": 1}`, `merged` one entry `agreement "1/2"`, `members [0]`, `dropped []`, `kept_index null`, `agreement_kind "models"`.

Validation by rule (every field and input):
- `Route.panel.size`: integer 1 to 3, refused at config load (merged `Panel`); `combine` on a `requisition_review` row: only `findings-union` (merged `PANEL_SURFACES`). `review_ticket` trusts both.
- `size` used by `review_ticket`: `len(members) or 1`, so an integer 1 to 3.
- `key_scope`: `None` or the existing `scoped_seq` pattern `[a-z][a-z0-9]*`; a non-`None` value forces size 1 (above).
- Member key scope `f"m{k}"`: always matches `scoped_seq`'s pattern; `k` is an integer from 0 to `size - 1`.
- `tier`: the existing `AgentTier` argument, passed to `Driver.panel_members` unchanged. `surface`: the literal `requisition_review`.
- `stem`, `stem_slot`, `run_seq`, `attempt`, `call_seq`, `prior`, `text`, `coverage_map`, `expected_budget`, `specs_dir`, `repo`: unchanged, validated as today.
- Each member reply: `RequisitionReply.model_validate_json` and `dependent_errors` as today; an invalid reply re-prompts that member, and after its retry cap ends the review as `invalid reply` (member not ok).
- `findings_union` inputs: `replies` and `members` equal length and nonempty (merged `ValueError`); `rma_code` is `str` or `None`.

## Boundary contract
### Requisition review panel use
- disposition: extend
- owner: clutch/requisition.py
- consumers: `clutch/runner.py` (drain gate), `clutch/rework.py`, `clutch/author.py` and `clutch/__main__.py` (`ticket review` verb) read `RequisitionVerdict.verdict`, `findings`, `calls`, `provider`, `model`, `ticket_sha`; the journal's `requisition_verdict` signal and `clutch/rework.py`'s review sequence scan read the `llm/...` keys
- observable change: `review_ticket` reads the panel size for its tier and, above 1 and with `key_scope` unset, runs N member reviews with keys `llm/<stem_slot>/m<k>-<run_seq>/requisition_review/<attempt>/<call_seq>` and returns one combined `RequisitionVerdict`, writing one `panel_facts` log event. Inputs: the same arguments; outputs: the same `RequisitionVerdict` shape; failure: each outcome in Goal; side effects: member spools under `requisition_review/m<k>/`, one `panel_facts` log line; ordering: lint and headroom checks, then members in index order; persistence: effect keys and spools only, no new journal event type
- compatibility: size 1, an unset panel or a set `key_scope` gives the same calls, keys, spool writes and verdict as before (criterion 1); six-part member keys are what `review-panel-r2` merged; `calls` is the total, which only advances the callers' next `call_seq` by at least what any member used; the requisition review prompt spec is unchanged, so no version bump
- acceptance: criteria 1 to 11
- tests: tests/unit/test_requisition_panel.py
- post-merge source of truth: clutch/requisition.py

### Rework review sequence scan
- disposition: extend
- owner: clutch/rework.py
- consumers: `rework` itself (the one caller of the new `next_review_seq`), whose `review_ticket(..., call_seq=...)` call feeds the journal's `llm/...` effect keys
- observable change: the next review `call_seq` is the maximum over the plain keys and the `m<k>-<key_attempt>` member keys, not the plain keys alone, so a rework review after a crash or a second attempt with a panel configured never reuses a completed member key
- compatibility: identical results when there are no member keys (every host without a requisition panel route), and an unchanged `rework` signature and result
- acceptance: criterion 13
- tests: tests/unit/test_rework_review_seq.py and tests/integration/test_rework_review_seq_call_site.py
- post-merge source of truth: clutch/rework.py

### Driver panel member accessor
- disposition: extend
- owner: clutch/driver.py
- consumers: `clutch/requisition.py::review_ticket` only
- observable change: new method `Driver.panel_members(tier, surface)` returns `providers.panel_members(config, tier, surface)` for a driver built by `Driver.from_config`, and `()` for a directly built driver or when the route does not resolve; no other `Driver` behavior changes
- compatibility: no existing method, field or call changes; the four test stand-ins that reach `review_ticket` gain the one method
- acceptance: criterion 9
- tests: tests/unit/test_requisition_panel.py
- post-merge source of truth: clutch/driver.py

### Findings union result type
- disposition: extend
- owner: clutch/panel.py
- consumers: `clutch/stages.py::review` (unchanged call), `clutch/requisition.py`, tests/unit/test_panel_combiners.py
- observable change: `findings_union` accepts keyword `rma_code` (default `"ticket"`) and returns the type of its first reply; with `rma_code=None` an `rma` result keeps every merged finding
- compatibility: every existing call passes no `rma_code` and `ReviewVerdict` replies, so its result and `PanelFacts` are unchanged (criterion 8)
- acceptance: criteria 8 and 10
- tests: tests/unit/test_requisition_panel.py and the unchanged tests/unit/test_panel_combiners.py
- post-merge source of truth: clutch/panel.py

## Scope in / Scope out
The implementer creates the new test file's meta header with `uv run clutch meta refresh tests/unit/test_requisition_panel.py` and then edits only the `# purpose:` line to a non-empty one-line statement; the header is never written by hand.

Scope in:
- clutch/requisition.py, in `review_ticket` only: compute `size` (and force 1 when `key_scope` is not `None`); run the existing loop once per member with the member key scope, member spool segment and per-member retry count; combine with `findings_union(..., rma_code=None)`; log `panel_facts`; re-raise the last `ProviderCallError` when every member is dropped. The size-1 path keeps one `llm_call` site; `llm_call` is called from exactly one place in the file (criterion 11). Import `PanelMember`, `DroppedMember`, `findings_union` as needed. Early returns before the loop (lint, render, coverage map) are not changed.
- clutch/driver.py: add `Driver.panel_members` and nothing else.
- clutch/rework.py: the replay hazard. `rework` chooses the next review `call_seq` from a scan of the journal for keys starting `llm/<stem>/<key_attempt>/requisition_review/<attempt>/` (the `review_seq` line before `render_attempt`), then calls `review_ticket(..., call_seq=review_seq + 1)`. A panel member's key has `m<k>-<key_attempt>` in the second part, so that scan never sees member completions: after a crash or a second rework attempt with a panel configured, the review would reuse call number 1 and the journal would replay the old member replies for a different proposal text. Extract that scan into one module-level function `next_review_seq(history, stem, key_attempt, attempt) -> int` in `clutch/rework.py` (the one call site is the line it replaces) that takes the maximum `call_seq` (the last `/` part) over BOTH key families: the plain prefix `llm/<stem>/<key_attempt>/requisition_review/<attempt>/` and the member keys `llm/<stem>/m<k>-<key_attempt>/requisition_review/<attempt>/` for every integer `k` (the member part matches `m\d+-<key_attempt>` exactly, so `m0-2` is a member of key_attempt `2` and `m0-12` is not), or 0 when neither family has a key. Nothing else in `clutch/rework.py` changes.
- tests/unit/test_rework_review_seq.py and tests/integration/test_rework_review_seq_call_site.py (new): see criterion 13.
- clutch/panel.py: `findings_union` gains `rma_code` and the type-of-first-reply result; no other function changes.
- tests/unit/test_requisition_stage_events.py, tests/unit/test_requisition_dependents.py, tests/unit/test_key_scope.py, tests/unit/test_requisition_sibling_tickets.py: each hand-built driver stand-in that reaches `review_ticket` gains `panel_members=lambda tier, surface: ()`; no other line changes.
- docs/how-clutch-works.md: section 8.2 (line ending "review fans out, while the other surfaces do not yet") says review and requisition review fan out and the rest do not yet; no other section changes.
- tests/unit/test_requisition_panel.py: new file holding every new test, built on fakes and monkeypatched `llm_call` as in tests/unit/test_requisition_stage_events.py.

Scope out:
- Diagnosis and triage (`review-panel-stage-use-majority`, row 192), per-member scorecard attribution (row 68), a shared stuck budget (Suggestion Box), the requisition review prompt spec (unchanged, no version bump), `clutch/runner.py`, `clutch/rework.py`, `clutch/author.py`, `clutch/__main__.py`, `clutch/providers.py`, `clutch/config.py`.
- Merge order: `index-box-neighbors-prompts` (fences `clutch/author.py`, `clutch/triage.py`, `docs/how-clutch-works.md`), `index-consumers-training-join` (`clutch/training.py`, `clutch/__main__.py`), `spools-tests-via-helper-fake-fs` (test spool helpers and two integration tests) and `spools-onto-evidence-store-r2` (draft; `clutch/driver.py` `Spool`) share no file with this fence except `docs/how-clutch-works.md` (different section) and `clutch/driver.py` for the draft: that draft's author re-greps `Spool(` and fences nothing here, because the new method touches no `Spool` code; either merge order leaves both ticket's tests passing. Nothing here fences a file those tickets fence, since the test files above are not theirs.

## Scope fence
- clutch/requisition.py
- clutch/driver.py
- clutch/panel.py
- clutch/rework.py
- tests/unit/test_rework_review_seq.py
- tests/integration/test_rework_review_seq_call_site.py
- tests/unit/test_requisition_panel.py
- tests/unit/test_requisition_stage_events.py
- tests/unit/test_requisition_dependents.py
- tests/unit/test_key_scope.py
- tests/unit/test_requisition_sibling_tickets.py
- docs/how-clutch-works.md

## Acceptance criteria
1. Unset panel is unchanged: with a stand-in driver whose `panel_members` returns `()`, and again with one returning a single member, `review_ticket` on a scripted reply sequence (first reply invalid JSON, second a valid `approve`, `retry_cap` 1) records exactly the literal expected sequence written in the test from the current code: `llm_call` keyword arguments with `run_seq=2` (plain int) and `call_seq` 1 then 2, spool writes `requisition_review/call-01/prompt.md`, `call-01/output.txt`, `call-02/...`, one `begin_watch`, one `stage_start` and one `stage_end` with `calls=2`, the returned `RequisitionVerdict` with `calls=2`, and no `panel_facts` event; a test that scopes the key (`m0-2`) or the spool (`m0`) for size 1 fails; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
2. Scoped review: with `key_scope="sup"` and a stand-in driver whose `panel_members` returns two members, `review_ticket` makes one member's calls with `run_seq="sup-2"` and no `m<k>` key and no `panel_facts` event, not a panel; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
3. Worked-example keys: size 2, runner-style arguments (`stem_slot="demo"`, `run_seq=2`, `attempt=2`, `call_seq=1`, `retry_cap=1`), member 0 first invalid then valid, member 1 valid: the recorded `llm_call` `run_seq` arguments are `"m0-2"`, `"m0-2"`, `"m1-2"` with `call_seq` 1, 2, 1, the effect keys built from them through `llm_key` equal the three literal strings in Goal, `member_index` of each is 0, 0, 1, the spool paths are the literal ones in Goal, `calls` is 3, and there is one `begin_watch` and one `stage_start`/`stage_end` pair with `calls=3`; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
4. Union result: m0 `snag` (the worked-example finding, summary `fence gap`) and m1 `approve` (`fine`): one `RequisitionVerdict` with verdict `snag`, summary `fence gap\nfine`, exactly that one finding, `mechanical` `None`, `provider` and `model` of m0's result, not `approve`; both `approve`: `approve`, no findings; m0 `approve` and m1 `rma` with finding code `requisition_review`: verdict `rma`, finding kept (not dropped for its code, not a validation error); the `panel_facts` event for the first case equals the literal in the worked example including `agreement "1/2"` and `members [0]`; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
5. Same finding twice: both members raise a finding on `(requisition_review, a.py, 3)` with different messages: one finding whose message is both messages joined by newline, `merged` `agreement "2/2"`, `members [0, 1]`, not two findings; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
6. Member failing: m0's `llm_call` raises `ProviderCallError`, m1 replies `snag`: verdict equals m1's, `panel_facts.dropped == [{"index": 0, "failure_class": "infra_error"}]`, `member_count` 2, `merged[0].members == [0]`; when the fake result's `provider` is `None`, `panel_facts.members[0].provider` is the provider name of `driver.panel_members(...)[1]` (member 1's), not member 0's; both members raising `ProviderCallError`: the last one is re-raised, no verdict, no `panel_facts`; a `ProviderDrought` from m0 propagates and m1's `llm_call` is never made; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
7. Member not ok: m0 `approve` and m1 timing out (`driver.race` raising `_StuckBudget`) returns m1's `timeout` snag `RequisitionVerdict` (`mechanical == "timeout"`) unchanged with no `panel_facts`; m0 returning an invalid reply past the retry cap returns that `invalid reply` snag and m1's `llm_call` is never made; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
8. `findings_union` keyword: with `ReviewVerdict` replies and no `rma_code`, the results of the existing cases are unchanged (`./dev.py test tests/unit/test_panel_combiners.py` still passes unedited); with `rma_code=None` and `RequisitionReply` replies, the result is a `RequisitionReply`, not a `ReviewVerdict`, and an `rma` result keeps a finding coded `requisition_review`, which the default would drop; checked by `./dev.py test tests/unit/test_requisition_panel.py tests/unit/test_panel_combiners.py`.
9. `Driver.panel_members`: a driver with `_notify_config=(config, {})` and a `requisition_review` row `panel: {size: 2, combine: findings-union}` over two candidates returns two `Served`, the second candidate's provider second; a directly built `Driver` returns `()`; a config with no `requisition_review` row and no `review` row returns `()` (the `ProviderSetupError` is swallowed); a config whose `review` row has a panel and no `requisition_review` row returns at most one member, not two; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
10. Real combination path: the panel test drives `review_ticket` with the real `findings_union` (not a stub) and with a real `RequisitionReply` parsed from a JSON string that carries `dependents`, so a member whose reply lists dependents does not fail `dependent_errors` and the combined verdict has no dependents field; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
11. Single call site: a source check in the test parses `clutch/requisition.py` with `ast` and finds exactly one call to `llm_call`, inside `review_ticket`, so the size-1 path and the member path share it; checked by `./dev.py test tests/unit/test_requisition_panel.py`.
12. Existing behavior holds: checked by `./dev.py test tests/unit/test_requisition_stage_events.py tests/unit/test_requisition_dependents.py tests/unit/test_key_scope.py tests/unit/test_requisition_sibling_tickets.py tests/unit/test_requisition_prior_review.py tests/unit/test_rework_review_seq.py tests/integration/test_rework_review_seq_call_site.py tests/integration/test_requisition.py tests/integration/test_rework.py`.
13. `tests/unit/test_rework_review_seq.py` asserts `next_review_seq` on in-memory history lists of objects with a `.key`: no keys gives `0`; the plain keys `llm/t/2/requisition_review/2/1` and `.../2` give `2`; only member keys `llm/t/m0-2/requisition_review/2/1`, `llm/t/m1-2/requisition_review/2/1` give `1`, not `0` (the old scan returned `0` for them, which is the replay hazard); both families mixed give the larger `call_seq`; a member key of another key_attempt (`llm/t/m0-12/requisition_review/2/5` for key_attempt `2`) and of another stem or attempt is ignored. Check: `./dev.py test tests/unit/test_rework_review_seq.py`. A second file, `tests/integration/test_rework_review_seq_call_site.py`, reads `clutch/rework.py` through a `Path(__file__)` anchor, parses it with `ast` and asserts exactly one call of `next_review_seq` and no remaining inline scan over the prefix `llm/{ticket.stem}/{key_attempt}/requisition_review/{attempt}/`. Check: `./dev.py test tests/integration/test_rework_review_seq_call_site.py`.
14. The new files' headers are valid: `uv run clutch meta check tests/unit/test_requisition_panel.py tests/unit/test_rework_review_seq.py tests/integration/test_rework_review_seq_call_site.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_requisition_panel.py tests/unit/test_panel_combiners.py tests/unit/test_requisition_stage_events.py tests/unit/test_requisition_dependents.py tests/unit/test_key_scope.py tests/unit/test_requisition_sibling_tickets.py tests/unit/test_requisition_prior_review.py tests/unit/test_review_panel_use.py tests/integration/test_requisition.py tests/integration/test_rework.py
uv run clutch meta check tests/unit/test_requisition_panel.py
```

## Definition of rejected
A size-1, unset-panel or scoped (`key_scope` set) review whose `llm_call` arguments, spool writes, stage events or returned verdict differ from today's; a second `llm_call` call site; a member key that is not `m<k>-<run_seq>` in the third part; a requisition panel that reads a `review` row's panel; a `panel_facts` record written to the journal; a swallowed `ProviderCallError` when every member failed; any edit to `clutch/runner.py`, `clutch/rework.py`, `clutch/author.py`, `clutch/__main__.py`, `clutch/providers.py` or the requisition review prompt spec; a `getattr` fallback on the driver.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one function restructured in `clutch/requisition.py`, a small accessor in `clutch/driver.py`, one keyword in `clutch/panel.py`, two new test files, a small extracted function in `clutch/rework.py`, four one-line stand-in edits and one doc sentence; the merged `findings_union`, member keys and `panel_members` carry the mechanism, and diagnosis, triage and the shared stuck budget are separate rows or suggestions.
