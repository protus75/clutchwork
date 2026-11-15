---
priority: P1
kind: bug
source: human
state: confirmed
---

## Depends on
none

## Context
- docs/how-clutch-works.md
- tickets/no-plan-host/evidence/unguarded-plan-reads.txt
- clutch/tickets.py
- clutch/author.py
- clutch/rework.py
- clutch/daemon.py
- clutch/runner.py
- clutch/requisition.py
- tests/test_author.py
- tests/test_reject_queue.py

## On-demand
- clutch/stages.py

## Goal / Why
`CLUTCH_PLAN.md` exists only in clutch's own repo, but six runtime paths read it with a bare `read_text()` and no existence check (listed in the evidence file). On a host repo without it, the Author stage (`author.py`), Rework (`rework.py`, `daemon.apply_rework`), and dead-dependency handling after a kill (`runner._dead_dependents`) raise `FileNotFoundError`. `parse_ticket` and `validate_ticket` already treat an absent plan as `plan=None`; these paths must do the same.

## Scope in / Scope out
- In: one function in `clutch/tickets.py` beside `PLAN_FILE` that returns the plan text under a given root, or `None` when the file is absent. Every runtime read of the plan in `clutch/` goes through it: `author.py`, `rework.py`, `daemon.py`, `runner.py` (`_dead_dependents` and `hardening_text`), and `stages.py` (seed review).
- In: `requisition.review_ticket` accepts `plan=None`; with no plan, the ticket has no plan units to resolve or harden, and review proceeds on the ticket and its Context alone. That covers both uses inside it, `hardenable_units` and `_base_render`; existing callers passing `plan=""` keep working.
- In: `tests/test_no_plan_host.py` adds, each in a temp repo with no `CLUTCH_PLAN.md`: `test_author_without_plan` (Author writes and reviews a ticket from a Box message with a scripted model), `test_rework_without_plan` (a Rework `update` proposal is validated and reviewed), and `test_kill_without_plan_files_dead_dependency` (`reject` of a stem with a confirmed dependent files its dead-dependency report).
- In: `tests/regress_no_plan_host.py`, the carried reproducer: in a temp repo with no `CLUTCH_PLAN.md` it runs the dead-dependency path of `reject`; it prints `{"regression_result": "pass"}` and exits 0 when that completes, prints `{"regression_result": "defect"}` and exits 1 on a `FileNotFoundError` naming `CLUTCH_PLAN.md`, and prints `{"regression_result": "error"}` and exits 2 on any other failure. Diagnostics go to stderr only.
- In: update `docs/how-clutch-works.md` section 13 (plan reads go through one function and tolerate an absent plan), so the doc matches the code when this merges.
- In: the already-guarded plan reads in `clutch/drain.py` and `clutch/__main__.py` also go through the one function, so no `read_text()` of the plan remains elsewhere in `clutch/`.
- In: if `uv run pytest -q` fails only on tests that also fail on the merge base, those failures are pre-existing: Check excuses them (base-red). Commit the work and list them in the run record; never stop with `premise_failed` for them.
- Out: removing the bootstrap plan machinery, plan lint, `## Plan contract` grammar, and every behavior when the plan file exists.

## Scope fence
- docs/how-clutch-works.md
- clutch/tickets.py
- clutch/author.py
- clutch/rework.py
- clutch/daemon.py
- clutch/runner.py
- clutch/stages.py
- clutch/requisition.py
- tests/test_no_plan_host.py
- tests/regress_no_plan_host.py
- clutch/drain.py
- clutch/__main__.py

## Acceptance criteria
1. `uv run python tests/regress_no_plan_host.py` prints exactly `{"regression_result": "pass"}` and exits 0.
2. `uv run pytest -q tests/test_no_plan_host.py` exits 0 with `test_author_without_plan`, `test_rework_without_plan`, and `test_kill_without_plan_files_dead_dependency`.
3. `clutch/` contains no `read_text()` of the plan file outside the one function in `clutch/tickets.py`.
4. `uv run pytest -q` exits 0.
5. `docs/how-clutch-works.md` section 13 says plan reads go through one function and an absent plan is tolerated.

## Verification
```
uv run python tests/regress_no_plan_host.py
uv run pytest -q tests/test_no_plan_host.py
uv run pytest -q
```

## Regression
```
uv run python tests/regress_no_plan_host.py
```
- carries: tests/regress_no_plan_host.py

## Definition of rejected
Reject the branch if any path in `clutch/` can still raise because `CLUTCH_PLAN.md` is absent, if behavior changes when the plan exists, or if the reproducer prints anything besides the result object on stdout.

## Time budget
- expected: 45m
- stuck: 90m
