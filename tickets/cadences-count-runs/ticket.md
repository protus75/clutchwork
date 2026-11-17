---
state: confirmed
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/retro.py::Window
- clutch/retro.py::select_trigger
- clutch/config.py::RetroDays
- clutch/config.py::Retro
- clutch/config.py::_check_references
- clutch/stats.py::SETTLED

## On-demand
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/integration/test_retro.py
- tests/integration/test_config.py
- tests/integration/test_drain.py

## Goal / Why
Decision 19 (`docs/roadmap.md` section 6) counts every cadence in runs, never wall-clock time. The retro's `elapsed` trigger still reads the clock: `clutch/retro.py::select_trigger` returns `elapsed` when the window is `retro.days.every` (7) days old, whatever happened in it. On 2026-11-03 it started retro 000014 (`tickets/retro/000014.md`) on a 24-day-old window that held no events: 0 merges and 0 spikes, and a forced retro needs a merge, so only `elapsed` could select it. It spent one model call (41,734 input tokens, $0.13) that returned no proposals, and committed an empty report. After this change the third retro trigger counts settled tickets: the distinct stems in the window whose state transition goes to `merged`, `already_satisfied` or `rejected`, the set `clutch/stats.py::SETTLED` already names. It fires at `retro.settled.every` (default 40), and retro selection reads no clock. The checkpoint push, the other clock cadence of roadmap row 100, is the sibling ticket `checkpoint-counts-settled`.

## Scope in / Scope out
Scope in:
- `clutch/config.py`: rename class `RetroDays` to `RetroSettled` and the `Retro.days` field to `settled`, in place with no alias. `RetroSettled` has `enabled: bool = True` and `every: Count = 40`. A config that still says `days:` is refused by the existing unknown-key check. `SCHEMA_VERSION` does not change. In `_check_references`, `retro.days.enabled` becomes `retro.settled.enabled`. Nothing else changes in this file.
- `clutch/retro.py`: `select_trigger` drops its `now` parameter. Its `elapsed` branch becomes a `settled` branch in the same place (after `merges`, before spikes). It returns `"settled"` when `settings.settled.enabled` and the number of distinct non-null `ticket` stems among `window.events` with a `STATE_TRANSITION` whose `to` is in `SETTLED` is at least `settings.settled.every`. Import `SETTLED` from `clutch.stats`; do not write the set again. The call in `Retro.__call__` drops `c.clock()`. Drop the `timedelta` import. `Window.started_at` and the report's `window_start` stay. Nothing else changes in this file.
- `clutch/serve.py`: the `select_trigger` call in `Serve.check_retro` drops `c.clock()`. Nothing else changes in this file.
- `tests/integration/test_drain.py`: the `select_trigger` call near line 1112 drops `checkout.clock()`. Nothing else changes in this file.
- `tests/integration/test_retro.py`: every `select_trigger` call drops its clock argument. The `elapsed` case of the parametrized trigger test becomes a `settled` case that journals settled transitions instead of advancing the clock. `test_custom_trigger_settings_and_disabled_forcing` and `test_disabled_trigger_never_fires` use `settled` settings and settled counts instead of `days` settings and window ages.
- `tests/integration/test_config.py`: `test_retro_yaml_values` and `test_retro_contradictory_settings_refused` use `settled` where they use `days`, and the latter also shows `retro: {days: {every: 2}}` refused as an unknown key, as it already does for `every_merges`.
- `clutch/docs/host-contract.md`: in the `config-fields` block, the two retro defaults entries `days: {enabled: true, every: 7}` become `settled: {enabled: true, every: 40}`, and the `RetroDays:` row becomes `RetroSettled:` with `defaults: {enabled: true, every: 40}`. The prose sentence naming the `merges`, `days`, and `spikes` blocks names `settled` instead of `days`.
- `docs/how-clutch-works.md`: only two places. In section 9.5 the default thresholds read "25 merges, 40 settled tickets, or 5 events of one spike kind", a settled ticket is defined as a stem whose state goes to merged, already satisfied or rejected, counted once, and `retro.days` and `days.every` become `retro.settled` and `settled.every`. In the section 11 config table the `retro` row names `settled` instead of `days`.
- New test `tests/unit/test_retro_settled_trigger.py` pins the new branch with in-memory events and no journal.

Scope out: the checkpoint push and `clutch/checkpoint.py` (ticket `checkpoint-counts-settled`), `retro.merges`, `retro.spikes`, `clutch/timers.py`, the config schema version, and any config migration; the unknown-key refusal already names the stale `retro.days` key, and no host config in this repo sets it.

## Scope fence
- clutch/config.py
- clutch/retro.py
- clutch/serve.py
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_retro_settled_trigger.py
- tests/integration/test_retro.py
- tests/integration/test_config.py
- tests/integration/test_drain.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_retro_settled_trigger.py` shows `select_trigger` with default settings and `merged_count` 0 returning `"settled"` for a window holding `rejected` or `already_satisfied` transitions on 40 distinct stems, and `None`, not `"settled"`, for 39.
2. The same test shows that `merged`, `already_satisfied` and `rejected` each count; that a second settled transition of a stem already counted does not raise 39 stems to 40 (`None`, not `"settled"`); and that 40 stems whose transitions go to `abandoned` or `gate_failed` return `None`, not `"settled"`.
3. The same test shows that `inspect.signature(select_trigger)` has no `now` parameter, that a window whose `started_at` is 365 days before its last event and which holds no settled stem returns `None`, not `"elapsed"`, and that with `settled.enabled` false a window of 40 settled stems returns `None`.
4. `./dev.py test tests/integration/test_config.py` shows `retro: {days: {every: 2}}` refused with key `retro.days` and `unknown key` in the message, not accepted; `retro: {settled: {every: 2}}` parsing to `settled.every == 2`; the default `retro.settled.every == 40`; and `retro: {merges: {enabled: false}, settled: {enabled: false}, spikes: {enabled: false}}` refused with key `retro.enabled`.
5. `./dev.py test tests/integration/test_retro.py` shows the parametrized trigger test's `settled` case returning `None` at 39 settled stems and `"settled"` at 40, with no clock advance.
6. `grep -rn --include=*.py --include=*.md "RetroDays\|retro\.days\|days\.every" clutch docs/how-clutch-works.md` prints nothing, `grep -rn --include=*.py "RetroDays" tests` prints nothing, and `grep -n "timedelta\|\"elapsed\"" clutch/retro.py` prints nothing.
7. `grep -n "days" clutch/docs/host-contract.md` prints nothing, and `grep -n "7 days" docs/how-clutch-works.md` prints nothing.

## Verification
```
./dev.py test tests/unit/test_retro_settled_trigger.py tests/unit/test_phase_events.py tests/unit/test_retro_check_vocabulary.py tests/integration/test_retro.py tests/integration/test_config.py tests/integration/test_drain.py tests/integration/test_host_contract.py
```

## Definition of rejected
A branch is rejected if retro selection still reads the clock or takes a `now` argument, if `RetroDays` or `retro.days` survive under an alias or a second code path, if a config migration or schema bump is added, if the settled states are written out again instead of imported from `clutch.stats.SETTLED`, or if it changes `clutch/checkpoint.py`.

## Time budget
- expected: 30m
- stuck: 60m
