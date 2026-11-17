---
state: draft
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/checkpoint.py
- clutch/retro.py::select_trigger
- clutch/config.py::RetroDays
- clutch/daemon.py

## On-demand
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/integration/test_checkpoint.py
- tests/integration/test_retro.py
- tests/integration/test_config.py
- tests/integration/test_drain.py

## Goal / Why
Decision 19 counts every cadence in runs, not wall-clock time. Two cadences still read the clock. The retro's `elapsed` trigger fires when the window is `retro.days.every` (7) days old. The checkpoint push fires when `CHECKPOINT_INTERVAL` (24 hours) has passed. After this change both count settled tickets. A settled ticket is one whose state transition goes to `merged`, `already_satisfied` or `rejected`, counted once per stem. Neither cadence reads the clock or arms a timer. A slow day no longer triggers a retro or a push on its own, and a run of rejected or already-satisfied tickets that never merge still triggers one. The existing merge counts (`retro.merges.every`, `CHECKPOINT_MERGES`) are unchanged.

## Scope in / Scope out
Scope in:
- `clutch/config.py`: rename class `RetroDays` to `RetroSettled`, and the `Retro.days` field to `settled`, in place with no alias. `RetroSettled` has `enabled: bool = True` and `every: Count = 40`. `Retro.days` is removed, so a config that still says `days:` is refused by the existing unknown-key check. `SCHEMA_VERSION` does not change. Line 441's check of `retro.days.enabled` becomes `retro.settled.enabled`.
- `clutch/retro.py`: `select_trigger` drops its `now` parameter, because nothing else in it reads the clock. The `elapsed` branch becomes a `settled` branch. It returns the trigger name `settled` when the number of distinct stems in `window.events` with a state transition `to` in `{merged, already_satisfied, rejected}` is at least `settings.settled.every`. It still sits after `merges` and before spikes. Drop the `timedelta` import if it becomes unused. The `Window.started_at` field stays, because `window_start` is still reported.
- `clutch/serve.py` and `tests/integration/test_drain.py`: the call sites of `select_trigger` drop the `now` argument. In `clutch/serve.py` the `checkpoint_push` call (around line 535) also drops `timers=` and `clock=`. Nothing else changes in either file.
- `clutch/checkpoint.py`: remove `CHECKPOINT_INTERVAL`, the `timers` and `clock` constructor parameters, and every `self.timers` and deadline use in `poll`. Add `CHECKPOINT_SETTLED = 10`. `poll` pushes when merges since the last completed push are at least `CHECKPOINT_MERGES`, or settled tickets since then are at least `CHECKPOINT_SETTLED`. Settled tickets are counted after the last completed push event in journal order, or over the whole journal when no push has completed. The counting is a pure module-level function `settled_since_last_push(events)` over an in-memory list of journal events, which `poll` calls; it is the seam through which a unit test runs the new lines with fakes. The push, failure and history-validation code and the effect result shape `{"merged": n}` are untouched.
- `clutch/daemon.py`: the `Checkpoint(...)` construction drops `timers=` and `clock=`. `daemon.checkpoint_push` drops its `timers` and `clock` parameters, which only forwarded to Checkpoint, and drops the `Timers` import if it becomes unused. Nothing else changes there. The `checkpoint_push` call sites in `tests/integration/test_checkpoint.py` (lines 71, 482 and 570) drop the same arguments.
- `clutch/docs/host-contract.md`: update only the retro defaults lines (the two `days: {enabled: true, every: 7}` entries), the prose naming the `days` block and its threshold, and the config-fields `RetroDays:` row at lines 227-229, which is renamed `RetroSettled:` with `defaults: {enabled: true, every: 40}` so it matches the config class name. Each of these becomes `settled` with `every: 40`.
- `docs/how-clutch-works.md`: update only two places. The Checkpoint push bullet in section 7.4 reads "after 5 merges or 10 settled tickets". The retro trigger sentence near line 696, which names `retro.days` and the 7-day elapsed trigger, says the retro fires after `retro.settled.every` (40) settled tickets.
- Tests: pin the new behavior in the new file `tests/unit/test_cadence_counts.py`. Update the existing assertions in `tests/integration/test_checkpoint.py`, `tests/integration/test_retro.py` and `tests/integration/test_config.py` that the rename and the removal force.

