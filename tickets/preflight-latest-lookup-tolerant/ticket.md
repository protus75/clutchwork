---
state: confirmed
source: box:suggestion
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/providers.py::ProviderLLM.preflight
- tests/unit/test_preflight_parallel.py

## Goal / Why
On 2026-11-17 the roadmap driver's authoring pass called `_preflighted_llm`. The `pnpm view <package> version` lookup in `ProviderLLM.preflight` timed out, and the `TimeoutError` escaped preflight, `clutch/roadmap.py::drive` (which catches only `Refusal`) and `drain._run_driver`. The drain exited with a traceback. That lookup only feeds the advisory 'is not the latest release' notice, so a slow registry or a host without pnpm should at most drop the notice. After this ticket, a `TimeoutError` or `ExecutableNotFound` from the latest-version lookup is treated as 'latest unknown': preflight adds no notice for that provider, raises nothing, and still runs every probe and returns the same refusals as before. Code in the same file already tolerates both errors around exec calls.

## Scope in / Scope out
In: in `ProviderLLM.preflight`, wrap only the `pnpm view` exec call so `TimeoutError` and `ExecutableNotFound` leave no notice for that adapter. `adapter.cli_version` is still set from the `--version` output. A lookup that returns empty output keeps today's '(unreadable)' notice. A new unit test file covers it.
Out: the driver step's handling of non-`Refusal` errors (a separate cause-class fix, declined before as box-000540, not folded in here); the `--version` exec call; the probes; docs.

## Scope fence
- clutch/providers.py
- tests/unit/test_preflight_latest_lookup.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_preflight_latest_lookup.py` runs preflight with a fake exec whose `pnpm view` argv raises `TimeoutError`. It asserts preflight returns without raising and that `preflight_notices == []`, not an escaped `TimeoutError`.
2. The same test file runs the case with `ExecutableNotFound` raised on the `pnpm view` argv. It asserts no raise and `preflight_notices == []`.
3. In both cases the test asserts the probe calls still ran, meaning the exec calls include the model probe argv for every routed model, and that the returned list equals the one a run with a succeeding `pnpm view` returns. A fix that skips probes after the error fails this.
4. The test file asserts that a `pnpm view` returning empty output still yields a notice containing '(unreadable)', so the existing behavior is kept.

## Verification
```
./dev.py test tests/unit/test_preflight_latest_lookup.py tests/unit/test_preflight_parallel.py
```

## Definition of rejected
A branch that catches a bare `Exception`, wraps the whole preflight body, or changes `clutch/roadmap.py` or `clutch/drain.py`. A branch that suppresses the `--version` or probe errors. A branch that passes only because the new test does not raise `TimeoutError` from the `pnpm view` argv.

## Time budget
- expected: 20m
- stuck: 40m
