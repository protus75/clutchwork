---
state: confirmed
source: human
priority: P1
kind: bug
---

## Depends on
- none

## Context
- clutch/observe.py::capability
- clutch/observe.py::frontmatter
- clutch/observe.py::current_step
- clutch/observe.py::running_stems
- clutch/observe.py::text_snapshot
- clutch/caps.py::lineage
- clutch/caps.py::capability
- clutch/runner.py::drive
- clutch/requisition.py::review_ticket
- clutch/stages.py::diagnose
- clutch/stages.py::review
- clutch/daemon.py::apply_rework
- tickets/watch-surface-tier-truth/evidence/watch-tier-mismatch.txt
- tickets/watch-surface-tier-truth/evidence/watch-tier-repro.py
- tests/integration/test_watch.py::test_text_snapshot_folds_the_whole_journal
- tests/integration/test_watch.py::test_running_needs_a_live_lock_holder_that_journaled_it
- tests/regress_provider_capture_overwrite.py

## Goal / Why
`clutch watch` prints, under `Now:` for a running ticket, the line `asked for tier/effort <tier>/<effort>`. It is wrong for every step except Implement. `clutch/observe.py::capability` returns the ticket's effective capability only when the surface is `implement`. For every other surface it returns the `tier:` and `effort:` from the prompt spec's frontmatter (`clutch/specs/<surface>.md`). The engine does not use those values for any step a running ticket can be on:

- `clutch/runner.py::drive` replaces the ticket's `agent_tier`/`agent_effort` with `clutch/caps.py::capability` (the latest retry rung after the last operator keep, else the frontmatter). `clutch/stages.py::implement`, `::review` and `::diagnose` pass that pair to the driver.
- `clutch/daemon.py::apply_rework` passes `runner.capability` of the committed ticket to Rework.
- `drive` passes that tier to `clutch/requisition.py::review_ticket`, which builds its request with `tier=tier, effort=spec.meta.effort`. Requisition review is the one step that pairs the ticket's tier with its spec's effort.

Reproduced at HEAD (`tickets/watch-surface-tier-truth/evidence/watch-tier-mismatch.txt`, produced by `evidence/watch-tier-repro.py` driving `text_snapshot` on a sandbox host). A ticket with the default `medium`/`medium` capability shows `high/high` on Review and Rework, `high/medium` on Diagnose, and `high/high` on Requisition. The engine passes `medium/medium`, `medium/medium`, `medium/medium` and `medium/high` respectively. The engine side is pinned by tests that pass at HEAD: `tests/integration/test_ladder.py::test_escalation_rung_reaches_next_implement_without_editing_ticket` (reviews follow the ticket and rung), `tests/integration/test_diagnose.py::test_review_snag_orders_harvest_draw_effect_signal_and_terminal` (diagnose at the ticket's `medium`), and `tests/integration/test_rework.py::test_escalate_order_does_not_edit_capability_or_draw_caps` (rework at the ticket's capability). So the code is the truth, and watch is what must change. An operator watching a Review sees an opus-tier, high-effort call that never happens. That is the figure they would act on when deciding whether a slow or failing step was under-powered.

When this ticket is done, the line shows the tier and effort the engine passes, for every surface a running ticket can be on. That is the ticket's effective capability for `implement`, `review`, `diagnose` and `rework`. For `requisition_review` it is the effective tier paired with `requisition_review.md`'s `effort:`. A ticket on an escalation rung shows the rung with ` (escalated)` on every surface, as Implement already does.

## Scope in / Scope out
Scope in, all in `clutch/observe.py::capability`:
- Remove the branch that returns `clutch/specs/<surface>.md` frontmatter for surfaces other than `implement`. Every surface computes the effective capability with the function's existing rung fold: the latest `retry` `cap_consumed` rung after the last operator `keep`, shown as `<tier>/<effort> (escalated)`, else the ticket's `agent_tier`/`agent_effort` with `medium` defaults.
- For `surface == "requisition_review"` only, the effort shown is the `effort` value from `clutch/specs/requisition_review.md`'s frontmatter, read with the module's existing `frontmatter` helper. The tier is still the effective tier, and the ` (escalated)` suffix still applies when a rung is active.
- Rewrite the docstring to say this.
- Keep the signature `capability(ctx, events, stem, surface) -> str` and the `<tier>/<effort>` and ` (escalated)` formats, so the carried test runs against the base code.

Also in scope, two new test files:
- `tests/integration/test_watch_surface_tier.py` holds the acceptance tests below. They write the ticket under `tmp_path`. The `text_snapshot` test copies the setup of `tests/integration/test_watch.py`: `config.yaml` from `tests.integration.test_config.VALID`, `watch.processes` and `watch.committed_ticket_shas` monkeypatched, and `clutch.lock` naming `os.getpid()`.
- `tests/regress_watch_surface_tier_truth.py`, in the shape of `tests/regress_provider_capture_overwrite.py`. It runs `pytest.main` on `tests/integration/test_watch_surface_tier.py`, with `-q -p no:cacheprovider` and stdout redirected to stderr. It prints exactly one `regression_result` JSON line: exit 0 → `pass`/0, exit 1 → `defect`/1, anything else → `error`/2.

