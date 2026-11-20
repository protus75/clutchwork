---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/retro.py::measurements
- clutch/retro.py::RetroProposal
- clutch/mergequeue.py::MergeQueue._facts
- clutch/box.py::Message
- clutch/box.py::Box.enqueue
- clutch/config.py::UnionStrategy
- tests/unit/test_retro_proposal.py
- docs/parallel-tickets-plan.md#8. Measurement

## On-demand
- clutch/specs/retro.md
- docs/how-clutch-works.md

## Goal / Why
`docs/parallel-tickets-plan.md` section 8 has a retro propose a `merge.strategies` entry or a split for any path that conflicts often, and row 48 (`status-hot-paths`) built only the table. Today nothing reads the conflicts. `clutch/mergequeue.py::MergeQueue._facts` journals one `merge_conflict_facts` signal per conflict with `conflicted_paths`, `strategy_paths` (the paths a configured `merge.strategies` entry already resolved) and `resolving_rung` (per signal, not per path) (`none`, `mechanical`, `model`, `rerun`, or the historical `rework`), and `clutch/retro.py::measurements` reads that signal only to count `integration_red_paths`. It never counts a conflicted path, the retro prompt never sees one, and `RetroProposal` has no shape that can name a path to split or to give a strategy: it accepts only prompt-spec paths or a test issue with test paths. Since the owner chose to run tickets in parallel, conflicts are the cost the plan said would show up, and the same few paths will keep costing a model resolve or a discarded rerun until someone acts on them.

After this change a retro window reports each path that conflicted at least twice, with its conflict count and how each conflict was resolved, and the retro can file a `retro_finding` that names such paths and whether to add a `merge.strategies` entry (`strategy`) or split the file (`split`). The finding goes to the Suggestion Box and Author and Triage see the action like any other retro proposal.

## Boundary contract
### Retro conflict measurement
- disposition: extend
- owner: clutch/retro.py::measurements
- consumers: `production_evidence`, `render_report` (the receipt JSON), the retro prompt's `window` block, and `clutch/scorecard.py`, which reads only `evidence["spikes"]`
- observable change: `measurements(window)` gains a `conflict_paths` list. Each row is `{"path": str, "conflicts": int, "rungs": {rung: int}}`, built from every `merge_conflict_facts` signal in the window, counting a path once per signal. A path's rung in a signal is `mechanical` when it is in that signal's `strategy_paths` (a strategy already covers it), otherwise the signal's `resolving_rung`. Rows with fewer than `CONFLICT_PATH_MIN` (2) conflicts are dropped, rows sort by conflicts descending then path ascending, and at most `CONFLICT_PATH_TOP` (10) rows are kept. A window with no such signal has `conflict_paths == []`. The existing `integration-red` spike count is unchanged.
- compatibility: every existing `measurements` key keeps its value; `tests/integration/test_status.py` compares `window.evidence` to `measurements(...)` computed by the same function, so it still holds
- acceptance: unit tests on hand-built windows rule out the wrong counts, the threshold, the cap and the ordering
- tests: `tests/unit/test_retro_conflict_paths.py`
- post-merge source of truth: `clutch/retro.py::measurements`

### Retro proposal shape
- disposition: extend
- owner: clutch/retro.py::RetroProposal, mirrored by clutch/box.py::Message
- consumers: `Retro.emit_proposals` (through `Box.enqueue`), Author (`clutch/author.py` request), Triage (`clutch/triage.py` request), and every reader of a stored `retro_finding` message
- observable change: a closed `ConflictAction = Literal["strategy", "split"]` and an optional `conflict_action` field on both models. A proposal is valid with exactly one of (a) `proposed_spec_paths`, (b) `test_issue` plus nonempty `proposed_paths`, (c) `conflict_action` plus nonempty `proposed_paths`. `Box.enqueue` takes and stores `conflict_action`. `Message` refuses `conflict_action` outside a `retro_finding`. The Author and Triage request JSON carries `conflict_action`.
- compatibility: a stored message or proposal without `conflict_action` stays valid and reads as `None`; shapes (a) and (b) validate exactly as before
- acceptance: coherence tests refuse each mixed shape on both models, and a stored message round-trips the field
- tests: `tests/unit/test_retro_conflict_paths.py`, the two request tests named in Scope
- post-merge source of truth: `clutch/box.py::ConflictAction` and `clutch/retro.py::RetroProposal`

### Retro prompt spec
- disposition: extend
- owner: clutch/specs/retro.md
- consumers: `Retro.__call__` (loads and renders it)
- observable change: the spec reads `measurements.conflict_paths` and allows the third proposal shape, with the rule for choosing `strategy` over `split`, treating `mechanical` as already handled
- compatibility: the existing two shapes and the empty-proposals reply are unchanged
- acceptance: the spec names the field and the evidence key, and its version is the next minor above main
- tests: `tests/integration/test_retro_conflict_spec.py`, plus the two version pins named in Scope
- post-merge source of truth: `clutch/specs/retro.md`

