---
state: draft
source: box:suggestion
priority: P0
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- none

## Context
- clutch/roadmap.py::current_release
- clutch/roadmap.py::choose
- tests/unit/test_roadmap_release_boundary.py
- tests/integration/test_roadmap_start_gates.py

## On-demand
- docs/roadmap.md
- docs/antigravity-plan.md
- docs/document-agent/plan.md
- docs/journal-sql-refactor-plan.md
- docs/stage-panels-plan.md
- docs/annotations-index-plan.md
- docs/evidence-trail-plan.md
- docs/parallel-tickets-plan.md

## Goal / Why
Replaces the rejected `roadmap-align-pypi-versions`, whose premise (five release sections) was false: `docs/roadmap.md` has six release sections (0.3.0, 0.4.0, 0.5.0, 0.6.0, 0.7.0 conditional, 0.8.0), plus the 0.3.0 last-group heading.

Now `current_release` maps pyproject `0.6.1` to `0.6.0`, but `clutch release ship` bumps to `0.7.0`. The section being built is therefore ranked by `roadmap.choose` and gated by start-block tag checks against the wrong release. After this ticket `current_release` returns `<major>.<minor+1>.0` (`0.7.0` for pyproject `0.6.1`), and every release section, start-block `--since` tag, release-audit stem and plan-doc slot reference is shifted by one minor (0.3.0..0.8.0 become 0.4.0..0.9.0), so each section matches the PyPI release it ships. This is a pure +1 shift: no gate or start block is added or removed.

Known base discrepancy: at HEAD `test_repository_start_and_ship_blocks` asserts the gate set {0.3.0, 0.4.0, 0.5.0, 0.6.0, 0.7.0} (five), although the 0.8.0 section already has a gate block. The implementer first runs that test at base, then sets the expected gate set to the keys the shifted roadmap parses to; a section with a gate block today keeps one after the shift.

## Boundary contract

### Current release version mapping
- disposition: replace
- owner: clutch/roadmap.py::current_release
- consumers: clutch/roadmap.py status and author_ahead (via choose), clutch/__main__.py release ship gate
- observable change: `current_release(repo)` returns `f"{major}.{minor+1}.0"` (`0.3.1` -> `0.4.0`, `0.6.1` -> `0.7.0`, `2.10.4` -> `2.11.0`) instead of `<major>.<minor>.0`; a missing or malformed pyproject version still returns `None`.
- compatibility: breaking return-value change; the roadmap release headings, gate `--release` and `--since` arguments, row 200 stem, plan-doc slot references and the tests pinning them migrate in this same change.
- acceptance: unit test pins the new mapping and fails on the unbumped minor; the repo roadmap start and gate blocks parse under the shifted release keys.
- tests: tests/unit/test_roadmap_release_boundary.py, tests/integration/test_roadmap_start_gates.py
- post-merge source of truth: clutch/roadmap.py::current_release and docs/roadmap.md

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py`: change `current_release` as above; nothing else changes there.
- `docs/roadmap.md`: renumber all six release sections and headings by +1 minor (including the intro prose, the 0.3.0 last-group heading and the conditional heading); renumber every start/gate `--release` and `--since` tag by +1 minor (including `v0.8.0` -> `v0.9.0`); rename row 200 `release-audit-060` to `release-audit-080` and update its release references to match; keep row numbers, merged strikes and historical ticket stems unchanged. No gate or start block is added.
- Plan docs (`docs/antigravity-plan.md`, `docs/document-agent/plan.md`, `docs/journal-sql-refactor-plan.md`, `docs/stage-panels-plan.md`, `docs/annotations-index-plan.md`, `docs/evidence-trail-plan.md`, `docs/parallel-tickets-plan.md`): shift only references to unshipped roadmap release slots by +1 minor; leave references to shipped PyPI versions alone.
- `tests/unit/test_roadmap_release_boundary.py`: update `test_current_release` and the caller test to the new mapping.
- `tests/integration/test_roadmap_start_gates.py`, `test_repository_start_and_ship_blocks`: two edits. (a) The expected start mapping key moves from `0.4.0` to `0.5.0`; its command tuple names only stems (`closed-sets-single-owner`, `active-slot-single-owner`, `merge-admission-single-owner`) and stays unchanged. (b) The expected gate key set becomes the base-checked pure +1 shift of the keys the roadmap parses to at HEAD, which is {0.4.0, 0.5.0, 0.6.0, 0.7.0, 0.8.0, 0.9.0} because the 0.8.0 section already has a gate block (the base assertion omitting 0.8.0 is corrected here).

Scope out: `pyproject.toml`, git tags, historical `tickets/` directories, `clutch/release.py`, and `clutch release ship` behavior. The frozen bootstrap design record and the release changelog are not edited.

## Scope fence
- clutch/roadmap.py
- docs/roadmap.md
- docs/antigravity-plan.md
- docs/document-agent/plan.md
- docs/journal-sql-refactor-plan.md
- docs/stage-panels-plan.md
- docs/annotations-index-plan.md
- docs/evidence-trail-plan.md
- docs/parallel-tickets-plan.md
- tests/unit/test_roadmap_release_boundary.py
- tests/integration/test_roadmap_start_gates.py

## Acceptance criteria
1. `current_release` returns `0.7.0` for pyproject `0.6.1`, `0.4.0` for `0.3.1` and `2.11.0` for `2.10.4`, never the unbumped `0.6.0`, `0.3.0` or `2.10.0`, and `None` for a missing version, checked by `./dev.py test tests/unit/test_roadmap_release_boundary.py`.
2. In `test_repository_start_and_ship_blocks`, `roadmap.gates(text, "start")` is keyed `0.5.0` with the unchanged stem command tuple, not `0.4.0`, and `set(roadmap.gates(text, "gate"))` equals {0.4.0, 0.5.0, 0.6.0, 0.7.0, 0.8.0, 0.9.0}, not the old {0.3.0, 0.4.0, 0.5.0, 0.6.0, 0.7.0}, checked by `./dev.py test tests/integration/test_roadmap_start_gates.py`.
3. `docs/roadmap.md` still parses and row 200 carries stem `release-audit-080`, checked by `./dev.py test tests/integration/test_roadmap_table.py tests/unit/test_roadmap_release_audit_order.py`.
4. The changed documents pass `uv run clutch meta check docs`.

## Verification
```
./dev.py test tests/unit/test_roadmap_release_boundary.py tests/integration/test_roadmap_start_gates.py tests/integration/test_roadmap_table.py tests/unit/test_roadmap_release_audit_order.py
uv run clutch meta check docs
```

## Definition of rejected
Any edit outside the scope fence, any change to `pyproject.toml`, tags or the journal, any test that still passes when `current_release` returns `<major>.<minor>.0`, any added or removed gate or start block, or any `docs/roadmap.md` section, start block or gate that still names an un-renumbered release.

## Time budget
- expected: 25m
- stuck: 50m
