---
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
- panel-combiners
- panel-routing-config

## Context
- clutch/llmeffect.py
- clutch/driver.py::Driver.run
- clutch/driver.py::Driver._run
- clutch/providers.py::panel_members
- clutch/providers.py::ProviderLLM.admitted_call
- clutch/panel.py::DroppedMember
- tests/fakes.py
- tests/unit/test_driver_hooks.py

## On-demand
- docs/stage-panels-plan.md
- docs/roadmap.md

## Goal / Why
Roadmap row 67, re-scoped after review of the first two drafts: this ticket delivers the driver and provider machinery that runs one stage as N independent member calls. The call sites that use the combined result move to a follow-up row filed here (see Scope in): review, diagnosis and triage call `Driver.run_panel`; requisition review runs its own re-prompt loop and calls `llm_call` directly (clutch/requisition.py:276), never `Driver.run`, so it cannot consume `run_panel` and instead builds member keys with `scoped_seq("m<k>", ...)` around its own `llm_call` in the follow-up row. The earlier drafts bundled both and failed on size and on undeclared consumers.

After this ticket:
- A member call is keyed with the member in the run-sequence segment through the existing `scoped_seq` scope seam: member k uses scope `m<k>`, so the key is `llm/<stem>/m<k>-<run_seq>/<surface>/<attempt>/<call>`. It keeps exactly six parts and an integer last part, so `clutch/rework.py`, `clutch/stats.py`, `clutch/scorecard.py`, `clutch/training.py` and `providers.py` evidence capture (which unpacks six parts and already accepts a non-decimal `run_seq`) need no change. Rejected: a seventh `/m<k>` part, which would break all five six-part consumers.
- `llmeffect.member_index(call_key)` returns the member index of such a key and `None` for any other key, including keys with another scope.
- `ProviderLLM.admitted_call` serves a member-keyed call first from the candidate `panel_members` assigns to that index, then the other row candidates in row order, so failover keeps today's order after the assigned candidate.
- `Driver.run_panel(...)` runs `size` members in turn (not `asyncio.gather`) and returns a `PanelResult` with the member `StageResult`s and the dropped members. Running in turn keeps the single `ProviderLLM._active` slot and `abort_current` correct, so no active-adapter set is needed. This departs from `docs/stage-panels-plan.md` section 3, which says `asyncio.gather`; the plan is updated here.

Scorecard accounting: key shape is unchanged, so each member's review call is counted by `clutch/scorecard.py` as one review exactly as a single review is today. Per-member attribution and the cost multiplier stay with `panel-scorecard`.

## Boundary contract
### Member effect key
- disposition: extend
- owner: clutch/llmeffect.py
- consumers: clutch/driver.py, clutch/providers.py, and the unchanged six-part readers clutch/rework.py, clutch/stats.py, clutch/scorecard.py, clutch/training.py
- observable change: new `member_index(call_key)` helper; member keys are `scoped_seq("m<k>", run_seq)` keys. `llm_key` and `scoped_seq` are unchanged. Inputs are a key string; output is an int or None; a malformed or foreign scope yields None and never raises.
- compatibility: every existing key keeps its shape; a member key has six parts with an integer last part, so existing parsers accept it; a crash mid-panel replays completed members through their distinct keys
- acceptance: `member_index` returns the index for member keys and None otherwise
- tests: tests/unit/test_panel_member_keys.py
- post-merge source of truth: clutch/llmeffect.py

### Member candidate assignment
- disposition: extend
- owner: clutch/providers.py
- consumers: clutch/llmeffect.py (`llm_call` passes `call_key` to `admitted_call`), evidence capture in clutch/providers.py
- observable change: `admitted_call` reads `member_index(call_key)`; when not None the route is `(panel_members(...)[k],)` followed by the remaining `candidates(...)` in row order. When `k >= len(panel_members(...))` (a row with no panel, or a panel for another surface, returns one entry) `admitted_call` raises `ValueError` naming the index and the member count before any adapter call, so a misconfigured size never reaches a provider and never surfaces as an `IndexError`. The evidence `route.reason` is `first` when the served candidate is that route's first entry. The raw `call` path (`resolve()`) never sees a key and is unchanged. Evidence record schema stays `clutch.evidence.call/1.0`; `run_seq` is the string `m<k>-<n>`, which the existing non-decimal branch already writes.
- compatibility: calls without a member key route exactly as today; `_active` single-slot tracking is unchanged because members run in turn
- acceptance: a `/m1` call on a two-candidate row with panel size 2 is served by the second candidate; a `/m1` call on a row whose `panel_members` has one entry raises `ValueError` with no adapter call
- tests: tests/unit/test_panel_member_keys.py
- post-merge source of truth: clutch/providers.py

