---
state: confirmed
source: box:roadmap_row
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- closed-sets-single-owner

## Context
- clutch/status.py
- clutch/stats.py
- clutch/author.py
- clutch/artifacts.py
- clutch/stages.py

## On-demand
- docs/roadmap.md

## Goal / Why
Roadmap row 112, first slice. Three closed-set homes collapse to one each, so a new terminal state or ticket kind is one edit:

- Settled and retired states: `clutch/status.py` owns `SETTLED`, a new `RETIRED = frozenset({"rejected"})` and a new `CLOSED = SETTLED | RETIRED`. `drain.RETIRED` and `stats.SETTLED` (the same name for a different set) are deleted. Every spelled-out `SETTLED | {"rejected"}` and `SETTLED | RETIRED` in `clutch/` becomes `CLOSED`, and `TERMINAL_STATES - SETTLED - {"rejected"}` or `- RETIRED` becomes `TERMINAL_STATES - CLOSED`. Sites that import `stats.SETTLED` (`checkpoint.py`, `retro.py`) import `status.CLOSED`, because the stats set already included `rejected`. `retro.py` imports `CLOSED` inside the function that uses it (the retro-due check), never at module level, because `clutch/status.py` imports `clutch.retro` at module load and a module-level import would make an import cycle.
- Kind tuple in `author.py`: the skeleton loop iterates `tickets.KINDS` instead of the literal `("feature", "chore", "bug")`. The skeleton order in the Author prompt changes to `feature, bug, chore`.
- Version split in `artifacts.py`: a new `artifacts.major(version: str) -> int` is the one parser of a spec version's major. `stages._major(spec)` and the inline split in `artifacts.py` call it.

The remaining sets of row 112 (failed-attempt terminals, surfaces, spike kinds, box classes, triage verdicts, control verbs, ask kinds, finding codes, conduct-file routing) go to a follow-up row added here, so none is lost.

## Scope in / Scope out
In: the definitions and call sites above. In `retro.py`, the `CLOSED` import goes in the function body of the retro-due check (where `SETTLED` is used now), and the module-level `from clutch.stats import SETTLED` is removed. Update `tests/integration/test_closed_sets.py` where it pins `drain.RETIRED` so it pins `status.RETIRED` and `status.CLOSED`. Add one row to the `### 0.3.0` table in `docs/roadmap.md`, numbered one above the highest row number in the parsed release tables (121, one above row 120 at the base commit), appended as that table's last row: Stem `closed-sets-rest`, Owner `roadmap`, Kind chore, P `P3`, Depends on `closed-sets-remaining`, empty Runs before, no authored marker, Content listing the nine sets left (failed-attempt terminals, surfaces, spike kinds, box classes, triage verdicts, control verbs, ask kinds, finding codes, conduct-file routing). No other part of `docs/roadmap.md` changes.

Out: `rework.py` keeps `from clutch.drain import SETTLED` (it still resolves because `drain.py` imports `SETTLED` from `status`); `roadmap.py:193` version parsing stays (it takes no `Spec`); the `tickets.py` literal; the CORE_TEMPLATE `--kind` list in `hostfiles.py`; every set in the follow-up row. No behavior change beyond the Author prompt's skeleton order. No compat alias keeps `drain.RETIRED` or `stats.SETTLED`.

## Scope fence
- clutch/status.py
- clutch/drain.py
- clutch/stats.py
- clutch/serve.py
- clutch/runner.py
- clutch/checkpoint.py
- clutch/retro.py
- clutch/scheduler.py
- clutch/observe.py
- clutch/watcher.py
- clutch/author.py
- clutch/artifacts.py
- clutch/stages.py
- docs/roadmap.md
- tests/integration/test_closed_sets.py
- tests/unit/test_closed_sets_remaining.py
- tests/integration/test_closed_sets_remaining.py

## Acceptance criteria
1. `tests/unit/test_closed_sets_remaining.py::test_closed_is_settled_plus_retired`: `status.CLOSED == frozenset({"merged", "already_satisfied", "rejected"})` and `status.RETIRED == frozenset({"rejected"})`, not a set without `rejected`.
2. `tests/unit/test_closed_sets_remaining.py::test_major`: `artifacts.major("3.12") == 3` and `artifacts.major("10.0") == 10`, not `1`.
3. `tests/unit/test_closed_sets_remaining.py::test_author_skeletons_follow_kinds`: the Author prompt's skeletons input lists one `<kind>:` block per entry of `tickets.KINDS`, in that order, not the old `feature, chore, bug` order.
4. `tests/integration/test_closed_sets_remaining.py::test_single_definitions` (an `ast` scan of `clutch/*.py`): `RETIRED` and `CLOSED` are assigned only in `status.py`; no `clutch/*.py` assigns a module-level `SETTLED` except `status.py`; no source contains the expression `SETTLED | {"rejected"}`, `SETTLED | RETIRED` or `- SETTLED - `; `stages.py` and `artifacts.py` contain no `.split(".")[0]` outside `artifacts.major`; `retro.py` has no module-level import of `CLOSED` or `SETTLED`. The pre-change tree fails this test.
5. `tests/integration/test_closed_sets_remaining.py::test_follow_up_row`: it reads `docs/roadmap.md` with `clutch.roadmap.parse(...)` and asserts on `Row` fields only, with no regex over raw row text. Exactly one row has `stem == "closed-sets-rest"`; `clutch.roadmap.release_name(row.release) == "0.3.0"`; owner is `roadmap`, kind `chore`, priority `P3`; `clutch.roadmap.depends_on(row, rows) == ("closed-sets-remaining",)` and `row.runs_before == ()`. It does not assert anything about row 112, whose text the roadmap driver rewrites when it links and strikes the row.
6. `tests/integration/test_closed_sets_remaining.py::test_no_import_cycle`: running `python -c 'import clutch.retro'` and, separately, `python -c 'import clutch.status'` in fresh subprocesses each exits 0, not an `ImportError` from a half-built module.
7. `tests/unit/test_closed_sets_remaining.py::test_retro_settled_counts_rejected`: it calls `clutch.retro.select_trigger` with an in-memory `Window` holding `state_transition` events for distinct stems ending `merged` and `rejected`, settings enabling only `settled` with `every` equal to the number of those stems, and `forced=False`; the result is `"settled"`, not `None`, which fails if `rejected` is dropped from the set `select_trigger` reads. It uses no disk or process.
8. `./dev.py test tests/integration/test_closed_sets.py tests/integration/test_author.py tests/unit/test_author.py tests/unit/test_roadmap_table.py tests/integration/test_roadmap_table.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_closed_sets_remaining.py tests/integration/test_closed_sets_remaining.py
./dev.py test tests/integration/test_closed_sets.py tests/integration/test_author.py tests/unit/test_author.py tests/unit/test_roadmap_table.py tests/integration/test_roadmap_table.py
./dev.py test tests/unit
```

## Definition of rejected
A second definition of `RETIRED`, `CLOSED` or the settled set remains in `clutch/`; `drain.RETIRED` or `stats.SETTLED` stays importable as an alias; a spec-major split stays outside `artifacts.major` in the two named files; `retro.py` imports `status` at module level; any set from the follow-up row is touched; or a test is weakened instead of updated to the new owner.

## Time budget
- expected: 55m
- reason: the nine other sets of row 112 are split into the follow-up row `closed-sets-rest`; this slice is mechanical renames across nine modules.
- stuck: 110m
