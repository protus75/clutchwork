---
state: confirmed
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
- clutch/roadmap.py::gates
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_roadmap_release_boundary.py
- tests/integration/test_roadmap_start_gates.py
- tests/integration/test_roadmap_ship.py

## On-demand
- docs/roadmap.md
- docs/antigravity-plan.md
- docs/document-agent/plan.md
- docs/journal-sql-refactor-plan.md
- docs/stage-panels-plan.md

## Goal / Why
Replaces the rejected `roadmap-align-pypi-versions` and `roadmap-release-slot-shift`.

Align `docs/roadmap.md` release headings and `clutch/roadmap.py::current_release` 1:1 with the PyPI version `clutch release ship` actually bumps to and tags.

Today `clutch/roadmap.py::current_release` maps `pyproject.toml` `<major>.<minor>.<patch>` to `<major>.<minor>.0` (`0.6.1` -> `0.6.0`), while `clutch release ship` gates `current_release(repo)` and then bumps `--minor` (`0.6.1` -> `v0.7.0`). Because `v0.3.0` was tagged at the start of the first roadmap phase, all six release sections in `docs/roadmap.md` (`0.3.0`, `0.4.0`, `0.5.0`, `0.6.0`, `0.7.0 (conditional)`, `0.8.0`) are off by one minor from the PyPI release they ship. Returning `f"{parts[0]}.{int(parts[1]) + 1}.0"` from `current_release` and shifting all six release sections (`0.3.0..0.8.0` -> `0.4.0..0.9.0`) makes every section match the PyPI release it ships, while keeping existing and phase-opening `--since` git tags (`v0.3.0`, `v0.4.0`, `v0.6.0`, `v0.7.0`, `v0.8.0`) unchanged so active and future release `start` blocks match real tags on `main`.

## Boundary contract

