---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- visual-review-surface

## Context
- eval/harness.py
- clutch/visual.py
- clutch/policy.py
- clutch/journal.py
- dev.py
- tests/integration/test_closed_sets.py
- tests/integration/test_vocabularies.py
- docs/how-clutch-works.md#2.2
- docs/how-clutch-works.md#9.6

## Goal / Why
Roadmap row 55 (Gemini plan B7). Today the visual judge's thresholds and rubric wording are unmeasured, and nothing records whether `review_visual` agrees with an independent reviewer. After this ticket:

- `eval/visual/<case>/case.json` is the fixture format: `mode`, `visual_criteria`, `inputs` and `candidate` image paths inside the case directory, a `panel` object (`provider`, `model`) naming the label panel member, and a `label` object (overall `accept` or `reject`, plus one `pass` or `fail` per rubric row id).
- `python -m eval.visual_harness label` has a panel member (a provider other than the judge's, the same refusal rule `eval/harness.py::refuse_same_author` applies) write each unlabelled case's `label`.
- `./dev.py visual-baseline` runs the `review_visual` judge over every labelled case and reports agreement with the panel's labels per rubric row and overall. It journals a `visual_baseline` signal. The signal carries `verdict`, bound to the judge's provider, model and `review_visual.md` major version, and is GO at overall agreement of 0.85 or above (the review baseline's `MIN_CATCH_RATE` in `eval/harness.py`) and NO_GO below. It is also NO_GO while fewer than 20 labelled cases exist, because the plan sets the fixture set at 20 to 50 cases and agreement over fewer is not evidence.
- No person approves the verdict. Populating `eval/visual/` is the output of running `label`, not hand-written code, so this ticket ships the format, the label command and the gate; the cases appear when the command runs.

Why: until a GO is recorded every graphics ticket parks (roadmap decision 17), and the release gate for 0.4.0 reads the recorded `visual_baseline` GO.

## Boundary contract
### visual_baseline verdict signal
- disposition: extend
- owner: clutch/policy.py
- consumers: eval/visual_harness.py now; the roadmap driver's release gate later
- observable change: `policy.py` gains `VISUAL_BASELINE_SIGNAL = "visual_baseline"` and `visual_identity(config, specs_dir)`, returning the `review_visual` routing rows per tier and the spec major, in the shape `baseline_identity` uses
- compatibility: `BASELINE_SIGNAL`, `BASELINED_SURFACES` and `baseline_identity` are unchanged, so review-baseline readers see no new surface
- acceptance: `visual_identity` differs when the `review_visual` route model or the spec major differs, and equals itself otherwise
- tests: tests/unit/test_visual_baseline.py
- post-merge source of truth: clutch/policy.py

### Journal signal vocabulary
- disposition: extend
- owner: clutch/journal.py
- consumers: eval/visual_harness.py, which journals the `visual_baseline` signal
- observable change: `SIGNAL_NAMES` gains `visual_baseline`, so `Journal.append` accepts the signal instead of raising
- compatibility: every existing signal name stays listed; no reader changes
- acceptance: `tests/integration/test_closed_sets.py` pins the extended set and `tests/integration/test_vocabularies.py` finds `visual_baseline` written through the imported `VISUAL_BASELINE_SIGNAL` constant
- tests: tests/integration/test_closed_sets.py, tests/integration/test_vocabularies.py
- post-merge source of truth: clutch/journal.py

### Visual baseline harness
- disposition: create
- owner: eval/visual_harness.py
- consumers: `./dev.py visual-baseline`; `python -m eval.visual_harness label`
- observable change: new module with a case loader, a pure `agreement` scorer, the same-provider refusal, `label` and `run` commands, and a report writer
- compatibility: eval/harness.py and its `review_baseline` signal are untouched
- acceptance: the loader refuses malformed cases, `agreement` is computed per row and overall, and the verdict flips at 0.85 and at 20 cases
- tests: tests/unit/test_visual_baseline.py
- post-merge source of truth: eval/visual_harness.py
- closest existing: eval/harness.py (`score`, `refuse_same_author`, `record_go`), clutch/visual.py (`Reply`, `parse_reply`, `rubric_ids`)
- earning reason: `eval/harness.py` is built around review fixtures (`Fixture`, `ReviewBaselineReport`, defect classes) and images with per-row labels share none of that schema; its scorer and report cannot score `visual.Reply` rows. The module reuses `clutch/visual.py` for judge replies and the identity pattern from `policy.py`, and it is a separate entry point under `eval/`, as the review baseline is.

### dev.py visual-baseline subcommand
- disposition: extend
- owner: dev.py
- consumers: the operator; docs/how-clutch-works.md section 2.2
- observable change: `./dev.py visual-baseline` runs `uv run python -m eval.visual_harness run`; the row names this command
- compatibility: `test`, `vscode` and `vscode-package` behave as before; engine verbs are still rejected by the parser
- acceptance: the subcommand launches exactly that argv and passes its exit code on
- tests: tests/integration/test_visual_baseline_dev.py
- post-merge source of truth: dev.py

### eval/visual fixtures
- disposition: create
- owner: eval/visual
- consumers: eval/visual_harness.py
- observable change: the directory and case format exist; cases are added by running `label`
- compatibility: no existing file moves
- acceptance: a case with a missing image, an unknown label value or a `panel` provider equal to the judge's is refused by the loader
- tests: tests/unit/test_visual_baseline.py
- post-merge source of truth: eval/visual_harness.py (the loader defines the format)
- closest existing: eval/fixtures/ (review fixtures with `expected.json`)
- earning reason: review fixtures hold a diff and defect class and cannot carry images or per-row labels.

## Scope in / Scope out
Scope in:
- `eval/visual_harness.py`: loader, `agreement`, verdict, `label`, `run`, report written to `eval/visual_report.json`. The judge is called through the same `visual.Reply` schema and `visual.parse_reply` validation as Check, and `graphics.judge_samples` with `visual.majority` when it exceeds 1. The module adds no new judge prompt: it renders the shipped `review_visual` spec as `clutch/stages.py` does. It imports `VISUAL_BASELINE_SIGNAL` with `from clutch.policy import VISUAL_BASELINE_SIGNAL` and journals the signal body as `{"signal": VISUAL_BASELINE_SIGNAL, ...}`, never a string literal, as `eval/harness.py` does with `BASELINE_SIGNAL`.
- `clutch/policy.py`: the constant and `visual_identity`.
- `clutch/journal.py`: add `visual_baseline` to `SIGNAL_NAMES`; edit nothing else there.
- `tests/integration/test_closed_sets.py`: add `visual_baseline` to the expected `SIGNAL_NAMES` set in the test at line 178; edit nothing else there.
- `dev.py`: the `visual-baseline` subcommand and its docstring line.
- `docs/how-clutch-works.md`: add a `visual-baseline` row to the section 2.2 table and a third bullet in section 9.6 for the `visual_baseline` verdict; edit nothing else there.
- `CLAUDE.md` and `AGENTS.md`: in each, the sentence saying `./dev.py` covers only `test`, `vscode`, `vscode-package` also names `visual-baseline` (outside the managed block; skip a file that has no such sentence). This is a repo-only rule, so it has no `CORE_TEMPLATE` home.

Scope out: `clutch/stages.py`, `clutch/specs/`, and any change to how graphics tickets park (the park reads the recorded signal in a later change); `eval/harness.py`; `tests/integration/test_vocabularies.py` (it passes unchanged once the harness journals through the imported constant); thresholds and rubric wording, which are tuned by re-running the command against the cases it produces.

## Scope fence
- eval/visual_harness.py
- eval/visual
- clutch/policy.py
- clutch/journal.py
- dev.py
- docs/how-clutch-works.md
- CLAUDE.md
- AGENTS.md
- tests/unit/test_visual_baseline.py
- tests/integration/test_visual_baseline_dev.py
- tests/integration/test_closed_sets.py

## Acceptance criteria
1. `agreement` over cases whose judge verdicts match the panel on 17 of 20 returns overall `0.85` and the verdict is GO; 16 of 20 returns `0.80` and NO_GO, not GO (`./dev.py test tests/unit/test_visual_baseline.py`).
2. With 19 labelled cases at 100% agreement the verdict is NO_GO, and with 20 it is GO; the report states the case count (`./dev.py test tests/unit/test_visual_baseline.py`).
3. `agreement` reports a per-row figure for each rubric id; a row id the judge omitted counts as a disagreement, not as skipped (`./dev.py test tests/unit/test_visual_baseline.py`).
4. The loader raises on a case whose image path is missing, whose label value is not in the closed set, or whose `panel.provider` equals the judge's provider; it does not return a partial list (`./dev.py test tests/unit/test_visual_baseline.py`).
5. `visual_identity` changes when the `review_visual` route model changes and when the spec major changes, and is equal across two calls on an unchanged config (`./dev.py test tests/unit/test_visual_baseline.py`).
6. `run` journals one signal through a real `Journal.append` with `signal == "visual_baseline"`, `verdict`, `identity`, `overall` and `case_count`, and writes `eval/visual_report.json` under the report path it is given (`./dev.py test tests/unit/test_visual_baseline.py`).
7. `journal.SIGNAL_NAMES` contains `visual_baseline`, the closed-set test pins it, and the signal-vocabulary scan finds it written by `eval/visual_harness.py` through `VISUAL_BASELINE_SIGNAL` (`./dev.py test tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py`).
8. `./dev.py visual-baseline` calls `subprocess.run` with `["uv", "run", "python", "-m", "eval.visual_harness", "run"]` and exits non-zero when that process does; `status`, `lint`, `new`, `confirm`, `drain` and `suggest` remain rejected by the parser with code 2 (`./dev.py test tests/integration/test_visual_baseline_dev.py tests/integration/test_dev.py`).
9. `docs/how-clutch-works.md` section 2.2 table has a `visual-baseline` row and section 9.6 names the `visual_baseline` verdict; review confirms by reading both sections once (one-time review check, no standing text test).

## Verification
```
./dev.py test tests/unit/test_visual_baseline.py tests/integration/test_visual_baseline_dev.py tests/integration/test_dev.py tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py
```

## Definition of rejected
A threshold other than 0.85 or a minimum other than 20 cases; a GO that is not bound to the judge's provider, model and spec major; a label panel member from the judge's provider accepted; labels or cases hand-written into `eval/visual/`; the `visual_baseline` signal journaled by a string literal instead of `VISUAL_BASELINE_SIGNAL`; any edit to `eval/harness.py`, `clutch/stages.py` or a prompt spec; an engine verb added to `dev.py`.

## Time budget
- expected: 30m
- stuck: 60m