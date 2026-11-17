---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:retro_finding
state: rejected
---

## Depends on
none

## Context
- tests/integration/test_implement_spec_mutation_check.py
- tests/unit/test_implement_incomplete.py

## On-demand
- clutch/specs/implement.md

## Goal / Why
The Implement spec lets an implementer reply `incomplete` after only reading, with no named blocker, and says "commit nothing further", which discards partial edits. Retro 51 counted eight such replies in four tickets (main-verb-groups, evidence-store, evidence-envelope, supervise-every-route). Two reached the Reject queue and needed an operator. Each cost one Implement call plus two or three Diagnose calls, and every diagnosis only said to do the whole ticket.

After this change the spec allows `incomplete` only for a named external stop the implementer cannot work past, such as a tool or provider failure or an exhausted session limit. Running out of reading time, a large change, or work not yet verified is never a stop: the implementer keeps editing. Before replying `incomplete`, the implementer commits any partial work already written. The `summary` names the stop and lists the acceptance criteria still unmet. The engine's own retry text in `clutch/stages.py` and the documented definition in `docs/how-clutch-works.md` say the same thing, so nothing invites an `incomplete` reply without a named stop.

Two things stay as they are. A real session-limit stop may still reply `incomplete`. A genuine ticket defect still goes to `premise_failed`, and unfinished work is never recast as `premise_failed`.

The next retro window should show no Implement `incomplete` reply whose summary names no external stop, and none left with uncommitted partial work.

Rule home: this rule governs the Implement prompt, which every host runs. It lives in `clutch/specs/implement.md` only, not in CLAUDE.md, AGENTS.md or `CORE_TEMPLATE`.

## Scope in / Scope out
Scope in:
- Rewrite the `incomplete` bullet in `clutch/specs/implement.md` (the outcome list under "Three first-class outcomes") with these parts:
  - `incomplete` is valid only when a named external stop prevents continuing: a tool or provider failure, or an exhausted session limit.
  - The `summary` must name that stop.
  - Reading time, change size, and "not yet verified" are never a stop; keep editing.
  - Commit any partial work already written before replying, instead of "commit nothing further".
  - The `summary` lists the acceptance criteria still unmet.
  - Keep the existing sentences "Never report unfinished work as `premise_failed`." and "Never use `incomplete` because mutation checks remain while the Verification commands pass."
- Make the first sentence of `## On-failure` ("If you stopped before finishing, reply `incomplete`; ...") agree with the new bullet, so the two do not contradict.
- Bump the spec `version` to the next minor above the version on main.
- Update the version pins that flip. In `tests/integration/test_implement_spec_mutation_check.py` change only the version assertion. In `tests/integration/test_stages.py` change only the `spec: implement` version in the run.md assertion near line 335. In `tests/unit/test_specs.py` change only the two implement version pins (the tuple entry near line 25 and the assertion near line 127).
- In `clutch/stages.py`, reword only the two `ValueError` message strings near lines 106 and 109 (the ones containing "reply incomplete when you stopped before finishing" and "incomplete for unfinished work"). They must name `incomplete` only for a named external stop (a tool or provider failure, or an exhausted session limit), and keep `premise_failed` for a ticket defect.
- In `docs/how-clutch-works.md`, reword only the line near 214 that defines `incomplete` as "work stopped before it was committed, without an established ticket defect". It must say a named external stop (a tool or provider failure, or an exhausted session limit) halted work after any partial work was committed, without an established ticket defect.
- Add a new integration test file `tests/integration/test_implement_incomplete_stop.py` that pins the new wording in the spec, the `clutch/stages.py` messages, and the doc line.

Scope out: the `ImplementReply` schema and fields, the validation logic and conditions in `clutch/stages.py` (only the two message strings change), `failed_attempt` and cap logic, Diagnose and the supervisor, and any other spec. No engine escalation or size routing. Any change to the mutation-check sentences other than the on-failure agreement is out. Any other line of `docs/how-clutch-works.md` is out.

## Scope fence
- clutch/specs/implement.md
- clutch/stages.py
- docs/how-clutch-works.md
- tests/integration/test_implement_incomplete_stop.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/integration/test_stages.py
- tests/unit/test_specs.py

## Acceptance criteria
1. The `incomplete` bullet in `clutch/specs/implement.md` names the allowed stops (tool or provider failure, exhausted session limit) and requires `summary` to name the stop. `./dev.py test tests/integration/test_implement_incomplete_stop.py` asserts these phrases are present and fails on the old text, which allowed any stop.
2. The bullet says reading time, a large change, and work not yet verified are never a stop. `./dev.py test tests/integration/test_implement_incomplete_stop.py` asserts this phrase, and fails if the bullet still says "commit nothing further".
3. The bullet requires committing partial work already written before replying `incomplete`, and requires `summary` to list the unmet acceptance criteria. `./dev.py test tests/integration/test_implement_incomplete_stop.py` asserts both phrases.
4. `## On-failure` no longer tells the implementer to reply `incomplete` for any stop. `./dev.py test tests/integration/test_implement_incomplete_stop.py` asserts the old sentence "If you stopped before finishing, reply `incomplete`;" is absent, and that the new text still says "Never report unfinished work as `premise_failed`." and "Never use `incomplete` because mutation checks remain while the Verification commands pass." (the second sentence is also pinned by the existing mutation-check test).
5. `load_spec` reports the bumped version, which is the next minor above the version on main. `./dev.py test tests/integration/test_implement_spec_mutation_check.py tests/unit/test_specs.py tests/integration/test_stages.py` passes with the pins updated, not still pinning the old version.
6. `./dev.py test tests/unit/test_implement_incomplete.py` still passes, so the reply shape and failed-attempt cap are unchanged.
7. The `ValueError` messages in `clutch/stages.py` no longer contain the phrases "incomplete when you stopped before finishing" or "incomplete for unfinished work", and still contain `premise_failed` and `incomplete`. `./dev.py test tests/integration/test_implement_incomplete_stop.py` asserts both absences and both presences in the `clutch/stages.py` source.
8. The `incomplete` definition in `docs/how-clutch-works.md` no longer contains "work stopped before it was committed" and names a named external stop. `./dev.py test tests/integration/test_implement_incomplete_stop.py` asserts the old phrase is absent and "named external stop" is present.

## Verification
```
./dev.py test tests/integration/test_implement_incomplete_stop.py tests/integration/test_implement_spec_mutation_check.py tests/unit/test_specs.py tests/unit/test_implement_incomplete.py tests/integration/test_stages.py
```

## Definition of rejected
The branch is rejected if `incomplete` can still be replied without naming an external stop. It is also rejected if `incomplete` still says to commit nothing further, if `premise_failed` is allowed for unfinished work, if the engine retry text or the how-clutch-works definition still invites `incomplete` for unfinished work, if the validation logic in `clutch/stages.py` changes, or if the version is not bumped. It is rejected if any file outside the fence changes.

## Time budget
- expected: 25m
- stuck: 50m
