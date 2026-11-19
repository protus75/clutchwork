---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- none

## Context
- clutch/gates.py
- clutch/tickets.py::parse_render
- pyproject.toml
- docs/gemini-graphics-refactor-plan.md#B4. Layer 1: deterministic checks (`image-quality-gate`)

## Goal / Why
Today clutch has no code that decodes or scores an image, so a `kind: graphics` ticket cannot get a mechanical image check at Check. After this ticket, the new module `clutch/images.py` holds the deterministic Layer 1 image checks from the plan, with no model call. The sibling ticket `image-quality-gate-wiring` registers them as the `image_quality` engine gate. The module decides these checks:
- the artifact exists, decodes as an image, and has a sane width, height and aspect ratio (Pillow);
- the artifact is not blank, by a pixel-variance floor (numpy);
- the artifact is not a copy of any `input:` image, by a perceptual-hash distance floor (imagehash);
- preservation: SSIM at reduced resolution against the base image, which is the first declared `input:` (scikit-image);
- presence: ORB keypoint matches between each non-base `input:` and the artifact, where a score near zero means the input was ignored (OpenCV).

It also returns two operator images as bytes: a side-by-side image of the inputs and candidate, and a diff heatmap against the base image. The libraries ship as two optional extras of the `clutchwork` package, `images` (Pillow, numpy, scikit-image, imagehash, opencv-python-headless) and `images-embed` (open_clip_torch and torch), and `clutch/images.py` imports them lazily. Core gains no dependency. It fails closed: when the `images` extra is missing, the module returns a failure whose paved road names `clutchwork[images]`, never a skip.

## Boundary contract
### Image check module
- disposition: create
- owner: clutch/images.py (checks, thresholds, lazy imports, operator-image bytes)
- consumers: the `image_quality` gate in the sibling ticket `image-quality-gate-wiring`, and later graphics tickets (the vision judge and candidate ranking) that read its scores
- observable change: a new importable module. It has a function `judge(artifact: Path, inputs: list[Path]) -> list[str]` that returns one failure message per failed check, each naming the failing path and the check, and returns an empty list when every check passes. It has `side_by_side(paths: list[Path]) -> bytes` and `heatmap(base: Path, artifact: Path) -> bytes` that return PNG bytes and write no file. A lazy-import seam `_load()` raises `ImportError` when the extra is missing, and `judge` turns that into one failure message containing `clutchwork[images]`.
- compatibility: nothing imports the module yet; no existing behaviour changes
- acceptance: each check has a passing and a failing image case; a missing extra reports the install road
- tests: tests/unit/test_images_checks.py using images generated under tmp_path
- post-merge source of truth: clutch/images.py
- closest existing: `BugEvidenceGate` and `DiffBudgetGate` in clutch/stages.py
- earning reason: neither can be reused, because both read git or command evidence and neither decodes pixels. A separate module keeps the lazily imported heavy libraries out of `clutch/stages.py`.

### Optional dependency extras
- disposition: create
- owner: pyproject.toml
- consumers: hosts running graphics tickets, and this repo's dev group so the unit tests can import the libraries
- observable change: `clutchwork[images]` and `clutchwork[images-embed]` become installable; `[project.dependencies]` is unchanged
- compatibility: hosts that install neither extra see no change
- acceptance: `[project.dependencies]` still lists only duckdb, pydantic and pyyaml
- tests: no unit test parses pyproject.toml; the check is `uv lock --check` plus one review of the diff
- post-merge source of truth: pyproject.toml
- closest existing: the `[dependency-groups]` dev table
- earning reason: dev dependencies are not installed on hosts, so the extras are the only way to ship the libraries optionally, as roadmap decision 18 requires.

