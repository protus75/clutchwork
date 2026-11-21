---
state: draft
source: human
priority: P3
kind: chore
---

## Depends on
- evidence-envelope

## Context
- docs/roadmap.md#6. Owner decisions (decided 2026-11-13)
- docs/evidence-trail-plan.md#1. Record layout
- clutch/driver.py::Spool
- clutch/stages.py::check_render
- clutch/retro.py
- tests/unit/test_stages_render_check.py

## Goal / Why
Roadmap row 183, the first of the two slices that precede `spools-onto-evidence-store` (decision 12). Two kinds of file live under `<state_dir>/spools/` that an agent opens by path, so `spools-onto-evidence-store` could not serve them from compressed blobs: the graphics render directory (`<state_dir>/spools/<stem>/<attempt>/render/`, the artifacts the visual judge and `image_quality` read) and the retro on-demand window file (`<state_dir>/spools/retro/<sequence>/1/retro/call-NN/window.jsonl`, named by `events_path` in the retro prompt). After this ticket both live under `<state_dir>/scratch/`: the render directory at `<state_dir>/scratch/<stem>/<attempt>/render/` and the window file at `<state_dir>/scratch/retro/<sequence>/call-NN/window.jsonl`. `<state_dir>/scratch/` is new; the evidence store's own temporary files stay in `<state_dir>/evidence/scratch/`. `Spool` itself, its other writers, and every other `spools/` path are untouched.

## Boundary contract
### Agent-read scratch files
- disposition: extend
- owner: clutch/stages.py and clutch/retro.py, each for its own path
- consumers: Check's graphics gates (`image_quality`, the visual judge, candidate selection) read the render directory; the retro model reads `events_path`; `spools-onto-evidence-store` later removes `spools/` without touching these files
- observable change: the two path prefixes above move from `<state_dir>/spools/` to `<state_dir>/scratch/`; file names, contents, redaction of the window file, and the `render_dir` and `events_path` values' form (an absolute path string) are unchanged
- compatibility: a render directory or window file already under `spools/` is a stale capture; nothing reads it, no migration, no dual read
- acceptance: the unit test below asserts the new paths and that the old ones are absent
- tests: `tests/unit/test_scratch_dir_paths.py`, `tests/unit/test_stages_render_check.py`, `tests/unit/test_stages_candidates_select.py`, `tests/unit/test_images_gate.py`, `tests/integration/test_image_candidates_select.py`, `tests/integration/test_retro.py`
- post-merge source of truth: `clutch/stages.py::render_scratch_dir` and `clutch/retro.py::window_scratch_path`

## Scope in / Scope out
Scope in:
- `clutch/stages.py`: add `render_scratch_dir(state_dir: Path, stem: str, attempt: int) -> Path` returning `state_dir / "scratch" / stem / str(attempt) / "render"`. Use it, passing `ctx.config.state_dir`, at the three places that build the `.../render` path today: `gather_evidence`'s `render_dir` value, the artifact copy in `check_render`, and the `spool` variable in `check_candidates`, which holds the render directory (rename that variable to `render`). Nothing else changes in this file.
- `clutch/retro.py`: add `window_scratch_path(state_dir: Path, sequence: int, call_seq: int) -> Path` returning `state_dir / "scratch" / "retro" / str(sequence) / f"call-{call_seq:02d}" / "window.jsonl"`. In `render_input`, write the window file there with `driver.spool._fs.write(path, driver.redactor.scrub(text).encode())` (the form `commit_report` already uses, so the redaction stays) instead of `driver.spool.write`, and set `events_path` to `str(path.resolve())`. Nothing else changes in this file.
- `docs/how-clutch-works.md`: add one `scratch/` row to the state-dir table (section 10.1, after `spools/`) naming the graphics render directory and the retro window file, as files agents read by path, distinct from `evidence/scratch/`.
- Tests: the unit `ctx` stand-ins gain `state_dir=<tmp>` on their `config` SimpleNamespace and nothing else (no getattr fallback): `tests/unit/test_stages_render_check.py`, `tests/unit/test_stages_candidates_select.py`, and `tests/unit/test_images_gate.py::test_check_runs_render_before_gate`, whose `render` path becomes `stages.render_scratch_dir(<state_dir>, "work", 2)`. `tests/unit/test_stages_render_check.py` and `tests/integration/test_image_candidates_select.py` assert the render path under `state_dir / "scratch"`; `tests/integration/test_retro.py` asserts the window file under `state_dir / "scratch/retro/1/call-01/window.jsonl"` and that no `window.jsonl` exists under `spools/`. A new `tests/unit/test_scratch_dir_paths.py` covers both helpers (their floors in `test-gate.toml` need a fenced unit test) with `tmp_path`.

Scope out: `Spool`, `clutch/driver.py`, harvest, the evidence store, `evidence/scratch/`, every other `spools/` writer, reader, test, and doc line (`spools-onto-evidence-store` moves those), any cleanup of `scratch/` (state-dir files are not pruned today; nothing here adds pruning). The roadmap row is not edited; the driver rewrites it.

Merge order: many confirmed tickets fence `clutch/stages.py`, `clutch/retro.py`, `docs/how-clutch-works.md` and these tests; this ticket's edits are one helper plus two or three call lines in separate regions, so either order merges textually. `graphics-render-check`, `image-quality-gate-wiring` and `image-candidates-select-r1` rewrite render-path tests: if one merges after this ticket it must build the path with `render_scratch_dir`, and if before, this ticket's test edits follow its text.

## Scope fence
- clutch/stages.py
- clutch/retro.py
- docs/how-clutch-works.md
- tests/unit/test_scratch_dir_paths.py
- tests/unit/test_stages_render_check.py
- tests/unit/test_stages_candidates_select.py
- tests/unit/test_images_gate.py
- tests/integration/test_image_candidates_select.py
- tests/integration/test_retro.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_scratch_dir_paths.py` shows `render_scratch_dir(tmp, "work", 4)` equals `tmp / "scratch/work/4/render"`, not a path under `spools`, and `window_scratch_path(tmp, 1, 2)` equals `tmp / "scratch/retro/1/call-02/window.jsonl"`.
2. `./dev.py test tests/unit/test_stages_render_check.py` shows a successful render copy lands at `state_dir / "scratch/work/4/render/output/a.png"` and nothing is written under `spools/work/4/render`.
3. `./dev.py test tests/integration/test_image_candidates_select.py` shows the side-by-side and heatmap files under `scratch/<stem>/0/render/a0` and no `render` directory under `spools/`.
4. `./dev.py test tests/integration/test_retro.py` shows an over-bound window writes `window.jsonl` at the scratch path, `events_path` equals that path, its lines equal the journal events, and `spools/` holds no `window.jsonl`.
5. `docs/how-clutch-works.md` section 10.1 has a `scratch/` row naming both file kinds, read by eye in review.

## Verification
```
./dev.py test tests/unit/test_scratch_dir_paths.py tests/unit/test_stages_render_check.py tests/unit/test_stages_candidates_select.py tests/unit/test_images_gate.py tests/integration/test_image_candidates_select.py tests/integration/test_retro.py
```

## Definition of rejected
- Any change to `Spool`, `driver.py`, or a `spools/` path other than the two moved files.
- A fallback read of the old `spools/` locations, or a migration of existing files.
- A change to the window file's redaction or the render directory's file layout beneath `render/`.

## Time budget
- expected: 15m
- stuck: 30m
