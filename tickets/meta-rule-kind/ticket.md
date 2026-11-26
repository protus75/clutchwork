---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/meta.py
- clutch/config.py::MetaKind
- clutch/config.py::MetaPath
- clutch/metafill.py::fill
- clutch/stages.py::check_meta
- tests/unit/test_meta_refresh.py
- tests/unit/test_check_meta_fill.py

## Goal / Why
Add `"rule"` (for AI rule files such as `CLAUDE.md`, `AGENTS.md`, and nested rule files) to the closed `clutch:meta` kind vocabulary, and enforce that a document cannot mix AI rules (`kind: rule`) and Spec/Contract (`kind: spec`) annotations against its configured `meta.paths` kind. This lets `clutch meta check`, `clutch meta fill`, and Check mechanically distinguish AI rule files from Specs/Contracts and reject cross-class mismatches.

## Boundary contract
### Meta kind vocabulary and check
- disposition: extend
- owner: clutch/meta.py
- consumers: clutch/config.py, clutch/metafill.py, clutch/stages.py, clutch/__main__.py
- observable change: add `"rule"` to `clutch/meta.py::KINDS` and `clutch/config.py::MetaKind`; `meta.check` emits `(path, "kind_mismatch")` when a file's block `kind` and its configured `meta.paths` `expected_kind` form `{"rule", "spec"}`; `metafill.fill` rejects `kind_mismatch` without calling `ask` or overwriting the block; `stages.check_meta` surfaces `kind_mismatch` as a `meta_drift` `Finding` with a paved road.
- compatibility: all existing `KINDS` (`doc`, `guide`, `spec`, `test`, `fixture`, `plan`) remain valid; non-`{"rule", "spec"}` kind pairs (such as `doc`/`plan`) are unaffected.
- acceptance: `kind: rule` parses, validates in `MetaPath`, and refreshes cleanly, while `rule`/`spec` mismatches produce `kind_mismatch` in `meta.check`, rejection in `metafill.fill`, and a `meta_drift` finding in `stages.check_meta`.
- tests: unit tests in `tests/unit/test_meta_rule_kind.py` using in-memory fakes only.
- post-merge source of truth: clutch/meta.py, clutch/config.py, clutch/metafill.py, clutch/stages.py

## Scope in / Scope out
Scope in:
- `clutch/config.py`: add `"rule"` to `MetaKind`.
- `clutch/meta.py`: add `"rule"` to `KINDS`; in `check()`, unpack `(path, expected_kind)` from `_files(...)` and append `(path, "kind_mismatch")` when `fields is not None` and `{fields["kind"], expected_kind} == {"rule", "spec"}`.
- `clutch/metafill.py`: in `fill()`, include `"kind_mismatch"` alongside `"malformed"` in `rejected` so mismatched files are rejected without calling `ask` or overwriting their kind.
- `clutch/stages.py`: in `check_meta()`, add `"kind_mismatch"` to `roads` with a paved road explaining that a document cannot mix `kind: rule` and `kind: spec` (align its `kind` or move it under the matching `meta.paths` root), and emit a `meta_drift` `Finding` when `(path, "kind_mismatch") in after`.
- `tests/unit/test_meta_rule_kind.py`: new unit test module covering `MetaKind`/`KINDS` parity, `MetaPath(root=..., kind="rule")`, `meta.parse`/`meta.refresh` with `kind: rule`, `meta.check` emitting `kind_mismatch` for both `rule`-under-`spec` and `spec`-under-`rule` (and not for matching pairs or non-`{rule, spec}` pairs), `metafill.fill` rejecting `kind_mismatch` without calling `ask`, and `stages.check_meta` returning a `meta_drift` finding for `kind_mismatch`.

Scope out:
- Do not change `clutch.toml` or annotate root agent rule files in this ticket.
- Do not change `meta.paths` directory-prefix matching semantics (`_files` exact-file matching is out of scope).
- Do not edit existing test files or hot test modules.

## Scope fence
- clutch/meta.py
- clutch/config.py
- clutch/metafill.py
- clutch/stages.py
- tests/unit/test_meta_rule_kind.py

## Acceptance criteria
1. `"rule"` is in `clutch.meta.KINDS` and `clutch.meta.KINDS == set(typing.get_args(clutch.config.MetaKind))` (ruling out drift between `meta.py` and `config.py`), verified by `./dev.py test tests/unit/test_meta_rule_kind.py`.
2. `MetaPath(root="rules/", kind="rule")` validates and `meta.parse` / `meta.refresh` accept and generate `kind: rule` blocks (ruling out `ValidationError` or `Malformed` on `kind: rule`), verified by `./dev.py test tests/unit/test_meta_rule_kind.py`.
3. `meta.check` returns `(path, "kind_mismatch")` when a file under a `kind="rule"` root carries `kind: spec` and when a file under a `kind="spec"` root carries `kind: rule`, and does not return `kind_mismatch` for matching `rule`/`rule`, `spec`/`spec`, or non-`{"rule", "spec"}` pairs (ruling out silent acceptance of mixed rule/spec annotations or false positives on existing kinds), verified by `./dev.py test tests/unit/test_meta_rule_kind.py`.
4. `metafill.fill` rejects `kind_mismatch` files in its `rejected` return list without invoking `ask` or modifying the file (ruling out silent model overwrite of a mismatched `kind`), verified by `./dev.py test tests/unit/test_meta_rule_kind.py`.
5. `stages.check_meta` returns a `meta_drift` `Finding` with message `f"{path}: kind_mismatch"` and a non-empty `paved_road` when `meta.check` reports `kind_mismatch` (ruling out `check_meta` dropping `kind_mismatch` findings), verified by `./dev.py test tests/unit/test_meta_rule_kind.py`.
6. Existing metadata unit tests pass unchanged under `./dev.py test tests/unit/test_meta_config.py tests/unit/test_meta_refresh.py tests/unit/test_meta_fill_drifted.py tests/unit/test_check_meta_fill.py tests/unit/test_meta_drift_check.py`.

## Verification
```
./dev.py test tests/unit/test_meta_rule_kind.py tests/unit/test_meta_config.py tests/unit/test_meta_refresh.py tests/unit/test_meta_fill_drifted.py tests/unit/test_check_meta_fill.py tests/unit/test_meta_drift_check.py
```

## Definition of rejected
- Any change outside the scope fence.
- `meta.KINDS` and `config.MetaKind` disagree on the allowed kinds.
- `meta.check` silently accepts `kind: spec` under a `kind: rule` root (or vice versa), or falsely flags non-`{"rule", "spec"}` pairs.
- `metafill.fill` or `meta.refresh` silently rewrites a mismatched `rule`/`spec` kind instead of reporting/rejecting it.
- Unit tests touch real repo files, processes, or network instead of in-memory fakes / `tmp_path`.

## Time budget
- expected: 10m
- stuck: 20m
