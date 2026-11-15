---
state: confirmed
source: human
priority: P3
kind: chore
---

## Depends on
- specs-move

## Context
- clutch/box.py
- clutch/retro.py

## On-demand
- clutch/drain.py
- clutch/merge.py
- clutch/tickets.py
- clutch/author.py
- clutch/triage.py
- docs/how-clutch-works.md
- docs/host-contract.md

## Goal / Why
`specs-move` moved the prompt specs from `<repo>/specs/` to `clutch/specs/` so a PyPI install carries them (2026-11-06). The code that matches spec paths in a diff or a ticket, the stored-path handling for box proposals, and the docs still name `specs/`. This is the second of two tickets replacing `specs-in-package`.

After this change every repo-path matcher, model-facing spec path, and doc names `clutch/specs/`.

## Scope in / Scope out
- In: repo-path matchers:
  - `drain.UPGRADE_PREFIXES` becomes `("clutch/",)`, which already covers the specs, and the module docstring says so;
  - `merge.py`'s changed-spec regex matches `clutch/specs/[^/]+\.md`;
  - the `tickets.py` check that refuses a spec file in `## Context` matches a parent of `clutch/specs`.
- In: stored box data stays valid. `Message.proposed_spec_paths` (`box.py`) and `RetroProposal.proposed_spec_paths` (`retro.py`) keep their `^specs/[a-z0-9_-]+\.md$` pattern, because `Box.messages` re-validates every stored box file. The field now means a spec path relative to the `clutch/` package:
  - `clutch/specs/retro.md` says "`specs/<name>.md` paths, relative to the `clutch/` package" instead of "repo-relative `specs/<name>.md` paths", and its `version` minor number goes up by one;
  - `author.py` and `triage.py` prefix each value with `clutch/` where they put `proposed_spec_paths` into a model request, so the model sees the real repo path.
- In: docstrings naming `specs/review.md` or `specs/implement.md` in `clutch/artifacts.py` and `clutch/stages.py`.
- In: tests that assert the values changed above: `tests/test_closed_sets.py`, `tests/test_drain_upgrade.py`, `tests/test_merge.py`, `tests/test_tickets.py`, `tests/test_author.py`, `tests/test_triage.py`, `tests/test_retro_box.py`, `tests/test_retro.py` (pinned retro `spec_version` moves to the new version), `tests/test_status.py` (its `version:` replace looks for the new version).
- In: docs.
  - `docs/how-clutch-works.md`: every repo `specs/` path (sections 1, 4.2, 4.4, 6.3, 6.5, 7.1 self-upgrade and the serve sentence recording the `clutch` and `specs` trees, now `clutch` only, and 8.4).
  - `docs/host-contract.md`: the `engine_plane_safety_inventory` example and the Instance custody sentence on restarting when `clutch/` or `specs/` changes.
- Out:
  - the spec move, loaders, `serve.py`, `config.yaml` (done in `specs-move`);
  - the `proposed_spec_paths` validation pattern, stored box files, journal events;
  - spec content beyond the one `retro.md` sentence and its version;
  - `pyproject.toml`; `CLUTCH_PLAN.md`.

## Scope fence
- clutch/drain.py
- clutch/merge.py
- clutch/tickets.py
- clutch/author.py
- clutch/triage.py
- clutch/artifacts.py
- clutch/stages.py
- clutch/specs/retro.md
- docs/how-clutch-works.md
- docs/host-contract.md
- tests/test_closed_sets.py
- tests/test_drain_upgrade.py
- tests/test_merge.py
- tests/test_tickets.py
- tests/test_author.py
- tests/test_triage.py
- tests/test_retro_box.py
- tests/test_retro.py
- tests/test_status.py

## Acceptance criteria
1. `drain.UPGRADE_PREFIXES == ("clutch/",)`. The first Verification command and `tests/test_closed_sets.py` check it.
2. A merged commit touching `clutch/specs/b.md` triggers the drain handoff in `tests/test_drain_upgrade.py`, and `merge.py` reports `clutch/specs/a.md` and `clutch/specs/z.md` as `changed_spec_paths` in `tests/test_merge.py`.
3. A ticket whose `## Context` lists `clutch/specs/review.md` gets the "prompt spec" finding in `tests/test_tickets.py`.
4. A box message with `proposed_spec_paths: ["specs/review.md"]` still loads through `Box.messages`, and the Author and Triage requests built from it hold `clutch/specs/review.md`, not `specs/review.md`. A test in `tests/test_author.py` and a test in `tests/test_triage.py` check this.
5. `uv run pytest -q` exits 0.

## Verification
```
uv run python -c "from clutch import drain; assert drain.UPGRADE_PREFIXES == ('clutch/',)"
uv run pytest -q
```

## Definition of rejected
Reject the branch if any of the following holds:
- both `specs/` and `clutch/specs/` repo paths are accepted by any matcher (no dual path);
- the `proposed_spec_paths` pattern changes, or a stored box file would fail to load;
- spec text changes beyond the one `retro.md` sentence and its version.

## Time budget
- expected: 60m
- stuck: 150m
