---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/serve.py::Serve.check_upgrade
- clutch/serve.py::Serve.select
- clutch/observe.py::running_stems
- clutch/observe.py::queue
- clutch/observe.py::STATUS_KEYS
- clutch/events.py
- clutch/journal.py
- tests/unit/test_snapshot_merged_tooltip.py
- tests/unit/test_view_events.py
- tests/integration/test_serve_upgrade.py
- docs/how-clutch-works.md#7.2

## Goal / Why
When a merge changes the engine's own `clutch/` tree, serve sets `Serve.upgrade` and `select()` refuses every ticket not already running until serve is idle and re-execs on the new code. Nothing records or shows that hold. On 2026-11-22 remove-help-before-after merged a `clutch/help.py` change at 13:38:37 UTC. Serve then ran only io-helpers-daemon for more than ten minutes, while the extension, `view watch` and `view status` showed retro-check-once and host-prompts as `ready`. The engine log went silent, and diagnosing that "two jobs aren't running" meant reading serve's source.

When done, the hold is a journaled fact and every operator surface says so:
- The journal carries a `serve_upgrade_pending` signal from the moment serve detects the changed tree.
- Snapshot rows for queued tickets and `view watch` queue lines say they are held for the engine upgrade, not `ready`.
- `view events` prints one line when the hold starts, so a supervising loop sees it.

## Boundary contract
### Journal signal vocabulary
- disposition: extend
- owner: clutch/journal.py
- consumers: clutch/serve.py (writer), clutch/observe.py and clutch/events.py (readers), clutch/audit.py closed-set validation
- observable change: new signal `serve_upgrade_pending` with body `{"signal": "serve_upgrade_pending", "clutch": <new clutch tree id>}`, appended once each time `Serve.check_upgrade` first sets `self.upgrade` (it is set at most once per serve process, so one signal per process)
- compatibility: additive; existing journals stay valid
- acceptance: criteria 1 and 2
- tests: tests/integration/test_serve_upgrade_pending.py, tests/integration/test_closed_sets.py
- post-merge source of truth: clutch/journal.py `SIGNAL_NAMES`

### Snapshot and watch status vocabulary
- disposition: extend
- owner: clutch/observe.py
- consumers: vscode-clutchwork (draws `status` and the `help.status` topic, no logic change), `view watch` queue lines
- observable change: new status key `upgrade_hold`. A ticket is in upgrade hold when the journal's latest `serve_upgrade_pending` signal is at or after the live lock holder's start (`lock_holder(state)`, the same freshness rule as `running_stems`) and no `serve_handoff` follows it. While that holds, each queued snapshot row whose status key would be `ready`, `after` or `retry_pending` gets status text `held: engine upgrade pending; starts after serve restarts on new code` and status key `upgrade_hold`, and each `view watch` queue line whose why would be `ready, not run yet` or `retry pending (...)` carries the same text in its place. Operator holds (including keep-or-kill), `held until the ticket changes` and `waits on ...` keep their reasons. With no live lock holder, or once a `serve_handoff` follows the signal, rows render exactly as before.
- compatibility: additive status key; rows outside the hold are unchanged
- acceptance: criteria 3, 4 and 5
- tests: tests/unit/test_observe_upgrade_hold.py, tests/unit/test_help_snapshot.py, tests/unit/test_help.py
- post-merge source of truth: clutch/observe.py `STATUS_KEYS`; help text in clutch/help.py

### view events kinds
- disposition: extend
- owner: clutch/events.py
- consumers: `clutch view events` readers, the drain-loop supervising prompt
- observable change: new kind `upgrade`. For each new `serve_upgrade_pending` journal signal, `changes` emits `upgrade - engine code changed; no new tickets start until running work finishes and serve restarts -- clutch view watch`
- compatibility: additive. The engine-log kinds `changes` selects stay exactly `engine_start`, `engine_stop` and `engine_lost`.
- acceptance: criterion 6
- tests: tests/unit/test_events_upgrade_pending.py, tests/unit/test_view_events.py
- post-merge source of truth: clutch/events.py `EVENTS`