### Driver panel fan-out
- disposition: create
- owner: clutch/driver.py
- consumers: the three stage call sites that run through `Driver.run` (review, diagnosis, triage) in the follow-up row filed by this ticket; requisition review is not a consumer
- observable change: `async Driver.run_panel(stage, consumed, *, size: int, <same keyword arguments as run except key_scope>) -> PanelResult`. `PanelResult` (dataclass in clutch/driver.py) holds `members: list[StageResult]` and `dropped: list[panel.DroppedMember]`. Member k calls `run` with `key_scope=f"m{k}"` when `size > 1`, and with `key_scope=None` when `size == 1`, so a size-1 panel has the same keys and calls as `run`. Each member runs its own stage event and re-prompt loop. Members share one detector identity: `begin_watch` keys the detector on (owner, run_sequence, surface, attempt) and `run_sequence` is the unscoped seq, so with a `ProviderLLM` member 1 reuses member 0's detector and its original budget; this ticket does not change `begin_watch`. Members share one stuck budget at the `_run` level: member k receives `stuck_budget` minus the clock seconds already spent for its `_run` deadline and stage event, and no further member starts once that is zero or less. A member whose outcome is `infra_error` and which is not a `ProviderDroughtResult` is appended to `dropped` as `DroppedMember(index=k, failure_class="infra_error")` and the next member runs. A `ProviderDroughtResult` member keeps its provider_drought record: it is appended to `members` as-is and ends the loop, so no later member runs against the same drought. Any other non-`ok` outcome (`timeout`, `budget_exceeded`) is appended to `members` and ends the loop. An abort propagates `CancelledError` out of `run_panel` (`abort_current` cancels the stage task, so `run` raises and returns no `StageResult`) and no further member starts. When every member is dropped `members` is empty and the caller reports `infra_error`. Spool for a member-keyed call is `<stem>/<attempt>/<surface>/m<k>/call-NN/`, so members never overwrite each other; unscoped spool names are unchanged.
- compatibility: `Driver.run` is untouched in signature and behavior except the member spool segment; `abort_current` aborts the active member and the loop starts no further member
- acceptance: size-2 fan-out yields two distinct member keys and spools; a dropped member, a drought member and the all-dropped case are reported as stated; abort raises CancelledError and stops the loop
- tests: tests/unit/test_driver_panel_fanout.py
- post-merge source of truth: clutch/driver.py
- closest existing: `Driver.run`, which refuses a second active stage (driver.py:236) and returns one `StageResult`; `llmeffect.llm_call`, which makes one call
- earning reason: three production stage call sites consume it (follow-up row), `run` cannot return member results or dropped members, and looping `run` at each call site would duplicate the budget, drop, drought and abort rules three times

## Scope in / Scope out
Scope in:
- clutch/llmeffect.py: add `member_index`.
- clutch/providers.py: `admitted_call` member route as stated; import `member_index` and `panel_members` use. No change at the six-part unpack in the capture path.
- clutch/driver.py: add `PanelResult` and `Driver.run_panel`; add the member spool segment in `_run` only when `member_index(call_key)` is not None. `begin_watch` is not changed.
- docs/how-clutch-works.md: update only the paragraph that describes `llm/<stem>/<run_seq>/...` effect keys and the stage-call description to mention member scopes and `run_panel`.
- docs/stage-panels-plan.md: update only section 3 Execution so members run in turn, not `asyncio.gather`, and the key reads `m<k>-<run_seq>`.
- docs/roadmap.md: edit only the content cell of row 67 to name driver fan-out, member effect keys and provider member assignment; append one new row `review-panel-stage-use` at the end of the table with the number after the highest existing row (88 at this commit; renumber nothing) (kind feature, priority P2, plan `docs/stage-panels-plan.md`, depends `review-panel-r2`, content: review, diagnosis and triage call `run_panel` and use the combined result, requisition review uses member keys around its own `llm_call`, with a full tie order for every `majority-verdict` verdict and surface); change row `panel-scorecard` to depend on `review-panel-stage-use`.
- New tests only in the two new unit files.

Scope out:
- Stage use of combined results in clutch/stages.py, clutch/requisition.py, clutch/runner.py, clutch/triage.py and the tie order for diagnosis (split, reject, abandon-human) and triage (tombstone): all in `review-panel-stage-use`.
- clutch/panel.py combiner changes, scorecard attribution (`panel-scorecard`), best-of-N.
- Per-member detector identity in `begin_watch`.
- clutch/rework.py, clutch/stats.py, clutch/scorecard.py, clutch/training.py: unchanged by design.
- Prompt spec edits.