### Current release version mapping
- disposition: replace
- owner: clutch/roadmap.py::current_release
- consumers: clutch/roadmap.py::author_ahead, clutch/roadmap.py::status, clutch/__main__.py::handle_ship
- observable change: `current_release(repo)` returns the next minor release `f"{parts[0]}.{int(parts[1]) + 1}.0"` above `pyproject.toml` (for example, `"0.3.0"` -> `"0.4.0"`, `"0.3.1"` -> `"0.4.0"`, `"0.6.1"` -> `"0.7.0"`, `"2.10.4"` -> `"2.11.0"`) instead of `<major>.<minor>.0`, matching the minor version that `clutch release ship` bumps to and tags. Missing, malformed, or non-numeric `pyproject.toml` versions still return `None`.
- compatibility: breaking change to `current_release()` return values; all callers, pinned unit and integration tests (`tests/unit/test_roadmap_release_boundary.py`, `tests/integration/test_roadmap_start_gates.py`, `tests/integration/test_roadmap_ship.py`), `docs/roadmap.md`, `docs/how-clutch-works.md`, and active plan docs migrate in this change.
- acceptance: `tests/unit/test_roadmap_release_boundary.py` proves `current_release` returns `<major>.<minor+1>.0` (and fails if `<major>.<minor>.0` is returned) and that `status` and `author_ahead` pass that value to `choose()`; `tests/integration/test_roadmap_table.py`, `tests/integration/test_roadmap_start_gates.py`, and `uv run clutch roadmap status` verify `docs/roadmap.md` parses cleanly with `0.4.0..0.9.0`.
- tests: `tests/unit/test_roadmap_release_boundary.py`, `tests/integration/test_roadmap_table.py`, `tests/integration/test_roadmap_start_gates.py`, and `tests/integration/test_roadmap_ship.py`
- post-merge source of truth: `clutch/roadmap.py::current_release` and `docs/roadmap.md`

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py`: change `current_release(repo)` to return `f"{parts[0]}.{int(parts[1]) + 1}.0"`; nothing else changes there.
- `docs/roadmap.md`: shift all six release slots by +1 minor (`0.3.0` -> `0.4.0`, `0.4.0` -> `0.5.0`, `0.5.0` -> `0.6.0`, `0.6.0` -> `0.7.0`, `0.7.0` -> `0.8.0`, `0.8.0` -> `0.9.0`) in Section 1 (intro prose, release table, and Section 1.1), Section 8 headings (`### 0.4.0`, `### 0.4.0, last group: the roadmap driver`, `### 0.5.0`, `### 0.6.0`, `### 0.7.0`, `### 0.8.0 (conditional)`, `### 0.9.0`), `start` and `gate` `--release` and `roadmap accept` arguments, row `200` stem (`release-audit-060` -> `release-audit-080` and `"recurred in 0.7.0"` -> `"recurred in 0.8.0"` so `_is_release_audit` matches `0.8.0`), and row `86` text (`0.8.0's ship gate` -> `0.9.0's ship gate`). Keep all `--since` git tags unchanged (`v0.3.0`, `v0.4.0`, `v0.6.0`, `v0.7.0`, `v0.8.0`) because `v0.3.0..v0.6.1` are real git tags on `main` and `v0.7.0` / `v0.8.0` will be created when `0.7.0` / `0.8.0` ship. Preserve all existing row numbers, merged strikes, historical ticket stems, and dated Section 6 decisions; add or remove no `start` or `gate` block.
- `docs/how-clutch-works.md`: update the `roadmap author [--ahead N]` row in section 2.1 to state that the current release is the next minor version above `pyproject.toml` (`<major>.<minor+1>.0`).
- `docs/antigravity-plan.md`, `docs/document-agent/plan.md`, `docs/journal-sql-refactor-plan.md`, `docs/stage-panels-plan.md`: update unshipped roadmap release-slot references to match the shifted slots (`0.6.0` -> `0.7.0`, `0.7.0` -> `0.8.0`, `0.8.0` -> `0.9.0`, and earlier dependency slot references `0.3.0..0.5.0` -> `0.4.0..0.6.0`; in `docs/antigravity-plan.md`, align phase descriptions so phase `0.6.0` shipped as `v0.6.0` and `0.6.1` drives phase `0.7.0` toward `v0.7.0`; in `docs/journal-sql-refactor-plan.md`, shift `0.6.0` -> `0.8.0` and `0.7.0` -> `0.9.0` with `v0.7.0` opening `0.8.0` and `v0.8.0` opening `0.9.0`).
- `tests/unit/test_roadmap_release_boundary.py`: update `test_current_release` to assert `"0.3.0"` -> `"0.4.0"`, `"0.3.1"` -> `"0.4.0"`, `"0.6.1"` -> `"0.7.0"`, `"2.10.4"` -> `"2.11.0"` (failing if `<major>.<minor>.0` is returned), and update `test_callers_pass_the_current_release` so `pyproject.toml` `"1.9.0"` selects `2.0.0` (`next: n-nine`) and `"1.0.0"` passes `"1.1.0"` to `choose()`.
- `tests/integration/test_roadmap_start_gates.py`: update `test_repository_start_and_ship_blocks` so `roadmap.gates(text, "start")` equals `{"0.5.0": (("uv", "run", "clutch", "roadmap", "merged", "closed-sets-single-owner", "active-slot-single-owner", "merge-admission-single-owner"),), "0.7.0": (("uv", "run", "clutch", "roadmap", "merged", "--release", "0.6.0", "--since", "v0.6.0", "--at-least", "1"),), "0.8.0": (("uv", "run", "clutch", "roadmap", "merged", "--release", "0.7.0", "--since", "v0.7.0", "--at-least", "1"),), "0.9.0": (("uv", "run", "clutch", "roadmap", "merged", "--release", "0.8.0", "--since", "v0.8.0", "--at-least", "1"),)}` and `set(roadmap.gates(text, "gate")) == {"0.4.0", "0.5.0", "0.6.0", "0.7.0", "0.8.0", "0.9.0"}`.
- `tests/integration/test_roadmap_ship.py`: update the fixture roadmap headings (`1.0.0` -> `1.1.0`, `1.1.0` -> `1.2.0`) and expected `gate` / `roadmap_gate` release assertions (`1.0.0` -> `1.1.0`, `1.1.0` -> `1.2.0`) so `pyproject.toml` `"1.0.0"` gates `1.1.0`, tags `v1.1.0`, and fails `1.2.0`.

