---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- visual-review-baseline

## Context
- eval/visual_harness.py
- clutch/visual.py::rubric_ids
- tests/unit/test_visual_baseline.py
- docs/how-clutch-works.md#9.6
- config.yaml

## Goal / Why
Roadmap row 170 (Gemini plan B7). `eval/visual/` holds only `.gitkeep`, so `eval/visual_harness.py` has no cases to score and no `visual_baseline` report exists. After this ticket:

- `eval/visual/<case>/` holds 20 to 24 cases, each a `case.json` plus PNG files (`candidate.png`, and `input.png` for `generate` cases). The images are synthetic, drawn with Pillow (a dev dependency) by a throwaway script kept outside the checkout and not committed. At least 6 cases are `mode: generate` (so the five fixed rubric rows `identity`, `placement`, `lighting`, `unchanged`, `artifacts` are scored) and the rest `mode: command` with one or two `visual_criteria` each. Each criterion is decidable from the candidate image alone. Cases are drawn so both outcomes occur: some candidates meet their criteria, others break one (wrong colour, shape off position, missing element, clipped or duplicated object, seams).
- Every `case.json` names `panel: {provider: codex, model: gpt-6.1-terra}` (the medium-tier model in `config.yaml`). The judge resolves to `claude` through the `review` route, so the panel is a different model family, as roadmap decision 13 requires. Every `label` is written by `uv run python -m eval.visual_harness label`, never by hand or by the implementing agent, and no person labels anything (decision 19). A case whose panel reply is `unsure` is redrawn, not hand-labelled.
- `eval/visual_report.json` is the committed output of one `./dev.py visual-baseline` run over exactly those cases: `case_count`, overall agreement, per-row agreement, and `verdict`. Either verdict is committed as measured; the report is not tuned to reach GO.

Why: the roadmap section 1 0.4.0 ship clause needs a recorded `visual_baseline` outcome and the plan's rubric and thresholds are guesses until measured. This is a one-time measurement that is verified by running the commands once; no recurring test or gate measures agreement, and no verb is added.

## Boundary contract
### Visual baseline fixture set
- disposition: reuse
- owner: eval/visual_harness.py
- consumers: `./dev.py visual-baseline`, `python -m eval.visual_harness label`
- observable change: `eval/visual/` goes from empty to 20 or more labelled cases and `eval/visual_report.json` exists; `load_cases` over them returns every case with no refusal
- compatibility: the loader, `agreement`, `visual_identity` and the case format are used unchanged; no code, spec or config file changes
- acceptance: `tests/integration/test_visual_fixtures.py` loads the cases through `load_cases` with the judge's resolved provider, so a case with a missing image, a missing label or a panel equal to the judge is refused
- tests: tests/integration/test_visual_fixtures.py
- post-merge source of truth: eval/visual_harness.py (format) and eval/visual (data)

## Scope in / Scope out
Scope in:
- Draw 20 to 24 cases under `eval/visual/<case>/`, at most 256 by 256 pixels each, with kebab-case case names, with `case.json` per the `CaseData` schema in `eval/visual_harness.py` (its `label` omitted until the panel writes it). Generate-mode cases pair an `input.png` with a `candidate.png` that is the input composited into a base, the good and the broken placements, as `generate` mode defines. At least 5 cases end with `accept` and at least 5 with `reject` as labelled by the panel; if the panel's labels fall short of that, draw more cases of the missing kind (up to 24 in total) and relabel only the unlabelled ones.
- Run `uv run python -m eval.visual_harness label` until every case is labelled (it skips labelled cases and stops on an `unsure` reply, so a rerun resumes), then `./dev.py visual-baseline` once. It writes `eval/visual_report.json` and journals the signal into this worktree's state directory only.
- Add `tests/integration/test_visual_fixtures.py` (a new file).
- Name in `run.md` the panel and judge provider and model, any case redrawn and why, the verdict and the rows below 0.85; a run record is not a fenced file.

Scope out: `eval/visual_harness.py`, the `clutch/` package including the `review_visual` rubric wording and layer-1 thresholds, `config.yaml`, `dev.py` and `docs/` stay unchanged, because the loader, the commands and the docs describe this format already. No verb, recurring test or gate that measures agreement is added. Journaling the `visual_baseline` signal in the main checkout's state directory happens when `./dev.py visual-baseline` runs there against these cases; the committed report is this ticket's record.

## Scope fence
- eval/visual
- eval/visual_report.json
- tests/integration/test_visual_fixtures.py

## Acceptance criteria
1. `eval/visual/` holds 20 to 24 case directories and `load_cases(CASES, judge_provider)` from `eval/visual_harness.py` returns all of them labelled; `load_cases(CASES, judge_provider, labelled_only=False)` returns the same count, so no case is unlabelled; checked by `./dev.py test tests/integration/test_visual_fixtures.py`. Here `judge_provider` is `visual_identity(load_config(None, cwd=ROOT))["review_visual"]["rows"]["medium"]["provider"]`, not a literal.
2. Every case's `panel.provider` differs from that judge provider and every case names the same `panel` provider and model, not blank; checked by `./dev.py test tests/integration/test_visual_fixtures.py`. A set whose panel equals the judge is refused, not accepted.
3. Overall labels include at least 5 `accept` and at least 5 `reject`, and at least 6 cases are `mode: generate` with their five fixed row ids labelled; checked by `./dev.py test tests/integration/test_visual_fixtures.py`. An all-`accept` set fails.
4. `eval/visual_report.json` parses as one JSON object with exactly the keys `case_count`, `overall`, `rows` and `verdict`; `verdict` is `GO` or `NO_GO`, `case_count` is at least 20, `overall` is between 0 and 1, and every `rows` key is a row id used in some case label; checked by `./dev.py test tests/integration/test_visual_fixtures.py`. The test does not pin `overall`, the verdict value or the case count of the report beyond these bounds.
5. No file other than those under `eval/visual/`, `eval/visual_report.json` and `tests/integration/test_visual_fixtures.py` differs from main; checked by `git diff --name-only main` listing only those paths.

## Verification
```
./dev.py test tests/integration/test_visual_fixtures.py
```

## Definition of rejected
A `label` written by hand or by anything but the panel through `eval.visual_harness label`; a panel from the judge's provider; a report not produced from exactly the committed cases; a changed code, spec, config or doc file; a new verb, standing agreement test or gate; images or reports carrying private data.

## Time budget
- expected: 55m
- stuck: 110m
- reason: image drawing, 20 or more sequential panel calls and 20 or more sequential judge calls share one fixture set, and the report must describe exactly that set, so splitting would commit a fixture set with no report or a report without its cases.
