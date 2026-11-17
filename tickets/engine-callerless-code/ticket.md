---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
none

## Context
- clutch/heartbeat.py
- clutch/timers.py::Timers
- clutch/git.py::Git.branch
- clutch/effects.py::effect
- clutch/requisition.py::_base_render
- clutch/requisition.py::base_render_chars
- clutch/requisition.py::RequisitionGate
- clutch/watchdog.py::watch_deadline
- clutch/watchdog.py::Detector
- clutch/driver.py::Driver.race
- tests/integration/test_watchdog_activation.py::test_production_hard_timeout_group_kill_is_harvested
- clutch/mergequeue.py::MergeQueue.retained_ticket
- clutch/serve.py::Serve.reconstruct_admissions
- clutch/serve.py::Responsiveness
- clutch/runner.py::pipeline
- clutch/stages.py::render_review
- clutch/stages.py::read_review
- clutch/stages.py::dirty_code

## Goal / Why
Roadmap row 127 (`docs/roadmap.md` §3.5, recurred in 0.3.0; merged row 25 did not cover it) lists engine symbols with no engine caller. Seven of them are called at HEAD only by their own tests, so they are reviewed, kept green and read by every agent while describing behavior the engine never runs:

- `clutch/heartbeat.py::is_fresh`: its docstring promises "an outside watcher", but no verb, module, harness or doc calls it; the design record's external heartbeat is a systemd timer or cron checking the file's mtime (`CLUTCH_PLAN.md` section 9). Callers: `tests/integration/test_heartbeat.py` only.
- `clutch/timers.py::Timers.wait_next`: the engine fires timers with `fire_due` (`clutch/restart.py`, `clutch/serve.py`, `clutch/__main__.py`). Callers: `tests/integration/test_restart_timers.py` only.
- `clutch/git.py::Git.branch`: the engine creates branches with `worktree_add -b`. Callers: `tests/integration/test_git.py` only.
- `clutch/effects.py::effect` (the decorator): callers `tests/integration/test_llm_effect.py` only; the engine calls `Effects.run` directly.
- `clutch/requisition.py::RequisitionGate` and `base_render_chars`: callers `tests/integration/test_requisition.py` only. `review_ticket` measures through `_base_render`, which stays.
- `clutch/watchdog.py::Detector.watch`: a second stuck-deadline path beside the one production runs (`Driver.race` with `watch_deadline`). Callers `tests/integration/test_watchdog.py` only, so its timeout tests prove nothing about the engine. That violates the conduct rule "No dual-path code".

After this ticket those seven are gone, and the tests that only drove them are ported to the production path or deleted.

