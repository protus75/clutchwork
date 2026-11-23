---
state: confirmed
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
- clutch/stages.py::check_meta
- clutch/meta.py::check
- clutch/meta.py::refresh
- clutch/meta.py::generated
- tests/unit/test_meta_fill.py
- tests/unit/test_check_meta_fill.py
- tests/integration/test_check_meta_fill_stage.py
- README.md

## Goal / Why
`metafill.fill` sends every non-malformed finding to the model, including `drifted` ones whose purpose is already valid, and then overwrites `purpose` (and a default `owner`) with the model's text. Check calls it on the changed files of every ticket, so a mechanical sweep (`disk-io-skip-per-file`) had 181 purpose lines rewritten for no reason, Review raised a scope snag, and the extra model calls cost money. After this ticket a `drifted` file with a non-empty purpose is refreshed mechanically, with only `verified` and `hash` updated, preserving its existing descriptive fields, with no model request for that path. Only `missing` and `empty_purpose` files go to the model. Restores the intended split: the model writes missing prose, `meta.refresh` handles drift. Neighbours `meta-path-selects-nothing`, `check-owns-meta-headers` and `implement-spec-meta-untouched-not-reported` cover other meta gaps and are not re-solved.

## Boundary contract
### Meta fill target selection
- disposition: extend
- owner: clutch/metafill.py
- consumers: `clutch meta fill` verb and Check's meta stage in clutch/stages.py
- observable change: findings with reason `drifted` (and no `missing` or `empty_purpose` finding for the same path) are no longer sent to the model. They are refreshed inside `metafill.fill` by updating only `verified` and `hash` with the existing parse, digest and compose functions, not through `meta.refresh`, and are reported in the returned `written` list when the file changes. Purpose, relates and owner of such files stay byte-identical.
- compatibility: `fill` signature and return shape `(written, rejected)` unchanged; `missing`, `empty_purpose` and `malformed` handling unchanged
- acceptance: a drifted file with a valid purpose goes through `fill` with the ask callable never invoked for it, and comes back with only `verified` and `hash` changed
- tests: new unit test file for drifted handling; existing fill tests updated only where they relied on drifted files reaching the model
- post-merge source of truth: clutch/metafill.py

## Scope in / Scope out
Scope in:
- In `clutch/metafill.py::fill`, use the existing `missing` and `empty_purpose` findings to select model targets. Refresh drifted-only paths mechanically by updating only `verified` and `hash` and preserve the parsed `purpose`, `owner` and `relates` fields exactly. Use the existing parse, digest and compose functions. Do not pass drifted-only paths through `meta.refresh`, default owner or relation generation.
- In `clutch/stages.py::check_meta`, refresh the remaining paths without applying the generic refresh to paths already refreshed mechanically by fill. Fenced tests must cover the real Check sequence and a mixed batch that includes both drift and a missing purpose. Keep malformed handling and empty-purpose failures.
- Update the existing mixed-batch expectation in `tests/unit/test_check_meta_fill.py`. Add `tests/unit/test_meta_fill_drifted.py`. Update the `meta_drift` row in `docs/how-clutch-works.md` to describe the actual Check behavior.
- In `tests/integration/test_check_meta_fill_stage.py`, seed the fixture with an empty purpose (`purpose=""`, an `empty_purpose` finding) instead of the drift-only `old purpose`, so Check still fills through FakeLLM and commits `clutch(work): meta`. Reword its `# purpose:` header line, which says it fills a drifted metadata purpose, to say it fills an empty purpose.
- In `README.md`, reword the `clutch meta fill` sentence so it says the model fills missing or empty blocks and drifted blocks are refreshed without the model.

Scope out: a new meta API, provider routing, new flags, and unrelated metadata normalization.

## Scope fence
- clutch/metafill.py
- clutch/stages.py
- tests/unit/test_meta_fill_drifted.py
- tests/unit/test_check_meta_fill.py
- tests/integration/test_check_meta_fill_stage.py
- docs/how-clutch-works.md
- README.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_meta_fill_drifted.py` proves a drifted-only file refreshes its hash and verified fields with no model request and preserves purpose, owner and relates, including an empty owner or a stale relation that generic refresh would normalize.
2. `./dev.py test tests/unit/test_meta_fill_drifted.py` covers a mixed batch. Only missing and empty-purpose paths reach the model, including a file with both an empty purpose and drift. Malformed files still produce a refusal finding.
3. `./dev.py test tests/unit/test_check_meta_fill.py` proves the Check sequence preserves the drifted file's existing descriptive fields through its final commit and still fills the separate missing header. It fails if the second refresh rewrites those fields.
4. `./dev.py test tests/integration/test_check_meta_fill_stage.py` proves Check fills an empty-purpose file through the scripted model and commits `clutch(work): meta`.
5. Review checks the `meta_drift` row in `docs/how-clutch-works.md` and the `clutch meta fill` sentence in `README.md` against Check and `metafill.fill`.

## Verification
```
./dev.py test tests/unit/test_meta_fill_drifted.py tests/unit/test_meta_fill.py tests/unit/test_check_meta_fill.py tests/unit/test_main_meta_fill.py tests/unit/test_meta_refresh.py tests/integration/test_check_meta_fill_stage.py
```

## Definition of rejected
A branch where a drifted file with a valid purpose still reaches the model or has its purpose or owner rewritten, or where a `missing` or `empty_purpose` file no longer gets model-written purpose.

## Time budget
- expected: 15m
- stuck: 30m