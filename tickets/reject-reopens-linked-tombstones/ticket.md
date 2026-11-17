---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Context
- clutch/runner.py::reject_ticket
- clutch/runner.py::_dead_dependents
- clutch/box.py::Box.resolve
- clutch/box.py::Box.record_verdict
- tests/unit/test_runner_dead_dependents.py

## Goal / Why
When a stem is rejected, every Suggestion Box message whose tombstone resolution links to that stem is pending again for triage, and the reopening is journaled once per message. Today a tombstone closes a message because an open ticket covers its problem. If that ticket is rejected, the message stays closed and the problem is tracked nowhere. `tombstone-box-000292-782578ef` (link `diagnose-spec-reachable-road-rule`) and `tombstone-box-000352-17213bc9` were made on 2026-11-09 against drafts that were rejected hours later, so both are orphaned. The existing `tombstone_auto_reopened` path in `clutch/box.py` fires only when the same signature is reported again, never when the linked stem dies.

The reopen runs on every `reject_ticket` call, including a call on an already-rejected stem. Re-running `clutch reject <stem>` on a stem that is already rejected therefore releases the two existing orphans; no separate sweep is needed.

## Scope in / Scope out
Scope in:
- `clutch/box.py`: add `Box.reopen_tombstone(id)`, which writes the message back with `status="pending"`, `resolution=None`, `verdict=None`, `reopen=True`, as `record_recurrence` does for a reopen.
- `clutch/runner.py`: add `_reopen_tombstones(dead, checkout)` and call it in `reject_ticket` next to `_dead_dependents`, on every call. It builds the box the way `_dead_dependents` does. For each message whose `resolution.kind == "tombstone"` and `resolution.link == dead`, it calls `Box.reopen_tombstone`, then appends one `SIGNAL` event `{"signal": "tombstone_reopened_by_reject", "box_id": <id>, "link": dead}` with `ticket=dead` and key `tombstone-reject-reopen/<id>/<dead>`, only if no event with that key exists. A message already pending is not touched, so a second call journals nothing new.
- `tests/unit/test_runner_dead_dependents.py`: its fake box is a `SimpleNamespace` with only `enqueue`; add `messages=lambda: []` so the new call finds nothing. No other expectation in the file changes.
- `docs/how-clutch-works.md`: update only the sentence or bullet describing what reject does to dependents, to say it also reopens tombstoned box messages linked to the rejected stem.
- A new test file `tests/unit/test_runner_reopen_tombstones.py`.

Scope out: the `tickets/decisions/tombstone-*.md` records are left in place; the decline/tombstone decision-record format and `reopen_after_days` are unchanged; `declined` resolutions are not reopened; no new verb or flag; settled (merged) stems do not trigger a reopen.

## Scope fence
- clutch/runner.py
- clutch/box.py
- tests/unit/test_runner_reopen_tombstones.py
- tests/unit/test_runner_dead_dependents.py
- docs/how-clutch-works.md

## Acceptance criteria
1. After `reject_ticket("X", checkout)` with a resolved message whose tombstone resolution links to `X`, `Box.get(id)` shows `status == "pending"`, `resolution is None`, `reopen is True`; it does not stay `resolved`. Checked by `./dev.py test tests/unit/test_runner_reopen_tombstones.py`.
2. A message tombstoned to a different stem `Y`, and a message with a `declined` resolution whose link is `X`, both stay `resolved` after `reject_ticket("X", ...)`. Checked by `./dev.py test tests/unit/test_runner_reopen_tombstones.py`.
3. The journal holds exactly one `tombstone_reopened_by_reject` signal per reopened message, and a second `reject_ticket("X", ...)` on the already-rejected stem leaves the count at one, not two. Checked by `./dev.py test tests/unit/test_runner_reopen_tombstones.py`.
4. A message tombstoned to `X` before `X` was already rejected (journal last state `rejected`) is reopened by a later `reject_ticket("X", ...)` call, which covers the two existing orphans. Checked by `./dev.py test tests/unit/test_runner_reopen_tombstones.py`.
5. The existing dead-dependent behavior is unchanged: `./dev.py test tests/unit/test_runner_dead_dependents.py` passes.
6. `docs/how-clutch-works.md` states that reject reopens linked tombstoned messages. Checked by `grep -n "tombstone" docs/how-clutch-works.md`, which must show the reject sentence.

## Verification
```
./dev.py test tests/unit/test_runner_reopen_tombstones.py tests/unit/test_runner_dead_dependents.py
```

## Definition of rejected
The branch is thrown away if it reopens tombstones for any stem other than the rejected one, reopens `declined` messages, journals a second signal on a repeat reject, or adds a new verb, flag, or sweep path.

## Time budget
- expected: 40m
- stuck: 80m
