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
- clutch/roadmap.py::run_gate
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks

## Goal / Why
Every release gate block in `docs/roadmap.md` (0.3.0 through 0.7.0) lists `./dev.py test` first. `run_gate` runs a block's commands in order and stops at the first failure. While a release still has unmerged rows, which is the usual state between settles, the driver pays for a full suite run of about 80 s before the cheap `uv run clutch roadmap merged ...` check fails. The driver does this after every settle in drain and serve. After this change each block lists its `roadmap merged` commands first and `./dev.py test` last. A release with unmerged rows then fails at the `roadmap merged` command within seconds and never runs `./dev.py test`. A release whose rows are all merged still runs the same commands, so the gate's pass condition is unchanged.

## Scope in / Scope out
Scope in:
- In `docs/roadmap.md`, edit only the five fenced `gate` blocks. In each, move the `./dev.py test` line to the end and keep the relative order of the other lines. The 0.3.0 block keeps its three `roadmap merged` lines in their current order.
- In `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks`, change the expected tuples to the new order: `./dev.py test` last for the first release and for every other release.

Scope out: `clutch/roadmap.py` and every other test. `run_gate` keeps stopping at the first failure. The commands in each block stay the same and only their order changes. No new gate rule, lint or knob.

## Scope fence
- docs/roadmap.md
- tests/integration/test_roadmap_gate.py

## Acceptance criteria
1. `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks` passes. For the first release it expects the three `roadmap merged` commands in their current order followed by `("./dev.py", "test")`. For every other release it expects `("uv", "run", "clutch", "roadmap", "merged", "--release", release)` followed by `("./dev.py", "test")`. A block with `./dev.py test` first fails the test.
2. In every block parsed from `docs/roadmap.md` by `roadmap.gates`, `("./dev.py", "test")` is the last command and appears exactly once. A block with it anywhere else fails the test. The same test asserts this.
3. Each `roadmap merged` command parses with `cli._parser()`, as the existing loop in the test checks.
4. `./dev.py test tests/unit/test_roadmap_gate.py` passes unchanged. The unit tests use their own fixture text, so the doc reorder does not affect them.

## Verification
```
./dev.py test tests/integration/test_roadmap_gate.py tests/unit/test_roadmap_gate.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
Any change outside the five gate blocks in `docs/roadmap.md` and the one test. A block that drops, adds or rewrites a command. A change to `run_gate` or to the driver.

## Time budget
- expected: 10m
- stuck: 30m
