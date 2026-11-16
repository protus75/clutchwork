---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- clutch/drain.py::Report.render
- clutch/drain.py::_Drain._settle
- clutch/status.py::run_admission
- clutch/status.py::_box_admission
- clutch/doctor.py::check
- clutch/retro.py::Retro.__call__
- clutch/box.py::Box.messages
- clutch/box.py::Box.enqueue
- clutch/box.py::Box.resolve
- clutch/box.py::read_registry
- tests/integration/test_engine_text_verbs.py
- tests/integration/test_drain.py::test_a_spent_retry_cap_stays_parked_and_is_never_reoffered
- tests/integration/test_drain.py::test_the_runtime_ceiling_stops_the_next_dispatch_and_exits_1
- tests/integration/test_retro.py::rig
- tests/integration/test_retro.py::test_failed_retro_suppresses_window_until_completion

## Goal / Why
`CLAUDE.md` section A says a road an operator reads names the `clutch` verb that does the work, never a hand-built argv ("Guides name verbs, not command lines"), and that every refusal ships a paved road ("Fail closed"). `engine-text-names-clutch-verbs` and `dev-py-dev-tasks-only` set the form: a bare `` `clutch <verb>` `` in backticks, which an operator runs with the host's own prefix (`clutch/docs/host-running.md`: "Use the same prefix for the other verbs"). Four groups of engine text still break those rules at HEAD c761b213:

1. Seven operator roads name the argv `uv run python -m clutch <verb>` (or `python -m clutch new`) instead of the verb: the kill and ceiling-halt heads in `clutch/drain.py::Report.render`; the halted re-offer road and the Reject-queue road in `clutch/drain.py::_Drain._settle`; the missing-ticket road in `clutch/status.py::run_admission`; the venv road in `clutch/doctor.py::check`; and `LOGIN_ROAD` on `ClaudeAdapter` and `CodexAdapter` in `clutch/providers.py`. A probe drain at HEAD prints `- spent: gate_failed at check; retry cap spent (3/3) -- edit tickets/spent/ticket.md, then uv run python -m clutch confirm spent; or retire it with uv run python -m clutch reject spent`, while the two neighbouring roads in the same function already say `` `clutch confirm {stem}` `` and `` `clutch reject {stem}` ``. The roadmap audit called the drain report "the one operator surface" with this defect; the grep `grep -rn "python -m clutch" clutch/` finds the other three files too.
2. `clutch/status.py::_box_admission` refuses an unknown box id with `Admission("refuse", f"unknown box id {id}")` and an empty `paved_road`. It is the only refusing admission in that module without one; `run_admission`, `review_admission`, `order_admission` and `lint_admission` all carry a road.
3. `clutch/retro.py::Retro.__call__` turns a failed retro stage into `raise ValueError(result.outcome)`, and its `except` journals `error_code: type(exc).__name__`. The `retro_failed` signal therefore says `ValueError` for every stage outcome: a probe at HEAD shows `error_code: "ValueError"` for an `invalid_artifact` reply and for a provider error (`infra_error`). The outcome survives only in the engine log, which is not the record.
4. Five `BoxError` sites in `clutch/box.py` name a fault and no repair: `Box.messages` (`invalid box file ...`), `Box.enqueue` (`stage and outcome must both be set or both be null`, and `invalid box message: ...`), `Box.resolve` (`box id ... is already resolved`), and `read_registry` (`invalid decision record <path>: ...`), which wraps the three fault-only errors `parse_record` raises (missing frontmatter, missing closing fence, invalid fields) plus any `OSError`. Together these are the roadmap's seven fault-only `BoxError`s, and an operator who runs `clutch status` on a corrupt box file gets a traceback that says what broke but not what to do.

After this change every one of those roads names a `clutch` verb or a repair, and a failed retro records which stage outcome it was.

