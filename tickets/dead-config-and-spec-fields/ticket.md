---
state: draft
source: box:roadmap_row
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/config.py::ReviewSurface
- clutch/config.py::Review
- clutch/config.py::Caps
- clutch/specs/__init__.py::SpecMeta
- clutch/specs/__init__.py::_parse_spec
- clutch/requisition.py
- clutch/docs/host-contract.md
- docs/how-clutch-works.md

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Four inert items are gone, so the code, the specs and the docs describe only what the engine reads. First, `caps.poison` (default 2) is read by nothing. Second, `review.trigger_map` is accepted by config and read by nothing. Third, `ReviewSurface` and the `review.surfaces` field exist only so config load can refuse any declared entry. Fourth, the spec frontmatter fields `consumes`, `emits` and `gates` are never read by the engine. Of these, only `gates` is checked, against `ENGINE_GATE_CODES`, and nothing acts on the result. Fifth, `requisition_review.md` declares a `context` input that `clutch/requisition.py` fills with the constant `included in render`. Removing them means a host author cannot set a knob that does nothing, and a spec author cannot fill in fields that mean nothing. This is roadmap row 25. Spec frontmatter is resolved by removal, not by wiring, because no consumer exists and the minimum change is to delete the fields.

## Scope in / Scope out
Scope in:
- `clutch/config.py`: delete the `poison` field from the caps model. Delete the `trigger_map` field from `Review`. Delete the `ReviewSurface` class and the `surfaces` field from `Review`. Delete the `review.surfaces` refusal in the config loader; an unknown key is then refused by the existing strict model. Leave `Trigger`, which another model still uses.
- `clutch/specs/__init__.py`: delete `consumes`, `emits` and `gates` from `SpecMeta`. Delete the per-gate vocabulary loop in `_parse_spec` and the `gate_codes` parameter of `lint_spec`, `load_spec` and `_parse_spec`. Delete the import of `ENGINE_GATE_CODES` if nothing else in the file uses it. Change the frontmatter paved road to name exactly the fields `llm_surface`, `tier`, `effort`, `version`. `ENGINE_GATE_CODES` itself stays in `clutch/gates.py`; `tickets.py` and `scorecard.py` still read it.
- The eight prompt specs `clutch/specs/{author,diagnose,implement,requisition_review,retro,review,rework,triage}.md`: remove the `consumes`, `emits` and `gates` frontmatter lines. In `requisition_review.md` also remove the `context` data block, which is the begin line, the `{{context}}` line and the end line. Version rule: only `requisition_review.md` changes body text, so it bumps `version` to the next minor above the version on main. The other seven keep their versions because their bodies do not change.
- `clutch/requisition.py`: remove the `"context": "included in render"` entry from the render inputs.
- `hosts/fixture/config.yaml`: remove the `surfaces: []` and `trigger_map: {}` lines.
- `clutch/docs/host-contract.md`: update the review config block (the `surfaces` and `trigger_map` lines), the `ReviewSurface` schema block, both `caps` examples and defaults lines (drop `poison`), the paragraph that says `review.surfaces` is refused, and the sentence that says `review.trigger_map` is accepted and read by nothing. Add nothing else.
- `docs/how-clutch-works.md`: drop the `review.surfaces` refusal text, the `trigger_map` sentence, the `poison` row of the caps table, and the matching clause in the config inventory row.
- Tests that name a removed item are updated to the new shape. They assert only what stays, and no removed-key test is added beyond one refusal check (criterion 2).
Scope out: `ENGINE_GATE_CODES`, the gate machinery, the `LlmStage.emits` and `LlmStage.gates` runtime fields (they are code, not spec frontmatter), the `Trigger` type, and every other spec body line.

## Scope fence
- clutch/config.py
- clutch/specs/__init__.py
- clutch/specs/author.md
- clutch/specs/diagnose.md
- clutch/specs/implement.md
- clutch/specs/requisition_review.md
- clutch/specs/retro.md
- clutch/specs/review.md
- clutch/specs/rework.md
- clutch/specs/triage.md
- clutch/requisition.py
- hosts/fixture/config.yaml
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/integration/test_config.py
- tests/integration/test_host_contract.py
- tests/integration/test_daemon_config.py
- tests/integration/test_fixture_host.py
- tests/integration/test_requisition.py
- tests/integration/test_rework.py
- tests/unit/test_specs.py

## Acceptance criteria
1. `Caps().model_dump()` has no `poison` key, and a config that sets `caps: {poison: 2}` is refused at load; checked by `./dev.py test tests/integration/test_config.py`, which fails if `poison` is still accepted.
2. A config with `review: {trigger_map: {}}` or `review: {surfaces: []}` is refused at load as an unknown key, not accepted; `ReviewSurface` no longer exists in `clutch.config`. Checked by `./dev.py test tests/integration/test_config.py`.
3. `load_spec` of a spec whose frontmatter carries `consumes`, `emits` or `gates` returns a `spec_frontmatter` finding, and a spec with only `llm_surface`, `tier`, `effort`, `version` loads with no finding. Checked by `./dev.py test tests/unit/test_specs.py`, which fails if the old fields are still tolerated or still required.
4. Every spec under `clutch/specs/*.md` loads with `load_spec`, and `load_spec(requisition_review.md).inputs` equals `("ticket", "render", "coverage_dependents", "sibling_tickets", "prior_review", "retry_findings")`, with no `context` entry. Checked by `./dev.py test tests/integration/test_requisition.py`.
5. The requisition review prompt rendered by `clutch/requisition.py` contains no `begin context` delimiter; checked by `./dev.py test tests/integration/test_requisition.py tests/integration/test_author.py`.
6. `clutch/docs/host-contract.md` and `docs/how-clutch-works.md` contain none of the strings `poison:`, `trigger_map` or `ReviewSurface`; checked by `./dev.py test tests/integration/test_host_contract.py`, which compares the inventory to the config models.
7. The hot-path suites that load config and specs still pass: `./dev.py test tests/integration/test_daemon_config.py tests/integration/test_fixture_host.py tests/integration/test_rework.py`.

## Verification
```
./dev.py test tests/integration/test_config.py tests/integration/test_host_contract.py tests/integration/test_daemon_config.py tests/integration/test_fixture_host.py tests/integration/test_requisition.py tests/integration/test_rework.py tests/integration/test_author.py tests/unit/test_specs.py
```

## Definition of rejected
The branch is rejected if any removed field is still accepted by config or spec loading, if it deletes or edits `ENGINE_GATE_CODES` or the gate machinery, if it adds a compatibility shim that tolerates the old keys, if it edits a spec body other than removing the `context` block, or if the docs still describe a removed item.

## Time budget
- expected: 45m
- stuck: 100m
