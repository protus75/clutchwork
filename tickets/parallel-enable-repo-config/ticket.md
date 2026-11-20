---
state: draft
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- config.yaml
- clutch/config.py::Parallel
- clutch/doctor.py

## Goal / Why
The 0.4.0 ship clause needs ten parallel serve merges, but this repo's `config.yaml` sets no `scheduler.parallel`, so `Scheduler.dispatch_next` stays single-flight and `roadmap merged --parallel` can never pass. After this ticket `config.yaml` sets `scheduler.parallel.enabled: true`, `max_runs: 2`, and `shared_paths: [docs/how-clutch-works.md]`. It also raises the implement-route provider's `limits.concurrency` to 2, so the `parallel` row in `clutch/doctor.py` (max_runs exceeds `limits.concurrency`) stays clear.

## Boundary contract
### Repo instance config
- disposition: extend
- owner: config.yaml (values) under the existing schema owned by clutch/config.py (`Parallel`, `Scheduler`)
- consumers: `load_config`, the scheduler's parallel admission, and the `clutch/doctor.py` parallel check
- observable change: `scheduler.parallel.enabled` becomes true with `max_runs` 2 and `shared_paths` listing `docs/how-clutch-works.md`; the codex provider's `limits.concurrency` rises from 1 to 2
- compatibility: no schema change; all existing keys keep their meaning, and the config still validates under the strict models
- acceptance: the repo `config.yaml` loads, reports parallel enabled with the stated values, and `max_runs` does not exceed the implement-route provider's concurrency
- tests: new integration test loading the repo `config.yaml` through `load_config`
- post-merge source of truth: config.yaml

## Scope in / Scope out
Scope in: add a `scheduler:` block to `config.yaml` with `parallel: {enabled: true, max_runs: 2}` and `shared_paths` set to the single path named in Goal / Why, and change codex `limits: {concurrency: 1, ...}` to `concurrency: 2`, because routing sends every implement tier to codex and the doctor check reads that provider. Add a new test file `tests/integration/test_repo_config_parallel.py`.
Scope out: any change to scheduler, doctor, or config schema code; claude's `limits.concurrency`; documentation (the existing engine description already covers `scheduler.parallel`); the `roadmap merged --parallel` run itself.

## Scope fence
- config.yaml
- tests/integration/test_repo_config_parallel.py

## Acceptance criteria
1. Loading the repo `config.yaml` with `load_config` gives `scheduler.parallel.enabled` true, `max_runs` 2, and `shared_paths == ["docs/how-clutch-works.md"]`, not the defaults (false, 2, `[]`); checked by `./dev.py test tests/integration/test_repo_config_parallel.py`.
2. For the implement route at the default routing tier, the first candidate's provider has `limits.concurrency >= scheduler.parallel.max_runs`, so the doctor condition `max_runs > concurrency` is false; checked by `./dev.py test tests/integration/test_repo_config_parallel.py`.
3. The existing config and doctor tests still pass; checked by `./dev.py test tests/integration/test_config.py tests/integration/test_doctor.py tests/unit/test_parallel_config.py`.

## Verification
```
./dev.py test tests/integration/test_repo_config_parallel.py tests/integration/test_config.py tests/integration/test_doctor.py tests/unit/test_parallel_config.py
```

## Definition of rejected
The branch changes scheduler, doctor, or config schema code, enables parallel without raising the implement provider's concurrency, or leaves `shared_paths` without `docs/how-clutch-works.md`.

## Time budget
- expected: 10m
- stuck: 20m
