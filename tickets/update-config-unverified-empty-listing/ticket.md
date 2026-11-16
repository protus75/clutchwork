---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/unit/test_update_config_verb.py
- clutch/docs/host-running.md

## On-demand
- clutch/__main__.py

## Goal / Why
When a provider's listing names no models and carries a problem, `clutch update-config` prints `not served; pick a served name` for every configured model of that provider. Nothing was checked, so the line is wrong. The suggested fix cannot be followed because no served names exist, and it can lead an operator to replace a working model. Today this happens for `codex` when `codex debug models` fails and for `qwen` when `ollama` is off PATH. It will happen for every `gemini` host once `gemini-provider` lands, because that adapter always returns an empty listing with a problem. After this change those configured names print an unverified status, so the operator is told nothing was checked rather than that the model is not served.

## Scope in / Scope out
Scope in:
- In the `update-config` branch of `clutch/__main__.py` (the `update_config` loop, the status chain after the `PLACEHOLDER` check), add one branch before the final `else`. When `listing.models` is empty and `listing.problems` is non-empty, the status is `unverified; no models listed (see problem above)`. The placeholder status still wins for a `PLACEHOLDER` name. A non-empty listing keeps `not served; pick a served name` for a name it lacks.
- The unverified status is not `current`, so the exit code stays 1 (`suggested |= status != "current"` is unchanged).
- In `tests/unit/test_update_config_verb.py`, the one existing assertion that expects `gpt-4.1 not served` under `serves: nothing listed` plus a problem flips to the unverified status. Add the tests for the criteria below in the same file, which covers only this verb.
- In `clutch/docs/host-running.md`, edit the `update-config` row so it says a name is reported as unverified when the provider's listing is empty with a problem.

Scope out: the `gemini-provider` ticket and any adapter's `list_models`; the generic wording for a non-empty listing; `docs/how-clutch-works.md`.

## Scope fence
- clutch/__main__.py
- tests/unit/test_update_config_verb.py
- clutch/docs/host-running.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_update_config_verb.py` has a test with a fake listing of no models and one problem. Each configured name prints a line containing `unverified`, and no output line contains `not served`.
2. A test with a non-empty listing that lacks a configured name still prints `not served; pick a served name` for that name. This rules out an `unverified` status applied to every name.
3. A test with an empty listing, a problem, and a configured name equal to `PLACEHOLDER` prints `is the placeholder; pick a served name`, not `unverified`.
4. A test with an empty listing and no problem still prints `not served; pick a served name`. It rules out keying on an empty listing alone.
5. `./dev.py test tests/unit/test_update_config_verb.py` has a test with an empty listing and a problem that asserts the verb returns exit code 1, not 0.
6. The `update-config` row in `clutch/docs/host-running.md` contains the word `unverified`. `./dev.py test tests/unit/test_host_running.py tests/unit/test_help.py` passes.

## Verification
```
./dev.py test tests/unit/test_update_config_verb.py tests/unit/test_host_running.py tests/unit/test_help.py
```

## Definition of rejected
The branch changes any adapter's `list_models`, prints `unverified` for a name missing from a non-empty listing, or adds a flag or option to `update-config`.

## Time budget
- expected: 20m
- stuck: 40m
