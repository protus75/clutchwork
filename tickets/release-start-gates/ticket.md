---
state: confirmed
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/roadmap.py::choose
- clutch/roadmap.py::gates
- clutch/roadmap.py::run_gate
- clutch/roadmap.py::status
- clutch/roadmap.py::author_ahead
- docs/roadmap.md#1. Release plan
- docs/how-clutch-works.md#7.5 Roadmap driver

## Goal / Why
Section 1 of `docs/roadmap.md` has a "Gate to start" column, but no command checks it and `clutch/roadmap.py::choose` never reads it (declined-box-000518; its reopen condition, the parser and gate blocks, has merged). After this change each release heading may carry a fenced `start` block, written under the same rules as the `gate` block: one argv command per line, run from the checkout root, passing when every command exits 0. The driver readies a release's rows only while its start block passes, and `clutch roadmap status` reports a failing start block as a wait on each affected row. A release with no `start` block starts unconditionally. A start clause that no merged verb can check is named in section 1 as unchecked, so the column states which clauses are enforced.

## Scope in / Scope out
In:
- `clutch/roadmap.py::gates` gains the signature `gates(text, fence="gate")`, so one parser serves both blocks. The default keeps every existing one-argument call returning `gate` blocks, and the refusal texts for `gate` stay byte-identical; a refusal for `start` names `start`.
- A new function `run_start(checkout, release)` in `clutch/roadmap.py` runs a release's start block through the same exec seam and child env as `run_gate`. It returns `(passed, lines)` with the failing command's line, and it journals nothing: a start check is a query, not a `roadmap_gate` signal. A command that times out, is not found, or exits non-zero fails the block. A release with no start block passes.
- `choose` gains one keyword parameter, `held: dict[str, str]`, defaulting to empty. It maps a release name to why that release's start block fails. A row that would become ready, and whose release is in `held`, becomes a `Wait` with reason `start gate of <release> fails: <failing command>` and road `make the release's start block pass`. Linked, open, and struck rows are unchanged. With the default, `choose` returns what it returns today.
- `author_ahead` and `status` run every release's start block that has unfinished rows and pass the failures as `held`. `merged` and `acceptance` keep calling `choose` without `held`.
- `docs/roadmap.md`: section 1 names `start` blocks (states which clauses of the "Gate to start" column a block checks and which are marked unchecked); the paragraph under section 8's table description gains the `start` block rule; add a `start` block under the 0.5.0 heading with `uv run clutch roadmap merged closed-sets-single-owner active-slot-single-owner merge-admission-single-owner`, the one start clause a merged verb can check. Every other non-`none` start clause is marked "(unchecked)" in the section 1 table. Update only those places; do not touch any row or `gate` block.
- `docs/how-clutch-works.md`: update section 7.5 (Roadmap driver) to say the driver and `roadmap status` read `start` blocks, and the `roadmap gate` table row only if it describes the gate block as the sole fenced block.
Out: a `start` journal signal; a new verb; changing `ship`, `run_gate`, or `merged`; rewriting rows in `docs/roadmap.md`; any change to the driver loop order; edits to `tests/unit/test_roadmap_gate.py` or `tests/integration/test_roadmap_gate.py`.

## Scope fence
- clutch/roadmap.py
- docs/roadmap.md
- docs/how-clutch-works.md
- tests/unit/test_roadmap_start_gates.py
- tests/integration/test_roadmap_start_gates.py

## Acceptance criteria
1. `gates(text, "start")` on a document with a `start` block under `### 0.5.0` returns that release's argv tuples, and `gates(text, "gate")` on the same text returns only the `gate` block, not the `start` block; asserted in `./dev.py test tests/unit/test_roadmap_start_gates.py`. A `start` block with no release heading or an empty block raises `Refusal`, not an empty result.
2. `choose(rows, states=..., files=..., held={"0.5.0": "x"})` returns a row of release 0.5.0 in `waits` with reason `start gate of 0.5.0 fails: x` and not in `ready`; the same call with no `held` returns that row in `ready`, not in `waits`; asserted in `tests/unit/test_roadmap_start_gates.py`.
3. `run_start` with a fake exec seam returns `passed` False for a nonzero exit, a timeout, and a missing executable, returns True for all exits 0, and True for a release with no start block; in each case the journal holds no `roadmap_gate` signal, not one; asserted in `tests/unit/test_roadmap_start_gates.py`.
4. `status` on a repo whose current release has a failing start block prints `waits: row <n> <stem>: start gate of <release> fails:` for a ready row and `next: none`, not that row's stem; asserted in `tests/integration/test_roadmap_start_gates.py`.
5. `author_ahead` with a failing start block files no `roadmap_row` message for that release's rows, and files one once the block passes; asserted in `tests/integration/test_roadmap_start_gates.py`.
6. `docs/roadmap.md` parses with `gates(text, "start")` and returns exactly one release (`0.5.0`), and `gates(text, "gate")` returns the same releases as before; asserted in `tests/integration/test_roadmap_start_gates.py`.
7. `./dev.py test tests/unit/test_roadmap_gate.py tests/integration/test_roadmap_gate.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_table.py tests/unit/test_roadmap_stuck_rows.py` exits 0 with no edits to those files; the one-argument calls `roadmap.gates(text)` in the first two still return `gate` blocks, not `start` blocks.

## Verification
```
./dev.py test tests/unit/test_roadmap_start_gates.py tests/integration/test_roadmap_start_gates.py
./dev.py test tests/unit/test_roadmap_gate.py tests/integration/test_roadmap_gate.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_table.py tests/unit/test_roadmap_stuck_rows.py
```

## Definition of rejected
A start block that is parsed but never read by `choose`, `status`, or `author_ahead`; a `start` check that journals a `roadmap_gate` signal; a release with no start block that waits; a second parser for the `start` fence instead of the parameterized `gates`; or an edit to any row or `gate` block in `docs/roadmap.md`.

## Time budget
- expected: 30m
- stuck: 60m
