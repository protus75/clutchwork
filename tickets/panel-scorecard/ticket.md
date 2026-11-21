---
state: draft
source: human
priority: P3
kind: feature
---

## Depends on
- review-panel-stage-use

## Context
- docs/stage-panels-plan.md#5. Measurement
- clutch/scorecard.py
- clutch/panel.py::findings_union
- clutch/llmeffect.py::member_index
- clutch/driver.py::Driver.run_panel
- clutch/retro.py::render_report
- clutch/status.py::render
- docs/how-clutch-works.md#9.6 Scorecard and baseline
- tests/integration/test_scorecard.py

## Goal / Why
Row 68 of the roadmap. Review panels are configured per routing row and multiply review spend by N, and the panels plan (section 5) says the scorecard is the measurement that decides whether a second reviewer earns that cost. Today the retro report and `clutch view status` show one row per surface and cannot say which panel member found what. After this ticket, when the retro window holds panel reviews, both print a `## Panel scorecard` section: per member slot, the reviews it took part in, its unique catches, and unique catches per 100 reviews; and once for the window, the cost multiplier. With no panel review in the window the section is absent and the scorecard names the outcome `no_panel_reviews`; nothing divides by zero.

How the data is read. Everything comes from the journal window the scorecard already folds, never the engine log. The `panel_facts` event goes to the engine log, which rotates, is not in the window, and is diagnostics, while the scorecard is a pure fold of journal events. Each panel member's call is already a journaled `effect_completion` keyed `llm/<stem>/m<k>-<run>/review/<attempt>/<call_seq>` (`Driver.run_panel` passes `key_scope="m<k>"`; `member_index` parses `k`), whose body carries `result.text` (the member's `ReviewVerdict` JSON), and `cost.usd`. Attribution reuses `findings_union`, the same merge the review stage ran and `panel_facts.merged[].members` recorded: a finding's merge key is `(code, path)` with the line rule inside `findings_union`, never reimplemented here. `panel_facts` is therefore not read; the member verdicts it summarizes are recomputed from the journaled replies.

