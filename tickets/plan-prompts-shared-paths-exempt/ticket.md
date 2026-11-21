---
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Context
- tests/integration/test_ask_plan_drain.py::prompts

## On-demand
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md

## Goal / Why
The Authoring rule in `plan-ticket-drain.md` and `plan-ticket-serve.md` says to author a row only when no confirmed, unmerged ticket fences a file the row will change, and otherwise to wait. The scheduler already treats paths in `scheduler.parallel.shared_paths` as non-overlapping (they waive the fence-overlap exclusion), so an operator following the prompt holds back rows the engine would run together. On 2026-11-21 `spools-scratch-dir` was held for `meta-fill-surface` because both fence `docs/how-clutch-works.md`, which cost parallel throughput. After this ticket both rendered prompts name the `shared_paths` exemption, so a row whose only fence overlap with a confirmed ticket is a shared path can be authored at once. The window size (3) and the wording tying it to `max_runs` are out of scope: that only restates reasoning and shows no harm.

## Boundary contract
### Plan-ticket prompt Authoring rule
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/plan-ticket-serve.md (rendered by `clutch prompt`)
- consumers: supervising agents running `clutch prompt plan-ticket-drain` or `clutch prompt plan-ticket-serve`
- observable change: the overlap sentence gains an exception for paths listed in `scheduler.parallel.shared_paths`; the existing phrase "confirmed, unmerged ticket" stays
- compatibility: all other prompt text is unchanged; existing phrase pins in the plan prompt tests still hold
- acceptance: both rendered prompts contain `shared_paths` in the overlap rule and still say to wait on any other overlapping fence
- tests: new tests/integration/test_ask_plan_shared_paths.py
- post-merge source of truth: the two prompt spec files

## Scope in / Scope out
Scope in: in the Authoring bullet that begins "Start before the first drain" (drain spec) and its counterpart in the serve spec, change only the sentence "Author a row only when no confirmed, unmerged ticket fences a file the row will change; otherwise wait for that ticket to merge." so it exempts a path listed in `scheduler.parallel.shared_paths` in config.yaml, which the scheduler already excludes from overlap. Add the new test file.
Scope out: the window of 3 and the "while a ticket is implemented" wording; any scheduler or config change; docs (no document describes this sentence).

## Scope fence
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- tests/integration/test_ask_plan_shared_paths.py

## Acceptance criteria
1. The rendered `plan-ticket-drain` prompt contains `shared_paths` in the overlap sentence, not only elsewhere; checked by `./dev.py test tests/integration/test_ask_plan_shared_paths.py`.
2. The rendered `plan-ticket-serve` prompt contains the same exemption, checked by `./dev.py test tests/integration/test_ask_plan_shared_paths.py`.
3. Both rendered prompts still contain "confirmed, unmerged ticket" and "otherwise wait for that ticket to merge", so the exemption does not replace the hold for non-shared paths; checked by `./dev.py test tests/integration/test_ask_plan_shared_paths.py`.
4. The existing plan prompt tests still pass, checked by `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/unit/test_ask_plan_drain.py tests/unit/test_ask_plan_serve.py`.

## Verification
```
./dev.py test tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/unit/test_ask_plan_drain.py tests/unit/test_ask_plan_serve.py
```

## Definition of rejected
A branch that edits the window size, the scheduler, config, or any file outside the fence, or that drops the hold for paths not in `shared_paths`.

## Time budget
- expected: 10m
- stuck: 20m