## Scope in / Scope out
Scope in:
- Create `clutch/images.py` with the five checks, the lazy-import seam, the missing-extra failure message, `judge`, `side_by_side` and `heatmap` as described in the boundary contract. The module never writes files.
- With an empty `inputs` list, only the exists, decodes and not-blank checks run. Not-a-copy, preservation and presence do not apply, and they do not count as skipped checks.
- Not-a-copy rejects only an unmodified input. It fails an artifact that is byte-identical to a non-base `input:`, or within a near-zero perceptual-hash distance of one. For the base image (the first `input:`) it fails only a byte-identical or near-zero-distance match, so a real edit of the base that passes preservation also passes not-a-copy. Name the base-image near-zero floor as a constant beside the other thresholds.
- Thresholds are fixed per-check engine defaults held as named module constants. The ticket-side grammar for tightening a threshold is plan open decision 1, so this ticket adds no grammar and no `tickets.py` change.
- Add the two extras to `pyproject.toml` and the `images` libraries to the dev dependency group, and refresh `uv.lock`.

Scope out:
- The `ImageQualityGate` class, `Evidence` fields, `CHECK_GATES` and `ENGINE_GATE_CODES` registration, Check ordering, the stage-layer writer, docs, and the roadmap row belong to `image-quality-gate-wiring`.
- The embedding presence check (CLIP/DINO via `images-embed`) is not run; this ticket only declares the extra.
- No spec file is changed, so no prompt-spec version bump applies.

## Scope fence
- clutch/images.py
- pyproject.toml
- uv.lock
- tests/unit/test_images_checks.py

## Acceptance criteria
1. For a valid 64x64 PNG with varied pixels and no inputs, `images.judge(...)` returns an empty list, checked by `./dev.py test tests/unit/test_images_checks.py`.
2. A missing file, a zero-byte file, and a non-image file each make `judge` return a message naming the artifact path, checked by `./dev.py test tests/unit/test_images_checks.py`. A test that passes on an empty list for these cases is wrong.
3. A solid single-colour image fails the not-blank check, and a noise image passes it, checked by `./dev.py test tests/unit/test_images_checks.py`.
4. An artifact byte-identical to an input fails the not-a-copy check, and a clearly different image passes it, checked by `./dev.py test tests/unit/test_images_checks.py`.
5. Preservation: an artifact equal to the base image outside a masked region passes, and an artifact whose whole frame is replaced by a different image fails, checked by `./dev.py test tests/unit/test_images_checks.py`.
6. Presence: a non-base input pasted into the artifact passes. An artifact that never contains the input fails with a message naming the input path, checked by `./dev.py test tests/unit/test_images_checks.py`. The pasted-input case uses a textured pattern generated under `tmp_path`, because a plain shape has too few ORB keypoints.
7. In one `judge` call, an artifact that is the base image with a pasted textured non-base input passes all five checks, not-a-copy included, checked by `./dev.py test tests/unit/test_images_checks.py`.
8. With `_load` patched to raise `ImportError`, `judge` returns one message containing `clutchwork[images]` and raises no exception, checked by `./dev.py test tests/unit/test_images_checks.py`.
9. `side_by_side` and `heatmap` return bytes that decode as PNG images, and calling them leaves the `tmp_path` listing unchanged, checked by `./dev.py test tests/unit/test_images_checks.py`.
10. Importing `clutch.images` imports none of PIL, numpy, skimage, imagehash or cv2, checked by `./dev.py test tests/unit/test_images_checks.py` using a subprocess-free `sys.modules` check.
11. `[project.dependencies]` in `pyproject.toml` is unchanged and `[project.optional-dependencies]` defines exactly `images` and `images-embed`, checked by `uv lock --check` exiting 0 and a review of the diff.

## Verification
```
./dev.py test tests/unit/test_images_checks.py
uv lock --check
```

## Definition of rejected
The branch is rejected if a check is skipped instead of failed when its library is missing. It is also rejected if any image library is added to `[project.dependencies]` or imported when `clutch/images.py` loads, if the module calls a model or writes a file, or if a unit test reads a repo file or starts a process.

## Time budget
- expected: 20m
- stuck: 40m
- reason: one module with five small independent checks and one test file, all testable with generated images.