## Scope in / Scope out
Scope in:
- `clutch/retro.py`: add module constants `CONFLICT_PATH_MIN = 2` and `CONFLICT_PATH_TOP = 10`; in `measurements`, fold `CONFLICT_FACTS` signals (reading `conflicted_paths`, `strategy_paths` and `resolving_rung`) into the `conflict_paths` list described above and return it under that key (the loop already tests `body.get("kind") == CONFLICT_FACTS`; keep that test for `integration_red_paths` and count paths beside it). Add `conflict_action: ConflictAction | None = None` to `RetroProposal` and replace its `_coherent` rule with the three-shape rule: `proposed_spec_paths` xor `proposed_paths`, and when `proposed_paths` is set exactly one of `test_issue` and `conflict_action` is set, when it is empty neither is. Import `ConflictAction` from `clutch/box.py` as `TestIssue` is. Nothing else changes in this file: `emit_proposals` already forwards every dumped field to `Box.enqueue`.
- `clutch/box.py`: add `ConflictAction` beside `TestIssue`; add the `conflict_action` field to `Message`, apply the same three-shape rule in `Message._coherent`, and include `conflict_action` in the "allowed only for retro_finding" refusal. Add the `conflict_action` parameter to `Box.enqueue` and pass it to `Message`.
- `clutch/author.py` and `clutch/triage.py`: add `"conflict_action": message.conflict_action` to the request dict next to `"test_issue"`. Nothing else in either file changes.
- `clutch/specs/retro.md`: bump `version` to the next minor above the version on main. Add one short rule under the test-issue list: when `measurements.conflict_paths` lists a path, propose `conflict_action: strategy` for paths whose conflicts reached the `model` or `rerun` rung (no `merge.strategies` entry covered them) and whose content a `union` or `regenerate` entry can rebuild, and `split` for hand-written files that keep reaching the `model` or `rerun` rung; a path whose conflicts are all `mechanical` already has an entry and is never proposed; `proposed_paths` names the proposed paths. Add the third shape to `## Output format`. Keep the reply-first-character sentence and every existing rule.
- `docs/how-clutch-works.md` section 9.5 only: the paragraph beginning "The retro reads the journal" says what the retro measures, and the one beginning "scorecard, proposals" says proposals identify spec paths or test-repair paths. Add that measurements include `conflict_paths` (paths with at least two journaled merge conflicts in the window, top ten, with resolving rungs), and that a proposal may instead name conflicted paths with `strategy` (add a `merge.strategies` entry) or `split`. Change nothing else in the file.
- Version pins that name the retro spec version: `tests/integration/test_retro.py` (the `spec_version` assertion in the provenance test) and `tests/integration/test_specs_delimiter_note.py` (the `("retro", ...)` row). Each becomes the new version string. The pin in `tests/integration/test_status.py` replaces the version with a regex and needs no edit.
- Stand-in closure: `tests/unit/test_triage_tombstone_rejected.py` builds a hand-made message namespace that Triage's request now reads `conflict_action` from; add `conflict_action=None` to it. No other test builds a message stand-in that reaches these request dicts (`tests/unit/test_retro_recurrence.py::message` validates a real `Message`).
- Two request tests, one sibling each: `tests/integration/test_author.py` and `tests/integration/test_triage.py` each gain `test_conflict_proposal_request` beside the existing `test_test_proposal_request`, enqueuing a `retro_finding` with `conflict_action="split"` and `proposed_paths=["clutch/big.py"]` and asserting the rendered prompt contains `"conflict_action": "split"`. These files are not on the do-not-grow list and the helpers the tests need are local to them.

Scope out: the `integration-red` spike and its counting; `retro.spikes` kinds (no `conflict` spike kind, so `SpikeKind`, `clutch/config.py` and `tests/integration/test_config.py` stay); any retro config knob for the threshold or cap; `clutch/observe.py` and the extension's Suggestion Box detail fields (a conflict finding shows its summary and Proposed paths; the action is not a separate field there); `clutch/help.py` (no new surface); Author or Triage prompt specs; the `status` hot-paths table; editing `merge.strategies` or splitting any file (the finding only proposes).

## Scope fence
- clutch/retro.py
- clutch/box.py
- clutch/author.py
- clutch/triage.py
- clutch/specs/retro.md
- docs/how-clutch-works.md
- tests/unit/test_retro_conflict_paths.py
- tests/integration/test_retro_conflict_spec.py
- tests/unit/test_triage_tombstone_rejected.py
- tests/integration/test_retro.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_author.py
- tests/integration/test_triage.py