Definitions (all over the current retro window, review surface only; rows 192 and 193 add the diagnosis, triage and requisition surfaces later and are not part of this ticket):
- A panel review is one group of completions sharing `(stem, run, attempt)` in which at least two distinct member slots delivered a reply that validates as a `ReviewVerdict` (after `unwrap_fence`, exactly as `project_scorecard` already parses review calls). A slot whose every call fails validation, or that was dropped (no completion), does not count as present. A group with one valid slot is not a panel review. A completion key without a member scope (`llm/<stem>/<n>/review/...`, a single reviewer) is never part of a panel review.
- A slot's reply in a group is its highest `call_seq` call that validates (earlier calls are re-prompts after an invalid reply).
- Slot cost in a group is the sum of `cost.usd` over all that slot's completions in the group, including invalid replies; a completion with no `cost` dict adds 0.0.
- Run `findings_union` over the present slots' replies in ascending slot order, with the constant placeholder `PanelMember(provider="unknown", model="unknown", verdict=reply.verdict)` (provider and model are never read, so a whitespace-only or missing value in a journaled body cannot raise). `MergedFinding.members` holds positions in that reply list, not slot numbers: its slot is `present_slots[position]`, where `present_slots` is the ascending list of present slots (if slot 0 is absent and slots 1 and 2 are present, position 0 is slot 1). A merged finding whose `members` list has exactly one entry is unique to that slot.
- A unique finding is confirmed when the ticket has a `state_transition` to `merged` later in journal order than the group's last completion. The implementer cannot reach `merged` without a later approving review, so a merged ticket's earlier unique finding was fixed or overruled by an approve. A ticket that never merges in the window confirms nothing. This does not measure findings that review missed and later code was blamed for; that is the escape column, unchanged.
- unique catches for slot `k` = the number of confirmed unique merged findings of slot `k`, summed over its panel reviews. reviews for slot `k` = the number of panel reviews where slot `k` is present. unique catches per 100 reviews = `100 * unique catches / reviews`, rendered with 2 decimals.
- cost multiplier = (sum over panel reviews of every present slot's cost) / (sum over panel reviews of the cost of the lowest-numbered present slot), rendered with 2 decimals. The lowest present slot stands for what a single reviewer would have cost.

Worked example (numbers). Ticket `a` merges after two panel reviews. Review 1 (attempt 0): slot 0 snags with finding F1 `(logic, a.py, 3)` and cost 1.00; slot 1 snags with F1 `(logic, a.py, 3)` and F2 `(logic, b.py, 9)` and cost 0.50. `findings_union` merges F1 as `members [0, 1]` and F2 as `members [1]`. Review 2 (attempt 1): both slots approve, 1.00 and 0.50. Slot 0: reviews 2, unique catches 0, per 100 = 0.00. Slot 1: reviews 2, unique catches 1 (F2, confirmed by the later merge), per 100 = 50.00. Cost multiplier = (1.00 + 0.50 + 1.00 + 0.50) / (1.00 + 1.00) = 3.00 / 2.00 = 1.50. Had ticket `a` never merged in the window, slot 1 would show unique catches 0 and 0.00.

Empty and degenerate cases (named outcomes): `no_panel_reviews` (no panel review in the window: no rows, multiplier `None`, no section printed); `no_cost_data` (panel reviews exist but the baseline sum is 0.0: rows are filled, multiplier `None`, printed as `n/a`); `measured` (everything else).

## Boundary contract
### Panel scorecard projection
- disposition: extend
- owner: clutch/scorecard.py
- consumers: `render_report` in clutch/retro.py (the retro receipt), `render` in clutch/status.py (`clutch view status`)
- observable change: `Scorecard` gains a `panel` field of type `PanelScorecard` (outcome, panel reviews, per-slot rows, cost multiplier); `panel_lines(card)` returns the markdown lines of the new section, empty for `no_panel_reviews`; retro and status append them after the surface table.
- compatibility: the surface table, `SurfaceScorecardRow`, `project_scorecard` inputs, and every existing field are unchanged; with no panel review the retro receipt and status output are byte-identical to today
- acceptance: the new unit test builds journal events and asserts the worked example's numbers, each named outcome, and ordering
- tests: tests/unit/test_panel_scorecard.py; the existing scorecard, status and retro integration tests must still pass unchanged
- post-merge source of truth: clutch/scorecard.py (`project_scorecard`, `PanelScorecard`, `panel_lines`) and docs/how-clutch-works.md section 9.6

## Scope in / Scope out
Scope in:
- `clutch/scorecard.py`: add frozen dataclasses `PanelSlotRow(slot: int, reviews: int, unique_catches: int, unique_per_100: float)` and `PanelScorecard(outcome: str, panel_reviews: int, slots: tuple[PanelSlotRow, ...], cost_multiplier: float | None)`; the constant `PANEL_OUTCOMES = ("no_panel_reviews", "no_cost_data", "measured")`; a `panel: PanelScorecard` field on `Scorecard` (last field, set by `project_scorecard`, no default); the fold described in Goal, inside `project_scorecard`'s event loop and a pass after it (dedupe completions by `event.key` exactly like the existing `seen` set; ignore a completion whose `body["result"]["text"]` is missing or invalid like the existing review parse); and `panel_lines(card) -> list[str]`, used by both renderers (two call sites).
- Field validation, every field: `slot` is `member_index(event.key)`, a non-negative int, else the completion is not a panel completion; `run` is the digits after `m<k>-` in key part 2; `attempt` is key part 4; `stem` is `event.ticket`, which must be non-empty; key part 3 must equal `review`; `result.text` must validate as `ReviewVerdict` after `unwrap_fence`; `result.provider` and `result.model` are not read; `cost.usd` is a number or `cost` is missing (counts 0.0). Any other shape means the completion is skipped, never raises.
- Ordering: slot rows ascending by `slot`. Groups are processed in journal order of their last completion; the confirmation test is journal order against the stem's `merged` transitions.
- Output: `panel_lines(card)` returns `[]` for `no_panel_reviews`, else `["", "## Panel scorecard", "", f"Panel reviews: {n}; cost multiplier: {x:.2f}" (`n/a` when `None`), "", "| Slot | Reviews | Unique catches | Unique catches per 100 reviews |", "| ---: | ---: | ---: | ---: |", one `| k | reviews | unique | per100:.2f |` row per slot]`.
- `clutch/retro.py` `render_report` and `clutch/status.py` `render`: after building the surface `table` list, `table.extend(panel_lines(card))`. The retro import of `panel_lines` stays lazy inside `render_report`, beside the existing `project_scorecard` import, because `clutch/scorecard.py` imports `clutch/retro.py`. Nothing else changes in either file.
- `docs/how-clutch-works.md`: in section 9.6 add one bullet describing the panel scorecard (journal-read, definitions, the three outcomes); in the retro paragraph in section 9 (the one saying "scorecard, proposals") nothing changes. Edit only 9.6.
- A new test file `tests/unit/test_panel_scorecard.py`. The implementer creates its clutch meta header with `uv run clutch meta refresh tests/unit/test_panel_scorecard.py` and then edits only the `# purpose:` line to a non-empty one-line sentence.

Scope out: the diagnosis, triage and requisition panel surfaces (the follow-up rows 192 and 193), `panel_facts` or the engine log, `Driver.run_panel` and the review stage, escape attribution, any change to prune-candidate rules, per-routing-row grouping (the journal does not record the row, so slots are the unit), any journal write, the extension, the roadmap, and prompt specs.

Rejected simpler approach: reading `panel_facts` from the engine log needs a new log reader inside a pure journal fold and loses data at rotation; the journal already holds every member reply and cost.

## Scope fence
- clutch/scorecard.py
- clutch/retro.py
- clutch/status.py
- docs/how-clutch-works.md
- tests/unit/test_panel_scorecard.py

## Acceptance criteria
1. With the worked example's events, `project_scorecard(window).panel` has `outcome == "measured"`, `panel_reviews == 2`, slot 0 `(reviews 2, unique_catches 0, unique_per_100 0.0)`, slot 1 `(2, 1, 50.0)` and `cost_multiplier == 1.5`, not slot 0 credited with F1 or slot 1 with 0 unique catches: `./dev.py test tests/unit/test_panel_scorecard.py`.
2. A unique finding on a ticket that never merges in the window counts 0 unique catches, not 1, and a finding both slots raised is never unique: `./dev.py test tests/unit/test_panel_scorecard.py`.
3. A window with only single-reviewer review completions, or with a group whose second slot never validates, gives `outcome == "no_panel_reviews"`, `slots == ()`, `cost_multiplier is None`, and `panel_lines` returns `[]`, with no `ZeroDivisionError`; a panel whose lowest slot cost is 0.0 gives `no_cost_data`, filled slot rows, `cost_multiplier is None` and the text `cost multiplier: n/a`: `./dev.py test tests/unit/test_panel_scorecard.py`.
4. A slot's re-prompted invalid reply then valid reply counts one review, uses the valid reply, and adds both calls' `cost.usd`; a completion with a malformed key, empty ticket, non-JSON text, a whitespace-only `provider` or `model`, or no `cost` is skipped or costs 0.0 without raising; duplicate completions of one key count once: `./dev.py test tests/unit/test_panel_scorecard.py`.
5. `PANEL_OUTCOMES == ("no_panel_reviews", "no_cost_data", "measured")`, and `panel_lines` for the worked example equals the exact lines listed in Scope in, slot rows ascending: `./dev.py test tests/unit/test_panel_scorecard.py`.
6. With no panel review, the existing retro and status output is unchanged: `./dev.py test tests/integration/test_scorecard.py tests/integration/test_status.py tests/integration/test_retro.py` pass without edits. Those tests only compare text after the heading, so byte-identity is also pinned in the new unit test: for a journal window with no panel review, `render_report(...)` and `clutch.status.render(...)` each end exactly at the last surface-scorecard row plus one `\n`, with no `## Panel scorecard` heading and no `panel` text after it, and equal the output produced when the panel code is bypassed (`./dev.py test tests/unit/test_panel_scorecard.py`).
7. The `docs/how-clutch-works.md` section 9.6 bullet names the three outcomes and the journal source: read `docs/how-clutch-works.md` section 9.6.
8. `render_report(window, measurements(window), {}, [], RetroArtifact(proposals=[]))` and `clutch.status.render(Status(merged=(), in_flight=(), blocked=(), intake=(), spend_usd=0.0, scorecard=project_scorecard(window)))`, built in memory from the worked-example window, each end with the exact `panel_lines` output joined by newlines plus a final newline, not the surface table alone: `./dev.py test tests/unit/test_panel_scorecard.py`.
9. A group whose present slots are 1 and 2, where slot 2 alone raises a finding on a ticket that merges, gives slot 2 `unique_catches == 1`, slot 1 `unique_catches == 0`, and no row for slot 0, not slot 1 credited: `./dev.py test tests/unit/test_panel_scorecard.py`.
10. The new test file header carries a non-empty `# purpose:` and all seven keys: `uv run clutch meta check tests/unit/test_panel_scorecard.py`.

## Verification
```
./dev.py test tests/unit/test_panel_scorecard.py tests/integration/test_scorecard.py tests/integration/test_status.py tests/integration/test_retro.py
uv run clutch meta check tests/unit/test_panel_scorecard.py
```

## Definition of rejected
Reads `panel_facts` or the engine log; reimplements the merge key instead of calling `findings_union`; divides by a zero count; prints a section or changes any byte of retro or status output when the window has no panel review; adds a journal write or a model call; touches a file outside the fence.

## Time budget
- expected: 25m
- stuck: 50m
