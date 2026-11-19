---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- graphics-kind
- graphics-render-check
- image-quality-checks

## Context
- clutch/stages.py::BugEvidenceGate
- clutch/stages.py::CHECK_GATES
- clutch/stages.py::check_render
- clutch/tickets.py::parse_render
- tests/integration/test_gates.py
- tests/integration/test_roadmap_table.py
- docs/gemini-graphics-refactor-plan.md#B4. Layer 1: deterministic checks (`image-quality-gate`)

## Goal / Why
Today a `kind: graphics` ticket has no mechanical image check at Check. After this ticket, Check runs a new engine gate with code `image_quality` on every artifact declared in the ticket's `## Render` block, with no model call. The gate judges each artifact with `clutch.images.judge` (delivered by `image-quality-checks`). It reads artifacts from the render directory that `graphics-render-check` fills. After a pass, the stage layer writes the side-by-side and heatmap operator images into that directory. The gate fails closed: a graphics ticket on a host without the `images` extra fails with the paved road that `judge` returns, never a skip. This lets later tickets (the vision judge and candidate selection) rely on cheap deterministic scores.

## Boundary contract
### image_quality gate
- disposition: create
- owner: gate class and registration in clutch/stages.py and clutch/gates.py; checks stay in clutch/images.py
- consumers: Check (`CHECK_GATES`), the severity and bypass machinery in `clutch/gates.py`, and later graphics tickets that read its scores
- observable change: a new engine gate code `image_quality`, hard by default. A graphics ticket whose artifact fails a check, or whose host lacks the `images` extra, fails Check with a finding naming the check and a paved road. Non-graphics tickets pass the gate untouched.
- compatibility: existing tickets and gate codes are unchanged; `ENGINE_GATE_CODES` and `DEFAULT_GATE_SEVERITY` gain one member; a config naming `image_quality` becomes valid
- acceptance: pass and fail at gate level; the missing-extra road reaches the finding; operator images are written to the attempt render directory through the filesystem seam
- tests: tests/unit/test_images_gate.py using generated images under tmp_path; the pinned gate-code and CHECK_GATES sets in tests/integration/test_closed_sets.py
- post-merge source of truth: clutch/gates.py for the code vocabulary, clutch/stages.py for the gate and writer
- closest existing: `BugEvidenceGate` in clutch/stages.py
- earning reason: no existing gate decodes pixels; the gate is the only Check-stage consumer of `clutch/images.py`.

## Scope in / Scope out
Scope in:
- Add `ImageQualityGate` immediately after `BugEvidenceGate` and add it to `CHECK_GATES` in `clutch/stages.py`. `Gate.check(artifact, workspace)` receives only `Evidence`, so add these `Evidence` fields. Each has a default so existing constructors outside the fence keep working (`tests/unit/test_merge_admission_params.py:15`, the `evidence()` helper at `tests/integration/test_stages.py:547`). The fields are `is_graphics: bool = False`, `render: dict = {}` (the parsed `## Render` block from `parse_render` in `clutch/tickets.py`), `render_dir: str = ""` (the directory `check_render` fills, `ctx.driver.spool.root/<stem>/<attempt>/render`), `attempt: int = 0` and `render_failed: bool = False`.
- Set `is_graphics` in `gather_safety_evidence` beside `is_bug`; mergequeue runs the safety gates on that Evidence. Set `render`, `render_dir` and `attempt` in the existing `model_copy(update=...)` in `gather_evidence`, which already receives `attempt`. `ImageQualityGate.check()` is a pure judge. It returns a pass report when `is_graphics` is false, `render_dir` is empty, or `render_failed` is true. Otherwise it calls `clutch.images.judge` on each artifact at `render_dir/<repo-relative artifact path>`, with the `input:` images resolved in the workspace, and turns each returned message into a finding.
- Order and failure signal: in `check` (clutch/stages.py), move the `check_render` call before `run_gates(CHECK_GATES, ...)`. Keep its reports and hard findings merged into `host_reports`/`host_hard` as they are today. Before `run_gates`, apply `evidence = evidence.model_copy(update={"render_failed": bool(render_hard)})`.
- Stage scope: `gather_evidence` sets `render`, `render_dir` and `attempt` only when its `stage` is `check`. At merge, `render_dir` stays `""` and the gate passes; merge does not re-judge images.
- Mode scope: only `mode: command` graphics tickets are judged. For generate mode, `render_dir` stays empty and the gate passes.
- Writer guard: after `run_gates`, `check()` calls a small writer function in `clutch/stages.py` only when all of these hold: `evidence.is_graphics` is true, `evidence.render_dir` is non-empty, `evidence.render_failed` is false, and the `image_quality` verdict is `pass`. The writer takes the filesystem seam as a parameter and writes the bytes from `images.side_by_side` and, when a base `input:` exists, `images.heatmap` into `render_dir` through that seam. It never writes under `tickets/`.
- Add `image_quality` to `ENGINE_GATE_CODES` in `clutch/gates.py`.
- Update `tests/integration/test_closed_sets.py`. Change only the two sets in `test_gates_closed_sets_and_constants` and the `tuple(ident(g) for g in stages.CHECK_GATES)` pin in `test_stages_closed_sets_and_constants`, which gains `"ImageQualityGate"` right after `"BugEvidenceGate"`.
- Update `tests/integration/test_mergequeue.py` and `tests/integration/test_serve_admission.py`. In each, change only one thing: insert `image_quality` right after `bug_evidence` in the expected recorded gate-code sequence that follows the `CHECK_GATES + MERGE_GATES` monkeypatch.
- In `tests/unit/test_stages_render_check.py`, `test_check_wiring` stubs `gather_evidence` with a `SimpleNamespace`. Replace that return value with a real `stages.Evidence(stem="work", head_sha="abc", claimed="ok", scope_fence=[], changed_files=[], inserted_lines=0, verification=[], run_record=None)` and leave the rest of that file unchanged.
- Add one `image_quality` row beside `bug_evidence` in the section 5 gate table of `docs/how-clutch-works.md`.
- Add one follow-up row `image-embed-presence` to `docs/roadmap.md` for the deferred embedding presence check; edit no existing row.