The row's other symbols have a caller and stay; this names each one:
- `Git.init`: `tests/harness/host_loop.py`, `tests/harness/daemon_soak.py`, `tests/harness/reliability_battery.py`, `tests/harness/shakeout/bench.py`, `tests/regress_retro_reemit_skip.py` and 25 call sites in 17 integration test files build their repositories with it. It is the test seam for "all git through `git.py`".
- `audit.audit`: `clutch/audit.py::audit_journal` and `tests/harness/shakeout/run.py`.
- `policy.baseline_identity`: `eval/harness.py` (four calls).
- `gates.lint_gate` and `providers.CliAdapter.parsed_failure`: `clutch/gates.py` and `clutch/providers.py` are on `engine_plane_safety_inventory` in `config.yaml`, so a ticket that fences them starts as a draft. Both are test seams (`tests/integration/test_gates.py`; `parsed_failure`'s own docstring says "Direct construction seam", used by `tests/integration/test_providers.py`). Neither is touched here.

The row's second half is three production paths with no test of their own (§3.5 "Untested production paths"). After this ticket each has a unit test in a new file that fails when its contract breaks; these are test-only additions.
- `mergequeue.MergeQueue.retained_ticket` re-admits a HELD merge receipt when serve restarts (`Serve.reconstruct_admissions`). No test calls it or `reconstruct_admissions`.
- `serve.Responsiveness` answers serve's liveness pings behind the heartbeat. `tests/integration/test_serve_lifecycle.py` reaches it only through a whole-serve rig that replaces `wait` for the component under test, so `wait`'s answer-while-working and cancel-the-owned-work behavior has no direct test.
- `runner.pipeline`'s `PreparedDispatch` builds the provider pipeline once per config snapshot for drain and run (`clutch/drain.py` calls `prepare()` at idle). `tests/integration/test_provider_cooldown_failover.py` passes it to drain but asserts nothing about its snapshot cache, its one-call use of a prepared callback, or `abort_current`.

## Scope in / Scope out
In:
- `clutch/heartbeat.py`: delete `is_fresh` and the imports only it used. The module docstring drops the `is_fresh` clause and says that serve refreshes the heartbeat file each healthy loop.
- `clutch/timers.py`: delete `Timers.wait_next`. Nothing else changes in this file.
- `clutch/git.py`: delete `Git.branch`. Nothing else changes in this file.
- `clutch/effects.py`: delete `effect` and the `functools` import.
- `clutch/requisition.py`: delete `base_render_chars` and `RequisitionGate`, and the `GateReport` import, which only `RequisitionGate` uses. `_base_render` and the `re` import stay.
- `clutch/watchdog.py`: delete `Detector.watch` and each import only it used (check `Cost`, `StageResult`, `_observe`, `LLMAborted` and `LLMResult`). `watch_deadline`, `WatchedLLM`, `Detector.start_call`, `flush_notifications` and `close_notifications` stay.
- `tests/integration/test_heartbeat.py`: import only `Heartbeat` from `clutch.heartbeat`. In `test_unhealthy_core_stops_refresh`, replace the two `is_fresh(...)` asserts with direct checks on the fake's recorded mtime: after the failed cycle and the clock advance, `fs.now - fs.metadata(heartbeat.path) > AGE`; after the healthy cycle, `fs.now - fs.metadata(heartbeat.path) <= AGE`. Delete `test_external_heartbeat_freshness` and `test_external_heartbeat_refuses_invalid_evidence`.
- `tests/integration/test_restart_timers.py`: in `test_timer_append_is_write_ahead`, replace `await owner.wait_next()` with `owner.fire_due()`; the timer there is armed at `time()`, so `wait_next` was already calling `fire_due` without sleeping. Delete `test_timer_deadline_wait_uses_injected_sleep`.
- `tests/integration/test_git.py`: drop the `g.branch` row from `test_op_argv`'s parameters and the `g.branch` block from `test_option_shaped_or_empty_refs_are_refused_before_exec`. In the conflicting-branch scenario, replace `g.branch(repo, "t-2", "HEAD~1")` followed by `g.worktree_add(repo, wt2, "t-3", "t-2")` with `g.worktree_add(repo, wt2, "t-3", "HEAD~1")`.
- `tests/integration/test_llm_effect.py`: delete `test_effect_decorator_keys_on_its_arguments_and_records_cost` and `test_singleton_effect_takes_a_bare_string_key`, and import only `Effects` from `clutch.effects`.
- `tests/integration/test_requisition.py`: drop the `RequisitionGate`, `base_render_chars` and `lint_gate` imports. `test_review_render_over_bound_is_mechanical_snag` sets `base` to the length of `clutch.requisition._base_render(repo, review_target(repo, "one-thing", TICKET), TICKET, SPECS)`. `test_base_render_matches_implement_and_gate` asserts `clutch.requisition._base_render(repo, ticket, TICKET, SPECS) == production` and drops its gate lines (`approved`, `snag`, `gate` and the two asserts on them).
- `tests/integration/test_watchdog.py`: port `test_missing_cost_preserves_adapter_refusal`, `test_meter_ignores_non_object_event_fields` and `test_watched_result_and_capture_are_preserved` to the meter shape production uses in `clutch/providers.py` (`operation`): `meter = rig.detector.start_call(served)`, then the same `client.call(...)` with `consumer=meter` (or the test's `start(meter)`), then `meter.complete()` after a successful call. Keep every existing assertion. Delete `test_watchdog_hard_timeout_group_cleanup` and `test_watchdog_real_group_cleanup`, which drive only `watch`'s own deadline. Production's stuck kill runs through `Driver.race` and `watch_deadline`, and `tests/integration/test_watchdog_activation.py::test_production_hard_timeout_group_kill_is_harvested` covers it unchanged.
- New `tests/unit/test_callerless_code_removed.py` (criterion 1).
- New `tests/unit/test_serve_responsiveness.py`, `tests/unit/test_runner_prepared_dispatch.py` and `tests/unit/test_mergequeue_retained_ticket.py` (criteria 9-17). They use fakes and `tmp_path` only: no process and no repo file. `test_runner_prepared_dispatch.py` monkeypatches `clutch.runner.snapshot_config` and `clutch.runner.prepare_pipeline` and passes a small dataclass checkout with `config` and `control` fields, because `prepare` calls `dataclasses.replace` on it. `test_mergequeue_retained_ticket.py` builds `MergeQueue(ctx, escalate=...)` over a fake ctx (`driver.effects.recorded`, `git._run` answering `show <ref>:<path>`, `git.rev_parse`, `git.status_porcelain`, `repo` and `worktree(stem)` under `tmp_path`) and uses receipts whose `review_provider` and `review_model` are `None`, so `stages.served_review` is not reached. The real `validate_ticket` checks the ticket text it serves against `tmp_path`, so the test writes there any file that ticket needs.
- Remove each import an edit leaves unused in the edited files.

Out:
- Every kept symbol named in the Goal, and `clutch/gates.py`, `clutch/providers.py`, `clutch/config.py` and `test-gate.toml`.
- `Timers`' `sleep` constructor parameter. With `wait_next` gone nothing reads it, but dropping it edits eight construction sites, including `tests/integration/test_providers.py`, which the running `evidence-rusage-capture` fences; it is filed in the Suggestion Box as `box-000688-17debde0`.
- `observe.uncommitted_tickets` (in §3.5 but not in row 127), `audit_journal`, and `docs/roadmap.md`.
- No source change in `clutch/mergequeue.py`, `clutch/serve.py` or `clutch/runner.py`.
- No document changes. A grep of `docs/`, `clutch/docs/`, `README.md`, `AGENTS.md` and `CLAUDE.md` finds no deleted name outside `docs/roadmap.md`.
- Merge order with `evidence-rusage-capture`: it adds an `on_rusage=None` keyword to exec fakes in `tests/integration/test_providers.py`. `test_watchdog.py` imports `PythonProviderExec` and `python_client` from there, and its only subclass that overrides `PythonProviderExec.run` is inside `test_watchdog_real_group_cleanup`, which this ticket deletes. No file is shared, so either merge order leaves both suites green.

## Scope fence
- clutch/heartbeat.py
- clutch/timers.py
- clutch/git.py
- clutch/effects.py
- clutch/requisition.py
- clutch/watchdog.py
- tests/integration/test_heartbeat.py
- tests/integration/test_restart_timers.py
- tests/integration/test_git.py
- tests/integration/test_llm_effect.py
- tests/integration/test_requisition.py
- tests/integration/test_watchdog.py
- tests/unit/test_callerless_code_removed.py
- tests/unit/test_serve_responsiveness.py
- tests/unit/test_runner_prepared_dispatch.py
- tests/unit/test_mergequeue_retained_ticket.py

## Acceptance criteria
1. `tests/unit/test_callerless_code_removed.py` asserts `hasattr` is False for `clutch.heartbeat.is_fresh`, `clutch.timers.Timers.wait_next`, `clutch.git.Git.branch`, `clutch.effects.effect`, `clutch.requisition.RequisitionGate`, `clutch.requisition.base_render_chars` and `clutch.watchdog.Detector.watch`. It also asserts `hasattr` is True for the kept neighbours `Git.init`, `Git.branch_delete`, `Timers.fire_due`, `Effects.run`, `requisition._base_render`, `watchdog.watch_deadline` and `Detector.start_call`. It fails if any listed symbol survives or a neighbour is deleted with it; checked by `./dev.py test tests/unit/test_callerless_code_removed.py`.
2. `./dev.py test tests/integration/test_heartbeat.py` passes, and `test_unhealthy_core_stops_refresh` still fails if a failed cycle refreshes the heartbeat (recorded mtime older than `AGE` after the advance) or if the healthy cycle does not (recorded mtime within `AGE`).
3. `./dev.py test tests/integration/test_restart_timers.py` passes. For the `fire` and `after-fire` points, `test_timer_append_is_write_ahead` raises the scripted `OSError` from `fire_due()` and keeps its journal and recovery assertions.
4. `./dev.py test tests/integration/test_git.py` passes. The conflict scenario still raises `RebaseRefused` and leaves the worktree HEAD and status unchanged.
5. `./dev.py test tests/integration/test_requisition.py tests/integration/test_spec_sibling_tickets.py` passes. `test_base_render_matches_implement_and_gate` compares `_base_render`'s whole string to the production Implement render, not just its length. The over-bound test still returns verdict `snag` with mechanical `review render over bound` and makes no LLM request.
6. `./dev.py test tests/integration/test_watchdog.py tests/integration/test_watchdog_activation.py` passes. The three ported tests keep each assertion they had: result text and usd, the observed events, tool ids, usage, tokens, spend, bases, the empty journal and the `reported no cost` refusal. `test_production_hard_timeout_group_kill_is_harvested` is not edited.
7. `./dev.py test tests/integration/test_llm_effect.py` passes.
8. `uv run ruff check .` exits 0, so no deletion leaves an unused import in `clutch/`. `pyproject.toml` ignores F401 under `tests/*`, so in a test file a leftover import of a deleted name fails at collection in the suites above instead.
9. `tests/unit/test_serve_responsiveness.py`: a new `Responsiveness()` reports `responsive()` False before any `ask()`, not True with nothing asked; after `ask()` it is False until `reply()`, then True. Checked by `./dev.py test tests/unit/test_serve_responsiveness.py`.
10. `tests/unit/test_serve_responsiveness.py`: while `wait(work)` awaits a coroutine blocked on an `asyncio.Event`, an `ask()` makes `responsive()` True without the work finishing; setting the event makes `wait` return the work's value; a work that raises makes `wait` raise that same exception.
11. `tests/unit/test_serve_responsiveness.py`: cancelling the task that runs `wait(work)` cancels the work too (the work observes `asyncio.CancelledError`), rather than leaving it running.
12. `tests/unit/test_runner_prepared_dispatch.py`: two `prepare()` calls with an unchanged snapshot build the pipeline once, not twice. A changed snapshot builds it again, and the checkout passed to `prepare_pipeline` carries the new snapshot as `config`. `stages` is the built callback's `stages`. Checked by `./dev.py test tests/unit/test_runner_prepared_dispatch.py`.
13. `tests/unit/test_runner_prepared_dispatch.py`: calling the dispatch with a ticket after `prepare()` builds nothing new and returns the callback's result, and the next call builds a fresh callback, so a prepared callback serves exactly one call. A callback that raises still leaves the next call building a fresh one.
14. `tests/unit/test_runner_prepared_dispatch.py`: `abort_current()` awaits the prepared callback's `abort_current` once, and with nothing prepared it returns without error.
15. `tests/unit/test_mergequeue_retained_ticket.py`: with no recorded review lift, a valid ticket at `main:tickets/<stem>/ticket.md`, an approving `review.md` built by `stages.render_review` whose `stem` and `reviewed_sha` match the receipt, an existing worktree directory, an empty status and equal HEAD shas, `retained_ticket` returns a `Ticket` with that stem. Checked by `./dev.py test tests/unit/test_mergequeue_retained_ticket.py`.
16. `tests/unit/test_mergequeue_retained_ticket.py`: with one recorded lift whose `commit` is `c1`, the ticket text is read from `c1:tickets/<stem>/ticket.md`, not `main:`. When `rev_parse` gives different shas for `main:tickets/<stem>/review.md` and `c1:tickets/<stem>/review.md`, it raises.
17. `tests/unit/test_mergequeue_retained_ticket.py`, parametrized: a `reviewed_sha` mismatch, a `snag` review, a missing worktree directory, a status line for a file outside `tickets/<stem>/`, and a worktree HEAD that differs from the branch sha each raise `ValueError` whose message starts with `retained admission <stem> is unavailable` and contains `restore the retained committed ticket`; none returns a ticket.

## Verification
```
./dev.py test tests/unit/test_callerless_code_removed.py tests/unit/test_serve_responsiveness.py tests/unit/test_runner_prepared_dispatch.py tests/unit/test_mergequeue_retained_ticket.py
./dev.py test tests/integration/test_heartbeat.py tests/integration/test_restart_timers.py tests/integration/test_git.py tests/integration/test_llm_effect.py tests/integration/test_requisition.py tests/integration/test_spec_sibling_tickets.py tests/integration/test_watchdog.py tests/integration/test_watchdog_activation.py
uv run ruff check .
```

## Definition of rejected
- A kept symbol (`Git.init`, `audit.audit`, `audit.audit_journal`, `policy.baseline_identity`, `gates.lint_gate`, `CliAdapter.parsed_failure`, `requisition._base_render`, `watchdog.watch_deadline`, `Timers.fire_due`, `Detector.start_call`) is deleted or changed.
- `clutch/gates.py`, `clutch/providers.py`, `clutch/config.py` or `test-gate.toml` is edited.
- A deleted name survives as an alias, re-export or wrapper.
- One of the three ported watchdog tests is deleted or loses an assertion.
- `clutch/mergequeue.py`, `clutch/serve.py` or `clutch/runner.py` is edited to make a new test pass.

## Time budget
- expected: 30m
- stuck: 60m
