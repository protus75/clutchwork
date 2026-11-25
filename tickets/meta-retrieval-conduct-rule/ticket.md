---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
none

## Context
- clutch/hostfiles.py::CORE_TEMPLATE
- tests/unit/test_hostfiles_duckdb_rule.py
- tests/unit/test_hostfiles_docs_on_main.py
- tests/unit/test_hostfiles_supervisor_verdicts.py
- tests/integration/test_core_supervisor_verdicts.py
- clutch/docs/host-authoring.md#What each section is for

## Goal / Why
Any host that configures `meta.paths` gets `clutch:meta` headers (`purpose`, `relates`, `owner`, `verified`, `hash`) on its tracked docs, guides, specs, tests, and fixtures, plus `clutch context suggest <stem>` and `clutch meta check`, yet `CORE_TEMPLATE` in `clutch/hostfiles.py` gives agents no guidance on using them or leaving header maintenance to Check. Adding one concise conditional rule to `CORE_TEMPLATE` and refreshing the repo's rendered conduct files delivers the habit to every host via `clutch host core` (and follows "A rule has one of two homes" in `CLAUDE.md`).

## Boundary contract
### Managed core conduct template
- disposition: extend
- owner: clutch/hostfiles.py
- consumers: `clutch host core`, `CoreDriftGate`, `CLAUDE.md`, `AGENTS.md`, `hosts/fixture/CLAUDE.md`, and every host repo adopting clutch
- observable change: add one conditional `clutch:meta` retrieval rule under `## Engine conduct` in `CORE_TEMPLATE` while trimming non-normative wording in existing `CORE_TEMPLATE` lines so `len(CORE_TEMPLATE) <= 8192` remains satisfied; refresh `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md` to match the updated template.
- compatibility: `CORE_TEMPLATE` remains a single literal `bytes` assignment starting with `## Ticket authoring`, within the 8192-byte cap, preserving every existing rule, section heading, and test-pinned phrase; `classify_core` reports `current` for all three tracked conduct files.
- acceptance: the new rule appears once under `## Engine conduct`, `len(CORE_TEMPLATE) <= 8192`, all existing `CORE_TEMPLATE` assertions pass, and `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md` match `CORE_TEMPLATE`.
- tests: `tests/unit/test_hostfiles_meta_rule.py`, `tests/integration/test_hostfiles.py`, `tests/integration/test_core_supervisor_verdicts.py`, `tests/integration/test_fixture_host.py`
- post-merge source of truth: `clutch/hostfiles.py`

## Scope in / Scope out
Scope in:
- In `clutch/hostfiles.py`:
  - Add one concise bullet under `## Engine conduct` in `CORE_TEMPLATE` (rule home: `CORE_TEMPLATE`, because `clutch:meta`, `clutch meta check`, and `clutch context suggest` apply to every host that enables `meta.paths`): when a file carries a `clutch:meta` header, use `purpose`, `relates`, and `owner` as a routing hint (still read the owning file before editing or citing, check `clutch meta check` if staleness is suspected, and run `clutch context suggest <stem>` on drafts), and never hand-edit `clutch:meta` blocks (`clutch meta refresh` / Check owns them).
  - Because `CORE_TEMPLATE` is currently 8183 bytes against the 8192-byte cap, tighten non-normative `Why:` or redundant phrasing in existing `CORE_TEMPLATE` lines without removing any rule, obligation, HARD label, section heading, or test-pinned substring checked by `tests/integration/test_hostfiles.py`, `tests/unit/test_hostfiles_docs_on_main.py`, `tests/unit/test_hostfiles_supervisor_verdicts.py`, and `tests/unit/test_hostfiles_duckdb_rule.py`, so `len(CORE_TEMPLATE) <= 8192`.
- Refresh the managed `clutch:core` block in `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md` to match the updated `CORE_TEMPLATE` (using `clutch host core` / `clutch.hostfiles.render`, leaving all project content outside the managed block untouched).
- Add `tests/unit/test_hostfiles_meta_rule.py` checking that the `clutch:meta` rule appears exactly once under `## Engine conduct` in `CORE_TEMPLATE`, names `purpose`, `relates`, `owner`, `clutch context suggest`, and the no-hand-edit boundary, and that `len(CORE_TEMPLATE) <= 8192`.

Scope out:
- Do not change any project content outside the `<!-- clutch:core begin -->`..`<!-- clutch:core end -->` block in `CLAUDE.md`, `AGENTS.md`, or `hosts/fixture/CLAUDE.md`.
- Do not raise the 8192-byte cap in `tests/integration/test_hostfiles.py` or `tests/unit/test_hostfiles_*.py`, and do not change `clutch/meta.py`, `clutch/index.py`, or any prompt spec under `clutch/specs/`.

## Scope fence
- clutch/hostfiles.py
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/unit/test_hostfiles_meta_rule.py

## Acceptance criteria
1. `CORE_TEMPLATE` in `clutch/hostfiles.py` contains exactly one `clutch:meta` retrieval bullet under `## Engine conduct` naming `purpose`, `relates`, `owner`, `clutch context suggest`, and forbidding hand-edits to `clutch:meta` blocks, and `len(CORE_TEMPLATE) <= 8192` (not exceeding the shared cap); verified by `./dev.py test tests/unit/test_hostfiles_meta_rule.py`.
2. Every existing `CORE_TEMPLATE` invariant and pinned phrase still passes without altering the 8192-byte cap; verified by `./dev.py test tests/unit/test_hostfiles_docs_on_main.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/unit/test_hostfiles_duckdb_rule.py tests/integration/test_hostfiles.py`.
3. `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md` carry the refreshed `CORE_TEMPLATE` inside their managed block and report `classify_core(...).state == "current"` (not `drifted` or `refused`); verified by `./dev.py test tests/integration/test_core_supervisor_verdicts.py tests/integration/test_fixture_host.py`.

## Verification
```
./dev.py test tests/unit/test_hostfiles_meta_rule.py tests/unit/test_hostfiles_docs_on_main.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/unit/test_hostfiles_duckdb_rule.py tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py tests/integration/test_fixture_host.py
```

## Definition of rejected
`len(CORE_TEMPLATE) > 8192`, any dropped existing rule or pinned phrase in `CORE_TEMPLATE`, any edit outside the managed `clutch:core` block in `CLAUDE.md`, `AGENTS.md`, or `hosts/fixture/CLAUDE.md`, or any of those three files left `drifted` against `CORE_TEMPLATE`.

## Time budget
- expected: 10m
- stuck: 20m
