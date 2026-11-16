---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/effects.py
- clutch/journal.py::run_terminals
- clutch/status.py::last_states
- docs/roadmap.md#2.3 Repeated helpers and projections
- tests/integration/test_merge.py::test_outbox_only_merge_regate_requires_lift_custody

## Goal / Why
Roadmap row 18 (duplication-table rows 5 and 6). Two lookups are hand-written at many call sites today:

- The latest `state_transition` body for a stem is scanned inline with `next(... reversed(...) ... EventType.STATE_TRANSITION and ticket == stem ...)` in `stages.py`, `serve.py`, `drain.py`, `providers.py` and `__main__.py` (the scan at `e.type == "state_transition"`).
- The result of a completed effect, looked up by key, is scanned inline in `stages.served_review`, `mergequeue.retained_ticket`, `merge.lifted_report_paths`, `runner.apply_admission` and `mergequeue._finish`. `checkpoint._history` is the sixth site named by the roadmap. `Effects._recorded` is a private copy of the same scan.

After this change each lookup has one owner: `journal.last_transition(events, stem)` and `Effects.recorded(key)`. In `observe.py`, `ticket_menu_inputs` derives its stem-to-state map through `status.last_states` instead of its own fold. A change to what counts as the latest transition, or as a completed effect, is then made in one place.

## Scope in / Scope out
Scope in:
- Add `last_transition(events, stem)` to `clutch/journal.py` beside `run_terminals`. It returns the body dict of the stem's latest `state_transition` event, or `None` when the stem has none. Callers that today use a default keep `or {}`.
- Add `require_transition(events, stem)` to `clutch/journal.py`. It returns `last_transition(events, stem)` or raises `RuntimeError` naming the stem when there is none. Every site that today uses `next(...)` without a default calls it. In `drain.py` these are the five sites at the scans near lines 596, 604, 700, 718 and 750. `_settle` (700, 718) and `_premise_road` (750) are plain methods, so today a missing transition raises a bare `StopIteration` there; once it propagates out of the async `run` frame that calls them it already reaches callers as `RuntimeError` (PEP 479). `require_transition` raising `RuntimeError` directly keeps that outcome. No site without a default is left inline.
- Replace every inline latest-transition scan of that shape with these in `stages.py`, `serve.py`, `drain.py`, `providers.py` and `__main__.py` (the scan at `e.type == "state_transition"`, near line 144). The `drain.py` scan that filters on `TERMINAL_STATES` (near line 108) is a different query and stays.
- Rename `Effects._recorded` to a public `Effects.recorded(key, ticket=None)` that returns the list of `body.get("result")` values of every `effect_completion` with that key, in journal order (an empty list when none). When `ticket` is given, only completions whose `ticket` equals it are included; a completion with the same key but another ticket is excluded. A completion with no `result` yields `None` in the list, never a `KeyError`. `Effects.run` replays with the first element and passes no `ticket`, so replay behavior is unchanged.
- Replace the five by-key scans (`stages.served_review`, `mergequeue.MergeQueue.retained_ticket`, `mergequeue.MergeQueue._finish`, `merge.lifted_report_paths`, `runner.apply_admission`) with `Effects.recorded`, reaching `Effects` through the `driver.effects`, `self.effects` or `Effects(journal)` that each site already has or builds nearby. A site that filters on `e.ticket == stem` today keeps that ownership check by passing `ticket=stem`: `served_review` and `lifted_report_paths` call `recorded(key, ticket=stem)`, so a completion whose key names the stem but whose `ticket` names another stem is still rejected (the custody cases in `tests/integration/test_merge.py`, including `wrong-stem`). A site that does not filter on ticket today passes no `ticket`. `lifted_report_paths` keeps its handling of a `None` result and its use of the last completion.
- `checkpoint._history` stays inline: it validates a whole history of keys, not a lookup of one key. The run record says so.
- In `observe.py`, convert only `ticket_menu_inputs` (the stem-to-state fold) to `status.last_states`. These folds stay, because they are not stem-to-`to`-state maps: `observe.py` lines building `{ticket: body+ts}` from dict events (in the snapshot code near 413 and 624) and the `__main__.py` dict scan near 599 are dict-shaped input (`e.get("type")`), and the `__main__.py` map near 177 needs the whole body (it reads `provider_drought`), which `last_states` does not return.

Scope out: no change to journal format, event types or the `drain.py` terminal-filtered scan; no change to `run_terminals`; no change to `checkpoint._history`; no new knobs beyond the `ticket` filter that preserves existing ownership checks; no behavior change at any call site; no change to assertions in `tests/integration/test_merge.py`. Other `STATE_TRANSITION` queries that are not latest-transition scans (folds and filters in `flake.py`, `caps.py`, `retro.py`, `stats.py`, `scorecard.py`, `audit.py`, `reconcile.py`, `checkpoint.py` and elsewhere) are untouched.

