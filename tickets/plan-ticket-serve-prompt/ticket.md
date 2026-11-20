---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- view-events-stream

## Context
- clutch/ask.py
- clutch/specs/ask/drain-loop.md
- clutch/docs/host-running.md
- tests/integration/test_ask.py
- tests/integration/test_ask_view_events.py
- tests/unit/test_ask_plan_drain.py

## On-demand
- clutch/specs/ask/plan-ticket-drain.md
- clutch/__main__.py
- docs/how-clutch-works.md

## Goal / Why
`clutch prompt plan-ticket-drain` hands an unattended operator a roadmap run that starts `clutch engine drain`, reads `${state_dir}/drain.out`, and treats a drain exit as the end of a run. There is no prompt for the continuous daemon: nothing tells an operator to start `clutch engine serve`, supervise it, or stop it when the plan is done. `docs/how-clutch-works.md` section 7 and `clutch/docs/host-running.md` call serve the normal mode, and serve alone runs the merge queue and parallel admission.

After this ticket `clutch prompt plan-ticket-serve` prints the same unattended roadmap kickoff for serve. The operator starts `clutch engine serve` under its agent's background-process facility, supervises it with `clutch view events` and `clutch prompt drain-loop`, and ends the run with `clutch engine stop` once the plan is complete. Serve never quiesces, so the stop condition and every "drain exits" road in the drain prompt change: the prompt carries the new ones and no stale drain wording.

## Boundary contract
### Operator prompt kinds
- disposition: extend
- owner: clutch/ask.py
- consumers: `clutch prompt <kind>` in clutch/__main__.py, the prompt rows in clutch/docs/host-running.md and docs/how-clutch-works.md
- observable change: `ask.KINDS` gains `plan-ticket-serve`; `clutch prompt plan-ticket-serve` prints the new spec, takes no stem, and refuses a stem like `plan-ticket-drain`
- compatibility: `plan-ticket-drain` and `drain-loop` render byte-identical to today
- acceptance: criteria 1-4
- tests: tests/unit/test_ask_plan_serve.py, tests/integration/test_ask_plan_serve.py
- post-merge source of truth: clutch/ask.py `KINDS` and clutch/specs/ask/plan-ticket-serve.md

## Scope in / Scope out
Scope in:
- Add `plan-ticket-serve` to `ask.KINDS` and render it in `ask.render` in the same branch as `plan-ticket-drain` and `drain-loop` (state_dir substitution).
- New spec `clutch/specs/ask/plan-ticket-serve.md`. It keeps the drain prompt's Before-you-start, Delegation, Authoring, and Closing rules and replaces what is drain-specific: start the daemon with `clutch engine serve` under the agent's background-process facility (serve has no detach flag; never add one here), supervise with `clutch view events` and `clutch prompt drain-loop`, never read `drain.out`, and stop with `clutch engine stop` when the stop condition holds. The stop condition is the drain prompt's with "no engine runs" replaced by "idle with nothing running or confirmed unrun". Roads that need no engine running (Reject-queue edits, `box dismiss`, `host doctor`) say to run `clutch engine stop`, do the step, and start serve again. Serve picks up confirmed tickets live, so the prompt tells the operator to confirm and leave the daemon running.
- Wire the CLI: `prompt_details`, the no-stem example list at `clutch/__main__.py` line 444, and `handle_prompt` line 1286 each name the new kind.
- Update the prompt row in `clutch/docs/host-running.md` and the verb table in `docs/how-clutch-works.md` section 2 with a `prompt plan-ticket-serve` row.
- `tests/integration/test_ask.py`: add `plan-ticket-serve` to the exclusion set of the stem-rendering parametrization, the one edit the new kind forces there.

Scope out: `plan-ticket-drain.md` (fenced only because it is read on demand; its text must not change) and `drain-loop.md` text (drain-loop still tells a supervisor to read drain.out; making it serve-aware is a separate ticket), the VS Code extension and `clutch/help.py`, any `--detach` flag for serve, and sharing text between the two plan prompts through templating.

Simpler approach rejected: a one-line overlay spec that says "render `plan-ticket-drain` and read drain as serve". The drain prompt's stop condition, `drain.out` reads, and "drain can exit right after starting" road would stay in force and contradict the overlay. A separate spec duplicates prose, but `clutch/specs/ask/` already holds each prompt as its own file.

## Scope fence
- clutch/ask.py
- clutch/__main__.py
- clutch/specs/ask/plan-ticket-serve.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/integration/test_ask.py
- tests/unit/test_ask_plan_serve.py
- tests/integration/test_ask_plan_serve.py

## Acceptance criteria
1. `ask.render("plan-ticket-serve", "", config, repo)` returns text containing `clutch engine serve`, `clutch view events`, `clutch prompt drain-loop`, `clutch engine stop`, and the state dir, and containing neither `drain.out` nor `clutch engine drain`; checked by `tests/unit/test_ask_plan_serve.py`.
2. `clutch prompt plan-ticket-serve x` exits 2 with `plan-ticket-serve takes no stem`, and with no stem exits 0 printing the spec; the test fails if the stem is ignored; checked by `tests/unit/test_ask_plan_serve.py`.
3. The rendered `plan-ticket-serve` and `plan-ticket-drain` prompts carry the same conduct-file check, window limit (`3 roadmap tickets confirmed and unrun`), and `Never push` rule, and `plan-ticket-drain` renders byte-identical to its text on main; checked by `tests/integration/test_ask_plan_serve.py`.
4. `clutch/docs/host-running.md` names `plan-ticket-serve` in its `prompt` row and `docs/how-clutch-works.md` has a row starting `| \`prompt plan-ticket-serve\` |`; checked by `tests/integration/test_ask_plan_serve.py`.
5. `tests/unit/test_main_help.py` still passes: the parser's prompt subcommands equal `ask.KINDS`, which includes the new kind.

## Verification
```
./dev.py test tests/unit/test_ask_plan_serve.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask.py tests/unit/test_main_help.py tests/unit/test_ask_plan_drain.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_view_events.py
```

## Definition of rejected
- The new prompt still tells the operator to run `clutch engine drain` or read `drain.out`.
- `plan-ticket-drain` or `drain-loop` text changes.
- A `--detach` flag or any other change to `engine serve`.
- A shell script or hand-built argv instead of a clutch verb in the prompt.

## Time budget
- expected: 20m
- stuck: 40m
