---
state: rejected
source: human
priority: P2
kind: feature
---

## Depends on
- route-kinds-filter
- graphics-kind

## Context
- clutch/providers.py::resolve
- clutch/providers.py::candidates
- clutch/doctor.py::check
- clutch/__main__.py::_lint
- clutch/__main__.py::stuck_ceiling_finding
- docs/gemini-graphics-refactor-plan.md#B3. Routing by ticket kind (`route-kinds-filter`)
- docs/gemini-graphics-refactor-plan.md#B5. Layer 2: the vision-model judge (`visual-review-surface`)

## On-demand
- docs/how-clutch-works.md
- clutch/docs/host-running.md

## Goal / Why
Part three of roadmap row 51 (Gemini plan B3, "Judge independence"). The owner's rule: the visual judge of a graphics ticket must be a general multimodal model, never the image model that produced the candidate, because a judge from the generator's family rates its own work kindly (plan "Risks", judge self-grading). Once `route-kinds-filter` lets a host route `graphics` Implement calls to their own model, nothing stops a config from routing the `review_visual` surface to that same model. After this ticket, `clutch host doctor` reports a FAIL row named `judge`, and `clutch ticket lint` reports a finding on every `kind: graphics` ticket, when any candidate that would serve `review_visual` for a graphics ticket has the same provider and model as any candidate that would serve its `implement` call. Each message names the tier, the shared provider and model, and the road: route `review_visual` for graphics to a general multimodal model of another family in `config.yaml`. The check lands before `visual-review-surface` (row 53) adds the judge call, so a host sees the problem at setup.

## Boundary contract
### Judge independence check
- disposition: create
- closest existing: clutch/providers.py::resolve and clutch/providers.py::candidates choose a row; clutch/doctor.py::check's `parallel` row inspects routing
- earning reason: two production consumers (`host doctor` and `ticket lint`) need the same decision, and neither existing function compares two surfaces' candidates
- owner: clutch/providers.py (one new public function `shared_judge(config, tier) -> str | None`)
- consumers: clutch/doctor.py::check, clutch/__main__.py::_lint
- observable change: `shared_judge` returns a message when a `(provider, model)` pair is in both `candidates(config, tier, "review_visual", "graphics")` and `candidates(config, tier, "implement", "graphics")`, else None; a `ProviderSetupError` from either lookup returns None, because an unroutable row is reported by the routing and preflight checks
- compatibility: a config where the pairs are disjoint gets no new doctor row and no new lint finding; the doctor row is emitted only on failure, like the `parallel` row, so every existing doctor row list is unchanged
- acceptance: criteria 1 to 4
- tests: tests/unit/test_route_kinds_judge.py, tests/integration/test_route_kinds_judge_lint.py
- post-merge source of truth: clutch/providers.py::shared_judge

### host doctor and ticket lint output
- disposition: extend
- owner: clutch/doctor.py::check and clutch/__main__.py::_lint
- consumers: operators, `clutch host doctor` and `clutch ticket lint` callers, the extension's doctor and lint commands
- observable change: doctor appends `FAIL judge: <messages>` when `shared_judge` returns a message for any tier in `clutch.policy.TIERS`; lint prints one finding for a `kind: graphics` ticket when `shared_judge(config, ticket.frontmatter.agent_tier)` returns a message, and that ticket counts as not valid (exit 1)
- compatibility: non-graphics tickets and disjoint configs print exactly what they print today
- acceptance: criteria 3 and 4
- tests: tests/unit/test_route_kinds_judge.py, tests/integration/test_route_kinds_judge_lint.py
- post-merge source of truth: clutch/doctor.py, clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/providers.py`: add `shared_judge(config, tier)` as described, reusing `candidates`.
- `clutch/doctor.py`: after the `parallel` check, when config loaded, collect `shared_judge` for each tier and emit one `judge` FAIL row joining the messages when any is present; no row otherwise.
- `clutch/__main__.py`: in `_lint`, for a valid `kind: graphics` ticket, add the `shared_judge` message as a printed finding beside the ceiling finding, with the same exit-code effect. Update the `does=` help text of `host doctor` and of `ticket lint` to name the check.
- `docs/how-clutch-works.md`: only the `ticket lint` and `host doctor` rows of the section 2 verb table.
- `clutch/docs/host-running.md`: only the `host doctor` and `ticket lint` rows of the verb table.
- New `tests/unit/test_route_kinds_judge.py` (configs under `tmp_path`, fake exec for doctor) and `tests/integration/test_route_kinds_judge_lint.py` (runs `clutch ticket lint` on a temporary repo).

Scope out:
- Deciding that a model is an image model, or that two models are one family, beyond equal `(provider, model)` pairs: clutch has no model-type registry, and the plan's "different family where possible" is guidance the check cannot decide.
- The `review_visual` spec and its call (`visual-review-surface`), the routing schema and resolver (`route-kinds-filter`), drought and rung (`route-kinds-filter-admission`).
- Intake, review and drain refusals; `ticket new`'s post-write lint; this repo's `config.yaml`; `clutch/help.py`, which reuses the `clutch/docs/host-running.md` rows.

## Scope fence
- clutch/providers.py
- clutch/doctor.py
- clutch/__main__.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/unit/test_route_kinds_judge.py
- tests/integration/test_route_kinds_judge_lint.py

## Acceptance criteria
1. With medium rows `implement kinds:[graphics] -> gemini/img` and `review_visual -> gemini/img`, `shared_judge(cfg, "medium")` returns a message containing `gemini`, `img` and `review_visual`; with `review_visual -> gemini/pro` it returns `None`, not a message; checked by `./dev.py test tests/unit/test_route_kinds_judge.py`.
2. With no `review_visual` row and a medium `review` row whose candidates include `gemini/img`, `shared_judge(cfg, "medium")` returns a message (the review fallback is what would serve the judge), and with a config whose graphics lookup raises `ProviderSetupError` it returns `None`, not an exception; checked by `./dev.py test tests/unit/test_route_kinds_judge.py`.
3. With a fake exec, `doctor.check` on the shared config yields a result named `judge` with `passed is False`, and on a disjoint config yields the names `["venv", "config", "git", "lock", "journal", "core"]` with no `judge` row; checked by `./dev.py test tests/unit/test_route_kinds_judge.py`.
4. On a temporary repo with the shared config, `clutch ticket lint` on a valid `kind: graphics` ticket exits 1 and prints the judge message, and on a `kind: feature` ticket exits 0 with no judge message; with a disjoint config the graphics ticket exits 0; checked by `./dev.py test tests/integration/test_route_kinds_judge_lint.py`.
5. Every existing test passes, including `tests/integration/test_doctor.py`, `tests/unit/test_main_host_group.py` and `tests/unit/test_main_help.py`; checked by `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_route_kinds_judge.py tests/integration/test_route_kinds_judge_lint.py
./dev.py test
```

## Definition of rejected
The doctor emits a `judge` row on a disjoint config; a non-graphics ticket gets a judge finding; the candidate comparison is reimplemented outside `providers.candidates`; a provider or model name list is hard-coded as "image models".

## Time budget
- expected: 25m
- stuck: 50m
