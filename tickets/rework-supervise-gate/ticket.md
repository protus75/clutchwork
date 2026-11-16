---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/rework.py
- clutch/daemon.py::apply_rework
- clutch/tickets.py::split_frontmatter
- clutch/tickets.py::_sections
- clutch/tickets.py::_criteria
- clutch/driver.py::LlmStage
- clutch/driver.py::Driver._run
- tests/integration/test_rework.py::original
- tests/integration/test_rework.py::order
- tests/integration/test_rework.py::requisition
- tests/integration/test_rework.py::invoke
- tests/integration/test_rework.py::signals
- tests/integration/test_rework.py::ticket_bytes
- tests/integration/test_rework.py::test_rework_spec_render_and_driver
- tests/unit/test_rework_review_prior.py
- docs/how-clutch-works.md#6.5 Rework
- docs/roadmap-driver-plan.md#2. The supervisor step

## On-demand
- clutch/specs/rework.md

## Goal / Why
Roadmap row 89 (`docs/roadmap.md`, owning design `docs/roadmap-driver-plan.md` section 2) has the engine do what the owner did by hand for 78 of 142 verdicts: read the diagnosis, apply its suggested ticket edit, have the edit reviewed, and keep the ticket. The engine piece that rewrites a ticket under review is Rework's `update` action (`clutch/rework.py::rework`, published by `clutch/daemon.py::apply_rework`), but three things stop it from doing that job today:

