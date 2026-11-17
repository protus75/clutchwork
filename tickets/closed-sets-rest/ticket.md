---
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: draft
---

## Depends on
- closed-sets-remaining

## Context
- clutch/stats.py
- clutch/specs/__init__.py
- clutch/providers.py
- clutch/policy.py

## Goal / Why
Roadmap row 128, first slice: surfaces. Today four modules spell surface names as separate literals: `stats.SURFACES`, `specs.ENGINE_LLM_SURFACES`, `providers.WRITING_SURFACES` and `policy.BASELINED_SURFACES`. After this ticket `clutch/specs/__init__.py` owns the one full set, `ENGINE_LLM_SURFACES`. The other three become named subsets that name each surface string only as a member of that owner, so adding a surface is one edit. The set of members in each subset does not change.

The other eight sets of row 128 (failed-attempt terminals, spike kinds, box classes, triage verdicts, control verbs, ask kinds, finding codes, conduct-file routing) are out of this ticket. Each is unified in a later slice, so none is lost.

## Scope in / Scope out
In: the four definitions above and their importers. A subset is derived from or checked against `ENGINE_LLM_SURFACES` in `specs/__init__.py`. Import placement avoids an import cycle: if `stats.py`, `providers.py` or `policy.py` cannot import `clutch.specs` at module level, import it inside the function that uses it. Each module keeps its existing set name and value type, so no call site changes.

Out: every other set of row 128; `clutch/help.py`, `clutch/gates.py`, `clutch/observe.py` and their surface literals; any change to which surfaces a subset holds; any compat alias.

## Scope fence
- clutch/stats.py
- clutch/specs/__init__.py
- clutch/providers.py
- clutch/policy.py
- tests/unit/test_closed_sets_surfaces.py

## Acceptance criteria
1. `tests/unit/test_closed_sets_surfaces.py::test_subsets_within_owner`: `stats.SURFACES`, `providers.WRITING_SURFACES` and `set(policy.BASELINED_SURFACES)` are each a subset of `specs.ENGINE_LLM_SURFACES`, not a set holding a name the owner lacks.
2. `tests/unit/test_closed_sets_surfaces.py::test_subset_values_unchanged`: `stats.SURFACES == {"requisition_review", "implement", "review", "diagnose", "rework", "retro"}`, `providers.WRITING_SURFACES == frozenset({"implement"})` and `policy.BASELINED_SURFACES == ("review", "author")`, not a changed membership or order.
3. `tests/unit/test_closed_sets_surfaces.py::test_no_second_spelling` (an `ast` scan of `clutch/stats.py`, `clutch/providers.py` and `clutch/policy.py`): none assigns a module-level set, tuple or frozenset literal that holds two or more surface-name strings. The pre-change tree fails this test.
4. `./dev.py test tests/unit tests/integration/test_closed_sets.py tests/integration/test_closed_sets_single_owner.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_closed_sets_surfaces.py
./dev.py test tests/unit tests/integration/test_closed_sets.py tests/integration/test_closed_sets_single_owner.py
```

## Definition of rejected
A second full spelling of the surface set remains in `stats.py`, `providers.py` or `policy.py`; a subset's members change; an alias or shim keeps an old name; any set from the other eight of row 128 is touched; or a test is weakened instead of updated.

## Time budget
- expected: 35m
- reason: the four definitions share one owner and one new test file; splitting would make the owner edit and its subsets land separately and leave a second spelling in between.
- stuck: 70m
