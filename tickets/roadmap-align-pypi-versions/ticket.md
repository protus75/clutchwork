---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Context
- clutch/roadmap.py::current_release
- clutch/roadmap.py::choose
- clutch/roadmap.py::status
- clutch/roadmap.py::_is_release_audit
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_roadmap_release_boundary.py
- tests/integration/test_roadmap_start_gates.py

## On-demand
- docs/roadmap.md
- docs/antigravity-plan.md
- docs/document-agent/plan.md
- docs/journal-sql-refactor-plan.md
- docs/stage-panels-plan.md

## Goal / Why
Align `docs/roadmap.md` release headings and `clutch/roadmap.py::current_release` 1:1 with the PyPI version `clutch release ship` actually bumps to and tags.

Today `clutch/roadmap.py::current_release` maps `pyproject.toml` `<major>.<minor>.<patch>` to `<major>.<minor>.0` (`0.6.1` -> `0.6.0`), while `clutch release ship` gates `current_release(repo)` and then bumps `--minor` (`0.6.1` -> `v0.7.0`). Because `v0.3.0` was tagged at the start of phase `0.3.0`, every roadmap phase is off by one minor from its PyPI release (`0.5.0` shipped as PyPI `0.6.0`, and current `0.6.0` will ship as PyPI `0.7.0`). Returning `<major>.<minor+1>.0` from `current_release` and renumbering `docs/roadmap.md` (`0.3.0`..`0.7.0` -> `0.4.0`..`0.8.0`) makes every roadmap section match the PyPI release it ships.

## Boundary contract

### Current release version mapping
- disposition: replace
- owner: clutch/roadmap.py::current_release
- consumers: clutch/roadmap.py::author_ahead, clutch/roadmap.py::status, clutch/__main__.py::handle_ship
- observable change: `current_release(repo)` returns the next minor release `f"{major}.{int(minor) + 1}.0"` above `pyproject.toml` (for example, `"0.3.0"` -> `"0.4.0"`, `"0.6.1"` -> `"0.7.0"`, `"2.10.4"` -> `"2.11.0"`) instead of `<major>.<minor>.0`, matching the minor version that `clutch release ship` bumps to and tags. Missing, malformed, or non-numeric `pyproject.toml` versions still return `None`.
- compatibility: breaking change to `current_release()` return values; all callers, unit/integration tests pinning the mapping or `docs/roadmap.md` release headings, `docs/roadmap.md`, `docs/how-clutch-works.md`, and active plan docs migrate in this change.
- acceptance: `tests/unit/test_roadmap_release_boundary.py` proves `current_release` returns `<major>.<minor+1>.0` (not `<major>.<minor>.0`) and that `status` and `author_ahead` pass that value to `choose()`; `uv run clutch roadmap status` parses the renumbered `docs/roadmap.md` cleanly.
- tests: `tests/unit/test_roadmap_release_boundary.py`, `tests/integration/test_roadmap_table.py`, and `tests/integration/test_roadmap_start_gates.py`
- post-merge source of truth: `clutch/roadmap.py::current_release`

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py`: change `current_release(repo)` to return `f"{parts[0]}.{int(parts[1]) + 1}.0"`.
- `tests/unit/test_roadmap_release_boundary.py`: update `test_current_release` and `test_callers_pass_the_current_release` to assert `<major>.<minor+1>.0` (including `"0.6.1"` -> `"0.7.0"`) and fail if the unbumped minor is returned.
- `docs/roadmap.md`: renumber release sections by +1 minor (`0.3.0` -> `0.4.0`, `0.4.0` -> `0.5.0`, `0.5.0` -> `0.6.0`, `0.6.0` -> `0.7.0`, `0.7.0` -> `0.8.0`) in Section 1 (intro prose and release table), Section 8 headings (`### 0.4.0` through `### 0.8.0`), `start` and `gate` blocks (`--release` and `roadmap accept` arguments; keep git tag `--since v0.3.0`, `v0.4.0`, `v0.6.0`, `v0.7.0` values aligned with the real git tags that open each phase), and unmerged row `200` stem (`release-audit-060` -> `release-audit-070` so `_is_release_audit` matches `0.7.0`). Preserve all existing row numbers, merged strikes, historical ticket stems, and decisions.
- `docs/antigravity-plan.md`, `docs/document-agent/plan.md`, `docs/journal-sql-refactor-plan.md`, `docs/stage-panels-plan.md`: update unshipped release-slot references (`0.6.0` -> `0.7.0`, `0.7.0` -> `0.8.0`) to match the renumbered roadmap.
- `docs/how-clutch-works.md`: update the `roadmap author [--ahead N]` row in section 2.1 to state that the current release is the next minor version above `pyproject.toml` (`<major>.<minor+1>.0`).
- `tests/integration/test_roadmap_start_gates.py`: update `test_repository_start_and_ship_blocks` so its expected gate release set is `{"0.4.0", "0.5.0", "0.6.0", "0.7.0", "0.8.0"}` and its start-block check matches the renumbered `docs/roadmap.md`.

Scope out:
- Do not edit `pyproject.toml`, past changelog entries, the frozen bootstrap design record, `.clutch/journal/`, git tags, or historical `tickets/` directories.
- Do not change `clutch release ship`, `clutch release bump`, or `clutch/release.py`.

## Scope fence
- clutch/roadmap.py
- docs/roadmap.md
- docs/how-clutch-works.md
- docs/antigravity-plan.md
- docs/document-agent/plan.md
- docs/journal-sql-refactor-plan.md
- docs/stage-panels-plan.md
- tests/unit/test_roadmap_release_boundary.py
- tests/integration/test_roadmap_start_gates.py

## Acceptance criteria
1. `clutch/roadmap.py::current_release` returns `"0.4.0"` for `0.3.0` and `0.3.1`, `"0.7.0"` for `0.6.1`, and `"2.11.0"` for `2.10.4` (never the unbumped minor `"0.3.0"`, `"0.6.0"`, or `"2.10.0"`), and still returns `None` for missing or invalid `pyproject.toml`, verified by `./dev.py test tests/unit/test_roadmap_release_boundary.py`.
2. `clutch/roadmap.py::status` and `clutch/roadmap.py::author_ahead` pass the next-minor `current_release` value to `choose()`, verified by `./dev.py test tests/unit/test_roadmap_release_boundary.py`.
3. `docs/roadmap.md` parses cleanly with releases `0.4.0`, `0.5.0`, `0.6.0`, `0.7.0`, and `0.8.0` (with row `200` renamed `release-audit-070` matching `0.7.0`) and valid `start`/`gate` blocks, verified by `./dev.py test tests/integration/test_roadmap_table.py tests/integration/test_roadmap_start_gates.py` and `uv run clutch roadmap status`.
4. `docs/how-clutch-works.md` section 2.1 and the four active plan docs (`docs/antigravity-plan.md`, `docs/document-agent/plan.md`, `docs/journal-sql-refactor-plan.md`, `docs/stage-panels-plan.md`) match the renumbered release slots and pass `uv run clutch meta check docs`.

## Verification
```
./dev.py test tests/unit/test_roadmap_release_boundary.py tests/integration/test_roadmap_table.py tests/integration/test_roadmap_start_gates.py
uv run clutch roadmap status
uv run clutch meta check docs
```

## Definition of rejected
Any edit outside `## Scope fence`, any modification to `pyproject.toml` or `.clutch/journal/`, any test that still passes when `current_release` returns `<major>.<minor>.0`, or any `docs/roadmap.md` parse/gate/meta failure.

## Time budget
- expected: 20m
- stuck: 40m