## Acceptance criteria
1. `tests/unit/test_retro_conflict_paths.py::test_conflict_paths_count_per_signal_and_rung` builds a window of `merge_conflict_facts` signals: path `a` in three signals (`resolving_rung` `model`, `model`, `rerun`, `strategy_paths: []`), path `b` in two signals whose `resolving_rung` is `model` but whose `strategy_paths` is `["b"]`, path `c` in one, and asserts `measurements(window)["conflict_paths"] == [{"path": "a", "conflicts": 3, "rungs": {"model": 2, "rerun": 1}}, {"path": "b", "conflicts": 2, "rungs": {"mechanical": 2}}]`. Ruled out: `b` given the signal's `model` rung instead of `mechanical`, `c` present (no threshold), `a` counted per ticket or per rung instead of per signal, and a missing `rungs` map.
2. `tests/unit/test_retro_conflict_paths.py::test_conflict_paths_cap_and_order` journals twelve paths with two conflicts each plus one path with three, and asserts the result has ten rows, the three-conflict path first, and the rest in ascending path order. Ruled out: twelve rows (no cap) and a cut that drops the busiest path.
3. `tests/unit/test_retro_conflict_paths.py::test_conflict_paths_ignore_other_signals` asserts `conflict_paths == []` for an empty window, for a window whose only signal is a `merge_conflict_facts` with `conflicted_paths: []`, and for a window holding two signals of another `kind` that each carry `conflicted_paths: ["a", "a2"]`. Ruled out: counting any signal that merely has a `conflicted_paths` key.
4. `tests/unit/test_retro_conflict_paths.py::test_integration_red_spike_unchanged` asserts a `merge_conflict_facts` signal with `integration_red_paths: ["x"]` and `conflicted_paths: ["p"]` still gives `measurements(window)["spikes"]["integration-red"] == 1` and adds no `conflict_paths` row (one conflict is under the threshold). Ruled out: the spike count changing.
5. `tests/unit/test_retro_conflict_paths.py::test_proposal_shapes_are_closed` asserts `RetroProposal.model_validate` accepts `{"fixed_failure": "f", "overcorrection_risk": "r", "conflict_action": "split", "proposed_paths": ["clutch/big.py"]}` and refuses each of: `conflict_action` without `proposed_paths`, `conflict_action` with `test_issue`, `conflict_action` with `proposed_spec_paths`, and `conflict_action: "merge"`. Ruled out: a model that accepts any mixed shape.
6. `tests/unit/test_retro_conflict_paths.py::test_message_conflict_finding_is_coherent` builds a `retro_finding` `Message` from a base dict local to the new file (shaped like `BASE` in `tests/unit/test_retro_proposal.py`) with `conflict_action="split"` and `proposed_paths` and asserts it validates, a `suggestion` message with `conflict_action` is refused, and a `Box(tmp_path / "box", LocalFileSystem()).enqueue(... conflict_action="strategy", proposed_paths=["a.txt"], ...)` stores a message whose `messages()[0].conflict_action == "strategy"`. Ruled out: the field dropped by `enqueue`, and `None` read back.
7. `tests/integration/test_retro_conflict_spec.py::test_retro_spec_names_conflict_shape` loads `clutch/specs/retro.md` through `load_spec` (no findings) and asserts its text contains `conflict_paths`, `conflict_action`, `strategy` and `split`, that it also contains `mechanical` (stated as already handled), and that `meta.version` is not `"1.5"`. Ruled out: a spec that was bumped but never mentions the shape.
8. `./dev.py test tests/integration/test_author.py::test_conflict_proposal_request tests/integration/test_triage.py::test_conflict_proposal_request` exits 0: each rendered prompt contains `"conflict_action": "split"`. Ruled out: the field left out of either request.
9. `./dev.py test tests/integration/test_retro.py tests/integration/test_specs_delimiter_note.py tests/integration/test_status.py tests/unit/test_retro_proposal.py tests/unit/test_triage_tombstone_rejected.py` exits 0 with the two version pins rewritten to the new version.
10. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_retro_conflict_paths.py tests/integration/test_retro_conflict_spec.py
./dev.py test tests/integration/test_author.py tests/integration/test_triage.py
./dev.py test tests/integration/test_retro.py tests/integration/test_specs_delimiter_note.py tests/integration/test_status.py tests/unit/test_retro_proposal.py tests/unit/test_triage_tombstone_rejected.py
./dev.py test
```

## Definition of rejected
The branch is rejected if it adds a config knob, flag or spike kind for the threshold, if it makes the engine write `merge.strategies` or split a file, if it changes the `integration-red` spike count or any existing `measurements` key, if it changes how shapes (a) and (b) validate, if it leaves the retro spec version unbumped or states a literal old-to-new bump, if it adds new tests to an existing hot test file, or if it hand-edits a generated file.

## Time budget
- expected: 45m
- stuck: 90m
- reason: one closed vocabulary threaded through one model pair and two request dicts, with a measurement and a spec change; splitting would leave a field no producer or consumer uses.
