---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Runs before
- implement-skips-full-suites

## Context
- clutch/stages.py::check_meta
- clutch/metafill.py
- clutch/meta.py::refresh
- tests/unit/test_meta_drift_check.py
- tests/integration/test_implement_spec_meta_headers.py
- docs/how-clutch-works.md#5.1 Engine gates

## On-demand
- clutch/specs/implement.md

## Goal / Why
Since `clutch:meta` headers became required on files under `docs/`, `clutch/docs/` and `tests/` (about merge 725), about 20 failed attempts came from Implement handling those headers itself: hand-typed or duplicated blocks, empty `purpose`, or a false premise claiming a changed file's header "drifted". Check already rewrites `verified` and `hash` for every file the diff adds or changes (`check_meta` calls `meta.refresh`) but leaves an empty or stale `purpose` as a `meta_drift` finding. After this ticket Check owns the headers completely: it refreshes them and fills empty or drift-flagged purposes with the existing `meta fill` model call. The Implement prompt tells Implement never to touch a header, so the failure class has nothing left to go wrong in.

## Boundary contract
### Check metadata step
- disposition: extend
- owner: clutch/stages.py::check_meta
- consumers: the Check stage and its `meta_drift` gate
- observable change: before `meta.refresh`, `check_meta` calls `metafill.fill` once for the changed files that the existing pre-refresh `meta.check` reports as `empty_purpose`, `missing` or `drifted` (fill selects exactly those through its own `meta.check`, so it must run before refresh repairs them), using `metafill.make_ask(ctx.driver, the loaded meta spec (as `clutch meta fill` loads it), worktree, len(ctx.driver.journal.read()))`, and commits refreshed and filled files together in its existing `clutch(<stem>): meta` commit; it returns a `meta_drift` finding only for a file that stays malformed or empty after the fill
- compatibility: `meta_drift` severity, finding shape and road texts are unchanged; files outside `meta.paths`, ticket files and deleted files are still ignored; no call is made when no file needs a purpose
- acceptance: criteria 1 and 2
- tests: tests/unit/test_check_meta_fill.py and tests/unit/test_meta_drift_check.py
- post-merge source of truth: clutch/stages.py

### Implement prompt metadata rule
- disposition: replace
- owner: clutch/specs/implement.md
- consumers: Implement
- observable change: rule 5 says Implement never adds, edits, copies or refreshes a `clutch:meta` header and never runs `clutch meta refresh`, `meta fill` or `meta check` for its diff, because Check writes headers for every file the diff adds or changes; a meta finding on a file the diff does not touch still goes to `second_problems`
- compatibility: the spec's other rules are unchanged; `version` bumps to the next minor above main
- acceptance: criterion 3
- tests: tests/integration/test_implement_spec_meta_headers.py
- post-merge source of truth: clutch/specs/implement.md

## Scope in / Scope out
Scope in:
- clutch/stages.py `check_meta`: add the fill step before the existing `meta.refresh` call, then run `refresh` as today for every changed file. Import `metafill` and `load_spec` inside `check_meta` (`clutch.metafill` imports `findings_text` from `clutch.stages`, so a module-level import would be circular); call it as `metafill.make_ask(...)` and `metafill.fill(...)` so tests can monkeypatch `clutch.metafill.make_ask`. A fill that returns no reply leaves those files' findings in place.
- clutch/specs/implement.md: replace rule 5 as stated and bump `version` to the next minor above main.
- tests/integration/test_implement_spec_meta_headers.py: replace the clause list with the new rule's clauses and update its version pin; tests/unit/test_specs.py and tests/integration/test_specs_delimiter_note.py: update the `implement` version pin. Nothing else changes in those three files.
- tests/unit/test_meta_drift_check.py: the expected findings change because empty and drift-flagged purposes are now filled; inject the fill through a fake `ask` (monkeypatch `metafill.make_ask`) and give the stand-in ctx the `driver` the new call reads.
- New tests/unit/test_check_meta_fill.py drives `check_meta` under `tmp_path` with a fake ask.
- docs/how-clutch-works.md section 5.1 `meta_drift` row: say Check refreshes headers and fills empty or drift-flagged purposes first, and the gate reports only what stays malformed or empty.
Scope out:
- `meta_drift` severity, `clutch meta` verbs, the meta prompt spec, the meta schema, and existing headers.

## Scope fence
- clutch/stages.py
- clutch/specs/implement.md
- docs/how-clutch-works.md
- tests/unit/test_check_meta_fill.py
- tests/unit/test_meta_drift_check.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_meta_headers.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_check_meta_fill.py` proves a new file with an empty purpose and a changed file whose header drifted both get the fake ask's purpose written and committed in the `meta` commit, and `check_meta` returns no finding for them, not `empty_purpose` or `purpose_unverified`.
2. `./dev.py test tests/unit/test_check_meta_fill.py` proves a fill that returns no reply leaves the `empty_purpose` finding, and a diff whose meta files all have purposes makes zero ask calls.
3. `./dev.py test tests/integration/test_implement_spec_meta_headers.py` proves the Implement Task contains the never-touch-headers rule and no longer tells Implement to run `clutch meta fill`, `clutch meta refresh` or `clutch meta check`.

## Verification
```
./dev.py test tests/unit/test_check_meta_fill.py tests/unit/test_meta_drift_check.py tests/unit/test_meta_drift_gate.py tests/integration/test_implement_spec_meta_headers.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/unit/test_meta_fill.py
```

## Definition of rejected
Making `meta_drift` hard or removing it, Implement still being told to run a meta verb, a second metadata writer, or files outside the fence change.

## Time budget
- expected: 15m
- stuck: 30m
