---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/events.py
- tests/unit/test_view_events.py

## Goal / Why
`clutch view events` prints a `gate - <release> failed -- clutch roadmap status` line every time the journal records a `roadmap_gate` signal, even when the release's last recorded result was the same. A supervising operator under its agent's monitor facility is woken for each line, so every repeat is a model request that reads the whole session context and decides nothing.

Measured on the journal at `.clutch/state` on 2026-11-23: 619 `roadmap_gate` signals, 613 of them repeat the previous result for the same release (release 0.5.0 failed 381 times, 0.4.0 122 times, 0.3.0 96 times). In the five supervisor sessions since 2026-11-18, 116 of 675 monitor wakeups were gate lines, and 62 of those turns made no tool call.

After this ticket the stream prints a gate line only when a release's result differs from the last result the stream knows for that release, including results already in the journal at the silent baseline. Every other line kind is unchanged. This is the instance fix for the monitoring cost; session rotation is `plan-prompts-session-handoff`.

## Boundary contract
### view events stream
- disposition: extend
- owner: clutch/events.py
- consumers: `clutch view events` and the supervisor prompts that monitor it (`clutch prompt plan-ticket-drain`, `clutch prompt plan-ticket-serve`)
- observable change: a `roadmap_gate` signal whose `passed` value equals the previous known result for its `release` prints no line; the first result for a release after the baseline, and every change of result, still prints
- compatibility: the line format, the closed `EVENTS` tuple, the silent baseline and the replay-after-truncation behavior are unchanged
- acceptance: unit tests in a new file drive `events.poll` with journal fixtures and assert the repeat prints nothing and a flip prints a line
- tests: `tests/unit/test_events_gate_repeat.py`
- post-merge source of truth: clutch/events.py

## Scope in / Scope out
Scope in:
- In `clutch/events.py`, remember the last `passed` value per `release` in the state `poll` and `changes` already carry between calls, seeded at the silent baseline from every journaled `roadmap_gate` signal, and reset the way the existing state resets when the journal shrinks. Emit the gate line only when the value differs.
- Add the tests in a new file `tests/unit/test_events_gate_repeat.py`.

Scope out:
- No new flag, no new line kind, no change to `start`, `settle`, `draft`, `reject_queue`, `release`, `upgrade` or engine lines.
- No change to how many `roadmap_gate` signals the engine journals.
- No documentation edit: the published `view events` descriptions say "actionable changes", which stays true.

## Scope fence
- clutch/events.py
- tests/unit/test_events_gate_repeat.py

## Acceptance criteria
1. A journal whose last `roadmap_gate` for release `v2` was `passed=False` at the baseline, then gains another `passed=False` signal for `v2`, makes `events.poll` return no lines, not a `gate - v2 failed` line; checked by `./dev.py test tests/unit/test_events_gate_repeat.py`.
2. Starting from a baseline with `v2` failed, a later `passed=True` signal returns `gate - v2 passed -- clutch roadmap status`, and a following `passed=False` returns `gate - v2 failed -- clutch roadmap status`, not nothing; checked by `./dev.py test tests/unit/test_events_gate_repeat.py`.
3. Two releases are tracked separately: a repeated failure for `v1` prints nothing while a first failure for `v2` prints its line; checked by `./dev.py test tests/unit/test_events_gate_repeat.py`.
4. The existing `view events` tests still pass unchanged, including the first-result gate line in `test_journal_deltas_and_noise`; checked by `./dev.py test tests/unit/test_view_events.py tests/unit/test_main_view_events.py tests/unit/test_events_upgrade_pending.py`.

## Verification
```
./dev.py test tests/unit/test_events_gate_repeat.py tests/unit/test_view_events.py tests/unit/test_main_view_events.py tests/unit/test_events_upgrade_pending.py
```

## Definition of rejected
The branch adds a flag or a second event stream, drops the first gate line for a release, changes any other line kind, or changes how `roadmap_gate` signals are journaled.

## Time budget
- expected: 12m
- stuck: 24m
