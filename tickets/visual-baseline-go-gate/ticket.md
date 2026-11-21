---
state: rejected
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/baseline.py::resolve_visual_baseline
- clutch/policy.py::visual_identity
- tests/unit/test_baseline_visual.py

## Goal / Why
Roadmap row 174 `visual-baseline-go-gate`. The 0.4.0 ship clause wants a `visual_baseline` GO recorded, and the 0.4.0 gate block has no command that checks it. When this ticket is done, `clutch roadmap visual-baseline` exits 0 only when the journal's latest `visual_baseline` signal is a GO whose identity equals the current `review_visual` routing rows and spec major, which is exactly what `clutch/baseline.py::resolve_visual_baseline` binds. Otherwise it exits 1 and prints the resolved state (`ABSENT`, `NO_GO` or `REVOKED`) and the paved road. The 0.4.0 gate block in `docs/roadmap.md` runs it. In this repo `eval/visual_report.json` says GO but the journal holds no signal, so the gate fails until the signal is recorded with `./dev.py visual-baseline`; that failure is the point. Running that recording is an operator step and is not part of this ticket.

## Boundary contract
### Visual baseline gate verb
- disposition: extend
- owner: clutch/baseline.py::resolve_visual_baseline
- consumers: the 0.4.0 gate block in docs/roadmap.md, `clutch roadmap gate 0.4.0`, and operators
- observable change: a new read-only verb `clutch roadmap visual-baseline` and a small function in clutch/baseline.py returning `(ok, lines)` from `resolve_visual_baseline(...).binds`. It adds no new binding logic and no second reader of the signal.
- compatibility: `resolve_visual_baseline`, `stages.py` select parking and every existing roadmap verb are unchanged.
- acceptance: GO with matching identity passes; ABSENT, NO_GO, and GO with a changed identity or spec major fail with the state named.
- tests: new unit tests in tests/unit/test_baseline_visual_check.py
- post-merge source of truth: clutch/baseline.py

## Scope in / Scope out
Scope in:
- `clutch/baseline.py`: add one function that calls `resolve_visual_baseline` and returns `(ok, lines)`; the first line names the state, failing lines include the paved road `run ./dev.py visual-baseline to record a GO for the current review_visual routing and spec major`.
- `clutch/__main__.py`: add the `visual-baseline` subcommand under the `roadmap` group via `_command` with does, reads, writes, lock, exits and examples (next to the existing `roadmap gate` and `roadmap merged` entries); handle it in the roadmap verb dispatch inside `main` (beside the `gate` and `merged` branches) using the checkout's journal, the loaded config and the packaged specs directory.
- `docs/how-clutch-works.md` section 2 verb table and `clutch/docs/host-running.md` verb table: add a row for the verb. `docs/roadmap.md`: add `uv run clutch roadmap visual-baseline` to the 0.4.0 gate block and update the paragraph under the 0.4.0 table so it no longer says `visual_baseline` GO is unchecked; leave the clause about a generated graphics ticket as that paragraph states it. Add no test pinning roadmap text.
Scope out:
- Recording the signal (`./dev.py visual-baseline`, `eval/visual_harness.py`), `clutch/stages.py`, `clutch/policy.py`, the `roadmap merged` verb and the generate-graphics gate (`graphics-generate-first-ticket`).

## Scope fence
- clutch/baseline.py
- clutch/__main__.py
- tests/unit/test_baseline_visual_check.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- docs/roadmap.md

## Acceptance criteria
1. With a journal holding a GO `visual_baseline` signal whose identity equals `visual_identity(config, specs_dir)`, the new function returns `ok` True, not False; checked by `./dev.py test tests/unit/test_baseline_visual_check.py`.
2. With no signal it returns False and its output names `ABSENT`; with a latest NO_GO it returns False naming `NO_GO`; with a GO whose identity differs (changed routing row or spec major) it returns False naming `REVOKED`, never a pass; checked by `./dev.py test tests/unit/test_baseline_visual_check.py`.
3. A failing result includes the `./dev.py visual-baseline` paved road line; checked by `./dev.py test tests/unit/test_baseline_visual_check.py`.
4. `clutch roadmap visual-baseline` is registered under the roadmap group with a description and examples, and exits 1 when the check fails and 0 when it passes; checked by `./dev.py test tests/unit/test_main_help.py tests/unit/test_baseline_visual_check.py`.
5. `docs/roadmap.md` still parses and its 0.4.0 gate block contains the new command; checked by `./dev.py test tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_table.py`.

## Verification
```
./dev.py test tests/unit/test_baseline_visual_check.py tests/unit/test_baseline_visual.py tests/unit/test_main_help.py tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_table.py
```

## Definition of rejected
The verb passes without a GO signal, or passes on a GO whose identity no longer matches the current routing and spec major; or it re-implements the binding instead of calling `resolve_visual_baseline`; or a test pins roadmap prose.

## Time budget
- expected: 15m
- stuck: 30m
