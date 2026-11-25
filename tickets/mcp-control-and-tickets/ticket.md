---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- mcp-read-server
- engine-serve-detach

## Context
- docs/antigravity-plan.md#3. Clutch MCP server vs. direct CLI boundary
- docs/antigravity-plan.md#Risks
- clutch/mcp.py
- clutch/status.py::lint_admission
- clutch/status.py::order_admission
- clutch/status.py::confirm_admission
- clutch/status.py::reject_admission
- clutch/status.py::triage_admission
- clutch/status.py::dismiss_admission
- clutch/box.py::Box
- clutch/control.py::AdmissionRequest
- clutch/control.py::TriageRequest
- clutch/control.py::ControlRequest
- clutch/control.py::read_active
- clutch/control.py::publish_request
- clutch/lockfile.py::ENGINE_VERBS
- clutch/lockfile.py::LockHeld
- tests/unit/test_mcp_protocol.py
- tests/unit/test_mcp_tools.py
- tests/unit/test_main_help.py
- tests/unit/test_host_running.py
- tests/unit/test_docs_verb.py
- tests/unit/test_lock_holder.py
- tests/unit/test_main_box_group.py
- tests/unit/test_main_ticket_group.py
- tests/unit/test_main_serve_detach.py
- tests/unit/test_drain_detach_cli.py
- tests/unit/test_ticket_lint_rules.py
- tests/unit/test_route_kinds_judge.py
- tests/unit/test_manual_retro_calibration_verbs.py
- tests/unit/test_reject_reason_paths.py
- tests/integration/test_main_verb_groups.py

