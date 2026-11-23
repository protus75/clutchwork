---
state: draft
source: box:suggestion
priority: P1
kind: feature
---

## Depends on
none

## Context
- clutch/roadmap.py::plan_path
- clutch/roadmap.py::choose
- tests/unit/test_roadmap_table.py::test_plan_path

## Goal / Why
`plan_path` accepts only `docs/<name>-plan.md`, so an Owner naming the nested plan `docs/document-agent/plan.md` never resolves. `choose` then turns the `None` into a Wait (`no unique plan for ...`) and every document-agent roadmap row stays held, which blocks the 0.7.0 release through the roadmap path. After this ticket `plan_path` also resolves `docs/<dir>/plan.md`, and `choose` treats a document-agent row as ready instead of waiting on `no unique plan`. The single-match rule is unchanged: zero or several candidates still return `None`.

## Boundary contract
### Roadmap plan resolver
- disposition: extend
- owner: clutch/roadmap.py (`plan_path`)
- consumers: `choose` in clutch/roadmap.py and the acceptance plan lookup in clutch/acceptance.py
- observable change: an Owner whose first word equals the whole directory name `<dir>`, or is a hyphen-separated word of `<dir>`, resolves to `docs/<dir>/plan.md` when exactly one candidate (flat or nested) matches
- compatibility: existing flat `docs/*-plan.md` and `roadmap` resolutions return the same results; ambiguity or no match still returns `None`
- acceptance: unit test over an in-memory file set
- tests: tests/unit/test_roadmap_nested_plan.py
- post-merge source of truth: clutch/roadmap.py

## Scope in / Scope out
Scope in: in `clutch/roadmap.py`, `plan_path` also counts files matching `docs/<dir>/plan.md` (single directory level) as candidates. A nested candidate matches when the Owner's first word equals the whole directory name `<dir>` or is one of the hyphen-separated parts of `<dir>`; flat candidates keep their existing rule. The existing exactly-one-match rule applies across flat and nested candidates together. The `choose` Wait paved-road text names both `docs/*-plan.md` and `docs/<name>/plan.md`. Add a new unit test file.
Scope out: roadmap row edits (the driver owns them), documentation, and the existing `tests/unit/test_roadmap_table.py` (its expectations stay valid and unchanged).

## Scope fence
- clutch/roadmap.py
- tests/unit/test_roadmap_nested_plan.py

## Acceptance criteria
1. `plan_path("document plan 1", {"docs/document-agent/plan.md", "docs/roadmap.md"})` returns `"docs/document-agent/plan.md"`, not `None`; checked by `./dev.py test tests/unit/test_roadmap_nested_plan.py`.
2. `plan_path("document-agent plan", files)` with the same file set also returns `"docs/document-agent/plan.md"` (first word equals the whole directory name), not `None`; checked by `./dev.py test tests/unit/test_roadmap_nested_plan.py`.
3. With both `docs/document-agent/plan.md` and `docs/document-extra-plan.md` present, `plan_path("document plan", files)` returns `None` (ambiguous), not either path; checked by `./dev.py test tests/unit/test_roadmap_nested_plan.py`.
4. `choose` over a parsed row whose Owner is `document-agent plan` with files containing `docs/document-agent/plan.md` yields the row as ready and no Wait whose reason starts with `no unique plan`; checked by `./dev.py test tests/unit/test_roadmap_nested_plan.py`.
5. Existing flat resolutions still hold, including `plan_path("roadmap (decision 4)", files) == "docs/roadmap.md"`; checked by `./dev.py test tests/unit/test_roadmap_table.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_nested_plan.py tests/unit/test_roadmap_table.py
```

## Definition of rejected
A branch that resolves nested plans by a second parallel lookup path, loosens the single-match rule, or edits `docs/roadmap.md` or existing tests is thrown away.

## Time budget
- expected: 10m
- stuck: 20m