## Scope in / Scope out
Scope in, with the exact new text for each road (the text before the road stays as it is):
- `clutch/drain.py::Report.render`: the kill head ends `Continue with` `` `clutch drain` ``. (with the full stop), and the ceiling-halt head ends the same way, replacing `` `uv run python -m clutch drain` `` in both.
- `clutch/drain.py::_Drain._settle`: the halted re-offer road (the `spent_cap is None` branch) becomes `` `clutch drain` re-offers it ``; the Reject-queue road in the `elif not (stem in held and to == "gate_failed" and spent_cap is None)` branch becomes `` f"edit {ticket_path(stem)}, then `clutch confirm {stem}`; or retire it with `clutch reject {stem}`" ``. No other road in `_settle` or `_premise_road` changes.
- `clutch/status.py::run_admission`: the missing-file road becomes `` f"author it with `clutch new {stem}`, fill it, then `clutch run {stem}`" ``.
- `clutch/status.py::_box_admission`: the unknown-id refusal gains the road `` name ids that `clutch status` lists ``, the road `clutch/__main__.py`'s `UnknownBoxId` handler already prints. The message text `unknown box id {id}` does not change, so `tests/unit/test_menu_admission.py::test_box_admissions` keeps passing unedited.
- `clutch/doctor.py::check`: the failing `venv` row's detail becomes `` no active Python venv; run `uv run clutch doctor` ``. The `uv run` prefix stays because the fault is the missing venv and `uv run` is the documented way to get one (`clutch/docs/host-contract.md`, Install).
- `clutch/providers.py`: `ClaudeAdapter.LOGIN_ROAD` becomes `` run claude interactively and complete /login, then `clutch drain` `` and `CodexAdapter.LOGIN_ROAD` becomes `` run codex login, then `clutch drain` ``. `QwenAdapter.LOGIN_ROAD` already names the verb and does not change.
- `clutch/retro.py::Retro.__call__`: when the retro stage returns an outcome other than `ok`, the `retro_failed` signal's `error_code` is that outcome (`infra_error`, `invalid_artifact`, and so on), not `ValueError`. An exception raised anywhere else in the retro (for example from `commit_report`) still journals `type(exc).__name__`, and both paths still call `failure_report`, which files one `failure_report` Box message whose origin is the signal's key, exactly as now. The signal body keeps exactly the four keys `kind`, `window_boundary`, `trigger`, `error_code`.
- `clutch/box.py`, each message gaining the road after `; `:
  - `Box.messages`: `` f"invalid box file {path}: {exc}; move it out of the box directory or restore it from backup" ``.
  - `Box.enqueue`: `"stage and outcome must both be set or both be null; pass both or neither"` and `` f"invalid box message: {exc}; correct the fields named above and enqueue again" ``.
  - `Box.resolve`: `` f"box id {id} is already resolved; its resolution stands and `clutch status` shows it" ``.
  - `read_registry`: `` f"invalid decision record {path}: {exc}; restore it from its last commit" ``. The road goes here, once, and not into the three `parse_record` raises: `read_registry` is `parse_record`'s only caller, it alone knows the path, and its one road also covers the `OSError` case that `parse_record` never sees. The `parse_record` messages do not change.
- Existing tests whose assertions pin an old road, each changed in that one assertion only:
  - `tests/integration/test_drain.py::test_the_runtime_ceiling_stops_the_next_dispatch_and_exits_1`: `"uv run python -m clutch drain" in out` becomes `` "Continue with `clutch drain`." in out ``. No new test goes in this file (it is on the contention list in `docs/parallel-tickets-plan.md` section 7).
  - `tests/integration/test_kill_cli_activation.py::test_live_drain_kill_reaches_production_driver`: the same flip on its last assertion.
  - `tests/integration/test_doctor.py::test_doctor_check_order`: the `FAIL venv` line of the expected render becomes `` FAIL venv: no active Python venv; run `uv run clutch doctor` ``.
  - `tests/harness/shakeout/providers.py::_auth_expiry`: its `road` literal becomes the new `ClaudeAdapter.LOGIN_ROAD` text; `tests/integration/test_shakeout.py` runs it.
  - `tests/integration/test_retro.py::test_failed_retro_suppresses_window_until_completion`: the expected body's `"error_code": "ValueError"` becomes `"error_code": "infra_error"`, the outcome the driver returns when the fake provider raises.
- New tests in two new files: `tests/unit/test_paved_roads.py` for the pure roads (drain heads, status admissions, the two `Box.enqueue` errors, both `LOGIN_ROAD`s) and for the new `clutch/retro.py` lines, which it runs against fakes because `clutch/retro.py` has a positive unit floor in `test-gate.toml` (it may import `MemoryJournal` from `tests/unit/test_retro_recurrence.py`, unchanged); and `tests/integration/test_paved_roads.py` for the roads that need a drain, a box directory, a decision registry, or a retro rig. The integration file may import `make_root`, `Script`, `Clock`, `START`, `drain`, `journal`, `commit_ticket` and `confirmed` from `tests/integration/test_drain.py`, `ticket` and `write` from `tests/integration/test_cli.py`, and `rig` and `merged` from `tests/integration/test_retro.py`, as other test modules already do; it changes none of them.

Scope out:
- `clutch/__main__.py`, including its `UnknownBoxId` handler suffix and the argparse `prog="python -m clutch"` usage line; neither is a road this row names.
- Every other road and message: `_Drain._premise_road`, the `run {stem}` / `review {stem}` roads elsewhere in `clutch/status.py`, `QwenAdapter.LOGIN_ROAD`, the `BoxError`s that already name a repair, and the `author.py` `BoxError`s.
- `Retro.failure_report` and its Box message (`outcome="infra_error"`, signature, summary); `tests/integration/serve_rig.py`'s synthetic `retro_failed` event, which asserts nothing about the value.
- Any shared road constant, verb-prefix helper, config knob, or `clutch/help.py` entry; a scan test that forbids `python -m clutch` in engine text (that class fix is filed separately to the Suggestion Box).
- Docs: `docs/how-clutch-works.md` already describes the roads as `clutch confirm|reject` and says nothing about `retro_failed`'s `error_code`, so no document is made false; `docs/roadmap.md` is an audit snapshot and is not edited here.

