---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- requisition-review-session-stem

## Context
- clutch/llm.py::LLMRequest
- clutch/providers.py::ClaudeAdapter.session_name
- clutch/driver.py::Driver.run
- clutch/driver.py::Driver.run_panel
- clutch/requisition.py::review_ticket
- clutch/metafill.py::make_ask
- tests/unit/test_claude_session_name.py

## On-demand
- clutch/author.py
- clutch/triage.py
- clutch/retro.py
- clutch/acceptance.py
- clutch/training.py
- clutch/__main__.py
- tests/config_helpers.py

## Goal / Why
`LLMRequest.ticket: str | None` has one reader: `ClaudeAdapter.session_name`, which names each `claude` session `Clutch <Surface> <ticket>`. A `None` value means "this call has no ticket", but it looks exactly like "this caller forgot its stem". Requisition Review passed `None` while it had a stem in scope (`requisition-review-session-stem`), and no type, test or review caught it, because `None` was always a legal value.

When this ticket is done, the field is `subject: str`. It is required, and an empty string is refused. Every call names what it acts on: the ticket stem for ticket work, or a label for ticketless work. A dropped stem is then a construction error instead of a silent unnamed session. Every `claude` session is named `Clutch <Surface> <subject>`, so ticketless sessions also say what they were for (`Clutch Triage box-000955`, not `Clutch Triage`).

## Boundary contract
### LLM request subject
- disposition: replace
- owner: clutch/llm.py
- consumers: `ClaudeAdapter.session_name` (`clutch/providers.py`); every `LLMRequest` constructor (`clutch/driver.py`, `clutch/requisition.py`, `clutch/training.py`, `clutch/providers.py` preflight, `clutch/__main__.py` probe); tests and test harnesses that build an `LLMRequest` (including the shared `req()` factory in `tests/config_helpers.py`) or read `req.ticket` / `request.ticket` off `FakeLLM.requests`
- observable change: `LLMRequest.ticket: str | None` becomes `LLMRequest.subject: str`; `__post_init__` raises `ValueError` when `subject` is not a non-empty `str`; `session_name(surface, subject)` always returns `Clutch <Surface> <subject>`
- compatibility: breaking rename with no shim. Every constructor and reader is updated in this change (old contract `ticket`, replacement `subject`). Ticket-scoped calls carry the same stem as before, so their session names are unchanged. Journal keys, spool paths, evidence records (`stem` comes from `CallCapture`, not the request) and `driver.run`'s own `ticket` argument keep their meaning.
- acceptance: constructing a request with `subject=None` or `subject=""` raises `ValueError`; ticketless session names carry their label
- tests: `tests/unit/test_llm_request_subject.py`, `tests/unit/test_claude_session_name.py`
- post-merge source of truth: clutch/llm.py

### Driver ticketless subject
- disposition: extend
- owner: clutch/driver.py
- consumers: the ticketless `driver.run`/`run_panel` callers in `clutch/author.py`, `clutch/triage.py`, `clutch/retro.py`, `clutch/acceptance.py`, `clutch/metafill.py`; tests that run the driver with `ticket=None`; tests that assert the exact driver kwargs of a ticketless caller (`tests/unit/test_triage_panel_use.py`, `tests/unit/test_roadmap_accept.py`)
- observable change: `Driver.run` and `Driver.run_panel` take keyword `subject: str | None = None`. With `ticket` set, `subject` must be `None` and the request subject is the ticket. With `ticket=None`, `subject` must be a non-empty `str`. Either violation raises `ValueError` before any call, following the existing `run_seq requires ticket=None` check.
- compatibility: ticket-scoped callers are unchanged; ticketless callers must now pass `subject`. Journal and spool keying by `ticket or surface` and `run_seq` are unchanged.
- acceptance: `driver.run(..., ticket=None)` without `subject` raises `ValueError`; with `subject="box-1"` the request carries `subject == "box-1"`
- tests: `tests/unit/test_llm_request_subject.py`
- post-merge source of truth: clutch/driver.py

## Scope in / Scope out
In:
- `clutch/llm.py`: rename the field `ticket` to `subject`, type `str`, keeping its position. Extend `__post_init__` to raise `ValueError("subject must be a non-empty string")` when it is not a non-empty `str`.
- `clutch/providers.py`: `session_name(surface, subject: str)` returns `f"Clutch {Surface} {subject}"` with no `None` branch. `invoke` passes `req.subject`. The parallel preflight probe builds its request with `subject=model`. `list_models` keeps passing `alias`.
- `clutch/__main__.py`: the probe verb's request uses `subject=model`.
- `clutch/driver.py`: add `subject` to `run`, `run_panel` and `_run` as specified in the boundary contract, and build `LLMRequest(subject=ticket if ticket is not None else subject, ...)`.
- `clutch/requisition.py`: `ticket=stem` becomes `subject=stem`.
- `clutch/training.py` `evaluate`: `subject=f"eval-{counts['total'] + 1}"`, computed before the increment.
- The ticketless driver callers pass these labels: `clutch/author.py` `subject=message.id`; `clutch/triage.py` `subject=message.id` in its shared `kwargs`; `clutch/retro.py` `subject=f"window-{window.sequence}"`; `clutch/acceptance.py` `subject=release`; `clutch/metafill.py` `subject=f"{len(paths)}-files"`.
- Tests and test harnesses: update every file that reads `.ticket` off an `LLMRequest` (`req.ticket` or `request.ticket`), builds an `LLMRequest`, runs the driver with `ticket=None`, or asserts the exact driver kwargs of a ticketless caller. Each is listed in `Scope fence`, and the only edit in each is the rename, or adding a `subject` label for ticketless runs. The shared `req()` factory in `tests/config_helpers.py` changes `ticket="t-1"` to `subject="t-1"`. Tests that built a request with `None` (`tests/integration/test_driver.py:362`, `tests/integration/test_fixture_host.py:369` and `:372`, `tests/unit/test_preflight_parallel.py`, `tests/unit/test_training_eval.py`) pass a label instead (`"probe"`, `"unknown"`, `"exhausted"`, the model name, `"eval-1"` and so on). `tests/unit/test_stages_helpers.py` changes `ticket=h.STEM` to `subject=h.STEM` in its `LLMRequest`. `tests/harness/shakeout/driver.py`, `tests/harness/daemon_soak.py`, `tests/integration/test_serve_scan_watch_overlap.py` and `tests/integration/test_serve_parallel_admission.py` read `subject` instead of `ticket` off recorded requests. In `tests/unit/test_triage_panel_use.py`, the expected kwargs dict gains `subject=<message id>`. In `tests/unit/test_roadmap_accept.py`, the expected kwargs dict gains `subject=release`. In `tests/unit/test_claude_session_name.py`, the `ticket=None` / `Clutch Retro` case becomes `subject="window-3"` / `Clutch Retro window-3`.
- New `tests/unit/test_llm_request_subject.py`, covering the acceptance criteria below.

