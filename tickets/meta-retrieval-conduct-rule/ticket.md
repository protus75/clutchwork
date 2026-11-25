---
state: draft
source: human
priority: P2
kind: chore
---

## Depends on
none

## Context
- CLAUDE.md#A. Engine conduct
- AGENTS.md
- clutch/docs/host-authoring.md#What each section is for
- docs/annotations-index-plan.md#1. The block

## Goal / Why
Tracked docs, guides, specs, tests, and fixtures carry `clutch:meta` headers (`purpose`, `relates`, `owner`, `verified`, `hash`), and `clutch context suggest <stem>` queries the project index built from them, but neither `CLAUDE.md` nor `AGENTS.md` tells chat or coding agents how to use them or warns them not to hand-edit the headers. Adding one concise rule in both repo conduct files (outside the managed `clutch:core` block) gives every CLI agent a consistent retrieval habit without expanding `CORE_TEMPLATE`.

## Boundary contract
none
- reason: Documentation-only agent conduct rule in `CLAUDE.md` and `AGENTS.md` outside the managed `clutch:core` block; no code, CLI, schema, or `CORE_TEMPLATE` boundary changes.

## Scope in / Scope out
Scope in:
- Add one behavioral rule (**Use `clutch:meta` headers as routing hints.**) under `## A. Engine conduct` in `CLAUDE.md` and the matching rule under `## Engine conduct` in `AGENTS.md`, outside the `<!-- clutch:core begin -->` / `<!-- clutch:core end -->` managed block.
- State the rule's home explicitly in the `Why:` line: this repo's `CLAUDE.md` and `AGENTS.md` (not `CORE_TEMPLATE` in `clutch/hostfiles.py`, keeping the shared template budget unchanged).
- Cover four concrete habits in the rule:
  1. Triage docs, guides, specs, tests, and fixtures by checking their `clutch:meta` header (`purpose`, `relates`, `owner`, `verified`) before reading whole files; treat the header as a routing hint, never a substitute for reading the owning artifact before editing or citing.
  2. Use `relates:` to locate coupled modules, docs, and tests; check for empty `purpose` or run `clutch meta check <path>` if staleness is suspected.
  3. Run `clutch context suggest <stem>` after drafting `## Scope fence` to pull section selectors and co-changed files.
  4. Never hand-edit `clutch:meta` blocks (`clutch meta refresh` and Check own them).
- Add `tests/integration/test_meta_retrieval_rule.py` reading `CLAUDE.md` and `AGENTS.md` via a `Path(__file__)` anchor to verify both files carry the rule outside the managed `clutch:core` block and remain `current` under `clutch.hostfiles.classify_core`.

Scope out:
- Do not modify `clutch/hostfiles.py` (`CORE_TEMPLATE`), the managed `<!-- clutch:core begin -->`..`<!-- clutch:core end -->` block, `clutch/meta.py`, `clutch/index.py`, or any prompt spec under `clutch/specs/`.

## Scope fence
- CLAUDE.md
- AGENTS.md
- tests/integration/test_meta_retrieval_rule.py

## Acceptance criteria
1. `CLAUDE.md` (under `## A. Engine conduct`, outside the `clutch:core` managed block) and `AGENTS.md` (under `## Engine conduct`, outside the `clutch:core` managed block) both include the `clutch:meta` retrieval rule naming `purpose`, `relates`, `owner`, `clutch context suggest`, and the prohibition on hand-editing `clutch:meta` blocks, failing if either file omits the rule or places it inside the managed block; verified by `./dev.py test tests/integration/test_meta_retrieval_rule.py`.
2. `clutch.hostfiles.classify_core` reports `state == "current"` (not `drifted` or `corrupt`) for both `CLAUDE.md` and `AGENTS.md`; verified by `./dev.py test tests/integration/test_meta_retrieval_rule.py tests/integration/test_hostfiles.py`.

## Verification
```
./dev.py test tests/integration/test_meta_retrieval_rule.py tests/integration/test_hostfiles.py
```

## Definition of rejected
Any edit inside the `<!-- clutch:core begin -->`..`<!-- clutch:core end -->` managed block, any edit to `clutch/hostfiles.py`, or updating only one of `CLAUDE.md` or `AGENTS.md`.

## Time budget
- expected: 5m
- stuck: 10m
