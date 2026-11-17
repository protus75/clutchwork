---
state: confirmed
source: human
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/checkpoint.py
- clutch/daemon.py::checkpoint_push
- clutch/stats.py::SETTLED
- clutch/caps.py::consume
- clutch/journal.py::ROLL_AGE

## On-demand
- docs/how-clutch-works.md
- tests/integration/test_checkpoint.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_daemon_composition.py
- tests/harness/daemon_soak.py
- tests/integration/test_daemon_soak_runner.py

## Goal / Why
Decision 19 (`docs/roadmap.md` section 6) counts every cadence in runs, never wall-clock time. Roadmap row 100 names two cadences that read the clock; this ticket is the checkpoint half, and `cadences-count-runs` is the retro half. Serve's checkpoint push (`clutch/checkpoint.py`) fires after `CHECKPOINT_MERGES` (5) merges or when `CHECKPOINT_INTERVAL` (24 hours) has passed, and it arms a journal timer `checkpoint-push/<window>` to hold that deadline. After this change it fires after 5 merges or `CHECKPOINT_SETTLED` (10) settled tickets since the last completed push, and it neither reads the clock nor arms a timer. A settled ticket is a distinct stem whose state transition goes to `merged`, `already_satisfied` or `rejected`, the set `clutch/stats.py::SETTLED` already names. A quiet day no longer pushes on its own, and a run of rejected or already-satisfied tickets, whose ticket-plane commits are on main, still reaches origin. The engine runs `serve` for every run once parallel runs land (decision 5), so this cadence runs in normal use.

## Scope in / Scope out
Scope in:
- `clutch/checkpoint.py`: remove `CHECKPOINT_INTERVAL`, the `timers` and `clock` constructor parameters and attributes, the `Timers`, `Clock`, `datetime` and `timedelta` imports, and the timer and deadline lines in `poll`. Add `CHECKPOINT_SETTLED = 10` and a pure module-level function `settled_since_last_push(events)`. It returns the number of distinct non-null `ticket` stems with a `STATE_TRANSITION` whose `to` is in `SETTLED`, among the events after the last `EFFECT_COMPLETION` whose key starts with `checkpoint-push/`, or among all events when there is none. Import `SETTLED` from `clutch.stats`; do not write the set again. `poll` returns without pushing unless merges since the last completed push are at least `CHECKPOINT_MERGES` or `settled_since_last_push` is at least `CHECKPOINT_SETTLED`. The push, the failure signal and its Box report, `_history`, `_merged`, and the completion result `{"merged": n}` are unchanged.
- `clutch/daemon.py`: `checkpoint_push` drops its `timers` and `clock` parameters and stops passing them to `Checkpoint`. Drop the `Timers` import, whose only use is there. Nothing else changes in this file.
- `clutch/serve.py`: the `checkpoint_push(...)` call in `Serve.run` drops `timers=` and `clock=`. Nothing else changes in this file.
- `tests/integration/test_checkpoint.py`: the rig and the `checkpoint_push` calls drop `timers` and `clock`. The `quiet-day` and `both` cases of `test_checkpoint_merge_and_daily_triggers` become settled-ticket cases. Every assertion on `rig.timers`, `owner.checkpoint.timers`, `CHECKPOINT_INTERVAL`, or a `checkpoint-push/` timer event is removed or rewritten to the settled trigger; a test whose only subject is the removed timer is deleted.
- `tests/integration/test_serve_lifecycle.py`: `test_serve_recurring_maintenance_uses_injected_time` waits for the `checkpoint-push/0` timer and advances 24 hours. It instead journals enough settled or merged transitions before serve starts that the first idle poll pushes, keeps its failed-then-retried two-push assertions, and asserts no `timer_fired` event instead of one. Nothing else changes in this file.
- `tests/integration/test_daemon_composition.py`: delete the one assertion `owner.checkpoint.timers is owner.core.restart.timers`. Nothing else changes in this file.
- `tests/harness/daemon_soak.py`: no soak member reaches 5 merges or 10 settled tickets, so after this change no member pushes and no timer fires. The checkpoint timer and its push completion were each member's only journal append after the `ROLL_AGE` (24 hour) boundary, which is what produced the second segment that `_observe`'s "journal age rotation missing" requirement checks. `_Member.recurring` replaces its final wait for the `checkpoint-push/0` completion with one production-written journal append after its five 6-hour advances: `caps.consume(self.journal, "rotation", "retry", "rotation")`, the same `caps.consume` call the soak already uses to seed caps, which writes one `cap_consumed` event for a stem that has no ticket. `_observe` keeps the "journal age rotation missing" requirement and the "checkpoint polling did not recur" requirement, and drops the "timer firing missing" and "checkpoint polling missing" requirements. Nothing else changes in this file.
- `tests/integration/test_daemon_soak_runner.py`: `test_daemon_soak_advances_each_member_24_hours` drops its `TIMER_FIRED` and `checkpoint-push/0` assertions, and `test_daemon_soak_requires_member_local_evidence` drops `"timer"` and `"checkpoint"` from its parametrized field tuple and removes their matching `missing()` clauses, since `_observe` no longer requires that evidence. Its journal-rotation case stays. Nothing else changes in this file.
- `docs/how-clutch-works.md`: only the Checkpoint push bullet in section 7.4, which reads "after 5 merges or 10 settled tickets (merged, already satisfied, or rejected) since the last push" instead of "after 5 merges or 24 hours".
- New test `tests/unit/test_checkpoint_settled_count.py` runs `settled_since_last_push` on in-memory event lists, with no journal.