Scope out:
- The checks, thresholds, lazy imports, operator-image bytes and the extras belong to `image-quality-checks`.
- Render-command execution (`graphics-render-check`), the judge spec (`visual-review-surface`), candidates (`image-candidates-select`) and calibration (`visual-review-baseline`).
- No spec file is changed, so no prompt-spec version bump applies.

## Scope fence
- clutch/images.py
- clutch/gates.py
- clutch/stages.py
- docs/how-clutch-works.md
- docs/roadmap.md
- tests/integration/test_closed_sets.py
- tests/integration/test_mergequeue.py
- tests/integration/test_serve_admission.py
- tests/unit/test_images_gate.py
- tests/unit/test_stages_render_check.py

## Acceptance criteria
1. `ENGINE_GATE_CODES` contains `image_quality` with default severity `hard`, and `stages.CHECK_GATES` names `ImageQualityGate` right after `BugEvidenceGate`, checked by `./dev.py test tests/integration/test_closed_sets.py`.
2. For a command-mode graphics ticket whose artifact in `render_dir` is a valid varied 64x64 PNG, `ImageQualityGate().check(...)` returns `pass` with no finding. A blank artifact returns `fail` with a finding naming the artifact path. Both are checked by `./dev.py test tests/unit/test_images_gate.py`.
3. With the `clutch.images` lazy-import seam patched to raise `ImportError`, the gate returns `fail` with a finding whose paved road contains `clutchwork[images]`, checked by `./dev.py test tests/unit/test_images_gate.py`.
4. When `Evidence.is_graphics` is false, the result is verdict `pass` with no findings, and `check()` writes no side-by-side or heatmap file anywhere, checked by `./dev.py test tests/unit/test_images_gate.py`.
5. The writer is given a `tmp_path`-backed filesystem and passing evidence with a base input. It writes the side-by-side and heatmap images into `render_dir`, both files decode, and nothing is written under a `tickets/` directory. With no `input:`, it writes only the side-by-side image. `ImageQualityGate.check()` itself writes no file, which the test confirms by comparing `tmp_path` listings. All of this is checked by `./dev.py test tests/unit/test_images_gate.py`.
6. A fake-exec `check` test uses a render command that writes a valid image, and the `image_quality` report is `pass`. When `check_render` reports a hard failure, `render_failed` is true, the `image_quality` report is `pass` with no missing-artifact finding, and the render directory has no side-by-side or heatmap file. Both are checked by `./dev.py test tests/unit/test_images_gate.py`.
7. When `gather_evidence` is called with the merge stage on a command-mode graphics ticket, `render_dir` stays empty and the gate returns `pass`. A generate-mode graphics ticket also leaves `render_dir` empty and returns `pass` with no finding. Both are checked by `./dev.py test tests/unit/test_images_gate.py`.
8. The recorded gate-code sequences include `image_quality` after `bug_evidence`, checked by `./dev.py test tests/integration/test_mergequeue.py tests/integration/test_serve_admission.py`.
9. `test_check_wiring` passes with a real `Evidence`, checked by `./dev.py test tests/unit/test_stages_render_check.py`.
10. `docs/roadmap.md` still parses after the added `image-embed-presence` row, checked by `./dev.py test tests/integration/test_roadmap_table.py`.

## Verification
```
./dev.py test tests/unit/test_images_gate.py tests/unit/test_stages_render_check.py tests/integration/test_closed_sets.py tests/integration/test_gates.py tests/integration/test_mergequeue.py tests/integration/test_serve_admission.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
The branch is rejected if a graphics check is skipped instead of failed when its library is missing, if the gate calls a model, if `Gate.check` writes a file, if image logic is reimplemented outside `clutch/images.py`, or if a unit test reads a repo file or starts a process.

## Time budget
- expected: 25m
- stuck: 50m
- reason: gate class, Evidence fields, a reorder in `check`, a small writer, and pinned-set updates; the checks already exist in `clutch/images.py`.