1. Its spec, `clutch/specs/rework.md` (version 1.1 at this writing), says "Change content only to narrow or divide the original goal". A supervisor's edit does the opposite: it keeps the goal and fixes the ticket around it.
2. Rework sees only the failure findings. Diagnose's lessons, which name the edit, never reach its prompt.
3. Nothing stops a proposal from rewriting `## Goal / Why`, dropping an acceptance criterion, or splitting the ticket. The supervising-session rule every host gets (`CORE_TEMPLATE` in `clutch/hostfiles.py`: fix lint or format, add a missing `## Scope fence` or `## Context` entry, correct a stale path, make a wording update; never change a ticket's goal or scope) is prose for chats, and the requisition review is the only check on a Rework proposal.

This ticket adds Rework's supervisor mode, the half of row 89 that `supervisor-rework` calls. `rework` and `apply_rework` take an optional `supervise` input, holding the trigger that put the ticket in the Reject queue and the diagnosis lessons. The spec renders that input in a new `supervise` data block, which holds `none` outside supervisor mode, and states the allowed-edit list. A mechanical allowed-edit gate checks every supervisor-mode proposal before any requisition review. It refuses a split, an `update` that leaves the ticket text unchanged, a changed `## Goal / Why`, and a proposal with fewer acceptance criteria. Each refusal ends the call at once, with no re-prompt and no review, and its road is "escalate to the operator". A supervisor-mode call that ends `gate_failed` returns the last proposal it refused as the result's artifact, so the caller can attach the engine's best attempt to the escalation. Outside supervisor mode Rework behaves exactly as it does now; its prompt only gains the `none` block.

## Scope in / Scope out
Scope in:
- `clutch/rework.py`:
  - A frozen dataclass `Supervise` with `trigger: str` and `lessons: tuple[str, ...]`.
  - A pure function `supervise_findings(stem: str, original: str, reply: ReworkReply) -> list[Finding]`. It reads sections with `clutch/tickets.py::split_frontmatter` and `clutch/tickets.py::_sections`, treating a text with no frontmatter as having no sections, and counts criteria with `clutch/tickets.py::_criteria`. Every finding it returns has code `supervise_edit`, path `tickets/<stem>/ticket.md`, and the paved road ``escalate to the operator: the stem stays in the Reject queue; edit tickets/<stem>/ticket.md, then `clutch confirm <stem>`, or retire it with `clutch reject <stem>` ``. The findings, in this order:
    - `split`: exactly one finding, `a supervisor edit cannot split the ticket`.
    - `update`: zero or more of these. `the proposal does not change the ticket text` when the proposal text equals `original`. ``the proposal changes `## Goal / Why` `` when the stripped `Goal / Why` section differs. `the proposal drops acceptance criteria (<new> of <old> remain)` when the proposal has fewer `_criteria` items than `original`.
    - `escalate`: no findings.
  - `rework` gains the keyword `supervise: Supervise | None = None`. Its render passes a fifth input, `supervise`: `none` when `supervise` is None, else `json.dumps({"trigger": ..., "lessons": [...]}, sort_keys=True)`. Its `review` callback first records the reply it was handed. When `supervise` is set, it then runs `supervise_findings(ticket.stem, text, artifact)`, before the stem, schema, scratch-tree, and requisition-review checks, and returns `GateReport(code="ticket_schema", verdict="fail", findings=...)` when that is non-empty. `LlmStage.terminal_findings` becomes `frozenset({"requisition_rma", "supervise_edit"})`. When `supervise` is set and the driver result is `gate_failed`, `rework` returns that result with `artifact` set to the last reply the callback recorded (None if the callback never ran). Every other outcome, and every result outside supervisor mode, is returned as now.
- `clutch/daemon.py::apply_rework`: gains the keyword `supervise: Supervise | None = None` and passes it to `rework` unchanged. Nothing else in `apply_rework` changes.
- `clutch/specs/rework.md`:
  - `version` becomes the next minor above its value on main at the base commit.
  - `## Task`: the sentence "Change content only to narrow or divide the original goal." becomes "Outside a supervisor edit, change content only to narrow or divide the original goal.". After the action list, add this paragraph: "When the supervise block is not `none`, this is a supervisor edit of a ticket the Reject queue holds for the trigger it names. Choose `update` or `escalate`, never `split`. Apply its diagnosis lessons using only these edits: fix lint or format, add a missing `## Scope fence` or `## Context` entry, correct a stale path, or reword. Never change `## Goal / Why`, remove an acceptance criterion, or widen the scope. An `update` must change the ticket text. When no allowed edit resolves the findings and lessons, reply `escalate`: the ticket stays with the operator."
  - `## Inputs`: between the findings block and the conflict block, add the line "The supervisor trigger and diagnosis lessons, or `none` outside a supervisor edit:" followed by a `supervise` data block in the same form as the others.
- `tests/integration/test_rework.py::test_rework_spec_render_and_driver`: three changes, each only to match the new spec. The pinned `version` becomes the new version. The `fixture` dict gains `"supervise": "none"`. The golden sha256 becomes the hash of the new render. No other line in the file changes.
- `docs/how-clutch-works.md` section 6.5: add one paragraph on supervisor mode (the `supervise` input, the update-or-escalate rule, the allowed-edit gate's four refusals ending the call before review, and the refused proposal returned on `gate_failed`). No other section changes. Section 8.4's `rework.md` row stays as is.
- New tests in two new files: `tests/unit/test_rework_supervise_gate.py` for the pure `supervise_findings`, which reads no disk (`clutch/rework.py` has a positive unit floor in `test-gate.toml`; the ticket texts are string constants in the test file); and `tests/integration/test_rework_supervise.py` for `rework` and `apply_rework` in supervisor mode. The integration file may import `ctx` from `tests/integration/test_mergequeue.py`, and `original`, `order`, `requisition`, `signals`, `ticket_bytes`, `SNAG` and `run` from `tests/integration/test_rework.py`, as `test_rework.py` itself imports `ctx`. It changes none of them.

Scope out:
- Who calls supervisor mode, the Reject-queue trigger, the supervisor keep, `caps.supervise`, the lineage change, and `rework.md`. Those are `supervise-cap-lineage` and `supervisor-rework`. Nothing in `clutch/runner.py`, `clutch/caps.py`, `clutch/config.py` or `clutch/drain.py` changes here.
- The spec's frontmatter `gates` list, `ENGINE_GATE_CODES`, `ReworkReply`, `ReworkOrder`, `record_supersedes`, and the `rework_order` signal.
- The prompt text of every other spec, and `clutch/specs/ask/*`.

## Scope fence
- clutch/rework.py
- clutch/daemon.py
- clutch/specs/rework.md
- docs/how-clutch-works.md
- tests/integration/test_rework.py
- tests/unit/test_rework_supervise_gate.py
- tests/integration/test_rework_supervise.py

## Acceptance criteria
1. `tests/unit/test_rework_supervise_gate.py::test_split_is_refused` asserts that `supervise_findings("original", ORIGINAL, reply)`, for a `split` reply of two fresh stems, returns exactly one finding. That finding has code `supervise_edit`, message `a supervisor edit cannot split the ticket`, path `tickets/original/ticket.md`, and a paved road containing `` `clutch confirm original` `` and `` `clutch reject original` ``. Ruled out: `[]`, which would let a split reach review.
2. `tests/unit/test_rework_supervise_gate.py::test_update_refusals` is parametrized over three `update` proposals of the two-criterion constant `ORIGINAL`. Each asserts the exact one-element list of messages. The text equal to `ORIGINAL` gives `the proposal does not change the ticket text`. A reworded `## Goal / Why` gives ``the proposal changes `## Goal / Why` ``. A copy with criterion 2 deleted gives `the proposal drops acceptance criteria (1 of 2 remain)`. Ruled out: `[]` in any case, and a whitespace-only Goal difference counted as a change (a fourth case adds a trailing blank line to the Goal and asserts `[]`).
3. `tests/unit/test_rework_supervise_gate.py::test_allowed_edits_pass` asserts `supervise_findings` returns `[]` for an `update` that adds a `## Scope fence` bullet, adds a `## Context` bullet, rewords `## Scope in / Scope out`, and rewords criterion 2 while keeping two criteria, and for an `escalate` reply. Ruled out: a gate that refuses any text change, or one that compares criteria text instead of count.
4. `tests/integration/test_rework_supervise.py::test_supervise_block_renders_trigger_and_lessons` calls `rework` with `supervise=Supervise("premise_bounce cap spent", ("Fence tests/x.py",))` and the script `[order()]` (escalate). It asserts the rework request's rendered prompt contains `{"lessons": ["Fence tests/x.py"], "trigger": "premise_bounce cap spent"}` between `<<clutch-data:begin supervise>>` and `<<clutch-data:end supervise>>`. A second call without `supervise` renders `none` in that block. Ruled out: lessons missing from the prompt, and a block that is absent outside supervisor mode.
5. `tests/integration/test_rework_supervise.py::test_gate_refusal_ends_before_review` is parametrized over the four refusals: split, unchanged, Goal changed, criterion dropped. Each runs `rework` in supervisor mode with `ctx.driver.retry_cap = 1` and a one-item script holding the refused reply. It asserts the outcome is `gate_failed`, every finding's code is `supervise_edit`, the FakeLLM recorded exactly one request (surface `rework`), `result.artifact` equals `ReworkReply.model_validate_json` of the refused reply, no `rework_order` signal was journaled, and `ticket_bytes(ctx)` is unchanged. Ruled out: a re-prompt (a second `rework` request), a `requisition_review` request, and `artifact is None`.
6. `tests/integration/test_rework_supervise.py::test_allowed_update_is_reviewed` runs supervisor mode with an `update` that only rewords `## Scope in / Scope out`, scripted `[order("update", ...), requisition()]`. It asserts the outcome is `ok`, `result.artifact` is a `ReworkOrder` with action `update`, exactly one `requisition_review` request was made, and one `rework_order` signal was journaled. Ruled out: the gate refusing an allowed edit.
7. `tests/integration/test_rework_supervise.py::test_review_snag_returns_the_last_proposal` runs the same allowed `update` with `ctx.driver.retry_cap = 0` and the script `[order("update", ...), requisition("snag")]`. In supervisor mode it asserts `gate_failed`, `result.artifact` equals that reply, and `SNAG.message` among the findings' messages. Without `supervise`, the same script asserts `gate_failed` and `result.artifact is None`. Ruled out: the proposal lost on a review snag, and a changed contract outside supervisor mode.
8. `tests/integration/test_rework_supervise.py::test_apply_rework_forwards_supervise` creates the directory `ctx.worktree("original")`. It monkeypatches `clutch.daemon.rework` with a recorder that returns `StageResult(outcome="gate_failed", artifact=None, findings=[SNAG], cost=Cost())`, then calls `daemon.apply_rework` twice: once with `supervise=S` and once without. It asserts the recorder saw `supervise is S` and then `supervise is None`, and that both results are that `gate_failed` result. Ruled out: `apply_rework` dropping or defaulting the input.
9. `./dev.py test tests/integration/test_rework.py` exits 0 with only the three edits `## Scope in / Scope out` names in `test_rework_spec_render_and_driver`. So `test_rework_refuses_invalid_or_unreviewed_orders` still asserts `result.artifact is None` for every non-supervisor `gate_failed` case, unedited.
10. The `uv run python -c` command in `## Verification` exits 0. It asserts that `load_spec(...)` of `clutch/specs/rework.md` lists `supervise` among its inputs, that `lint_spec` of the file returns `[]`, and that the file contains `Outside a supervisor edit, change content only to narrow or divide the original goal.`. Ruled out: a spec without the block or with the old narrowing sentence unqualified.
11. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_rework_supervise_gate.py
./dev.py test tests/integration/test_rework_supervise.py
./dev.py test tests/integration/test_rework.py tests/integration/test_retro.py tests/integration/test_daemon_composition.py tests/integration/test_watchdog_activation.py tests/unit/test_rework_review_prior.py
uv run python -c "from pathlib import Path; from clutch.specs import load_spec, lint_spec; text = Path('clutch/specs/rework.md').read_text(); assert 'supervise' in load_spec(text).inputs; assert lint_spec(text) == []; assert 'Outside a supervisor edit, change content only to narrow or divide the original goal.' in text"
./dev.py test
```

## Definition of rejected
The branch is rejected if supervisor mode allows a `split`; if the allowed-edit gate runs after a requisition review call or lets the driver re-prompt; if a non-supervisor Rework result, render (beyond the `none` block), finding, or signal changes; if `clutch/runner.py`, `clutch/caps.py`, `clutch/config.py` or `clutch/drain.py` changes; if a new config field, verb, journal signal, or `ENGINE_GATE_CODES` member is added; or if any existing assertion other than the three named in `## Scope in / Scope out` is changed or weakened.

## Time budget
- expected: 70m
- stuck: 150m
