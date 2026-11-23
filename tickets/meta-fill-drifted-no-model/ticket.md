---
state: draft
source: box:suggestion
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/metafill.py::fill
- clutch/meta.py::check
- clutch/meta.py::refresh
- clutch/meta.py::generated
- tests/unit/test_meta_fill.py
- tests/unit/test_check_meta_fill.py

## Goal / Why
`metafill.fill` sends every non-malformed finding to the model, including `drifted` ones whose purpose is already valid, and then overwrites `purpose` (and a default `owner`) with the model's text. Check calls it on the changed files of every ticket, so a mechanical sweep (`disk-io-skip-per-file`) had 181 purpose lines rewritten for no reason, Review raised a scope snag, and the extra model calls cost money. After this ticket a `drifted` file with a non-empty purpose is refreshed mechanically, exactly as `meta.refresh` does (only `verified` and `hash` change), with no model request for that path. Only `missing` and `empty_purpose` files go to the model. Restores the intended split: the model writes missing prose, `meta.refresh` handles drift. Neighbours `meta-path-selects-nothing`, `check-owns-meta-headers` and `implement-spec-meta-untouched-not-reported` cover other meta gaps and are not re-solved.

## Boundary contract
### Meta fill target selection
- disposition: extend
- owner: clutch/metafill.py
- consumers: `clutch meta fill` verb and Check's meta stage in clutch/stages.py
- observable change: findings with reason `drifted` (and no `missing` or `empty_purpose` finding for the same path) are no longer sent to the model; they are refreshed through `meta.refresh` and reported in the returned `written` list when the file changes. Purpose, relates and owner of such files stay byte-identical.
- compatibility: `fill` signature and return shape `(written, rejected)` unchanged; `missing`, `empty_purpose` and `malformed` handling unchanged
- acceptance: a drifted file with a valid purpose goes through `fill` with the ask callable never invoked for it, and comes back with only `verified` and `hash` changed
- tests: new unit test file for drifted handling; existing fill tests updated only where they relied on drifted files reaching the model
- post-merge source of truth: clutch/metafill.py

## Scope in / Scope out
Scope in: in `fill`, compute model targets only from `missing` and `empty_purpose` findings; pass the remaining drifted-only paths to `meta.refresh` with the same config, root, fs, tracked, sha, and add changed paths to `written`. Update an existing test in `tests/unit/test_meta_fill.py`, `tests/unit/test_check_meta_fill.py` or `tests/unit/test_main_meta_fill.py` only if it fails because it expected a drifted file to be sent to the model. Scope out: `meta.py`, `stages.py`, the meta prompt spec, and docs; no new flags.

## Scope fence
- clutch/metafill.py
- tests/unit/test_meta_fill_drifted.py
- tests/unit/test_meta_fill.py
- tests/unit/test_check_meta_fill.py
- tests/unit/test_main_meta_fill.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_meta_fill_drifted.py` passes a test where a drifted file with a valid purpose and non-default owner goes through `fill`: the fake `ask` is called zero times for it, and purpose, relates and owner are byte-identical, not the model's text.
2. The same test asserts that file's `verified` and `hash` are updated to the current sha and body digest, so `meta.check` returns no finding for it afterward, and the path appears in `written`.
3. `./dev.py test tests/unit/test_meta_fill_drifted.py` passes a test where one batch holds a drifted file and a `missing` file: `ask` receives only the missing path, not the drifted one.
4. `./dev.py test tests/unit/test_meta_fill_drifted.py` passes a test where a file is both `drifted` and `empty_purpose`: it is sent to the model and its purpose is filled.
5. `./dev.py test tests/unit/test_meta_fill.py tests/unit/test_check_meta_fill.py tests/unit/test_main_meta_fill.py` passes.

## Verification
```
./dev.py test tests/unit/test_meta_fill_drifted.py tests/unit/test_meta_fill.py tests/unit/test_check_meta_fill.py tests/unit/test_main_meta_fill.py tests/unit/test_meta_refresh.py
```

## Definition of rejected
A branch where a drifted file with a valid purpose still reaches the model or has its purpose or owner rewritten, or where a `missing` or `empty_purpose` file no longer gets model-written purpose.

## Time budget
- expected: 15m
- stuck: 30m
