---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
none

## Context
- clutch/hostfiles.py::CORE_TEMPLATE
- tests/integration/test_hostfiles.py

## Goal / Why
`CORE_TEMPLATE` tells every host's supervising session it "may not confirm or reject" and may not "rewrite a ticket the engine authored". `clutch/specs/ask/drain-loop.md` has the supervising agent loop run `confirm --yes` and `reject --yes` when a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation says so (decision 19 in `docs/roadmap.md`). One rule has two homes that disagree (box-000508 was declined; `driver-loop` merged without the change).

After this change the template allows a confirm or reject, and an edit to any ticket, when such a Recommendation names it. It drops "rewrite a ticket the engine authored" from the forbidden list, because every ticket is written by an AI agent and the distinction protects nothing. The template stays at or under its 8,192-byte limit (8,109 bytes today), and the managed blocks in `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` match it.

## Scope in / Scope out
Scope in:
- In `clutch/hostfiles.py::CORE_TEMPLATE`, rewrite the last bullet of the first section (the supervising-session rule). The session may confirm or reject, and edit a ticket, only as a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation names. It still may not retry a stem whose caps are spent, edit a running ticket, or change a ticket's goal or scope without such a Recommendation. The phrase "rewrite a ticket the engine authored" is removed.
- Pay for the added bytes by compressing one rule in `CORE_TEMPLATE` that has since gained its gate (per `CLAUDE.md` section A, "When a rule gains its gate, compress it to one line"). Keep every phrase that `tests/integration/test_hostfiles.py` pins.
- Refresh the managed blocks in `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` with `clutch core`. Never hand-edit them.
- In `tests/integration/test_hostfiles.py`, regenerate the pinned `GOLDEN` value (it is base64 of `render(b"")`, which embeds the full current `CORE_TEMPLATE`) by running the file's `__main__` regenerator, `uv run python -m tests.integration.test_hostfiles`, after the template change. Change no pinned phrase and no other line in that file.
- Rule home: this is a rule every host should follow, so it lives in `CORE_TEMPLATE` and reaches this repo only through `clutch core`.
- Add a new unit test file `tests/unit/test_hostfiles_supervisor_verdicts.py` that asserts on the in-memory `CORE_TEMPLATE` bytes only (no repo file read), and a new integration test file `tests/integration/test_core_supervisor_verdicts.py` that reads the three managed blocks from disk.

Scope out:
- No prompt spec and no other documentation changes.

## Scope fence
- clutch/hostfiles.py
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/integration/test_hostfiles.py
- tests/unit/test_hostfiles_supervisor_verdicts.py
- tests/integration/test_core_supervisor_verdicts.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_hostfiles_supervisor_verdicts.py` asserts, as bytes, that `clutch.hostfiles.CORE_TEMPLATE` contains neither `b"may not confirm or reject"` nor `b"rewrite a ticket the engine authored"`, and does contain `b"clutch prompt diagnose"` and `b"clutch prompt drafts"`. It fails if the old sentence is still present.
2. The same unit test asserts, as bytes, that the supervising-session rule contains `b"Recommendation"`, so a bare "may confirm or reject" with no condition does not pass.
3. The same unit test asserts `len(CORE_TEMPLATE) <= 8192` (CORE_TEMPLATE is a bytes literal, so no `.encode()`), and `./dev.py test tests/integration/test_hostfiles.py` still passes with all its pinned phrases and the regenerated `GOLDEN`.
4. `./dev.py test tests/integration/test_core_supervisor_verdicts.py` reads `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` and asserts each contains `CORE_TEMPLATE` byte for byte between the `clutch:core` markers. A stale managed block fails it.

## Verification
```
./dev.py test tests/unit/test_hostfiles_supervisor_verdicts.py tests/integration/test_core_supervisor_verdicts.py tests/integration/test_hostfiles.py
```

## Definition of rejected
The branch is thrown away if `CORE_TEMPLATE` exceeds 8,192 bytes, if a phrase pinned by `tests/integration/test_hostfiles.py` is dropped, if a managed block was hand-edited and differs from the template, or if the template still forbids a confirm or reject that a Recommendation names.

## Time budget
- expected: 20m
- stuck: 40m
