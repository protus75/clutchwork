---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- clutch/hostfiles.py::CORE_TEMPLATE
- tests/integration/test_hostfiles.py::test_core_template_is_host_neutral
- tests/unit/test_hostfiles_supervisor_verdicts.py
- tests/integration/test_core_supervisor_verdicts.py

## Goal / Why
Every host's managed `clutch:core` block carries one rule: embedded databases use DuckDB, never SQLite. Code never opens, reads, or writes a SQLite file. A third-party tool's internal SQLite file, such as coverage.py's `.coverage`, is never read by project code; read the tool's non-SQLite report or rerun the tool instead.

Why: the owner decided on 2026-11-19 that DuckDB is the only embedded database across every host. Snapshot work already targets DuckDB (`snapshot-duckdb-under-one-second`). On 2026-11-19 a chat session proposed reading coverage.py's `.coverage` SQLite file to replace a 926 MB contexts JSON. Nothing written told agents not to reach for SQLite.

Rule home: every host, so the rule lives in `CORE_TEMPLATE` and reaches this repo only through `clutch host core`. A grep of `clutch/` and `eval/` for `sqlite` (case-insensitive) on main finds no use, so no code migration is in scope.

## Boundary contract
### Managed core conduct block
- disposition: extend
- owner: clutch/hostfiles.py
- consumers: every host's routed conduct files (`CLAUDE.md`, `AGENTS.md`) through `clutch host core`, the `core_drift` check gate, and `hosts/fixture/CLAUDE.md`
- observable change: `CORE_TEMPLATE` gains one `## Engine conduct` bullet naming DuckDB as the only embedded database; an existing bullet is shortened to keep the template within 8192 bytes
- compatibility: hosts with a stale block get `core_drift` "drifted" with the existing paved road `run clutch host core`; marker format and render function are unchanged
- acceptance: the new bullet is present as bytes, the template stays at most 8192 bytes, and all three managed blocks match the template byte for byte
- tests: tests/unit/test_hostfiles_duckdb_rule.py, tests/integration/test_hostfiles.py, tests/integration/test_core_supervisor_verdicts.py
- post-merge source of truth: clutch/hostfiles.py::CORE_TEMPLATE

## Scope in / Scope out
Scope in:
- In `clutch/hostfiles.py::CORE_TEMPLATE`, add one bullet at the end of `## Engine conduct` with this meaning: "Embedded databases use DuckDB, never SQLite; code never opens, reads, or writes a SQLite file, including a tool's internal one such as coverage.py's `.coverage`. Why: one embedded engine across every host (owner decision 2026-11-19)." The bullet contains the bytes `DuckDB, never SQLite`.
- `CORE_TEMPLATE` is 8186 bytes on main against the 8192 cap. Pay for the new bullet by shortening one or more existing bullets with no change in meaning. Keep every phrase pinned by `tests/integration/test_hostfiles.py::test_core_template_is_host_neutral` and `tests/unit/test_hostfiles_supervisor_verdicts.py`. Do not add any term that `test_core_template_is_host_neutral` forbids.
- Refresh the managed blocks in `CLAUDE.md` and `AGENTS.md` by running `clutch host core` at the repo root. Refresh `hosts/fixture/CLAUDE.md` by running `clutch host core` with `hosts/fixture` as the working directory. Never hand-edit a managed block.
- In `tests/integration/test_hostfiles.py`, regenerate the pinned `GOLDEN` value with the file's own `__main__` regenerator (`uv run python -m tests.integration.test_hostfiles`) after the template change. Change no other line in that file.
- Add a new unit test file `tests/unit/test_hostfiles_duckdb_rule.py` that asserts on the in-memory `CORE_TEMPLATE` bytes only and reads no repo file.

Scope out:
- No code change outside `CORE_TEMPLATE`; no SQLite-to-DuckDB migration (none exists in `clutch/` or `eval/`).
- The unit coverage gate's use of coverage contexts is a separate ticket.
- No change to `tests/integration/test_core_supervisor_verdicts.py`; it already checks all three managed blocks against the template.

## Scope fence
- clutch/hostfiles.py
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/integration/test_hostfiles.py
- tests/unit/test_hostfiles_duckdb_rule.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_hostfiles_duckdb_rule.py` asserts that exactly one line of `clutch.hostfiles.CORE_TEMPLATE` contains `b"DuckDB, never SQLite"`, and that this line comes after `b"## Engine conduct"`. It fails on main, where the bytes are absent, and fails if the bullet is placed in `## Chat session conduct`, which ticket agents skip.
2. The same unit test asserts `len(CORE_TEMPLATE) <= 8192`; a template that adds the bullet without compressing fails.
3. `./dev.py test tests/integration/test_hostfiles.py tests/unit/test_hostfiles_supervisor_verdicts.py` passes with every pinned phrase unchanged and the regenerated `GOLDEN`; a stale `GOLDEN` fails it.
4. `./dev.py test tests/integration/test_core_supervisor_verdicts.py` passes: `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md` each carry `CORE_TEMPLATE` byte for byte between the `clutch:core` markers. Any unrefreshed block fails it.

## Verification
```
./dev.py test tests/unit/test_hostfiles_duckdb_rule.py tests/unit/test_hostfiles_supervisor_verdicts.py tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py
```

## Definition of rejected
- A managed block in `CLAUDE.md`, `AGENTS.md`, or `hosts/fixture/CLAUDE.md` is hand-edited instead of rendered by `clutch host core`.
- A pinned phrase in `test_hostfiles.py` or `test_hostfiles_supervisor_verdicts.py` is changed or removed to make room.
- The 8192-byte cap in any test is raised.
- The rule is written only into this repo's files outside the managed block.

## Time budget
- expected: 15m
- stuck: 30m