## Scope fence
- clutch/drain.py
- clutch/status.py
- clutch/doctor.py
- clutch/providers.py
- clutch/retro.py
- clutch/box.py
- tests/unit/test_paved_roads.py
- tests/integration/test_paved_roads.py
- tests/integration/test_drain.py
- tests/integration/test_kill_cli_activation.py
- tests/integration/test_doctor.py
- tests/integration/test_retro.py
- tests/harness/shakeout/providers.py

## Acceptance criteria
1. `tests/unit/test_paved_roads.py::test_drain_heads_name_the_drain_verb` asserts that `Report(killed=True).render()` and `Report(halted="12h elapsed").render()` each contain `` Continue with `clutch drain`. `` and neither contains `python -m clutch`. Ruled out: today's `` `uv run python -m clutch drain` `` head, and a head that drops the continue road.
2. `tests/unit/test_paved_roads.py::test_missing_ticket_road_names_clutch_verbs` asserts `run_admission("item", [], False, None).paved_road` equals `` author it with `clutch new item`, fill it, then `clutch run item` ``. Ruled out: today's `` `python -m clutch new item` `` road.
3. `tests/unit/test_paved_roads.py::test_unknown_box_id_carries_a_road` asserts that `triage_admission("missing", [])` and `dismiss_admission("missing", [])` each return an `Admission` with outcome `refuse`, message `unknown box id missing`, and `paved_road` equal to ``name ids that `clutch status` lists``. Ruled out: today's empty `paved_road`, and a changed message that would break `tests/unit/test_menu_admission.py::test_box_admissions`.
4. `tests/unit/test_paved_roads.py::test_enqueue_errors_name_a_repair` builds `Box(Path("box"), None)` (no I/O: both errors raise before any read) and asserts that `enqueue(message_class="suggestion", origin="x", summary="s", stage="check")` raises `BoxError` whose text is exactly `stage and outcome must both be set or both be null; pass both or neither`, and that `enqueue(message_class="bug_report", origin="x", summary="s")` raises `BoxError` whose text starts `invalid box message: ` and ends `; correct the fields named above and enqueue again`. Ruled out: today's fault-only texts.
5. `tests/unit/test_paved_roads.py::test_login_roads_name_the_drain_verb` asserts ``ClaudeAdapter.LOGIN_ROAD == "run claude interactively and complete /login, then `clutch drain`"`` and ``CodexAdapter.LOGIN_ROAD == "run codex login, then `clutch drain`"``. Ruled out: today's `uv run python -m clutch drain` suffix.
6. `tests/unit/test_paved_roads.py::test_retro_error_code_names_the_stage_outcome` runs `Retro(checkout, pipeline)(forced=True)` with no disk, process or spec-file read, in two cases. The fakes: a `SimpleNamespace` checkout whose journal is `MemoryJournal` holding one `merged` transition, whose `config` carries `retro`, `state_dir` and `drain.max_ticket_minutes`, whose `clock` returns a fixed `datetime`, and whose `git.rev_parse` is an async fake; `clutch.retro.production_evidence` monkeypatched to return `{"merged_count": 1}`; `clutch.runner.SPECS_DIR` monkeypatched so `/ "retro.md"` yields an object whose `read_text()` returns `""`; `clutch.retro.load_spec` monkeypatched to return a spec whose `meta` has `version`, `tier` and `effort`; `clutch.daemon.storm_producer` monkeypatched to return a box with `messages()` returning `[]` and a recording `enqueue`; and a pipeline whose `stages.driver` has an async `run` and a no-op `log.event`. Case `outcome`: `run` returns an object with `outcome == "invalid_artifact"`; the test asserts the one journaled `retro_failed` body's `error_code` is `invalid_artifact` and the recorded `enqueue` has `origin == "retro-failed/initial/forced"`. Case `exception`: `git.rev_parse` raises `OSError("disk full")`; the test asserts `error_code` is `OSError`, `run` was never called, and the same one `enqueue`. Ruled out: `ValueError` in the first case (today's value), and a stage outcome or `ValueError` in the second.
7. `tests/integration/test_paved_roads.py::test_reject_queue_road_names_confirm_and_reject` commits a confirmed ticket `spent`, journals `running`, `gate_failed` at `check` and three `retry` draws (as `test_a_spent_retry_cap_stays_parked_and_is_never_reoffered` does), drains, and asserts the report's parked block contains the line ``- spent: gate_failed at check; retry cap spent (3/3) -- edit tickets/spent/ticket.md, then `clutch confirm spent`; or retire it with `clutch reject spent` ``. Ruled out: today's line, which names `uv run python -m clutch confirm spent`.
8. `tests/integration/test_paved_roads.py::test_halted_reoffer_road_names_the_drain_verb` writes one ticket `red` whose scripted dispatch returns `gate_failed` and moves the fake clock past the 12-hour ceiling (as `test_the_runtime_ceiling_stops_the_next_dispatch_and_exits_1` does), asserts the drain exits 1, and asserts the parked block contains ``- red: gate_failed at review; 3 of 3 retry units left -- `clutch drain` re-offers it``. Ruled out: today's `` `uv run python -m clutch drain` re-offers it ``.
9. `tests/integration/test_paved_roads.py::test_box_reads_name_a_repair` asserts, against a `tmp_path` box and registry: `Box.messages()` over a box directory holding `bad.json` containing `{}` raises `BoxError` whose text contains `bad.json` and ends `; move it out of the box directory or restore it from backup`; a second `resolve` of a resolved message raises `BoxError` whose text is exactly `` box id <id> is already resolved; its resolution stands and `clutch status` shows it ``; and `read_registry` over a `tickets/decisions/b.md` containing `body only` raises `BoxError` whose text contains `b.md` and `decision record missing YAML frontmatter`, ends `; restore it from its last commit`, and contains `restore it from its last commit` exactly once. Ruled out: today's fault-only texts, and a road placed inside `parse_record` that the wrapper would then lose or repeat.
10. `tests/integration/test_paved_roads.py::test_retro_failure_records_the_stage_outcome` uses `rig` with the single reply `not json at all` (the driver returns `invalid_artifact` for it with `retry_cap = 0`), journals a merge, runs the retro forced, and asserts the one `retro_failed` body equals `{"kind": "retro_failed", "window_boundary": "initial", "trigger": "forced", "error_code": "invalid_artifact"}` and that the box holds one `failure_report` message whose origin is that signal's key. Ruled out: `ValueError`, today's value, and a hard-coded `infra_error`.
11. `tests/integration/test_paved_roads.py::test_retro_exception_keeps_its_class_name` uses `rig` with the reply `{"proposals": []}`, replaces the hook's `commit_report` with a coroutine that raises `OSError("disk full")`, runs the retro forced after a merge, and asserts the `retro_failed` body's `error_code` is `OSError` and that the box holds one `failure_report` message whose origin is that signal's key. Ruled out: an implementation that writes a stage outcome (`ok` or `infra_error`) for an exception that did not come from the stage.
12. `./dev.py test tests/integration/test_drain.py tests/integration/test_kill_cli_activation.py tests/integration/test_doctor.py tests/integration/test_retro.py tests/integration/test_shakeout.py tests/integration/test_providers.py tests/integration/test_box.py tests/integration/test_status.py tests/unit/test_menu_admission.py` exits 0 with only the five assertions `## Scope in / Scope out` names changed, so `test_failed_retro_suppresses_window_until_completion` now pins `infra_error` instead of `ValueError` and the untouched `match=` assertions on `invalid box file`, `bad.json` and the resolved id still hold.
13. The `uv run python -c` command in `## Verification` exits 0: none of `clutch/drain.py`, `clutch/status.py`, `clutch/doctor.py` or `clutch/providers.py` contains `python -m clutch`. Ruled out: any of the seven old roads left in place.
14. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_paved_roads.py
./dev.py test tests/integration/test_paved_roads.py
./dev.py test tests/integration/test_drain.py tests/integration/test_kill_cli_activation.py tests/integration/test_doctor.py tests/integration/test_retro.py tests/integration/test_shakeout.py tests/integration/test_providers.py tests/integration/test_box.py tests/integration/test_status.py tests/unit/test_menu_admission.py
uv run python -c "import pathlib; bad = [p for p in ('clutch/drain.py', 'clutch/status.py', 'clutch/doctor.py', 'clutch/providers.py') if 'python -m clutch' in pathlib.Path(p).read_text()]; assert not bad, bad"
./dev.py test
```

## Definition of rejected
The branch is rejected if any changed road names `python -m clutch`, `./dev.py`, or another hand-built argv instead of a `` `clutch <verb>` ``; if it adds a verb-prefix helper, shared road constant, config knob, shim, or alias; if the retro stage outcome is recovered by parsing an exception's text, or the `retro_failed` body gains or loses a key; if `Retro.failure_report`, its Box message, or `clutch/__main__.py` changes; if a new test is added to `tests/integration/test_drain.py`; or if any existing assertion other than the five named in `## Scope in / Scope out` is changed or weakened.

## Time budget
- expected: 50m
- stuck: 120m