## Scope in / Scope out
Scope in:
- clutch/journal.py: add `serve_upgrade_pending` to `SIGNAL_NAMES`, next to `serve_handoff`.
- clutch/serve.py `check_upgrade`: when it sets `self.upgrade`, append the `serve_upgrade_pending` signal through `self.checkout.journal`. Dispatch and handoff behavior stay unchanged.
- clutch/observe.py: add `upgrade_hold` to `STATUS_KEYS`, plus one predicate implementing the freshness rule above. Apply it to queued snapshot rows (the `why_queued` path) and to `queue()` lines used by `view watch`.
- clutch/events.py: add `upgrade` to `EVENTS` and emit its line from the journal signal. Keep the engine-log kind selection equal to `engine_start`, `engine_stop` and `engine_lost`, replacing the `EVENTS[7:]` slice with an explicit selection if the slice would shift.
- clutch/help.py: add the `status.upgrade_hold` entry (what it is and that it clears when serve re-execs) in the status group.
- tests/unit/test_help_snapshot.py, tests/unit/test_help.py: add `upgrade_hold` to their pinned status sets.
- tests/integration/test_closed_sets.py: add `serve_upgrade_pending` to the pinned `SIGNAL_NAMES` set.
- tests/unit/test_view_events.py: update the pinned `EVENTS` tuple.
- Create tests/unit/test_observe_upgrade_hold.py: snapshot rows and `observe.queue` lines under, before, after and without the hold (criteria 3 to 5), using the monkeypatched-snapshot pattern of tests/unit/test_snapshot_merged_tooltip.py.
- Create tests/unit/test_events_upgrade_pending.py: the `view events` upgrade line (criterion 6).
- Create tests/integration/test_serve_upgrade_pending.py: serve journals one `serve_upgrade_pending` signal after a `clutch/` merge (criterion 1), reusing the rig helpers tests/integration/test_serve_upgrade.py imports from tests/integration/serve_rig.py without editing that rig.
- docs/how-clutch-works.md section 7.2: in the self-upgrade paragraph ("A git-checkout engine records its `clutch` tree..."), state that a detected change journals `serve_upgrade_pending`, and that queued rows show the upgrade hold until `serve_handoff`.

Scope out:
- No change to when serve stops admitting or re-execs.
- Retro-pending and stop-requested holds in `select()` hide the same way. File that to the Suggestion Box; do not fold it in here.
- `view status` (`clutch/status.py`) and the `engine drain` self-upgrade path are unchanged.
- No JavaScript change. The extension already draws `status` and its help topic.

## Scope fence
- clutch/journal.py
- clutch/serve.py
- clutch/observe.py
- clutch/events.py
- clutch/help.py
- docs/how-clutch-works.md
- tests/integration/test_closed_sets.py
- tests/unit/test_help_snapshot.py
- tests/unit/test_help.py
- tests/unit/test_view_events.py
- tests/unit/test_observe_upgrade_hold.py
- tests/unit/test_events_upgrade_pending.py
- tests/integration/test_serve_upgrade_pending.py

## Acceptance criteria
1. After a merge changes the engine checkout's `clutch` tree, serve's journal holds exactly one `serve_upgrade_pending` signal whose `clutch` equals the new `HEAD:clutch` tree. It is appended before the `serve_handoff`, not zero or two signals. Checked by `tests/integration/test_serve_upgrade_pending.py` in `./dev.py test tests/integration/test_serve_upgrade_pending.py`.
2. `journal.SIGNAL_NAMES` contains `serve_upgrade_pending`, and the pinned set in `tests/integration/test_closed_sets.py` matches it, checked by `./dev.py test tests/integration/test_closed_sets.py`.
3. With a live lock holder that started before a `serve_upgrade_pending` signal and no later `serve_handoff`, a confirmed queued ticket's snapshot row has status key `upgrade_hold` and status text `held: engine upgrade pending; starts after serve restarts on new code`, not `ready`. Under the same hold, a ticket whose dependency is unsettled keeps its `waits_on` status, and an operator-held ticket keeps its `held_operator` status. Checked by `tests/unit/test_observe_upgrade_hold.py`.
4. The same ticket's row shows `ready` in each of three cases, so stale signals never hold rows: the signal predates the lock holder's start, a `serve_handoff` follows the signal, or no lock holder is live. Checked by `tests/unit/test_observe_upgrade_hold.py`.
5. Under the hold, `observe.queue` returns the upgrade-hold text as the why for that ticket. `STATUS_KEYS` includes `upgrade_hold`, and `clutch/help.py` has a `status.upgrade_hold` topic. Checked by `tests/unit/test_observe_upgrade_hold.py`, `tests/unit/test_help_snapshot.py` and `tests/unit/test_help.py`.
6. `events.changes` emits exactly one `upgrade - engine code changed; no new tickets start until running work finishes and serve restarts -- clutch view watch` line for a newly appended `serve_upgrade_pending` signal and none on the silent baseline. Engine-log rows of kinds other than `engine_start`, `engine_stop` and `engine_lost` are still not emitted. Checked by `tests/unit/test_events_upgrade_pending.py` and `tests/unit/test_view_events.py`.

## Verification
```
./dev.py test tests/unit/test_observe_upgrade_hold.py tests/unit/test_events_upgrade_pending.py tests/unit/test_view_events.py tests/unit/test_help_snapshot.py tests/unit/test_help.py
./dev.py test tests/integration/test_serve_upgrade_pending.py tests/integration/test_closed_sets.py tests/integration/test_serve_upgrade.py tests/integration/test_help.py
```

## Definition of rejected
- Serve's admission or re-exec behavior changes: a ticket starts during the hold, or the handoff timing differs.
- The hold is kept only in memory or in the engine log, so the snapshot cannot derive it from the journal and lock.
- Rows show the upgrade hold after a `serve_handoff`, or when no engine holds the lock.
- JavaScript in `vscode-clutchwork/` changes.

## Time budget
- expected: 25m
- stuck: 50m
