---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/images.py
- clutch/stages.py::ImageQualityGate
- clutch/tickets.py::parse_render
- tests/unit/test_images_checks.py
- docs/gemini-graphics-refactor-plan.md#B4. Layer 1: deterministic checks (`image-quality-gate`)
- pyproject.toml

## On-demand
- clutch/docs/host-authoring.md

## Goal / Why
Plan B4 defers the embedding presence check: when a ticket asks for `presence: embedding`, the `image_quality` gate scores CLIP similarity between an `input:` image and the output instead of counting ORB keypoint matches. ORB fails on inputs that the generator restyled or re-lit, and a near-zero embedding score still shows that the generator ignored the input. After this ticket a graphics ticket can declare a bullet `- presence: embedding` in `## Render`. The gate then runs the embedding check for every non-base `input:` of every declared artifact. A host without `clutchwork[images-embed]` fails the gate with that install road, never a skip. Default behavior without the bullet is unchanged (ORB).

Check design (the smallest that meets the plan): embed the input and the output with open_clip; split the output into a 3x3 grid of equal tiles plus the whole frame; the input is present when the maximum cosine similarity over those 10 views is at least `MIN_EMBED_SIMILARITY` (engine default 0.25, a guess that the B7 calibration tunes). Rejected simpler approach: whole-frame similarity only, because an insert covering a small region dilutes below any useful floor. Rejected richer approach: a caller-supplied crop location, because no ticket grammar for regions exists yet (plan open decision 1).

## Boundary contract
### Image presence check
- disposition: extend
- owner: clutch/images.py
- consumers: `ImageQualityGate` in clutch/stages.py
- observable change: `images.judge` takes keyword `embedding: bool = False`; when true, each non-base input is checked by embedding similarity instead of ORB and a failure reads `<input>: presence check failed in <artifact> (embedding)`; a missing `images-embed` extra yields one message naming `clutchwork[images-embed]`.
- compatibility: with `embedding=False` every existing message and result is unchanged; the model loader is imported lazily so `import clutch.images` still imports no heavy library.
- acceptance: the embedding check passes for an output containing the input and fails for an unrelated output, with a fake embedder.
- tests: tests/unit/test_images_embedding.py
- post-merge source of truth: clutch/images.py

### Render grammar
- disposition: extend
- owner: clutch/tickets.py
- consumers: lint, intake, Check (`render` dict read by `ImageQualityGate`)
- observable change: `## Render` accepts one optional bullet `- presence: embedding`; any other value or a second bullet is a finding with a fix.
- compatibility: existing Render blocks stay valid; the parsed dict gains a `presence` key only when declared.
- acceptance: valid bullet parses to `{"presence": ["embedding"]}`; `- presence: orb` and duplicates are refused.
- tests: tests/unit/test_graphics_presence_grammar.py
- post-merge source of truth: clutch/tickets.py

### Gate wiring
- disposition: reuse
- owner: clutch/stages.py `ImageQualityGate`
- consumers: Check
- observable change: the gate passes `embedding=True` to `images.judge` when the ticket's render declares `presence: embedding`; the paved road for a missing extra names the `images-embed` install.
- compatibility: tickets without the bullet behave as before.
- acceptance: the gate report fails with the embedding message for a declared ticket and is untouched otherwise.
- tests: tests/unit/test_images_embedding.py
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
Scope in:
- clutch/images.py: add `MIN_EMBED_SIMILARITY = 0.25`, an `_embedder()` loader (lazy `open_clip` and `torch` import, returns a callable mapping a list of PIL images to unit-norm vectors) as the one injectable seam, and the `embedding` keyword on `judge`. Keep `_embedder` small: import, create model and preprocess, encode under no-grad, normalize. When `embedding` is true the non-base inputs skip ORB and use the grid-plus-whole-frame similarity rule above. An ImportError from the embedder loader returns one message containing `clutchwork[images-embed]`.
- clutch/tickets.py: extend the `parse_render` bullet regex and the invalid-entry fix text with `presence`; accept only `embedding`, at most once.
- clutch/stages.py: `ImageQualityGate.check` passes `embedding=` from the render dict, and the paved road also matches the `images-embed` message.
- clutch/docs/host-authoring.md: in `## Graphics tickets`, add one sentence on the `- presence: embedding` bullet and its extra; edit only that section.
- tests/unit/test_images_checks.py: add "open_clip" and "torch" to the `names` tuple in `test_import_is_lazy`; nothing else changes there.
- New tests: tests/unit/test_images_embedding.py and tests/unit/test_graphics_presence_grammar.py. The embedding test also runs the real `_embedder()` body (coverage of the new loader lines) with fake `open_clip` and `torch` modules installed through `monkeypatch.setitem(sys.modules, ...)`; the fakes return in-memory tensors, with no weights and no network.
Scope out: threshold calibration (`visual-review-baseline`), crop-location grammar, CLIP model weight management, pyproject extras (already declare `images-embed`; pyproject.toml is read-only context), the `heatmap` and `side_by_side` previews, and the roadmap row status.