Scope out:
- Do not edit `pyproject.toml`, `uv.lock`, past changelog entries, the frozen bootstrap design record, `.clutch/journal/`, git tags, or historical `tickets/` directories.
- Do not change `clutch/release.py` or `clutch release ship` / `clutch release bump` behavior.
- Do not add or remove any `start` or `gate` block in `docs/roadmap.md`.

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
- tests/integration/test_roadmap_ship.py

## Acceptance criteria
1. `clutch/roadmap.py::current_release` returns `"0.4.0"` for `0.3.0` and `0.3.1`, `"0.7.0"` for `0.6.1`, and `"2.11.0"` for `2.10.4` (never `"0.3.0"`, `"0.6.0"`, or `"2.10.0"`), and returns `None` for missing or invalid `pyproject.toml`, verified by `./dev.py test tests/unit/test_roadmap_release_boundary.py`.
2. `clutch/roadmap.py::status` and `clutch/roadmap.py::author_ahead` pass the next-minor `current_release` value to `choose()` (passing `"1.1.0"` rather than `"1.0.0"` for `1.0.0`, and selecting `2.0.0` rather than `1.0.0` for `1.9.0`), verified by `./dev.py test tests/unit/test_roadmap_release_boundary.py`.
3. `docs/roadmap.md` parses cleanly with all six shifted release sections (`0.4.0`, `0.5.0`, `0.6.0`, `0.7.0`, `0.8.0 (conditional)`, `0.9.0`, including `0.4.0, last group: the roadmap driver`), row `200` renamed `release-audit-080` matching `0.8.0`, `start` keys `{"0.5.0", "0.7.0", "0.8.0", "0.9.0"}` preserving `--since` tags `v0.6.0`, `v0.7.0`, and `v0.8.0`, and `gate` keys `{"0.4.0", "0.5.0", "0.6.0", "0.7.0", "0.8.0", "0.9.0"}`, verified by `./dev.py test tests/integration/test_roadmap_table.py tests/unit/test_roadmap_release_audit_order.py tests/integration/test_roadmap_start_gates.py` and `uv run clutch roadmap status`.
4. `tests/integration/test_roadmap_ship.py` aligns its fixture roadmap headings (`1.1.0`, `1.2.0`) and `gate`/`roadmap_gate` assertions with `current_release("1.0.0") == "1.1.0"`, verified by `./dev.py test tests/integration/test_roadmap_ship.py` and review inspection.
5. `docs/how-clutch-works.md` section 2.1 (`roadmap author [--ahead N]`) and the four active plan docs (`docs/antigravity-plan.md`, `docs/document-agent/plan.md`, `docs/journal-sql-refactor-plan.md`, `docs/stage-panels-plan.md`) match the shifted release slots (`0.4.0..0.9.0` and `<major>.<minor+1>.0`), verified by `uv run clutch roadmap status` and diff inspection during Review.

## Verification
```
./dev.py test tests/unit/test_roadmap_release_boundary.py tests/unit/test_roadmap_release_audit_order.py tests/integration/test_roadmap_table.py tests/integration/test_roadmap_start_gates.py tests/integration/test_roadmap_ship.py
uv run clutch roadmap status
```

## Definition of rejected
Any edit outside `## Scope fence`, any modification to `pyproject.toml`, `uv.lock`, past changelog entries, `.clutch/journal/`, or git tags, shifting `--since v0.6.0`/`v0.7.0`/`v0.8.0` tags instead of keeping the phase-opening tags, any test that still passes when `current_release` returns `<major>.<minor>.0`, or any `docs/roadmap.md` parse/gate/audit-stem mismatch.

## Time budget
- expected: 20m
- stuck: 40m
