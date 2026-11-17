---
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: rejected
---

## Depends on
- closed-sets-remaining

## Context
- clutch/stats.py
- clutch/specs/__init__.py::ENGINE_LLM_SURFACES
- clutch/providers.py::WRITING_SURFACES
- clutch/policy.py::BASELINED_SURFACES

## Goal / Why
Roadmap row 128, first slice: surfaces. Four modules each define a surface-name set as separate literals: `stats.SURFACES`, `specs.ENGINE_LLM_SURFACES`, `providers.WRITING_SURFACES` and `policy.BASELINED_SURFACES`. After this ticket `clutch/specs/__init__.py` is the only module that defines a surface-name set. It defines the full set `ENGINE_LLM_SURFACES` and the three subsets `STATS_SURFACES`, `WRITING_SURFACES` and `BASELINED_SURFACES` (a tuple, to keep its order). It calls `check_surface_subset` at import for each subset. `stats.py`, `providers.py` and `policy.py` take their subsets from there and keep their current module attribute names. A misspelt or removed surface then fails at import, and adding a surface to a set is one file edit. No subset's members change. Surface-name literals used inside function bodies, such as `'implement'` and `'review'` in `stats.py` and `providers.py`, are not set definitions and stay as they are.

The other eight sets of row 128 (failed-attempt terminals, spike kinds, box classes, triage verdicts, control verbs, ask kinds, finding codes, conduct-file routing) are out of this ticket. Each gets a later slice.

## Scope in / Scope out
In: in `clutch/specs/__init__.py`, add `STATS_SURFACES`, `WRITING_SURFACES` and `BASELINED_SURFACES` beside `ENGINE_LLM_SURFACES`. Also add the callable `check_surface_subset(name: str, subset: Collection[str]) -> None`, which raises `ValueError` when `set(subset) - ENGINE_LLM_SURFACES` is non-empty. The module calls it at import once for each of the three subsets. In `stats.py`, `providers.py` and `policy.py`, replace the module-level literal definition with an import from `clutch.specs`, so that `stats.SURFACES`, `providers.WRITING_SURFACES` and `policy.BASELINED_SURFACES` still resolve with the same value and type. `clutch/specs/__init__.py` imports neither `stats`, `providers` nor `policy`, and `providers.py` and `policy.py` already import it, so no import cycle arises. `stats.py` takes the new import at module level.

Out: every other set of row 128; function-body surface literals in `stats.py` and `providers.py`; `clutch/help.py`, `clutch/gates.py`, `clutch/observe.py`, `clutch/baseline.py`, `clutch/driver.py` and `hosts/fixture/scaffold.py` with their own surface literals; any change to which surfaces a subset holds; any compat alias or second spelling. Existing tests in `tests/integration/test_closed_sets.py` already pin these values and stay untouched.

## Scope fence
- clutch/stats.py
- clutch/specs/__init__.py
- clutch/providers.py
- clutch/policy.py
- tests/unit/test_closed_sets_surfaces.py
- tests/integration/test_closed_sets_surfaces.py

## Acceptance criteria
1. `tests/unit/test_closed_sets_surfaces.py::test_subsets_within_owner`: `stats.SURFACES`, `providers.WRITING_SURFACES` and `set(policy.BASELINED_SURFACES)` are each a subset of `specs.ENGINE_LLM_SURFACES`, not a set holding a name the owner lacks.
2. `tests/unit/test_closed_sets_surfaces.py::test_subset_values_unchanged`: `stats.SURFACES == {"requisition_review", "implement", "review", "diagnose", "rework", "retro"}`, `providers.WRITING_SURFACES == frozenset({"implement"})` and `policy.BASELINED_SURFACES == ("review", "author")`, not a changed membership, type or order.
3. `tests/integration/test_closed_sets_surfaces.py::test_no_second_spelling` (an `ast` scan of `clutch/stats.py`, `clutch/providers.py` and `clutch/policy.py`): no module-level assignment in these files holds a string constant that is a member of `specs.ENGINE_LLM_SURFACES`. Function bodies, test code and docstrings are not scanned. The pre-change tree fails this test.
4. `tests/unit/test_closed_sets_surfaces.py::test_owner_rejects_stray_subset`: `specs.check_surface_subset("x", {"not_a_surface"})` raises `ValueError`, not returns `None`; `specs.check_surface_subset("x", {"implement"})` returns `None`.
5. `./dev.py test tests/unit tests/integration/test_closed_sets.py tests/integration/test_closed_sets_single_owner.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_closed_sets_surfaces.py tests/integration/test_closed_sets_surfaces.py
./dev.py test tests/unit tests/integration/test_closed_sets.py tests/integration/test_closed_sets_single_owner.py
```

## Definition of rejected
A module-level assignment in `stats.py`, `providers.py` or `policy.py` still holds a surface-name string; a subset's members, type or order change; a shim keeps an old name beside a new one; any set from the other eight of row 128 is touched; or a test is weakened instead of updated.

## Time budget
- expected: 30m
- stuck: 60m
