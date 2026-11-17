---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: rejected
---

## Depends on
- none

## Context
- clutch/roadmap.py::rejection_reason
- clutch/runner.py::verdict
- clutch/runner.py::verdict_locked
- clutch/runner.py::reject_ticket
- clutch/__main__.py::_verdict
- tests/unit/test_roadmap_rejection_reason.py

## Goal / Why
After this ticket, `clutch ticket reject <stem> --reason "<text>"` records the text on the `reject_verdict` kill signal. `clutch/roadmap.py::rejection_reason` then returns text containing it. Today `ticket reject` takes no reason, and `rejection_reason` reads only the Reject-queue terminal reason and the Diagnose lessons. When an operator rejects a roadmap-row draft (closed-sets-rest, row 128, 2026-11-17, rejected for fencing protected files it did not need), the re-file request to Author says only `rejected`. Author then redrafts without the reason, can reproduce the same design, and each repeat spends a re-file unit.

The reason rides only on the direct writer-lock path. When a running drain or serve holds the lock, the request path has a strict shape that carries no reason. In that case `--reason` is refused with a road instead of silently dropped.

## Scope in / Scope out
Scope in:
- `clutch/__main__.py`: add an optional `--reason TEXT` argument to `ticket reject` only, not `confirm`. `_verdict` gains `reason=None` as a keyword-only parameter; its existing positional parameters stay unchanged. `handle_verdict` passes it as `reason=getattr(args, 'reason', None)`, so `confirm`, which has no such attribute, passes `None` and the positional arguments checked at `tests/unit/test_main_ticket_verdicts.py:42` (`verdict.await_args.args[4:] == (True, False)`) still hold. `_verdict` forwards the reason to `runner.verdict`. When `runner.verdict` raises `LockHeld` and a reason was given, `_verdict` raises `runner.Refusal` with the paved road "stop the engine or omit --reason" and submits no request. Update the reject command's `does`, `writes` and `examples` in `_command` to mention `--reason`. With several stems, the same reason applies to each.
- `clutch/runner.py`: `verdict`, `verdict_locked` and `reject_ticket` take an optional `reason` keyword that defaults to `None`. `reject_ticket` adds a `reason` key to the `reject_verdict` kill signal only when a reason is given. `apply_admission` and the other callers are unchanged.
- `clutch/roadmap.py::rejection_reason`: prepend the `reason` of the stem's latest operator `reject_verdict` kill signal that carries one, before the terminal reason and lessons. With none, behavior is unchanged.
- `tests/unit/test_roadmap_rejection_reason.py`: the one existing expectation that may change is the case where a `reject_verdict` signal carrying a `reason` alone yields `rejected`. It must now cover only a signal whose `verdict` is not `kill` or whose actor is not `operator`.
- `tests/unit/test_reject_reason_verdict.py` (new): unit tests that run the new lines in `clutch/__main__.py` and `clutch/runner.py` with fakes, since both files carry coverage floors.
- `tests/integration/test_reject_reason.py` (new): real-lock, parser, help and document checks.
- Docs: update the `reject` row of the verb table in `docs/how-clutch-works.md` section 2 (the row starting `| `ticket reject <stem>`) and the `| `ticket reject` |` row in `clutch/docs/host-running.md` to name `--reason`. In the host-running row the backticked verb cell stays exactly `ticket reject`, and `--reason` goes in the description column, so `tests/unit/test_host_running.py:18` and the verb lookup in `clutch/help.py` still hold.

Scope out: the control-request shape and `clutch/control.py`, `drain.py` and `serve.py`; carrying the reason through an engine-submitted request (separate work); the extension; `confirm`; Reject-queue behavior.

## Scope fence
- clutch/__main__.py
- clutch/runner.py
- clutch/roadmap.py
- tests/unit/test_roadmap_rejection_reason.py
- tests/unit/test_reject_reason_verdict.py
- tests/integration/test_reject_reason.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md

## Acceptance criteria
1. In `tests/unit/test_roadmap_rejection_reason.py`, a journal holding an operator `reject_verdict` kill signal `{"verdict": "kill", "actor": "operator", "reason": "fence too wide"}` for the stem makes `rejection_reason` return a string containing `fence too wide`, not `"rejected"`; run by `./dev.py test tests/unit/test_roadmap_rejection_reason.py`.
2. In the same file, when that signal coexists with a routed Reject-queue terminal reason and diagnosis lessons, the result contains all three, with the operator reason first; and a kill signal with no `reason` still yields exactly `"rejected"` when nothing else exists, not an empty string; checked by `./dev.py test tests/unit/test_roadmap_rejection_reason.py`.
3. In `tests/integration/test_reject_reason.py`, rejecting a draft through `reject_ticket(stem, checkout, reason="fence too wide")` journals a `reject_verdict` kill signal whose `reason` equals `fence too wide`. Without a reason the signal has no `reason` key, not `reason: None`; checked by `./dev.py test tests/integration/test_reject_reason.py`.
4. In the same file, `clutch ticket reject --reason x <stem>` parses; `clutch ticket confirm --reason x <stem>` exits 2 as an unrecognized argument; and with the writer lock held by an engine, `reject --reason x` raises a `Refusal` and writes no admission request file, not a submitted request; checked by `./dev.py test tests/integration/test_reject_reason.py`.
5. In the same file, `--reason` appears in the `ticket reject` subparser's `format_help()` and its option strings, and in the `| `ticket reject` |` row of `clutch/docs/host-running.md` and the `| `ticket reject <stem>` row of `docs/how-clutch-works.md`; a run with `--reason` removed from any of the four fails; checked by `./dev.py test tests/integration/test_reject_reason.py`.
6. In `tests/unit/test_reject_reason_verdict.py`, with `runner.verdict` monkeypatched to raise `LockHeld`, `_verdict(checkout, 'x', 'reject', None, True, False, reason='r')` raises `runner.Refusal` and publishes nothing, not a submitted request; `reject_ticket(stem, fake_checkout, reason='r')` against an in-memory fake journal records a `reason` key, and without `reason` the key is absent; `runner.verdict` forwards `reason` to `verdict_locked`; checked by `./dev.py test tests/unit/test_reject_reason_verdict.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_rejection_reason.py tests/unit/test_reject_reason_verdict.py tests/integration/test_reject_reason.py tests/unit/test_main_help.py tests/unit/test_main_ticket_verdicts.py tests/unit/test_roadmap_refile.py tests/unit/test_roadmap_status.py tests/unit/test_help.py tests/unit/test_host_running.py tests/integration/test_help.py
```

## Definition of rejected
A branch where `rejection_reason` still returns `rejected` after an operator reject with a reason; where `--reason` is silently dropped on the engine-request path; where `confirm` accepts `--reason`; or where `clutch/control.py`, `drain.py` or `serve.py` change.

## Time budget
- expected: 15m
- stuck: 30m
