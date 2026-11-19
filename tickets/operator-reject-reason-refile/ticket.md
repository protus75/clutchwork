---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: confirmed
---

## Depends on
- none

## Context
- clutch/roadmap.py::rejection_reason
- clutch/control.py::AdmissionRequest
- clutch/control.py::validate_request
- clutch/control.py::publish_request
- clutch/control.py::decisions
- clutch/runner.py::verdict
- clutch/runner.py::verdict_locked
- clutch/runner.py::reject_ticket
- clutch/runner.py::apply_admission
- clutch/__main__.py::_verdict
- clutch/__main__.py::_submit_engine

## On-demand
- clutch/specs/ask/drafts.md

## Goal / Why
After this ticket, `clutch ticket reject --reason TEXT <stem>` records TEXT on the operator `reject_verdict` kill signal on both paths: the direct writer-lock path, and the running engine's inbox path. `clutch/roadmap.py::rejection_reason` returns TEXT first, followed by the Reject-queue terminal reason and the Diagnose lessons. A roadmap re-file therefore carries the operator's judgment.

Today an operator reject has no reason field. `rejection_reason` reads only the Reject-queue terminal reason and the diagnosis lessons, then falls back to the literal `rejected`. The re-file loses why the draft was rejected, so Author can redraft the same design. That happened with closed-sets-rest-r1 (box-000678). Its reject at 2026-11-17 14:46Z went through the running engine's inbox, which is the path the earlier attempt reject-reason-reaches-refile (state rejected) refused `--reason` on. This ticket covers that path, so the earlier attempt's gap does not recur.

