---
state: confirmed
source: box:roadmap_row
priority: P3
kind: feature
---

## Depends on
none

## Context
- clutch/config.py::Evidence
- clutch/config.py::Graphics
- clutch/config.py::Config
- clutch/docs/host-contract.md#Complete field inventory
- tests/unit/test_evidence_config.py
- docs/training-data-plan.md

## On-demand
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 57, section 1 of `docs/training-data-plan.md`. Today `Config` has no `training_data` block. After this ticket a config may carry `training_data: {enabled, exclude}` (default `enabled: false`, `exclude: []`), and existing configs load unchanged. The model owns a fixed always-excluded glob list (`.env*`, `*.pem`, `*.key`, `id_*`) that the host's `exclude` adds to and can never remove from (fail closed). The model also owns the refusal that later `training export` and `training eval` verbs call when training is off, with the paved road "set training_data.enabled: true; only attempts after that carry a diff". Why: the later tickets (`training-attempt-manifest`, `training-export`, `training-eval`) all need one switch, one exclusion list and one refusal, and none may invent its own.

## Boundary contract
### Config model
- disposition: extend
- owner: clutch/config.py (`Config`)
- consumers: every config loader; the host-contract field inventory test
- observable change: `Config` accepts an optional `training_data` block, default `TrainingData()`; unknown keys inside it are refused like every other strict model
- compatibility: configs without the key load unchanged and get the default
- acceptance: a config omitting `training_data` yields `enabled` false and empty `exclude`
- tests: tests/unit/test_training_config.py, tests/integration/test_host_contract.py
- post-merge source of truth: clutch/config.py

### TrainingData block
- disposition: create
- owner: clutch/config.py (`TrainingData`)
- consumers: `training export` and `training eval` (later tickets `training-export` and `training-eval`), plus the attempt manifest writer (`training-attempt-manifest`)
- observable change: `TrainingData.effective_exclude()` returns the fixed list followed by the host's extra globs without duplicates; `TrainingData.require_enabled()` raises `ValueError` carrying the paved road when `enabled` is false and returns `None` when true
- compatibility: new surface, no existing consumers
- acceptance: a host `exclude` never removes a fixed entry; refusal text names `training_data.enabled: true`
- tests: tests/unit/test_training_config.py
- post-merge source of truth: clutch/config.py
- closest existing: `Evidence` and `Graphics` in clutch/config.py
- earning reason: neither holds a switch, an exclusion list or a refusal; three planned production consumers (manifest writer, export, eval) must share one definition of the fixed list and the refusal rather than each carrying a copy

## Scope in / Scope out
Scope in:
- Add `TrainingData` (a `StrictModel`) to clutch/config.py with `enabled: bool = False` and `exclude: list[str] = []` (non-empty strings), the fixed glob tuple, `effective_exclude()` and `require_enabled()`; add `training_data: TrainingData = TrainingData()` to `Config`.
- docs/how-clutch-works.md: add one row for `training_data` to the section 11 config table (beside `evidence.max_gb`); change nothing else there.
- clutch/docs/host-contract.md: in the `config-fields` inventory add `training_data: {enabled: false, exclude: []}` to the `Config` defaults and a `TrainingData` entry (required none, defaults `{enabled: false, exclude: []}`); change nothing else there.
- New tests in tests/unit/test_training_config.py.

Scope out: the verbs `training export` and `training eval`, the attempt manifest, `clutch/training.py`, the host training guide, and any CLI or help change. Those are `training-attempt-manifest`, `training-export`, `training-eval` and `training-docs`, filed from the same plan.

## Scope fence
- clutch/config.py
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_training_config.py

## Acceptance criteria
1. `Config.model_fields["training_data"].default == TrainingData()` and `TrainingData().enabled is False` and `TrainingData().exclude == []`, checked by `./dev.py test tests/unit/test_training_config.py`; a result of `None` or a missing field fails.
2. `TrainingData(exclude=["data/customers/**"]).effective_exclude()` equals `[".env*", "*.pem", "*.key", "id_*", "data/customers/**"]`, and `TrainingData(exclude=[".env*"]).effective_exclude()` still lists `.env*` exactly once, checked by `./dev.py test tests/unit/test_training_config.py`.
3. `TrainingData().require_enabled()` raises `ValueError` whose message contains `training_data.enabled: true`, and `TrainingData(enabled=True).require_enabled()` returns `None` without raising, checked by `./dev.py test tests/unit/test_training_config.py`.
4. `TrainingData(unknown=1)` and `TrainingData(exclude=[""])` each raise `pydantic.ValidationError`, not silently load, checked by `./dev.py test tests/unit/test_training_config.py`.
5. The host-contract inventory lists `training_data` and `TrainingData` and matches `clutch/config.py` field for field, checked by `./dev.py test tests/integration/test_host_contract.py`.

## Verification
```
./dev.py test tests/unit/test_training_config.py tests/unit/test_evidence_config.py tests/integration/test_host_contract.py
```

## Definition of rejected
The branch is rejected if it adds a way to remove a fixed exclude entry, adds the export or eval verbs, a `training_data.dir` or retention knob, or a compatibility shim for configs, or edits a file outside the fence.

## Time budget
- expected: 15m
- stuck: 30m