## On-demand
- clutch/tickets.py
- clutch/observe.py
- clutch/serve.py
- clutch/runner.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 221 (`mcp-control-and-tickets`, `docs/antigravity-plan.md` §3, Risks #1). `mcp-read-server` added read-only MCP observation and prompt tools, and `engine-serve-detach` added `clutch engine serve --detach`, so supervising agents and the upcoming Antigravity MCP App still have to shell out for ticket creation/linting/ordering/verdicts, Suggestion Box actions, and engine lifecycle control.

After this ticket:
- `clutch/mcp.py` exposes 11 model-visible mutation and engine-control tools (`clutch_ticket_new`, `clutch_ticket_lint`, `clutch_ticket_order`, `clutch_ticket_confirm`, `clutch_ticket_reject`, `clutch_box_suggest`, `clutch_box_triage`, `clutch_box_dismiss`, `clutch_engine_start`, `clutch_engine_control`, `clutch_engine_retro`) plus 2 `app`-only UI verdict tools (`clutch_app_ticket_confirm`, `clutch_app_ticket_reject` with `_meta.ui.visibility = ["app"]`).
- Every tool calls its existing shared Python domain owner (`clutch/tickets.py`, `clutch/box.py`, `clutch/serve.py`, `clutch/observe.py`, `clutch/runner.py`) with zero duplicated admission or business logic in `clutch/mcp.py`, and maps `Refusal`, `LockHeld`, and related domain exceptions to structured MCP tool errors (`code`, `message`, `paved_road`).
- Model-visible `clutch_ticket_confirm` and `clutch_ticket_reject` always record `actor: "operator"` (`extension=False`), refusing same-content repeat keeps, while `clutch_app_ticket_confirm` and `clutch_app_ticket_reject` record `actor: "extension"` (`extension=True`) for human UI clicks.
- `clutch_engine_start` (`mode: "drain" | "serve"`) always spawns detached via `serve.start_detached`, so daemon lifetime never ties to the MCP stdio pipe.

Rejected simpler approach: shelling out to `clutch` CLI subcommands from `clutch/mcp.py` or reimplementing admission checks directly inside `clutch/mcp.py`. Shelling out fails in sandboxed shells without `~/.local/bin` on `PATH` and loses structured findings, while duplicating admission rules in `clutch/mcp.py` drifts from CLI and snapshot admission.

## Boundary contract

### Shared ticket authoring, linting, and ordering
- disposition: extend
- owner: clutch/tickets.py
- consumers: `clutch/__main__.py` (`_new`, `_lint`, `_order`), `clutch/mcp.py`
- observable change: adds `new_ticket(repo, stem, kind="feature", *, evidence=(), reference=(), inputs=(), fs=None, ...)` returning `(rel, guide, findings)`, `lint_tickets(checkout, stems=(), ...)` returning `{"valid": int, "total": int, "exit_code": int, "findings": [{"path": str, "code": str, "message": str, "paved_road": str}, ...], "refusals": [{"path": str, "message": str, "paved_road": str}, ...]}`, and `order_ticket(checkout, stem, *, priority=None, runs_before=None, empty_road=..., ...)` returning `{"stem": str, "path": str, "priority": str, "runs_before": list[str]}` (all raising `runner.Refusal(..., code=...)` on refusals); each accepts injected helper callbacks defaulting to `clutch/tickets.py` implementations, and `clutch/__main__.py` `_new`, `_lint`, and `_order` pass `clutch.__main__` module-global helpers (`LocalFileSystem`, `template`, `validate_ticket`, `lint_findings`, `evidence_findings`, `missing_evidence_findings`, `stem_findings`, `order`, `admission_facts`, `lint_admission`, `order_admission`, `_intake_claims`, `_pending`, `_porcelain`) so monkeypatches on `clutch.__main__` remain effective.
- compatibility: `_new`, `_lint`, and `_order` preserve their exact signatures, monkeypatchable CLI seams, stdout/stderr text, and exit codes.
- acceptance: criterion 2 and criterion 6
- tests: tests/unit/test_mcp_control_and_tickets.py, tests/unit/test_docs_verb.py, tests/unit/test_new_evidence.py, tests/unit/test_graphics_new.py, tests/unit/test_ticket_lint_rules.py, tests/unit/test_route_kinds_judge.py, tests/unit/test_main_ticket_group.py
- post-merge source of truth: clutch/tickets.py

### Shared Suggestion Box suggest
- disposition: extend
- owner: clutch/box.py
- consumers: `clutch/__main__.py` (`handle_suggest`), `clutch/mcp.py`
- observable change: adds `suggest(state_dir, fs, journal, summary, *, origin="session", occurrence_id=None) -> tuple[str, bool]` refusing blank summaries with `runner.Refusal("blank summary", "pass the idea as one quoted argument", code="blank_summary")` and delegating to `Box(...).enqueue(message_class="suggestion", ...)`; `clutch/__main__.py::handle_suggest` delegates to it.
- compatibility: `Box` methods and `clutch box suggest` CLI stdout and exit codes remain unchanged.
- acceptance: criterion 3 and criterion 6
- tests: tests/unit/test_mcp_control_and_tickets.py, tests/unit/test_main_box_group.py
- post-merge source of truth: clutch/box.py

### Shared detached engine start
- disposition: extend
- owner: clutch/serve.py
- consumers: `clutch/__main__.py` (`handle_detach`), `clutch/mcp.py`
- observable change: adds `start_detached(repo, state_dir, verb, *, config_path=None, env, spawn=seams.spawn_detached) -> tuple[int, Path]` refusing if `observe.lock_holder(state_dir)` is non-None (`code="lock_held"`), spawning `[sys.executable, "-m", "clutch", *(["--config", str(config_path)] if config_path else []), "engine", verb]` via `spawn` with `output=state_dir / f"{verb}.out"`, and calling `capture_startup_baseline` and `wait_detached_startup` via `clutch.serve` module globals when `verb == "serve"`; `clutch/__main__.py::handle_detach` delegates to it forwarding `spawn=spawn`.
- compatibility: `clutch engine drain --detach` and `clutch engine serve --detach` preserve their exact child argv, `serve.*` monkeypatch seams, startup confirmation, stdout, and exit codes.
- acceptance: criterion 4 and criterion 6
- tests: tests/unit/test_mcp_control_and_tickets.py, tests/unit/test_main_serve_detach.py, tests/unit/test_drain_detach_cli.py
- post-merge source of truth: clutch/serve.py

### Engine ping liveness projection
- disposition: extend
- owner: clutch/observe.py
- consumers: `clutch/mcp.py`
- observable change: adds `ping_engine(state_dir, read=Path.read_bytes) -> dict` reading `clutch.lock` via `lock_holder` and `lock_verb` and, when the holder verb is in `ENGINE_VERBS`, reading `control.read_active`, returning `{"alive": bool, "engine": bool, "verb": str | None, "pid": int | None, "started_at": str | None, "lifecycle_id": str | None, "hold_id": str | None}`.
- compatibility: additive; existing `observe` functions and `snapshot` payload remain unchanged.
- acceptance: criterion 4
- tests: tests/unit/test_mcp_control_and_tickets.py
- post-merge source of truth: clutch/observe.py

### Shared verdict, control, triage, dismiss, and retro submission
- disposition: extend
- owner: clutch/runner.py
- consumers: `clutch/__main__.py`, `clutch/mcp.py`
- observable change: moves the single canonical writer-lock context `_locked(state_dir, verb, *, instance_id=None, clock, lock_factory=None)` (calling `Lockfile(...)` when `lock_factory is None` else `lock_factory(...)`, acquiring, yielding, and releasing in `finally`) into `clutch/runner.py`, while `clutch/__main__.py::_locked` becomes a thin wrapper delegating to `runner._locked(..., lock_factory=Lockfile)` so `entry.Lockfile` monkeypatches stay intact with zero duplicated lock logic; adds `submit_engine(...)`, `submit_verdict(...)`, `control_engine(...)`, `dismiss_boxes(...)`, `triage_or_submit(...)`, and `run_or_submit_retro(...)` sharing `_locked` / `Lockfile` acquisition, `LockHeld` -> `ENGINE_VERBS` inbox submission (`AdmissionRequest`, `TriageRequest`, `ControlRequest`), blank reject-reason refusal, and non-engine holder refusal (`code="lock_held"`), accepting injected CLI seams (`lock_factory`, `lock_ctx_factory`, `read_active_fn`, `publish_fn`, `build_control_fn`, `preflighted_llm_fn`, `config_reloader_fn`, `submit_fn`); `clutch/__main__.py` (`_submit_engine`, `_verdict`, `_control`, `handle_dismiss`, `handle_triage`, `_retro`) resolves those seams via `clutch.__main__` module globals and delegates to them; and `tests/integration/test_main_verb_groups.py::test_shared_call_has_one_owner` updates its AST owner table to parse `clutch/runner.py` for the moved calls (`Lockfile` in `_locked`, `_require_engine` / `control.read_active` / `control.publish_request` in `submit_engine`) and `clutch/__main__.py` for `observe.Context` in `_observe_context`.
- compatibility: `runner.verdict`, `runner.verdict_locked`, `runner.apply_admission`, and CLI monkeypatch hooks (`entry.Lockfile`, `entry._locked`, `entry.control.*`, `entry.build_control`, `entry._preflighted_llm`, `runner.verdict`, `runner.reap`) remain intact.
- acceptance: criteria 2, 3, 4, and 6
- tests: tests/unit/test_mcp_control_and_tickets.py, tests/unit/test_lock_holder.py, tests/unit/test_reject_reason_paths.py, tests/unit/test_manual_retro_calibration_verbs.py, tests/unit/test_main_box_group.py, tests/integration/test_main_verb_groups.py
- post-merge source of truth: clutch/runner.py

### Admission-gated MCP control and ticket tools
- disposition: extend
- owner: clutch/mcp.py
- consumers: Antigravity MCP clients, future `mcp-app-dashboard` and `ask-specs-mcp-supervision`
- observable change: adds 11 model-visible tools (`clutch_ticket_new`, `clutch_ticket_lint`, `clutch_ticket_order`, `clutch_ticket_confirm`, `clutch_ticket_reject`, `clutch_box_suggest`, `clutch_box_triage`, `clutch_box_dismiss`, `clutch_engine_start`, `clutch_engine_control`, `clutch_engine_retro`) and 2 `app`-only tools (`clutch_app_ticket_confirm`, `clutch_app_ticket_reject` with `_meta: {"ui": {"visibility": ["app"]}}` in `tools/list`), adds injectable `spawn=seams.spawn_detached` on `ClutchMCPServer`, forces `extension=False` (`actor: "operator"`) on model-visible verdict tools and `extension=True` (`actor: "extension"`) on `app`-only verdict tools, projects `lint_tickets` `exit_code in (0, 1)` to `{"valid", "total", "valid_all": exit_code == 0, "findings"}` while raising `runner.Refusal(..., code="lint_refused")` when `exit_code == 2`, suppresses domain `print()` noise from the JSON-RPC `stdout` pipe during `serve_stdio`, and maps `LockHeld`, `CommitLockTimeout`, `IntakeRefused`, `ProviderSetupError`, `ExecutableNotFound`, and `hostfiles.MarkerCorruption` alongside `Refusal` to `isError: true` structured errors (`code`, `message`, `paved_road`).
- compatibility: all 9 existing read-only tools and 10 MCP Prompts keep their exact schemas and behavior; `tests/unit/test_mcp_tools.py` updates its `tools/list` name set to include the 13 added tools.
- acceptance: criteria 1, 2, 3, 4, and 5
- tests: tests/unit/test_mcp_control_and_tickets.py, tests/unit/test_mcp_tools.py
- post-merge source of truth: clutch/mcp.py

### `mcp serve` CLI help and command docs
- disposition: extend
- owner: clutch/__main__.py, clutch/docs/host-running.md, docs/how-clutch-works.md
- consumers: operators, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`
- observable change: updates the `mcp` group and `mcp serve` command help in `clutch/__main__.py`, the `| \`mcp serve\` |` row in `clutch/docs/host-running.md`, and the `| \`mcp serve\` |` row in `docs/how-clutch-works.md` section 2.1 to document the ticket, Suggestion Box, and detached engine-control tools alongside the read-only tools.
- compatibility: `clutch mcp serve` CLI argv and column-1 table names remain unchanged.
- acceptance: criteria 6 and 7
- tests: tests/unit/test_main_help.py, tests/unit/test_host_running.py, tests/unit/test_main_mcp_serve.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
In:
- `clutch/tickets.py`:
  - Add `new_ticket(repo, stem, kind="feature", *, evidence=(), reference=(), inputs=(), fs=None, template_fn=template, validate_fn=validate_ticket, lint_fn=lint_findings, evidence_fn=evidence_findings, missing_evidence_fn=missing_evidence_findings)` executing stem, evidence/reference/input validation, duplicate/symlink checks, `template_fn`, `validate_fn`, `lint_fn`, and `evidence_fn`/`missing_evidence_fn`, writing via `fs` (defaulting to `LocalFileSystem()`) and returning `(rel, guide, findings)` while raising `runner.Refusal(..., code=...)` on failures.
  - Add `async def lint_tickets(checkout, stems=(), *, admission_facts_fn=None, lint_admission_fn=None, pending_fn=_pending, porcelain_fn=_porcelain, intake_claims_fn=_intake_claims, validate_fn=validate_ticket, lint_fn=lint_findings, evidence_fn=evidence_findings, judge_fn=None, stuck_ceiling_fn=None)` returning `{"valid": valid, "total": total, "exit_code": exit_code, "findings": [{"path": str, "code": str, "message": str, "paved_road": str}, ...], "refusals": [{"path": str, "message": str, "paved_road": str}, ...]}` and handling linked-worktree journals.
  - Add `order_ticket(checkout, stem, *, priority=None, runs_before=None, empty_road="supply priority or runs_before", stem_findings_fn=stem_findings, admission_facts_fn=None, lock_holder_fn=None, order_admission_fn=None, order_fn=order, validate_fn=validate_ticket)` writing via `checkout.fs` and returning `{"stem": stem, "path": rel, "priority": ..., "runs_before": [...]}`.
- `clutch/box.py`:
  - Add `suggest(state_dir, fs, journal, summary, *, origin="session", occurrence_id=None) -> tuple[str, bool]` refusing blank summaries (`code="blank_summary"`) and calling `Box(...).enqueue(message_class="suggestion", ...)`.
- `clutch/observe.py`:
  - Add `ping_engine(state_dir, read=Path.read_bytes) -> dict` using `lock_holder`, `lock_verb`, `ENGINE_VERBS`, and `control.read_active`.
- `clutch/serve.py`:
  - Add `start_detached(repo, state_dir, verb, *, config_path=None, env, spawn=seams.spawn_detached) -> tuple[int, Path]` refusing when `observe.lock_holder(state_dir)` is non-None (`code="lock_held"`), spawning `[sys.executable, "-m", "clutch", *(["--config", str(config_path)] if config_path else []), "engine", verb]` via `spawn`, and calling `capture_startup_baseline` + `wait_detached_startup` via `clutch.serve` module globals when `verb == "serve"`.
- `clutch/runner.py`:
  - Move the single canonical writer-lock context `_locked(state_dir, verb, *, instance_id=None, clock, lock_factory=None)` (calling `Lockfile(...)` when `lock_factory is None` else `lock_factory(...)`, acquiring, yielding, and releasing in `finally`) from `clutch/__main__.py` into `clutch/runner.py`; `clutch/__main__.py::_locked` stays a thin wrapper passing `lock_factory=Lockfile` so `entry.Lockfile` monkeypatches still intercept CLI locks with zero duplicate lock-context code.
  - Add `submit_engine(checkout, exc, verb, *, stem=None, extension=False, ids=None, reason=None, read_active_fn=control.read_active, publish_fn=control.publish_request)` validating `ENGINE_VERBS` via `_require_engine`, running per-stem `intake` on pending tickets, calling `read_active_fn` and `publish_fn`, refusing missing hold on `"resume"` and blank `reason` on `"reject"`.
  - Add `submit_verdict(stem, checkout, *, kill, extension=False, reason=None, submit_fn=submit_engine)` refusing blank `reason` when `kill=True` (`code="blank_reason"`), calling `verdict(...)` (with `redirect_stdout` capturing print output so JSON-RPC stdio stays clean) and falling back on `LockHeld` to `submit_fn`, returning `{"stem": stem, "verb": ..., "actor": "extension" if extension else "operator", "submitted": bool, "request_id": str | None, "outcome": ...}`.
  - Add `control_engine(checkout, verb, *, lock_factory=Lockfile, submit_fn=submit_engine)` acquiring `lock_factory` or submitting `"pause" | "resume" | "stop" | "kill"` on `LockHeld`, refusing `"kill"` / `"stop"` when nothing runs (`code="nothing_running"`) and returning `status: "nothing_running"` for `"pause"` / `"resume"`.
  - Add `dismiss_boxes(checkout, ids, *, lock_ctx_factory, reap_fn=reap, dismiss_fn=triage.dismiss)` acquiring the lock context, calling `reap_fn`, and returning `dismiss_fn(checkout, ids)`.
  - Add `triage_or_submit(checkout, ids, *, lock_ctx_factory, build_control_fn, preflighted_llm_fn, submit_fn=submit_engine, reap_fn=reap, validate_ids_fn=triage.validate_ids, triage_pass_fn=triage.triage_pass)` acquiring lock -> `reap_fn` -> `validate_ids_fn` -> `triage_pass_fn`, or submitting `"triage"` on `LockHeld`.
  - Add `run_or_submit_retro(checkout, pipeline_fn, *, config_path=None, lock_ctx_factory, build_control_fn, config_reloader_fn, submit_fn=submit_engine, reap_fn=reap)` acquiring lock -> `reap_fn` -> `Retro(checkout, dispatch)(forced=True)`, or submitting `"retro"` on `LockHeld`.
- `clutch/mcp.py`:
  - Add `spawn=seams.spawn_detached` parameter on `ClutchMCPServer.__init__` and `contextlib.redirect_stdout(sys.stderr)` protection around `server.dispatch` inside `serve_stdio`.
  - Add Pydantic `BaseModel` (`extra="forbid"`) schemas and `TOOLS` entries for:
    - Model-visible tools: `clutch_ticket_new`, `clutch_ticket_lint`, `clutch_ticket_order`, `clutch_ticket_confirm`, `clutch_ticket_reject`, `clutch_box_suggest`, `clutch_box_triage`, `clutch_box_dismiss` (`ids: list[str] = Field(min_length=1)`), `clutch_engine_start`, `clutch_engine_control`, `clutch_engine_retro`.
    - App-only tools (advertised in `tools/list` with `"_meta": {"ui": {"visibility": ["app"]}}`): `clutch_app_ticket_confirm`, `clutch_app_ticket_reject`.
  - Enforce `extension=False` (`actor: "operator"`) on `clutch_ticket_confirm` / `clutch_ticket_reject` (forbidding any `extension` field via `extra="forbid"`) and `extension=True` (`actor: "extension"`) on `clutch_app_ticket_confirm` / `clutch_app_ticket_reject`.
  - Route `clutch_ticket_lint` to `tickets.lint_tickets`: when `result["exit_code"] == 2`, raise `runner.Refusal(first["message"], first["paved_road"], code="lint_refused")` from `result["refusals"][0]`; otherwise return `{"valid": result["valid"], "total": result["total"], "valid_all": result["exit_code"] == 0, "findings": result["findings"]}`.
  - Route `clutch_engine_start` `mode: Literal["drain", "serve"]` to `serve.start_detached`; route `clutch_engine_control` `action == "ping"` to `observe.ping_engine` and `"pause" | "resume" | "stop" | "kill"` to `runner.control_engine`.
  - Map `LockHeld` (`code="lock_held"`), `CommitLockTimeout`, `IntakeRefused`, `ProviderSetupError`, `ExecutableNotFound`, and `hostfiles.MarkerCorruption` (in addition to `Refusal`, `ConfigError`, `JournalCorruption`, `GitError`, `UnknownBoxId`, `ValueError`) in `tools/call` to `isError: True` with `structuredContent: {"code": ..., "message": ..., "paved_road": ...}`.
- `clutch/__main__.py`:
  - Delegate `_new`, `_lint`, `_order`, `handle_suggest`, `handle_detach`, `_submit_engine`, `_verdict`, `_control`, `handle_dismiss`, `handle_triage`, and `_retro` to the shared domain owners above while explicitly passing `clutch.__main__` module globals (`LocalFileSystem`, `template`, `validate_ticket`, `lint_findings`, `evidence_findings`, `missing_evidence_findings`, `stem_findings`, `order`, `admission_facts`, `lint_admission`, `order_admission`, `_intake_claims`, `_pending`, `_porcelain`, `Lockfile`, `_locked`, `control.read_active`, `control.publish_request`, `build_control`, `_preflighted_llm`, `_config_reloader`, `_submit_engine`, `spawn`) so existing CLI output, exit codes, and test monkeypatch hooks remain identical.
  - Update `_parser()` `mcp` group and `mcp serve` help strings (`summary`, `does`, `writes`, `description`) to reflect read, ticket, Suggestion Box, and detached engine-control tools.
- `clutch/docs/host-running.md`: update the `| \`mcp serve\` |` row description to reflect read, ticket, Suggestion Box, and detached engine-control MCP tools (noting that mutation tools submit to the running engine's inbox on `LockHeld`) while keeping column 1 exact and keeping `Yes` in column 2 (`Works while serve runs?`).
- `docs/how-clutch-works.md`: update the `| \`mcp serve\` |` row in section 2.1 to reflect read, ticket, Suggestion Box, and detached engine-control MCP tools (plus app-only UI verdict tools).
- `tests/integration/test_main_verb_groups.py`: update `test_shared_call_has_one_owner` to parse `clutch/runner.py` for the moved single-owner calls (`Lockfile` in `_locked`, `_require_engine` / `control.read_active` / `control.publish_request` in `submit_engine`) and `clutch/__main__.py` for `observe.Context` in `_observe_context`.
- `tests/unit/test_mcp_tools.py`: update `test_schemas_and_prompts` expected `tools/list` name set to all 22 tools. Nothing else in `tests/unit/test_mcp_tools.py` changes.
- New unit test file `tests/unit/test_mcp_control_and_tickets.py` using `tmp_path`, `io.StringIO`, and in-memory fakes only (zero real subprocesses, network, or repo file reads): builds a `tmp_path` checkout (`tickets/` + `config.yaml` from `tests.config_helpers.VALID`) or monkeypatches `server.checkout` to return a `runner.Checkout` over `tmp_path`, `FakeFileSystem`, `Journal`, `GitFake`, and `FakeClock`, injects `spawn=Mock(...)` into `ClutchMCPServer`, and fakes `build_control` / `_preflighted_llm` / `Retro` for lock-free `triage` and `retro`, covering all 13 new tools, `_meta.ui.visibility`, `actor: "operator"` vs `actor: "extension"` separation, admission refusals, `LockHeld` and domain error mapping, `stdout` purity during `serve_stdio`, and exercising `clutch/mcp.py` to meet its 90% coverage floor.
- Engine-written `# clutch:meta` header lines on newly created files under `tests/` updated by Check's meta step.

Out:
- `ui://clutch/dashboard.html`, `clutch_open_dashboard`, `clutch_app_snapshot`, `clutch_app_stats`, `com.google.antigravity/ui` entrypoints, and `clutch/ui/` (deferred to `mcp-app-dashboard`).
- `clutch/specs/ask/*.md` (`ask-specs-mcp-supervision`), `clutch/antigravity.py` (`host-antigravity-plugin`), `clutch/help.py`, `vscode-clutchwork/`, and `README.md`.
- Adding tests to any of the seven hot test files (`tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`) or existing unit/integration test files beyond the exact-set update in `tests/unit/test_mcp_tools.py` and the moved-owner AST rows in `tests/integration/test_main_verb_groups.py`.

## Scope fence
- clutch/mcp.py
- clutch/tickets.py
- clutch/box.py
- clutch/observe.py
- clutch/serve.py
- clutch/runner.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_mcp_tools.py
- tests/unit/test_mcp_control_and_tickets.py
- tests/integration/test_main_verb_groups.py

## Acceptance criteria
1. `tests/unit/test_mcp_tools.py` checks `tools/list` returns all 22 tool names; `tests/unit/test_mcp_control_and_tickets.py` checks the 20 model-visible tools (9 read-only plus 11 control/ticket tools) omit `visibility: ["app"]`, while `clutch_app_ticket_confirm` and `clutch_app_ticket_reject` include `"_meta": {"ui": {"visibility": ["app"]}}` (and neither `clutch_ticket_confirm` nor `clutch_ticket_reject` accepts an `extension` parameter, rejecting it via JSON-RPC `-32602`). Verified by `./dev.py test tests/unit/test_mcp_tools.py tests/unit/test_mcp_control_and_tickets.py`.
2. `tests/unit/test_mcp_control_and_tickets.py`: `clutch_ticket_new` creates a valid draft skeleton (and copies `--evidence` / `--reference` files) returning `stem`, `path`, `guide`, and structured lint `findings`, and returns `isError: true` on bad/existing stem or missing bug evidence; `clutch_ticket_lint` returns `valid`, `total`, `valid_all`, and structured `findings` (`path`, `code`, `message`, `paved_road`) when `lint_tickets` returns `exit_code` 0 or 1, and returns `isError: true` with `code: "lint_refused"` whenever `lint_tickets` returns `exit_code == 2` (such as a missing/escaped named stem or unreadable `tickets/` directory); `clutch_ticket_order` updates `priority` and `runs_before` (including clearing `## Runs before` with `runs_before: []`) and refuses settled/running/invalid tickets (`isError: true`); `clutch_ticket_confirm` and `clutch_ticket_reject` always invoke `runner.submit_verdict` with `extension=False` (recording `actor: "operator"` in `AdmissionRequest` and refusing same-content repeat keeps), whereas `clutch_app_ticket_confirm` and `clutch_app_ticket_reject` invoke it with `extension=True` (`actor: "extension"`), and `clutch_ticket_reject` refuses blank `reason` (`isError: true`). Verified by `./dev.py test tests/unit/test_mcp_control_and_tickets.py`.
3. `tests/unit/test_mcp_control_and_tickets.py`: `clutch_box_suggest` files a suggestion via `box.suggest` returning `id` and `created` and refuses blank summaries (`isError: true`); `clutch_box_triage` runs a lock-free pass or submits a `TriageRequest` to a running `drain`/`serve` and refuses non-engine lock holders (`code: "lock_held"`, `isError: true`) and unknown box IDs; `clutch_box_dismiss` dismisses named IDs via `triage.dismiss` when unlocked and returns `isError: true` with `code: "lock_held"` when `clutch.lock` is held (or `-32602` on empty `ids: []`). Verified by `./dev.py test tests/unit/test_mcp_control_and_tickets.py`.
4. `tests/unit/test_mcp_control_and_tickets.py`: `clutch_engine_start` invokes `serve.start_detached` (through the injected `spawn` seam, never spawning a child of the MCP stdio process) for `"drain"` and `"serve"`, refuses when `observe.lock_holder` reports a live lock (`code: "lock_held"`, `isError: true`), and surfaces `serve` startup timeouts/refusals as `isError: true`; `clutch_engine_control` returns live lock/active projection for `"ping"` (distinguishing stopped, non-engine holder, and running `serve`/`drain`), submits `ControlRequest` for `"pause"`, `"resume"`, `"stop"`, and `"kill"` when an engine runs, returns `status: "nothing_running"` for `"pause"`/`"resume"` when idle, and returns `isError: true` for `"stop"`/`"kill"` when idle or missing hold on `"resume"`; `clutch_engine_retro` submits `"retro"` when an engine runs or runs `Retro` when idle. Verified by `./dev.py test tests/unit/test_mcp_control_and_tickets.py`.
5. `tests/unit/test_mcp_control_and_tickets.py`: `serve_stdio` emits strictly valid JSON-RPC lines on `stdout` even when underlying domain functions write to `sys.stdout` (redirected away from the JSON-RPC pipe), and maps `LockHeld`, `CommitLockTimeout`, `IntakeRefused`, `ProviderSetupError`, `ExecutableNotFound`, and `MarkerCorruption` to `isError: true` with non-empty `code`, `message`, and `paved_road`; Check's `unit` mechanical gate (`clutch coverage gate` against `test-gate.toml`) passes with `clutch/mcp.py` meeting the 90% default floor (`./dev.py test tests/unit/test_mcp_control_and_tickets.py`).
6. Existing CLI, help, host-running, ticket, box, verdict, lock-holder, serve-detach, verb-group ownership, and retro tests pass (`./dev.py test tests/unit/test_mcp_protocol.py tests/unit/test_mcp_tools.py tests/unit/test_main_mcp_serve.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_docs_verb.py tests/unit/test_new_evidence.py tests/unit/test_graphics_new.py tests/unit/test_ticket_lint_rules.py tests/unit/test_route_kinds_judge.py tests/unit/test_main_ticket_group.py tests/unit/test_main_box_group.py tests/unit/test_lock_holder.py tests/unit/test_reject_reason_paths.py tests/unit/test_verdict_extension.py tests/unit/test_verdict_menu_parity.py tests/unit/test_main_serve_detach.py tests/unit/test_drain_detach_cli.py tests/unit/test_serve_detach.py tests/unit/test_manual_retro_calibration_verbs.py tests/integration/test_help.py tests/integration/test_mcp_read_server.py tests/integration/test_main_verb_groups.py` exits `0`).
7. `clutch/__main__.py` (`mcp` / `mcp serve` help), `clutch/docs/host-running.md` (`| \`mcp serve\` |`), and `docs/how-clutch-works.md` (section 2.1 `| \`mcp serve\` |`) document the added ticket, Suggestion Box, and detached engine-control MCP tools accurately and pass `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/integration/test_help.py`.

## Verification
```
./dev.py test tests/unit/test_mcp_control_and_tickets.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_protocol.py tests/unit/test_main_mcp_serve.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_docs_verb.py tests/unit/test_new_evidence.py tests/unit/test_graphics_new.py tests/unit/test_ticket_lint_rules.py tests/unit/test_route_kinds_judge.py tests/unit/test_main_ticket_group.py tests/unit/test_main_box_group.py tests/unit/test_lock_holder.py tests/unit/test_reject_reason_paths.py tests/unit/test_verdict_extension.py tests/unit/test_verdict_menu_parity.py tests/unit/test_main_serve_detach.py tests/unit/test_drain_detach_cli.py tests/unit/test_serve_detach.py tests/unit/test_manual_retro_calibration_verbs.py tests/integration/test_help.py tests/integration/test_mcp_read_server.py tests/integration/test_main_verb_groups.py
```

## Definition of rejected
- Any business logic, admission rule, lock-file probe, or CLI subprocess invocation lives inside `clutch/mcp.py` instead of calling the shared Python domain owners.
- Model-visible `clutch_ticket_confirm` or `clutch_ticket_reject` accepts `extension=True` / records `actor: "extension"`, or `clutch_app_ticket_confirm` / `clutch_app_ticket_reject` omits `_meta.ui.visibility = ["app"]`.
- `clutch_engine_start` spawns `drain` or `serve` attached to the MCP stdio process instead of detached via `serve.start_detached`.
- Any domain `print()` leaks onto the JSON-RPC `stdout` stream during `serve_stdio`, or `Refusal` / `LockHeld` / domain errors fail to return `isError: true` with `code`, `message`, and `paved_road`.
- Any file outside `## Scope fence` is modified, or `clutch/mcp.py`, `clutch/tickets.py`, `clutch/box.py`, `clutch/observe.py`, `clutch/serve.py`, `clutch/runner.py`, or `clutch/__main__.py` drops below its `test-gate.toml` unit coverage floor.

## Time budget
- expected: 25m
- stuck: 50m