## Boundary contract
### Admission request shape
- disposition: extend
- owner: clutch/control.py
- consumers: `_submit_engine` in clutch/__main__.py (publisher), the inbox consumer `consume` and `settle_admissions` in clutch/control.py, `settle_admissions` in clutch/drain.py, `apply_verdict` in clutch/serve.py
- observable change: a reject `AdmissionRequest` may carry an optional `operator_reason` (a nonempty string, named apart from the decision body's `reason`). It is carried into the accepted decision body and passed to the verdict callback only when present.
- compatibility: requests and journaled decision bodies without the field stay valid and byte-identical, because an absent reason is omitted, never written as null. A `confirm` request carrying the field, an empty string, or a non-string is refused with the shape road.
- acceptance: `validate_request` and `decisions` accept both shapes and refuse the malformed forms
- tests: new unit test file for request and decision validation
- post-merge source of truth: clutch/control.py

### Reject verdict signal
- disposition: extend
- owner: clutch/runner.py
- consumers: clutch/roadmap.py::rejection_reason, status and stats readers of `reject_verdict` (unchanged)
- observable change: the `reject_verdict` kill signal gains an optional `reason` key, set only when the operator gave one. `verdict`, `verdict_locked`, `reject_ticket` and `apply_admission` take an optional `reason` keyword that defaults to None.
- compatibility: a signal without a reason is journaled exactly as today; existing readers ignore the extra key; every call made without a reason is byte-identical to today's call
- acceptance: the reason lands on the signal on both the direct path and the `apply_admission` path
- tests: new unit and integration files
- post-merge source of truth: clutch/runner.py

### Rejection reason text
- disposition: extend
- owner: clutch/roadmap.py
- consumers: roadmap re-file (`refile_row` callers) in clutch/roadmap.py
- observable change: `rejection_reason(events, stem)` puts the `reason` of the latest `reject_verdict` signal whose `verdict` is `kill` and `actor` is `operator` first, then the existing terminal reason and lessons
- compatibility: with no operator reason the result is unchanged, including the `rejected` fallback
- acceptance: result starts with the operator reason; unchanged otherwise
- tests: new unit test file
- post-merge source of truth: clutch/roadmap.py::rejection_reason

### Reject verb
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators, the drafts prompt, the extension (unchanged)
- observable change: `clutch ticket reject` accepts `--reason TEXT`; `confirm` does not
- compatibility: existing invocations and the positional arguments of `_verdict` are unchanged
- acceptance: parser, help and both paths carry the reason
- tests: new unit and integration files
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/__main__.py`: add `--reason` to the `reject` subparser only (the `for verb in ("confirm", "reject")` loop must not add it to `confirm`). Update the reject command's `writes` and `examples` in `_command`. `_verdict` gains a keyword-only `reason=None`; its positional parameters stay. `handle_verdict` passes `getattr(args, "reason", None)`. `_verdict` forwards it to `runner.verdict` and to `_submit_engine`, which builds the request with it.
- `clutch/control.py`: `AdmissionRequest` gains `operator_reason: str | None = None`. `publish_request` and `validate_request` omit the key when None and allow it only on `reject` as a nonempty string. The accepted decision body in `consume` carries it only when set. `decisions` accepts the optional key. `settle_admissions` passes `reason=` to the verdict callback only when the body has one, so existing 4-argument callbacks keep working.
- `clutch/drain.py` and `clutch/serve.py`: the callbacks `apply` (in `settle_admissions`) and `apply_verdict` take an optional `reason=None` and forward it to `runner.apply_admission`.
- `clutch/runner.py`: `verdict`, `verdict_locked`, `reject_ticket` and `apply_admission` take the optional `reason`. `reject_ticket` adds `reason` to the kill signal only when given.
- Forwarding rule: every forwarding hop passes `reason=` only when it is not None, and otherwise makes the exact call it makes today with no extra argument or keyword. The hops are `_verdict` to `runner.verdict`, `runner.verdict` to `verdict_locked`, `apply_admission` to `verdict_locked`, `verdict_locked` to `reject_ticket`, and `apply_verdict` (clutch/serve.py) and drain's `apply` to `apply_admission`. With this rule the reason-free calls stay identical to what tests/unit/test_verdict_extension.py pins (the `verdict_locked` await arguments, the five positional arguments of the `apply_admission` await, and the four arguments of the settle callback), so that file is not edited and is run as a preservation check.
- `clutch/roadmap.py::rejection_reason`: put the `reason` of the latest `reject_verdict` signal whose `verdict` is `kill` and `actor` is `operator` first.
- `clutch/specs/ask/drafts.md`: the Recommendation step for rejected drafts gives one `clutch ticket reject --yes --reason "<why>" STEM` command per rejected draft, with the reason drawn from that draft's verdict. Do not change the version or any other text.
- Docs: the `ticket reject` row of the verb table in `docs/how-clutch-works.md` section 2 and the `ticket reject` row in `clutch/docs/host-running.md` name `--reason`; the backticked verb cell in the host-running row stays exactly as it is.
- Tests: new files only (see fence).

Scope out: `confirm`; the extension; Reject-queue behavior; the control-request shape for non-admission verbs; any existing test file, unless an assertion this change forces to flip names it.

## Scope fence
- clutch/__main__.py
- clutch/control.py
- clutch/drain.py
- clutch/serve.py
- clutch/runner.py
- clutch/roadmap.py
- clutch/specs/ask/drafts.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/unit/test_control_operator_reason.py
- tests/unit/test_roadmap_operator_reject_reason.py
- tests/unit/test_reject_reason_paths.py
- tests/integration/test_reject_reason_both_paths.py

## Acceptance criteria
1. In `tests/unit/test_roadmap_operator_reject_reason.py`, a journal holding an operator `reject_verdict` kill signal with `reason` `fence too wide` makes `rejection_reason` return a string starting with `fence too wide`, not `rejected`; with a routed Reject-queue terminal reason and diagnosis lessons also present, the result contains all three with the operator reason first; a kill signal with no `reason` and nothing else still returns exactly `rejected`; checked by `./dev.py test tests/unit/test_roadmap_operator_reject_reason.py`.
2. In `tests/unit/test_control_operator_reason.py`, `validate_request` accepts a reject request with `operator_reason` `x` and one without the key; it raises `ValueError` for a `confirm` request carrying the key, for an empty string, and for a non-string value, not a request object; `publish_request` of an `AdmissionRequest` without a reason writes JSON with no `operator_reason` key, not `null`; `decisions` yields both an accepted reject body with the key and the same body without it, and still raises on any other extra key; checked by `./dev.py test tests/unit/test_control_operator_reason.py`.
3. In `tests/unit/test_reject_reason_paths.py`, modelled on `tests/unit/test_verdict_extension.py` with fakes and monkeypatched callees, each forwarding hop has a named test that checks the reason is passed when given and that the call carries no `reason` keyword when absent, not `reason=None`: (a) `reject_ticket(stem, fake_checkout, reason="r")` against an in-memory fake journal records a kill signal whose `reason` is `r`, and without a reason the signal has no `reason` key, not `reason: None`; (b) `runner.verdict` forwards `reason` to a patched `verdict_locked`; (c) `verdict_locked(kill=True, reason="r")` forwards it to a patched `reject_ticket`; (d) `apply_admission` forwards `reason` to a patched `verdict_locked`; (e) drain's `settle_admissions` `apply` callback and serve's `apply_verdict` forward `reason` to a patched `runner.apply_admission`; (f) `ControlPlane.settle_admissions` passes `reason=` to the callback only when the body has `operator_reason`, so a 4-argument callback still works; (g) `consume` puts `operator_reason` in the accepted body only when the request sets it; (h) with `runner.verdict` raising `LockHeld`, `_verdict(..., "reject", ..., reason="r")` publishes a request whose `operator_reason` is `r`, not a request without it; (i) `handle_verdict` and the reject parser pass `args.reason` to `_verdict`, and a `confirm` parse has no `reason` attribute; checked by `./dev.py test tests/unit/test_reject_reason_paths.py`.
4. In `tests/integration/test_reject_reason_both_paths.py`, on the direct-lock path `clutch ticket reject --yes --reason X <stem>` journals a kill signal with `reason` `X`, and `rejection_reason(events, stem)` then starts with `X`. On the inbox path, with the writer lock held by an engine, the published request is accepted by the inbox consumer and applied by `apply_admission`, the same kill signal carries `X`, and `rejection_reason` starts with `X`, not `rejected`; checked by `./dev.py test tests/integration/test_reject_reason_both_paths.py`.
5. In the same file, `clutch ticket confirm --reason x <stem>` exits 2 as an unrecognized argument, not 0; `--reason` appears in the `ticket reject` subparser's help text; the `ticket reject` rows of `docs/how-clutch-works.md` and `clutch/docs/host-running.md` contain `--reason`; checked by `./dev.py test tests/integration/test_reject_reason_both_paths.py`.
6. In the same file, the drafts prompt rendered from `clutch/specs/ask/drafts.md` contains `ticket reject --yes --reason`, not only the bare `ticket reject --yes STEM` form; checked by `./dev.py test tests/integration/test_reject_reason_both_paths.py`.
7. The unchanged `tests/unit/test_verdict_extension.py` still passes, so reason-free calls to `verdict_locked`, `apply_admission` and the settle callback carry exactly their current arguments, not an added `reason=None`; checked by `./dev.py test tests/unit/test_verdict_extension.py`.
8. The unchanged `tests/unit/test_roadmap_rejection_reason.py` passes, including `test_other_stems_and_verdict_are_ignored`; checked by `./dev.py test tests/unit/test_roadmap_rejection_reason.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_operator_reject_reason.py tests/unit/test_control_operator_reason.py tests/unit/test_reject_reason_paths.py tests/integration/test_reject_reason_both_paths.py tests/unit/test_verdict_extension.py tests/unit/test_roadmap_rejection_reason.py tests/unit/test_main_ticket_verdicts.py tests/unit/test_main_help.py tests/unit/test_roadmap_refile.py tests/unit/test_host_running.py tests/unit/test_help.py tests/integration/test_control.py tests/integration/test_control_cli.py tests/integration/test_drain_admissions.py tests/integration/test_ask_drafts.py tests/unit/test_ask_drafts.py
```

## Definition of rejected
A branch where `rejection_reason` still returns `rejected` after an operator reject with `--reason` on either path; where `--reason` is refused or silently dropped when the engine holds the lock; where `confirm` accepts `--reason`; where a request or decision body without a reason changes shape; or where an existing control, drain or serve test only passes because its assertion was loosened.

## Time budget
- expected: 25m
- stuck: 50m
