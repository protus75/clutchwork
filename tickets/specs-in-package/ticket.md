---
state: rejected
source: human
priority: P3
kind: chore
---

## Depends on
none

## Context
- clutch/runner.py
- clutch/policy.py
- config.yaml

## On-demand
- clutch/drain.py
- clutch/serve.py
- clutch/merge.py
- clutch/tickets.py
- clutch/author.py
- clutch/triage.py
- clutch/box.py
- clutch/retro.py
- eval/harness.py
- eval/diagnose.py
- docs/how-clutch-works.md
- docs/host-contract.md

## Goal / Why
clutch is to ship on PyPI so a host installs it with `uv tool install clutch` instead of running it from a clutch checkout (2026-11-06). A wheel carries only the `clutch/` package. The prompt specs live outside it, in `<repo>/specs/`, and every loader finds them as `Path(__file__).resolve().parent.parent / "specs"`. An installed engine therefore has no prompts.

After this change:
- the specs live in `clutch/specs/`;
- every loader resolves them as `Path(__file__).resolve().parent / "specs"`, one path for a checkout and an install alike;
- `<repo>/specs/` no longer exists.

## Scope in / Scope out
- In: `git mv specs clutch/specs`, including any subdirectory present at the time (for example `specs/ask/` if `ask-prompt-verb` has merged). Spec text is unchanged except `clutch/specs/retro.md`, below.
- In: engine loaders resolve `clutch/specs/`:
  - `runner.SPECS_DIR` and `policy.SPECS`;
  - `clutch/ask.py`, if it exists;
  - `eval/harness.py` and `eval/diagnose.py` (`SPECS` and the docstring and help text naming `specs/review.md`);
  - the spec-version read in `watch.py`, or in `clutch/observe.py` if `observe-verbs-host-extension` has merged.
- In: repo-path matchers that look for spec files in a diff or ticket now look under `clutch/specs/`:
  - `drain.UPGRADE_PREFIXES` becomes `("clutch/",)`, which already covers the specs, and the module docstring says so;
  - `serve.engine_trees` reads only `HEAD:clutch`, and the `serve_handoff` signal body drops its `specs` key;
  - `merge.py`'s changed-spec regex matches `clutch/specs/[^/]+\.md`;
  - the `tickets.py` check that refuses a spec file in `## Context` matches a parent of `clutch/specs`.
- In: stored box data stays valid. `Message.proposed_spec_paths` (`box.py`) and `RetroProposal.proposed_spec_paths` (`retro.py`) keep their `^specs/[a-z0-9_-]+\.md$` pattern, because `Box.messages` re-validates every stored box file and 25 of them hold that form today. The field now means a spec path relative to the `clutch/` package:
  - `clutch/specs/retro.md` says "`specs/<name>.md` paths, relative to the `clutch/` package" instead of "repo-relative `specs/<name>.md` paths";
  - `author.py` and `triage.py` prefix each value with `clutch/` where they put `proposed_spec_paths` into a model request, so the model sees the real repo path.
- In: `config.yaml` `engine_plane_safety_inventory` names `clutch/specs/` instead of `specs/`, so spec edits stay inventoried.
- In: tests that read the real spec files, or assert the paths and values changed above, follow the move.
- In: docs.
  - `docs/how-clutch-works.md`: every `specs/` path in sections 1, 4.2, 4.4, 6.3, 6.5, 7.1 (self-upgrade) and 8.4.
  - `docs/host-contract.md`: the `engine_plane_safety_inventory` example and the Instance custody sentence on restarting when `clutch/` or `specs/` changes.
- Out:
  - spec content beyond the one `retro.md` sentence;
  - spec versions and the baseline identity (`baseline_identity` reads versions, not paths);
  - stored box files and journal events;
  - packaging (`pyproject.toml`), which is `pypi-package`;
  - `CLUTCH_PLAN.md`.

## Scope fence
- specs/
- clutch/specs/
- clutch/runner.py
- clutch/policy.py
- clutch/drain.py
- clutch/serve.py
- clutch/merge.py
- clutch/tickets.py
- clutch/author.py
- clutch/triage.py
- clutch/ask.py
- clutch/observe.py
- watch.py
- eval/harness.py
- eval/diagnose.py
- config.yaml
- tests/test_author.py
- tests/test_baseline.py
- tests/test_closed_sets.py
- tests/test_diagnose_eval.py
- tests/test_drain_upgrade.py
- tests/test_eval_harness.py
- tests/test_fixture_host.py
- tests/test_merge.py
- tests/test_requisition.py
- tests/test_retro_box.py
- tests/test_serve.py
- tests/test_specs.py
- tests/test_stages.py
- tests/test_tickets.py
- tests/test_triage.py
- tests/test_watchdog_activation.py
- tests/test_ask.py
- tests/test_watch.py
- docs/how-clutch-works.md
- docs/host-contract.md
- clutch/__main__.py
- clutch/artifacts.py
- clutch/stages.py
- clutch/box.py
- clutch/retro.py
- tests/test_config.py
- tests/test_driver.py
- tests/test_echo_stage.py
- tests/test_llm_effect.py
- tests/test_mergequeue.py
- tests/test_policy.py
- tests/test_provider_cooldown_failover.py
- tests/test_retro.py
- tests/test_status.py

## Acceptance criteria
1. `specs/` does not exist and `clutch/specs/review.md` does. The first Verification command checks both, and fails if `runner.SPECS_DIR` is not `clutch/specs`.
2. `drain.UPGRADE_PREFIXES == ("clutch/",)`, not `("clutch/", "specs/")`. `tests/test_closed_sets.py` asserts it.
3. A merged commit touching `clutch/specs/b.md` triggers the drain handoff in `tests/test_drain_upgrade.py`, and `merge.py` reports `clutch/specs/a.md` and `clutch/specs/z.md` as `changed_spec_paths` in `tests/test_merge.py`.
4. A ticket whose `## Context` lists `clutch/specs/review.md` gets the "prompt spec" finding in `tests/test_tickets.py`.
5. A box message with `proposed_spec_paths: ["specs/review.md"]` still loads through `Box.messages`, and the Author request built from it holds `clutch/specs/review.md`, not `specs/review.md`. A test in `tests/test_author.py` checks this.
6. `config.yaml` lists `clutch/specs/` in `engine_plane_safety_inventory`. The second Verification command checks it.
7. `uv run pytest -q` exits 0.

## Verification
```
uv run python -c "from pathlib import Path; from clutch import runner, policy; assert not Path('specs').exists() and Path('clutch/specs/review.md').is_file(); assert runner.SPECS_DIR == policy.SPECS == Path('clutch/specs').resolve()"
uv run python -c "from clutch.config import load_config; from pathlib import Path; assert 'clutch/specs/' in load_config(None, cwd=Path('.')).engine_plane_safety_inventory"
uv run pytest -q
```

## Definition of rejected
Reject the branch if any of the following holds:
- any loader still resolves specs outside the `clutch/` package;
- both `specs/` and `clutch/specs/` paths are accepted anywhere (no dual path);
- the `proposed_spec_paths` pattern changes, or a stored box file would fail to load;
- spec text changes beyond the one `retro.md` sentence;
- `pyproject.toml` changes.

## Time budget
- expected: 75m
- stuck: 180m