## Scope fence
- clutch/journal.py
- clutch/effects.py
- clutch/status.py
- clutch/stages.py
- clutch/serve.py
- clutch/drain.py
- clutch/providers.py
- clutch/__main__.py
- clutch/observe.py
- clutch/merge.py
- clutch/mergequeue.py
- clutch/runner.py
- tests/unit/test_journal_last_transition.py
- tests/unit/test_effects_recorded.py
- tests/integration/test_scan_owners.py

## Acceptance criteria
1. `tests/unit/test_journal_last_transition.py` builds events in `tmp_path` where stem `a` has transitions `running` then `gate_failed` then `running`, and checks `last_transition(events, "a")` returns the body of the last `running` event, not the first and not the `gate_failed` one; `last_transition(events, "absent")` returns `None`, not `{}`; a stem `b` whose events interleave with `a` does not leak into `a`'s result; and `require_transition(events, "absent")` raises `RuntimeError` whose message contains `absent`, not `StopIteration` and not a returned `None`.
2. `tests/unit/test_effects_recorded.py` checks that `Effects.recorded(key)` returns `[]` for a key with no completion (not `[None]`, and no raised error), returns both results in journal order when a key completed twice, ignores an `effect_intent` with the same key, returns `[None]` (not a `KeyError`) for a completion journaled without `result`, and that `Effects.run` still replays the first recorded result without re-running the action.
3. `tests/unit/test_effects_recorded.py` journals two completions with the same key, one with `ticket="a"` and one with `ticket="foreign"`, and checks that `Effects.recorded(key, ticket="a")` returns only the `a` result, `Effects.recorded(key, ticket="absent")` returns `[]`, and `Effects.recorded(key)` returns both. The forged-ownership custody cases pass with assertions unchanged: `./dev.py test tests/integration/test_merge.py` exits 0, including the `wrong-stem` cases of `test_outbox_only_merge_regate_requires_lift_custody`.
4. `tests/integration/test_scan_owners.py` parses `clutch/*.py` with `ast` and fails, naming file and line, on each of: (a) in any module other than `journal.py` and `status.py`, a `next(...)` call whose first argument is a generator expression over `reversed(...)` and whose condition compares `.type` with `EventType.STATE_TRANSITION` or `"state_transition"` and compares `.ticket` with `==`, unless the condition references `TERMINAL_STATES`; this fails on `__main__.py` at base (the scan near line 144) and does not flag the `drain.py` terminal-filtered scan or any fold or filter that is not a `next(reversed(...))` lookup; (b) any dict comprehension outside `status.py` whose value is a `["to"]` subscript of an event body keyed by `.ticket`; (c) inside only the five functions `stages.served_review`, `mergequeue.MergeQueue.retained_ticket`, `mergequeue.MergeQueue._finish`, `merge.lifted_report_paths` and `runner.apply_admission`, any list comprehension, generator expression, or `next(...)`/`any(...)` argument that compares `.type` with `EventType.EFFECT_COMPLETION` and `.key` with `==`. `mergequeue.py`'s `any(...)` generator in `_finish` is caught by (c). Modules and functions outside these five (for example `triage.py`, `box.py`, `author.py`, `retro.py`, `checkpoint.py`) are not checked.
5. `Effects._recorded` no longer exists: `grep -rn "_recorded(" clutch/` returns no hit.
6. The existing suites for the touched modules pass unchanged in assertions: `./dev.py test tests/integration/test_effects.py tests/integration/test_journal.py tests/integration/test_drain.py tests/integration/test_stages.py tests/integration/test_mergequeue.py tests/integration/test_merge.py` exits 0.

## Verification
```
./dev.py test tests/unit tests/integration/test_effects.py tests/integration/test_journal.py tests/integration/test_drain.py tests/integration/test_stages.py tests/integration/test_mergequeue.py tests/integration/test_merge.py tests/integration/test_scan_owners.py
```

## Definition of rejected
A call site changes behavior (a default that was `{}` becomes `None`, a raise becomes a silent default, a completion without `result` raises, or `served_review` or `lifted_report_paths` accepts a completion whose `ticket` is not the stem). An assertion in `tests/integration/test_merge.py` is changed. A compatibility alias for `_recorded` or a second lookup path is left in place. The new tests pass on an implementation that still has the inline scans, including the `e.type == "state_transition"` scan in `__main__.py` or the `any(...)` scan in `mergequeue._finish`.

## Time budget
- expected: 45m
- stuck: 90m