Scope out: `CHECKPOINT_MERGES`, `retro.merges`, `retro.spikes`, the journal timer machinery in `clutch/timers.py`, any other cadence, and the config schema version. No config migration is written, because the unknown-key refusal already names the stale `days` key.

Reason the budget exceeds 30m: the two cadences share one decision and one doc change, and splitting would leave a half-renamed config on main.

## Scope fence
- clutch/config.py
- clutch/retro.py
- clutch/serve.py
- clutch/checkpoint.py
- clutch/daemon.py
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_cadence_counts.py
- tests/integration/test_checkpoint.py
- tests/integration/test_retro.py
- tests/integration/test_config.py
- tests/integration/test_drain.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_cadence_counts.py` shows `select_trigger` returning `"settled"` for a window holding 40 settled transitions across 40 distinct stems, and `None`, not `"settled"`, for 39.
2. The same unit test shows that a stem with two `merged` transitions counts once, and that `rejected` and `already_satisfied` transitions each count toward the 40.
3. The same unit test shows that a window whose `started_at` is 365 days old with 0 settled tickets returns `None`, not `"elapsed"`. Once a window holds 40 settled tickets and `settled.enabled` is false, it returns `None`.
4. `./dev.py test tests/integration/test_config.py` shows a config containing `retro: {days: {every: 2}}` refused as an unknown key, not accepted. It also shows `retro: {settled: {every: 2}}` parsing to `settled.every == 2`, and the default `retro.settled.every == 40`.
5. `./dev.py test tests/integration/test_checkpoint.py` shows a poll with 10 settled tickets and 0 merges since the last push performing the push. It shows a poll with 9 settled tickets, fewer than 5 merges, and a clock advanced by 30 days performing no push, not a push.
6. `./dev.py test tests/integration/test_checkpoint.py` shows that after a completed push, the next window counts only settled tickets journaled after that push's completion event. Settled tickets from before it do not count.
7. `./dev.py test tests/unit/test_cadence_counts.py` shows `settled_since_last_push` on in-memory event lists returning 10 for 10 settled tickets and 9, not 10, for 9; counting only events after a completed-push event when one exists; and counting a stem with two settled transitions once. This runs the new `clutch/checkpoint.py` lines with fakes and no real journal.
8. `grep -rn "CHECKPOINT_INTERVAL\|retro.days\|RetroDays" clutch tests docs/how-clutch-works.md` prints nothing, and `grep -n "timers" clutch/checkpoint.py` prints nothing.
9. `grep -n "days" clutch/docs/host-contract.md` prints no line naming a retro `days` block, and `grep -n "24 hours" docs/how-clutch-works.md` prints no line about the checkpoint push.

## Verification
```
./dev.py test tests/unit/test_cadence_counts.py tests/integration/test_checkpoint.py tests/integration/test_retro.py tests/integration/test_config.py tests/integration/test_drain.py tests/integration/test_serve_lifecycle.py tests/integration/test_host_contract.py
```

## Definition of rejected
A branch is rejected if either cadence still reads the clock or arms a timer. It is also rejected if `RetroDays`, `retro.days` or `CHECKPOINT_INTERVAL` survive under an alias or a second code path, if a config migration or schema bump is added, or if the settled count includes states other than `merged`, `already_satisfied` and `rejected`.

## Time budget
- expected: 45m
- stuck: 90m
- reason: the two cadences share Decision 19 and one doc change, and splitting would leave a half-renamed config on main.