Scope out: the retro trigger, `clutch/retro.py` and `clutch/config.py` (ticket `cadences-count-runs`), `CHECKPOINT_MERGES`, `clutch/timers.py` and its other users, `clutch/caps.py`, `clutch/journal.py` and its roll rule, and the restart path's `Timers` in `clutch/serve.py`. A `checkpoint-push/<n>` timer already in a journal still fires once harmlessly; nothing reads it.

## Scope fence
- clutch/checkpoint.py
- clutch/daemon.py
- clutch/serve.py
- docs/how-clutch-works.md
- tests/unit/test_checkpoint_settled_count.py
- tests/integration/test_checkpoint.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_daemon_composition.py
- tests/harness/daemon_soak.py
- tests/integration/test_daemon_soak_runner.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_checkpoint_settled_count.py` shows `settled_since_last_push` on in-memory event lists returning 10 for 10 settled stems with `merged`, `already_satisfied` and `rejected` each present, and 9, not 10, for 9.
2. The same test shows it counting only transitions after the last `checkpoint-push/<n>` completion when one exists, counting a stem with two settled transitions once, and not counting `abandoned`, `gate_failed`, or null-ticket transitions.
3. `./dev.py test tests/integration/test_checkpoint.py` shows a poll with 10 settled tickets and 0 merges since the last push performing the push, and a poll with 9 settled stems in all, 4 of them merged, and the injected clock advanced 30 days performing no push, not a push.
4. The same test shows that after a completed push, the next window counts only settled tickets journaled after that push's completion, and that no poll journals a `timer_armed` or `timer_fired` event.
5. `./dev.py test tests/integration/test_serve_lifecycle.py tests/integration/test_daemon_soak_runner.py` exits 0, with the serve lifecycle test showing two pushes, the first failed and the second retried, and no `timer_fired` event, and the soak runner's journal-rotation evidence case still present and passing.
6. `grep -rn --include=*.py --include=*.md "CHECKPOINT_INTERVAL" clutch tests docs/how-clutch-works.md` prints nothing, `grep -n "timers\|clock\|timedelta" clutch/checkpoint.py` prints nothing, `grep -n "after 5 merges or 24 hours" docs/how-clutch-works.md` prints nothing, and `grep -n "journal age rotation missing" tests/harness/daemon_soak.py` prints one line.

## Verification
```
./dev.py test tests/unit/test_checkpoint_settled_count.py tests/integration/test_checkpoint.py tests/integration/test_serve_lifecycle.py tests/integration/test_daemon_soak_runner.py tests/integration/test_daemon_composition.py
```

## Definition of rejected
A branch is rejected if the checkpoint still reads the clock or arms a timer, if `CHECKPOINT_INTERVAL` survives under an alias or a second code path, if the settled states are written out again instead of imported from `clutch.stats.SETTLED`, if the push, failure report, `_history` validation or the `{"merged": n}` result changes, if the soak drops or weakens its journal age rotation requirement or appends a journal event through anything but a production writer, or if it changes `clutch/retro.py` or `clutch/config.py`.

## Time budget
- expected: 30m
- stuck: 60m