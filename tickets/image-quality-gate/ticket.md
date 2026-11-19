---
state: draft
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- graphics-kind
- graphics-render-check

## Context
- clutch/gates.py
- clutch/stages.py::BugEvidenceGate
- clutch/stages.py::CHECK_GATES
- clutch/tickets.py::parse_render
- pyproject.toml
- tests/integration/test_closed_sets.py
- docs/gemini-graphics-refactor-plan.md#B4. Layer 1: deterministic checks (`image-quality-gate`)

## Goal / Why
Today a `kind: graphics` ticket has no mechanical image check at Check. After this ticket, Check runs a new engine gate with code `image_quality` on every artifact declared in the ticket's `## Render` block, with no model call. The gate lives in the new module `clutch/images.py` and decides these checks:
- the artifact exists, decodes as an image, and has a sane width, height and aspect ratio (Pillow);
- the artifact is not blank, by a pixel-variance floor (numpy);
- the artifact is not a copy of any `input:` image, by a perceptual-hash distance floor (imagehash);
- preservation: SSIM at reduced resolution against the base image, which is the first declared `input:` (scikit-image);
- presence: ORB keypoint matches between each non-base `input:` and the artifact, where a score near zero means the input was ignored (OpenCV).

The gate reads each artifact from the render directory that `graphics-render-check` fills (the attempt's `render` directory under the spool), and the stage layer writes two operator images into that same directory: a side-by-side image of the inputs, reference and candidate, and a diff heatmap against the base image. The libraries ship as two optional extras of the `clutchwork` package, `images` (Pillow, numpy, scikit-image, imagehash, opencv-python-headless) and `images-embed` (open_clip_torch and torch), and `clutch/images.py` imports them lazily. Core gains no dependency. It fails closed: a graphics ticket on a host without the `images` extra fails the gate with a paved road, never a skip. This is Layer 1 of the grading design in the plan, and it lets later tickets (the vision judge and candidate selection) rely on cheap deterministic scores.

## Boundary contract
### image_quality gate
- disposition: create
- owner: clutch/images.py (checks and operator-image bytes); gate class and registration in clutch/stages.py and clutch/gates.py
- consumers: Check (`CHECK_GATES`), the severity and bypass machinery in `clutch/gates.py`, and later graphics tickets that read its scores
- observable change: a new engine gate code `image_quality`, hard by default; a graphics ticket whose artifact fails a check, or whose host lacks the `images` extra, fails Check with a finding naming the check and a paved road; non-graphics tickets pass the gate untouched
- compatibility: existing tickets and gate codes are unchanged; `ENGINE_GATE_CODES` and `DEFAULT_GATE_SEVERITY` gain one member; a config naming `image_quality` becomes valid
- acceptance: each check has a passing and a failing image case; a missing extra reports the install road; operator images are written to the attempt render directory through the filesystem seam
- tests: tests/unit/test_images_gate.py using generated images under tmp_path; the pinned gate-code and CHECK_GATES sets in tests/integration/test_closed_sets.py
- post-merge source of truth: clutch/images.py for the checks and clutch/gates.py for the code vocabulary
- closest existing: `BugEvidenceGate` and `DiffBudgetGate` in clutch/stages.py
- earning reason: neither can be reused, because both read git or command evidence and neither decodes pixels. A separate module keeps the lazily imported heavy libraries out of `clutch/stages.py`, and the gate has two later consumers: the judge's score inputs and candidate ranking.

### Optional dependency extras
- disposition: create
- owner: pyproject.toml
- consumers: hosts running graphics tickets, and this repo's dev group so the unit tests can import the libraries
- observable change: `clutchwork[images]` and `clutchwork[images-embed]` become installable; `[project.dependencies]` is unchanged
- compatibility: hosts that install neither extra see no change
- acceptance: `[project.dependencies]` still lists only duckdb, pydantic and pyyaml
- tests: a unit test that parses pyproject.toml is not added; the check is a one-time review of the diff
- post-merge source of truth: pyproject.toml
- closest existing: the `[dependency-groups]` dev table
- earning reason: dev dependencies are not installed on hosts, so the extras are the only way to ship the libraries optionally, as roadmap decision 18 requires.

## Scope in / Scope out
Scope in:
- Create `clutch/images.py` with the five checks, the lazy imports, the missing-extra finding, and functions that return the side-by-side and heatmap images as bytes. It never writes files itself.
- Add a gate class (a new `ImageQualityGate` placed immediately after `BugEvidenceGate`) to `CHECK_GATES` in `clutch/stages.py`. `Gate.check(artifact, workspace)` receives only `Evidence`, so add these `Evidence` fields, each with a default so existing constructors outside the fence keep working (`tests/unit/test_merge_admission_params.py:15`, the `evidence()` helper at `tests/integration/test_stages.py:547`): `is_graphics: bool = False`, `render: dict = {}` (the parsed `## Render` block from `parse_render` in `clutch/tickets.py`; this ticket calls `parse_render`), `render_dir: str = ""` (the directory `check_render` fills, `ctx.driver.spool.root/<stem>/<attempt>/render`) and `attempt: int = 0`. Set `is_graphics` in `gather_safety_evidence` beside `is_bug` (mergequeue runs the safety gates on that Evidence), and set `render`, `render_dir` and `attempt` in `gather_evidence`'s existing `model_copy(update=...)` (it already receives `attempt`). `ImageQualityGate.check()` is a pure judge over that evidence: it returns a pass report for any ticket where `is_graphics` is false, and otherwise reads each artifact and `input:` image from `render_dir` and the workspace through `clutch/images.py`.
- Order: in `check` (clutch/stages.py), `check_render` currently runs after `run_gates(CHECK_GATES, ...)`, so the gate would read an empty render directory. Move the `check_render` call before `gather_evidence` and `run_gates(CHECK_GATES, ...)`, keep its reports and hard findings merged into `host_reports`/`host_hard` as today, and when it reported a hard failure `ImageQualityGate` skips its artifact reads (the render failure is already the finding) and returns `pass` for that evidence, because the failure is already recorded.
- Artifact location: the gate reads each declared artifact at `render_dir/<repo-relative artifact path>`, exactly where `check_render` writes it. For generate mode the same layout holds: the candidate files sit in `render_dir` under their declared repo-relative paths.
- No `input:` declared (always the case for command-mode tickets, since `parse_render` rejects `input:` there): the not-a-copy, preservation and presence checks do not apply (they are not an enabled check that was skipped), only the presence-of-file, not-blank and decodes checks run, and the writer emits only the side-by-side image (no base image, so no heatmap).
- Not-a-copy rejects only an unmodified input: it fails an artifact byte-identical to, or within a near-zero perceptual-hash distance of, a non-base `input:`; for the base image (the first `input:`) it fails only a byte-identical or near-zero-distance match, so a real edit of the base that passes preservation also passes not-a-copy. Name the base-image near-zero floor as a constant in `clutch/images.py` beside the other thresholds.
- After the gate passes, the stage layer calls the `clutch/images.py` functions and writes the side-by-side and heatmap images into `render_dir` through `ctx.fs`, never from inside `Gate.check` and never under `tickets/`. The writer is a small function in `clutch/stages.py` that takes the filesystem seam as a parameter so a unit test can pass a fake or a `tmp_path`-backed one.
- Add `image_quality` to `ENGINE_GATE_CODES` in `clutch/gates.py`.
- Update `tests/integration/test_closed_sets.py`: the only expectations that change are the two sets in `test_gates_closed_sets_and_constants` and the `tuple(ident(g) for g in stages.CHECK_GATES)` pin in `test_stages_closed_sets_and_constants`, which gains `"ImageQualityGate"` immediately after `"BugEvidenceGate"`.
- Update `tests/integration/test_mergequeue.py` and `tests/integration/test_serve_admission.py`: the only change in each is inserting `image_quality` immediately after `bug_evidence` in the expected recorded gate-code sequence that follows the `CHECK_GATES + MERGE_GATES` monkeypatch.
- Add the two extras to `pyproject.toml` and the `images` libraries to the dev dependency group, and refresh `uv.lock`.
- Update the gate table in `docs/how-clutch-works.md` (the row beside `bug_evidence`, section 5) with one row for `image_quality`.
- Thresholds are fixed per-check engine defaults held as named constants in `clutch/images.py`. The first `input:` is the base image. The ticket-side grammar for tightening a threshold is plan open decision 1, which a design panel settles first, so this ticket adds no grammar and no `tickets.py` change.

Scope out:
- The embedding presence check (CLIP/DINO via the `images-embed` extra) is not run by this ticket. It needs a ticket-side switch that does not exist, so it is deferred to a follow-up row `image-embed-presence` that this ticket adds to `docs/roadmap.md` (fenced for that one row; no existing row is edited). This ticket still ships the `images-embed` extra declaration.
- Render-command execution and artifact copying (`graphics-render-check`), the judge spec (`visual-review-surface`), candidates and the select commit (`image-candidates-select`), and threshold calibration (`visual-review-baseline`) are separate tickets.
- No spec file is changed, so no prompt-spec version bump applies.

## Scope fence
- clutch/images.py
- clutch/gates.py
- clutch/stages.py
- pyproject.toml
- uv.lock
- docs/how-clutch-works.md
- docs/roadmap.md
- tests/integration/test_closed_sets.py
- tests/integration/test_mergequeue.py
- tests/integration/test_serve_admission.py
- tests/unit/test_images_gate.py

## Acceptance criteria
1. `ENGINE_GATE_CODES` contains `image_quality` with default severity `hard`, and `stages.CHECK_GATES` names `ImageQualityGate` right after `BugEvidenceGate`, checked by `./dev.py test tests/integration/test_closed_sets.py`; the test fails if the code, the severity or the CHECK_GATES entry is missing.
2. For a graphics ticket whose artifact is a valid 64x64 PNG with varied pixels, `ImageQualityGate().check(...)` returns verdict `pass`, not `fail`, checked by `./dev.py test tests/unit/test_images_gate.py`.
3. A missing artifact file, a zero-byte file, and a non-image file each produce a `fail` report whose finding names the artifact path, checked by `./dev.py test tests/unit/test_images_gate.py`; a test that passes on a `pass` verdict is wrong.
4. A solid single-colour image fails the not-blank check, and a noise image passes it, checked by `./dev.py test tests/unit/test_images_gate.py`.
5. An artifact byte-identical to an `input:` image fails the not-a-copy check, while a clearly different image passes, checked by `./dev.py test tests/unit/test_images_gate.py`.
6. Preservation: an artifact equal to the base image outside a masked region passes, and an artifact with the whole frame replaced by a different image fails, checked by `./dev.py test tests/unit/test_images_gate.py`.
7. Presence: a non-base input that is pasted into the artifact produces more keypoint matches than the engine floor and passes; an artifact that never contains the input fails with a finding naming the input path, checked by `./dev.py test tests/unit/test_images_gate.py`. The pasted-input case uses a textured pattern generated under `tmp_path`, because a plain shape has too few ORB keypoints and is marked hand-built.
8. A ticket whose `Evidence.is_graphics` is false yields verdict `pass` with no findings and no image library import, checked by `./dev.py test tests/unit/test_images_gate.py`.
9. With the lazy-import seam made to raise `ImportError`, the gate returns `fail` with a finding whose paved road contains `clutchwork[images]`, not a `pass` or an unhandled exception, checked by `./dev.py test tests/unit/test_images_gate.py`.
10. The stage-layer writer, given a `tmp_path`-backed filesystem fake and a passing evidence, writes the side-by-side and heatmap images into `render_dir`; both files exist and decode, and nothing is written under a `tickets/` directory, checked by `./dev.py test tests/unit/test_images_gate.py`. `ImageQualityGate.check()` itself writes no file, checked by the same test listing `tmp_path` before and after.
11. `[project.dependencies]` in `pyproject.toml` is unchanged and `[project.optional-dependencies]` defines exactly `images` and `images-embed`, checked by `uv lock --check` exiting 0 and a review of the diff.
12. `docs/roadmap.md` still parses and its gate commands are valid after the added `image-embed-presence` row, checked by `./dev.py test tests/integration/test_roadmap_table.py`.
13. A command-mode graphics ticket with no `input:` and a valid artifact passes `ImageQualityGate().check(...)` with verdict `pass` and no finding, not `fail`, and the writer given that evidence writes only the side-by-side image, checked by `./dev.py test tests/unit/test_images_gate.py`.
14. In one `ImageQualityGate().check(...)` call, an artifact that is the base image with a pasted textured non-base input passes all five checks, not-a-copy included, checked by `./dev.py test tests/unit/test_images_gate.py`.
15. A fake-exec `check` test in `tests/unit/test_images_gate.py` shows the artifact `check_render` writes into `render_dir` is the file `ImageQualityGate` judges: with a render command that writes a valid image the Check report for `image_quality` is `pass`, not a missing-artifact `fail`; and when `check_render` reports a hard failure the `image_quality` report is `pass` with no missing-artifact finding, checked by `./dev.py test tests/unit/test_images_gate.py`.

## Verification
```
./dev.py test tests/unit/test_images_gate.py tests/integration/test_closed_sets.py tests/integration/test_gates.py tests/integration/test_mergequeue.py tests/integration/test_serve_admission.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
The branch is rejected if a graphics check is skipped, not failed, when its library is missing; if any image library is added to `[project.dependencies]` or imported at module load of `clutch/images.py`; if the gate calls a model; if `Gate.check` writes a file; or if a unit test reads a repo file or starts a process.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one gate with five small independent checks sharing a single module and one test file. Splitting would put the lazy-import and finding scaffolding in a ticket with no consumer.