Out: `driver.run`'s `ticket` parameter and its journal, spool, watch and evidence semantics; the `--name` flag itself; the Codex adapter; docs (no document describes the request field or session names); the requisition `event_context`; `Effects.run` and `thresh.run` calls with `ticket=None` in tests (they are not `Driver.run` and need no change).

## Scope fence
- clutch/llm.py
- clutch/providers.py
- clutch/__main__.py
- clutch/driver.py
- clutch/requisition.py
- clutch/training.py
- clutch/author.py
- clutch/triage.py
- clutch/retro.py
- clutch/acceptance.py
- clutch/metafill.py
- tests/config_helpers.py
- tests/unit/test_llm_request_subject.py
- tests/unit/test_claude_session_name.py
- tests/unit/test_route_kinds_filter.py
- tests/unit/test_training_eval.py
- tests/unit/test_preflight_parallel.py
- tests/unit/test_triage_panel_use.py
- tests/unit/test_roadmap_accept.py
- tests/unit/test_stages_helpers.py
- tests/unit/test_evidence_envelope.py
- tests/unit/test_panel_member_keys.py
- tests/unit/test_requisition_session_stem.py
- tests/integration/test_providers.py
- tests/integration/test_driver.py
- tests/integration/test_fixture_host.py
- tests/integration/test_evidence_envelope.py
- tests/integration/test_llm_effect.py
- tests/integration/test_watchdog_activation.py
- tests/integration/test_provider_cooldown_failover.py
- tests/integration/test_provider_capture_overwrite.py
- tests/integration/test_serve_admission.py
- tests/integration/test_serve_merge_overlap.py
- tests/integration/test_serve_scan_head.py
- tests/integration/test_serve_scan_watch_overlap.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/test_triage.py
- tests/integration/serve_rig.py
- tests/harness/shakeout/drain.py
- tests/harness/shakeout/driver.py
- tests/harness/daemon_soak.py
- tests/regress_requisition_events_owner_stem.py
- tests/regress_requisition_session_stem.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_llm_request_subject.py` passes and asserts the following:
   - `LLMRequest(..., subject=None, ...)` and `LLMRequest(..., subject="", ...)` each raise `ValueError` (not a request with an empty name).
   - `Driver.run` with `ticket=None` and no `subject` raises `ValueError` before any `FakeLLM` call (`FakeLLM.requests == []`).
   - `Driver.run` with `ticket="abc"` and `subject="x"` raises `ValueError`.
   - `Driver.run` with `ticket=None, subject="box-1"` records a request with `subject == "box-1"`, and with `ticket="abc"` records `subject == "abc"`.
2. `./dev.py test tests/unit/test_claude_session_name.py` passes with the Implement argv ending `["--name", "Clutch Implement abc"]` and the retro argv ending `["--name", "Clutch Retro window-3"]`, not `Clutch Retro`.
3. `uv run python tests/regress_requisition_session_stem.py` still prints `{"regression_result": "pass"}`, reading `subject`.
4. `./dev.py test tests/unit/test_llm_request_subject.py` also scans `clutch/llm.py` and `clutch/providers.py` (anchored on `Path(__file__)`) and asserts no line matches `ticket=None, worktree` or an `LLMRequest` `.ticket` read, and scans `clutch/` and `tests/` and asserts no line matches `req(uest)?\.ticket\b`, skipping each file's leading `# clutch:meta` header block (the engine's Check writes those header lines and may describe this very pattern). `CallCapture.ticket` in `clutch/providers.py` is a different object and is read with plain attribute access, not `getattr`; the scan allows it.
5. `./dev.py test tests/unit/test_llm_request_subject.py` asserts that `tests/config_helpers.py` contains no `ticket="t-1"`.
6. `./dev.py test` passes on the full suite.

## Verification
```
./dev.py test tests/unit/test_llm_request_subject.py tests/unit/test_claude_session_name.py
uv run python tests/regress_requisition_session_stem.py
./dev.py test
```

## Definition of rejected
`LLMRequest` still accepts `None` or an empty subject; a default value is given to `subject` on `LLMRequest`; a compat alias keeps `ticket` readable; `driver.run`'s `ticket` journal or spool semantics change; or a ticketless caller passes a generic constant (such as `"all"` or the surface name) instead of the label named in Scope in.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one mechanical rename across a closed list of constructors and readers; splitting the LLMRequest rename from the driver subject would leave main with requests that cannot be built for ticketless runs