## Scope fence
- clutch/llmeffect.py
- clutch/providers.py
- clutch/driver.py
- docs/how-clutch-works.md
- docs/stage-panels-plan.md
- docs/roadmap.md
- tests/unit/test_panel_member_keys.py
- tests/unit/test_driver_panel_fanout.py

## Acceptance criteria
1. `member_index("llm/t/m1-3/review/1/2")` returns `1`, a plain key `llm/t/3/review/1/2` returns `None` (not `0`), and a key with another scope such as `llm/t/sup-3/review/1/2` returns `None`; checked by `./dev.py test tests/unit/test_panel_member_keys.py`.
2. A member key built with `scoped_seq("m1", 3)` through `llm_key` has exactly six parts and an integer last part, so a six-part reader accepts it; checked by `./dev.py test tests/unit/test_panel_member_keys.py`.
3. On a two-candidate row with panel size 2 and fake adapters, a `/m1` call is served by the second candidate with evidence `route.reason` equal to `first`, and a `/m0` call is served by the first candidate; on a three-candidate row, member 1's route is the second candidate, then the first, then the third, not row order; checked by `./dev.py test tests/unit/test_panel_member_keys.py`.
4. A `/m1` call on a row whose `panel_members` has one entry raises `ValueError` before any fake adapter is called, not `IndexError`; checked by `./dev.py test tests/unit/test_panel_member_keys.py`.
5. A call with no member key on the same row is served by the first candidate exactly as before, not by a panel member; checked by `./dev.py test tests/unit/test_panel_member_keys.py`.
6. A member-keyed evidence capture with the existing fake fs and git seams writes a start record with schema `clutch.evidence.call/1.0`, `id` equal to the full key and `run_seq` equal to `"m1-1"`, and does not raise; checked by `./dev.py test tests/unit/test_panel_member_keys.py`.
7. `run_panel` with `size=2` and fake LLM, clock and filesystem makes two calls with keys carrying scopes `m0` and `m1`, and writes prompt files under `<surface>/m0/call-01/` and `<surface>/m1/call-01/`, so neither overwrites the other; checked by `./dev.py test tests/unit/test_driver_panel_fanout.py`.
8. `run_panel` with `size=1` makes the same call keys and the same number of calls as `run` with the same arguments, not `m0`-scoped keys; checked by `./dev.py test tests/unit/test_driver_panel_fanout.py`.
9. When member 0's provider call fails with a `ProviderCallError`, `PanelResult.dropped` equals `[DroppedMember(index=0, failure_class="infra_error")]` and `members` holds member 1's result; when both fail, `members` is `[]` and `dropped` has two entries; checked by `./dev.py test tests/unit/test_driver_panel_fanout.py`.
10. With a fake clock that advances 30 seconds during member 0 and `stuck_budget=100`, member 1's `_run` deadline and stage event carry `stuck_budget` 70, not 100; with an advance of 100 or more, member 1 makes no LLM call. The test uses a non-`ProviderLLM` fake and asserts only the deadline and stage event, not a detector; checked by `./dev.py test tests/unit/test_driver_panel_fanout.py`.
11. `abort_current` during member 0 of a size-2 panel makes `run_panel` raise `CancelledError` (not return a `PanelResult`), leaves the fake LLM with one call, not two, and `Driver._active` is `None` afterwards; checked by `./dev.py test tests/unit/test_driver_panel_fanout.py`.
12. When member 0 raises `ProviderDrought`, `PanelResult.members` holds member 0's `ProviderDroughtResult` with its provider_drought record intact, `dropped` is `[]`, and the fake LLM has one call because member 1 makes none; checked by `./dev.py test tests/unit/test_driver_panel_fanout.py`.
13. The roadmap still parses and its gate commands are valid after the row edits; checked by `./dev.py test tests/integration/test_roadmap_table.py`. That the new `review-panel-stage-use` row exists is a one-time review check, not a test.
14. Existing driver, effect and provider behavior is unchanged; checked by `./dev.py test tests/integration/test_driver.py tests/integration/test_llm_effect.py tests/integration/test_providers.py`.

## Verification
```
./dev.py test tests/unit/test_panel_member_keys.py tests/unit/test_driver_panel_fanout.py tests/integration/test_driver.py tests/integration/test_llm_effect.py tests/integration/test_providers.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
A seventh `/m<k>` key part or any edit to rework, stats, scorecard or training parsers; `asyncio.gather` members sharing the single `_active` slot; any stage call site using `run_panel` in this diff; a panel test that passes when both members get the same candidate or the same spool path.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one driver method, one provider route rule and one key helper form a single tested unit; stage use and tie order are already split into `review-panel-stage-use`, and codex medians for comparable tickets are under 10m.
