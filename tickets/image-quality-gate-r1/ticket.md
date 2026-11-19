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

## Runs before
- image-quality-checks
- image-quality-gate-wiring

## Context
- pyproject.toml
- docs/gemini-graphics-refactor-plan.md#Gemini provider and graphics ticket kind: refactor plan
- tickets/gemini-provider/evidence/fact-09-wheels-py314.txt

## Goal / Why
Roadmap row 52, first of two parts (the dependency half; the gate code is delivered by `image-quality-checks` and `image-quality-gate-wiring`). The first attempt at this row failed only the diff budget: 1617 inserted lines against 1500, of which `uv.lock` alone was 1268. Hand-written code was about 350 lines. Splitting the dependency work from the gate work keeps each diff under the budget.

After this ticket, `pyproject.toml` declares two optional extras and `uv.lock` is refreshed to match:
- `images`: Pillow, numpy, scikit-image, imagehash, opencv-python-headless.
- `images-embed`: open-clip-torch and torch, for the embedding presence check only.

The five `images` libraries also join the `dev` dependency group so the gate's tests can import them. `[project.dependencies]` stays duckdb, pydantic and pyyaml: core clutch gains no dependency (plan decision 18). `images-embed` is not added to the dev group, so the dev environment never installs torch.

If `uv lock` cannot resolve a library on Python 3.14 (the project floor), stop and report which one, citing the wheel evidence file; do not pin an older Python or drop the library.

## Boundary contract
### Packaging extras
- disposition: extend
- owner: pyproject.toml
- consumers: `clutch/images.py` and the `image_quality` gate (later tickets), hosts installing `clutchwork[images]` or `clutchwork[images-embed]`, the dev environment
- observable change: `[project.optional-dependencies]` gains `images` and `images-embed`; the `dev` dependency group gains the five `images` libraries; `uv.lock` records them
- compatibility: `[project.dependencies]` is unchanged, so a plain install resolves and imports exactly as before; no code imports the new libraries in this ticket
- acceptance: the lock matches pyproject, and the core dependency list is exactly duckdb, pydantic and pyyaml
- tests: `uv lock --check` and a tomllib read of pyproject.toml (no new test file; a standing pin on dependency text is not added)
- post-merge source of truth: pyproject.toml and uv.lock

## Scope in / Scope out
Scope in:
- Add `[project.optional-dependencies]` to `pyproject.toml` with `images` and `images-embed` as listed above.
- Add pillow, numpy, scikit-image, imagehash and opencv-python-headless to the `dev` group.
- Run `uv lock` to refresh `uv.lock`.

Scope out:
- `clutch/images.py`, the gate, the Evidence fields, docs, and tests: delivered by `image-quality-checks` and `image-quality-gate-wiring`.
- Any change to `[project.dependencies]`.
- Engine cause, for the operator only: `DiffBudgetGate` (`clutch/stages.py`) counts every inserted line of the diff, so a required `uv.lock` refresh counts against the review budget. A generated-file exclusion is a separate decision, not this ticket's scope.

## Scope fence
- pyproject.toml
- uv.lock

## Acceptance criteria
1. `uv lock --check` exits 0, so `uv.lock` matches `pyproject.toml`.
2. `uv run python -c "import tomllib; d = tomllib.load(open('pyproject.toml','rb')); assert sorted(d['project']['optional-dependencies']) == ['images', 'images-embed']"` exits 0; a missing or extra extra fails it.
3. `uv run python -c "import tomllib; d = tomllib.load(open('pyproject.toml','rb')); assert [x.split('>')[0].split('=')[0].strip().lower() for x in d['project']['dependencies']] == ['duckdb', 'pydantic', 'pyyaml']"` exits 0; any added core dependency fails it.
4. `uv run python -c "import PIL, numpy, skimage, imagehash, cv2"` exits 0 in the dev environment, so the dev group carries the `images` libraries.
5. `./dev.py test` exits 0, so the existing suites still pass.

## Verification
```
uv lock --check
uv run python -c "import PIL, numpy, skimage, imagehash, cv2"
./dev.py test
```

## Definition of rejected
Any change to `[project.dependencies]`, torch or open-clip-torch in the `dev` group, a hand-edited `uv.lock`, a lock that fails `uv lock --check`, or any file outside the fence changed.

## Time budget
- expected: 12m
- stuck: 24m