Scope out:
- Every engine call site. The tier and effort that `clutch/runner.py`, `clutch/stages.py`, `clutch/requisition.py`, `clutch/daemon.py`, `clutch/author.py`, `clutch/triage.py`, `clutch/retro.py` and `clutch/__main__.py` pass do not change. The prompt specs' frontmatter and `clutch/specs/__init__.py::SpecMeta` do not change either.
- Making the engine and watch share one function that owns each surface's (tier, effort). `observe.capability` keeps its own copy of the rung fold, which uses the same window as `clutch/caps.py::lineage` at HEAD. Deciding whether spec `tier:` is honored or removed is also out. Both are the cause fix, filed as Suggestion Box `box-000475-4d3dbe7a`.
- Surfaces with no ticket (`author`, `triage`, `retro`). `running_stems` lists only ticket stems journaled `running`, so these surfaces never reach the `Now:` block. The `clutch review` verb and the Author gate's requisition review journal no `running` either.
- `observe.snapshot` and the VS Code extension. The snapshot does not call `capability`, so no snapshot field, JavaScript reader or `clutch/help.py` entry changes.
- Documentation. No document describes the `asked for tier/effort` line: `docs/how-clutch-works.md` and `clutch/docs/host-running.md` describe `watch` only as the live text view.
- `tests/integration/test_watch.py`. New tests go in the new file.

## Scope fence
- clutch/observe.py
- tests/integration/test_watch_surface_tier.py
- tests/regress_watch_surface_tier_truth.py

## Acceptance criteria
1. `tests/integration/test_watch_surface_tier.py::test_ticket_surfaces_show_the_ticket_capability` writes `tickets/alpha/ticket.md` with frontmatter `agent_tier: low` and `agent_effort: max`. With no events, it asserts `watch.capability(ctx, [], "alpha", surface) == "low/max"` for each of `implement`, `review`, `diagnose` and `rework`. Ruled out: `high/high` for review and rework and `high/medium` for diagnose, which are today's spec values; and `medium/medium`, which a fix that ignored the ticket's frontmatter would give.
2. `tests/integration/test_watch_surface_tier.py::test_requisition_review_pairs_ticket_tier_with_spec_effort` reads `effort = load_spec((Path(clutch.__file__).parent / "specs" / "requisition_review.md").read_text()).meta.effort` and asserts `effort != "max"`, so the case stays discriminating. For the same ticket it asserts `watch.capability(ctx, [], "alpha", "requisition_review") == f"low/{effort}"`. Ruled out: `high/high`, which is today's spec tier, and `low/max`, which takes the ticket's effort instead of the one the request uses.
3. `tests/integration/test_watch_surface_tier.py::test_escalation_rung_shows_on_every_ticket_surface` journals one `cap_consumed` event for `alpha` with body `{"cap": "retry", "ticket_sha": "x", "rung": {"tier": "max", "effort": "medium"}}`. It asserts `capability(..., "review") == "max/medium (escalated)"` and `capability(..., "requisition_review") == f"max/{effort} (escalated)"`. Ruled out: `high/high`, which is today's result; and `low/max` or `low/high`, which ignore the rung the engine uses.
4. The same file's `test_operator_keep_resets_the_rung_on_review` appends, after that rung, a `signal` event for `alpha` with body `{"signal": "reject_verdict", "verdict": "keep", "actor": "operator"}`. It asserts `capability(..., "review") == "low/max"`, not `max/medium (escalated)`, matching `clutch/caps.py::capability`'s keep window.
5. The same file's `test_watch_now_line_shows_the_engine_capability` sets up a sandbox like `evidence/watch-tier-repro.py`: a live lock holder (`os.getpid()`), `alpha` journaled `running` after the lock's `started_at`, and an `engine.log` `stage_start` for `alpha` on surface `review`. It asserts `watch.text_snapshot(ctx)` contains the line `     asked for tier/effort low/max`. Ruled out: `asked for tier/effort high/high`.
6. `uv run python tests/regress_watch_surface_tier_truth.py` prints exactly `{"regression_result": "pass"}` and exits 0 on the branch head. On the merge base, with the carried files copied over it, it prints `{"regression_result": "defect"}` and exits 1.
7. `./dev.py test tests/integration/test_ladder.py tests/integration/test_diagnose.py tests/integration/test_rework.py tests/integration/test_watch.py` exits 0 with those files unchanged, so the tiers the engine passes and the existing watch behavior are unchanged.
8. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_watch_surface_tier.py
uv run python tests/regress_watch_surface_tier_truth.py
./dev.py test tests/integration/test_ladder.py tests/integration/test_diagnose.py tests/integration/test_rework.py tests/integration/test_watch.py
./dev.py test
```

## Definition of rejected
- Any engine call site changes the tier or effort it passes to a model call, or any `clutch/specs/*.md` frontmatter changes. This ticket aligns the display with the code, never the code with the display.
- `watch` still shows a prompt spec's `tier:` for any surface a running ticket can be on.
- The change adds a config knob, a CLI flag, a snapshot field, or extension code, or edits `tests/integration/test_watch.py`.

## Time budget
- expected: 25m
- stuck: 60m

## Regression
```
uv run python tests/regress_watch_surface_tier_truth.py
```
- carries: tests/regress_watch_surface_tier_truth.py
- carries: tests/integration/test_watch_surface_tier.py
