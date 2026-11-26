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
- tests/unit/test_hostfiles_meta_rule.py
- tests/unit/test_hostfiles_duckdb_rule.py
- tests/unit/test_hostfiles_docs_on_main.py
- tests/unit/test_hostfiles_supervisor_verdicts.py
- tests/integration/test_core_supervisor_verdicts.py
- clutch/docs/host-authoring.md#What each section is for

## Goal / Why
The `Own open threads` / `Still open:` rule under `## Chat session conduct` in `CORE_TEMPLATE` (`clutch/hostfiles.py`) tells interactive chat sessions to end each reply with a `Still open:` list, but does not require numbering items, writing in plain English instead of CS/AI jargon or terse prose, or evaluating options when an open item is a question. Updating that rule in `CORE_TEMPLATE` (the canonical home for every-host rules per "A rule has one of two homes" in `CLAUDE.md`) and refreshing the repo's rendered conduct files delivers consistent, readable, decision-ready open-thread tracking to every host via `clutch host core`.

## Boundary contract
### Managed core conduct template
- disposition: extend
- owner: clutch/hostfiles.py
- consumers: `clutch host core`, `CoreDriftGate`, `CLAUDE.md`, `AGENTS.md`, `hosts/fixture/CLAUDE.md`, and every host repo adopting clutch
- observable change: update the `Own open threads` / `Still open:` bullet under `## Chat session conduct` in `CORE_TEMPLATE` so every open item is numbered, explained in plain English (not CS/AI jargon or terse prose), and—when the item is a question with identified options—rates the options on need, ease of maintenance, and gold plating before making a recommendation; trim non-normative wording in existing `CORE_TEMPLATE` lines as needed so `len(CORE_TEMPLATE) <= 8192` remains satisfied; refresh `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md` to match the updated template.
- compatibility: `CORE_TEMPLATE` remains a single literal `bytes` assignment starting with `## Ticket authoring`, within the 8192-byte cap, preserving every existing rule, section heading, and test-pinned phrase; `classify_core` reports `current` for all three tracked conduct files.
- acceptance: the updated open-threads rule appears once under `## Chat session conduct` with all three requirements, `len(CORE_TEMPLATE) <= 8192`, all existing `CORE_TEMPLATE` assertions pass, and `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md` match `CORE_TEMPLATE`.
- tests: `tests/unit/test_hostfiles_open_threads_rule.py`, `tests/unit/test_hostfiles_meta_rule.py`, `tests/unit/test_hostfiles_docs_on_main.py`, `tests/unit/test_hostfiles_supervisor_verdicts.py`, `tests/unit/test_hostfiles_duckdb_rule.py`, `tests/integration/test_hostfiles.py`, `tests/integration/test_core_supervisor_verdicts.py`, `tests/integration/test_fixture_host.py`
- post-merge source of truth: `clutch/hostfiles.py`

## Scope in / Scope out
Scope in:
- In `clutch/hostfiles.py`:
  - Update the `- HARD: Own open threads ...` bullet under `## Chat session conduct` in `CORE_TEMPLATE` (rule home: `CORE_TEMPLATE`, because chat open-thread tracking applies to every host) to require:
    1. Number all items in the `Still open:` list.
    2. Explain each item in plain English, not CS/AI jargon or terse prose.
    3. When an item is a question with identified options, rate the options on need, ease of maintenance, and gold plating, then make a recommendation.
  - Because `CORE_TEMPLATE` is currently 8145 bytes against the 8192-byte cap, tighten non-normative `Why:` clauses or redundant phrasing in existing `CORE_TEMPLATE` lines without removing any rule, obligation, HARD label, section heading, or test-pinned substring checked by `tests/integration/test_hostfiles.py`, `tests/unit/test_hostfiles_docs_on_main.py`, `tests/unit/test_hostfiles_supervisor_verdicts.py`, `tests/unit/test_hostfiles_duckdb_rule.py`, and `tests/unit/test_hostfiles_meta_rule.py`, so `len(CORE_TEMPLATE) <= 8192`.
- Refresh the managed `clutch:core` block in `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md` to match the updated `CORE_TEMPLATE` (using `clutch host core` / `clutch.hostfiles.render`, leaving all project content outside the managed block untouched).
- Add `tests/unit/test_hostfiles_open_threads_rule.py` checking that the `Still open:` / open-threads rule appears exactly once under `## Chat session conduct` in `CORE_TEMPLATE`, requires numbering all items, plain English (not CS/AI jargon or terse prose), and rating options on need, ease of maintenance, and gold plating with a recommendation, and that `len(CORE_TEMPLATE) <= 8192`.

Scope out:
- Do not change any project content outside the `<!-- clutch:core begin -->`..`<!-- clutch:core end -->` block in `CLAUDE.md`, `AGENTS.md`, or `hosts/fixture/CLAUDE.md`.
- Do not raise the 8192-byte cap in `tests/integration/test_hostfiles.py` or `tests/unit/test_hostfiles_*.py`, and do not change any prompt spec under `clutch/specs/`.

## Scope fence
- clutch/hostfiles.py
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/unit/test_hostfiles_open_threads_rule.py

## Acceptance criteria
1. `CORE_TEMPLATE` in `clutch/hostfiles.py` contains exactly one `Own open threads` / `Still open:` bullet under `## Chat session conduct` (not duplicated or moved to another section) that requires numbering all items, explaining in plain English without CS/AI jargon or terse prose, and for questions with identified options rating options on need, ease of maintenance, and gold plating and making a recommendation, while keeping `len(CORE_TEMPLATE) <= 8192` (not exceeding the shared cap); verified by `./dev.py test tests/unit/test_hostfiles_open_threads_rule.py`.
2. Every existing `CORE_TEMPLATE` invariant and pinned phrase still passes without altering the 8192-byte cap; verified by `./dev.py test tests/unit/test_hostfiles_meta_rule.py tests/unit/test_hostfiles_docs_on_main.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/unit/test_hostfiles_duckdb_rule.py tests/integration/test_hostfiles.py`.
3. `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md` carry the refreshed `CORE_TEMPLATE` inside their managed block and report `classify_core(...).state == "current"` (not `drifted` or `refused`); verified by `./dev.py test tests/integration/test_core_supervisor_verdicts.py tests/integration/test_fixture_host.py`.

## Verification
```
./dev.py test tests/unit/test_hostfiles_open_threads_rule.py tests/unit/test_hostfiles_meta_rule.py tests/unit/test_hostfiles_docs_on_main.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/unit/test_hostfiles_duckdb_rule.py tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py tests/integration/test_fixture_host.py
```

## Definition of rejected
`len(CORE_TEMPLATE) > 8192`, any dropped existing rule or pinned phrase in `CORE_TEMPLATE`, any edit outside the managed `clutch:core` block in `CLAUDE.md`, `AGENTS.md`, or `hosts/fixture/CLAUDE.md`, or any of those three files left `drifted` against `CORE_TEMPLATE`.

## Time budget
- expected: 10m
- stuck: 20m