## Scope fence
- clutch/images.py
- clutch/tickets.py
- clutch/stages.py
- clutch/docs/host-authoring.md
- tests/unit/test_images_checks.py
- tests/unit/test_images_embedding.py
- tests/unit/test_graphics_presence_grammar.py

## Acceptance criteria
1. With a fake embedder patched over `images._embedder` that returns the same vector for the input and for one tile of the output, `images.judge(edited, [base, insert], embedding=True)` returns `[]`, not a presence failure, checked by `./dev.py test tests/unit/test_images_embedding.py`.
2. With a fake embedder returning orthogonal vectors for input and output views, `images.judge(other, [base, insert], embedding=True)` returns a message containing `presence check failed` and `(embedding)` and naming the insert path, not `[]`, checked by `./dev.py test tests/unit/test_images_embedding.py`.
3. With `_embedder` raising ImportError, `images.judge(edited, [base, insert], embedding=True)` returns exactly one message containing `clutchwork[images-embed]`, not an ORB result, checked by `./dev.py test tests/unit/test_images_embedding.py`.
4. `images.judge(edited, [base, insert])` with no `embedding` argument never calls `_embedder` and returns the same results as before, checked by `./dev.py test tests/unit/test_images_embedding.py tests/unit/test_images_checks.py`.
5. `ImageQualityGate.check` on an evidence whose render declares `presence: ["embedding"]` yields a failing report carrying the embedding message when the fake embedder is orthogonal, and a passing report without the declaration, checked by `./dev.py test tests/unit/test_images_embedding.py`.
6. `parse_render` of a block with `- presence: embedding` returns `presence == ["embedding"]` and no findings; `- presence: orb` and two `- presence:` bullets each return a finding, not an empty list, checked by `./dev.py test tests/unit/test_graphics_presence_grammar.py`.
7. `import clutch.images` imports none of `PIL`, `numpy`, `skimage`, `imagehash`, `cv2`, `open_clip` or `torch`; a module-level `import torch` makes the test fail, checked by `./dev.py test tests/unit/test_images_checks.py::test_import_is_lazy`.
8. The Graphics tickets section of `clutch/docs/host-authoring.md` names `presence: embedding` and `clutchwork[images-embed]`, and `clutch ticket lint image-embed-presence` exits 0, checked by `uv run clutch ticket lint image-embed-presence`.
9. With fake `open_clip` and `torch` modules in `sys.modules`, the real `images._embedder()` returns a callable whose output vectors each have unit norm (1.0 within 1e-6), not raw unnormalized vectors, and it opens no network connection, checked by `./dev.py test tests/unit/test_images_embedding.py`.

## Verification
```
./dev.py test tests/unit/test_images_embedding.py tests/unit/test_graphics_presence_grammar.py tests/unit/test_images_checks.py tests/unit/test_images_gate.py tests/unit/test_graphics_kind.py tests/unit/test_host_authoring.py
```

## Definition of rejected
The branch is thrown away if any default (no `presence` bullet) result changes, if `open_clip` or `torch` is imported at module load, if a test downloads model weights or touches the network, or if a missing extra is skipped instead of failing the gate.

## Time budget
- expected: 25m
- stuck: 50m
