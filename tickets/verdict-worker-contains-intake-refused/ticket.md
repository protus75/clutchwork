---
state: confirmed
source: box:suggestion
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- serve-live-verdicts

## Context
- clutch/runner.py::apply_admission
- clutch/serve.py::Serve.apply_verdict
- clutch/tickets.py::IntakeRefused
- tests/unit/test_serve_scan_intake_refused.py
- tests/unit/test_runner_verdict_reread.py

## Goal / Why
When an operator session leaves a non-ticket file staged in the shared checkout (for example `config.yaml` or `vscode-clutchwork/package.json`) and a verdict (confirm or reject) is queued, serve must log `verdict_refused` and keep running. Today the verdict settlement worker reaches `verdict_locked`, which calls intake with `stems={stem}`. Intake raises `IntakeRefused` on any stray staged path before it filters stems. `IntakeRefused` is not a `runner.Refusal`, so the `except Refusal` in `runner.apply_admission` does not catch it. The exception leaves the worker, serve logs `engine_stop` and `worker_failure`, and every in-flight run ends `infra_error`.

The earlier containment in `Serve.scan` (the `IntakeRefused` catch) covers only the scan poll. It does not re-solve this path. The verdict worker came with `serve-confirm-during-check` and `serve-live-verdicts`. `serve-contains-dispatch-exception` contains dispatch exceptions, not this worker.

## Boundary contract
### Verdict admission refusal
- disposition: extend
- owner: clutch/runner.py (`apply_admission`)
- consumers: `Serve.apply_verdict` in clutch/serve.py, which logs `verdict_refused` from the returned `refusal`; the CLI verdict verbs, which already catch `IntakeRefused` at the top level
- observable change: `apply_admission` returns `{"refusal": <message with paved road>}` when `verdict_locked` raises `IntakeRefused`, as it already does for `Refusal`. The exception no longer escapes to the worker.
- compatibility: the return shape, the `Refusal` handling and every other exception path are unchanged. No journal event is added on the refused path.
- acceptance: with `verdict_locked` raising `IntakeRefused`, `apply_admission` returns a non-None refusal containing the finding message, and `Serve.apply_verdict` logs `verdict_refused` and does not raise
- tests: a new unit test file
- post-merge source of truth: clutch/runner.py

## Scope in / Scope out
Scope in: in `clutch/runner.py::apply_admission`, catch `IntakeRefused` together with `Refusal` around the `verdict_locked` call and turn it into the same `refusal` string. Add any import this needs. Add one new unit test file covering `apply_admission` and `Serve.apply_verdict` when `verdict_locked` raises `IntakeRefused`.

Scope out: `Serve.scan`; the `IntakeRefused` definition; intake's stray-path rule; how a refused verdict is retried, which is the operator's re-issue after unstaging; docs, because no documented behavior changes. A lint or gate for uncontained exception types in workers is not cheap and is out of scope; the owner is told so it can go to the Suggestion Box.

## Scope fence
- clutch/runner.py
- tests/unit/test_runner_verdict_intake_refused.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_runner_verdict_intake_refused.py` passes. It asserts that `runner.apply_admission` with `verdict_locked` patched to raise `IntakeRefused` returns a refusal string containing the finding message, and not an escaped `IntakeRefused`.
2. The same test file asserts that `Serve.apply_verdict` under that condition returns normally and logs one `verdict_refused` event. It also asserts that no `engine_stop` or `worker_failure` event is logged.
3. The same test file asserts that a `Refusal` from `verdict_locked` still gives the same `refusal` result as before (`refusal` is not None).
4. `./dev.py test tests/unit/test_runner_verdict_reread.py tests/unit/test_serve_scan_intake_refused.py` still passes.

## Verification
```
./dev.py test tests/unit/test_runner_verdict_intake_refused.py tests/unit/test_runner_verdict_reread.py tests/unit/test_serve_scan_intake_refused.py
```

## Definition of rejected
A branch that catches `IntakeRefused` in the worker loop or in `Serve` by swallowing every exception. A branch that changes intake's refusal rule. A branch that adds a second code path beside the existing `Refusal` handling.

## Time budget
- expected: 15m
- stuck: 30m
