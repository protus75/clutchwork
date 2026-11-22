---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/scheduler.py::Scheduler.dispatch_next
- clutch/drain.py::write_queue
- clutch/drain.py::fill_slots
- clutch/tickets.py::fences_overlap
- clutch/observe.py::queue
- clutch/observe.py::snapshot
- clutch/help.py
- tests/unit/test_help.py::test_vocabularies_covered
- tests/unit/test_scheduler_parallel_fill.py
- tests/unit/test_scheduler_write_queue_seams.py
- docs/how-clutch-works.md#7.1

## Goal / Why
On 2026-11-22 serve ran with `scheduler.parallel.max_runs: 2` but kept one slot idle while four tickets showed `ready`. The cause was a fence overlap with a starvation barrier, fixed separately by `barrier-admits-disjoint`. Nothing on screen showed the idle slot or the reason. The owner had to ask a chat session, which read `engine.log` `dispatch_skip` lines and diffed the two scope fences by hand. Whenever dispatch has ready tickets and a free slot but starts nothing, the waiting tickets still read `ready`.

After this ticket, whenever the scheduler has a free slot and a ready ticket but dispatches nothing, the reason is written to `queue.json`. `view watch` and the extension's queued rows then show which ticket waits on what, for example `waits for a free slot: overlaps llm-request-subject`. A slot that sits idle for a reason is visible without anyone reading logs.

## Boundary contract
### queue.json view file
- disposition: extend
- owner: clutch/drain.py::write_queue
- consumers: clutch/observe.py `queue` (view watch text) and `snapshot` (extension rows)
- observable change: `write_queue` takes two optional positional arguments. `waiting` is a mapping of stem to the sorted list of in-flight or barrier stems whose fences overlap it. `hold` is `"max_unmerged"` or `None`. The JSON gains a `"waiting"` key only when `waiting` is non-empty and a `"hold"` key only when `hold` is not `None`. Otherwise the written object is byte-identical to today.
- compatibility: existing callers (`clutch/drain.py` single-flight drain, scheduler dispatch writes with nothing waiting) and every existing exact-equality assertion on `queue.json` content keep passing. Existing monkeypatches of `write_queue` take `*args`, so scheduler calls pass the new arguments positionally.
- acceptance: a dispatch pass with a free slot and an overlap-skipped ready ticket writes `waiting`; a pass that is stopped by `max_unmerged` while a ready ticket exists writes `hold`
- tests: tests/unit/test_slot_idle_reason.py
- post-merge source of truth: clutch/drain.py::write_queue

### Scheduler idle-pass write
- disposition: extend
- owner: clutch/scheduler.py::Scheduler.dispatch_next
- consumers: queue.json readers above
- observable change: on a pass that dispatches nothing while a slot is free and at least one ready ticket exists, the scheduler calls `write_queue` with the ready order and the current `waiting`/`hold`. It does so only when `(waiting, hold)` differs from the last value it wrote, so the 10-second poll does not rewrite the watched file each pass. Every dispatching pass writes as today, with the current `waiting`.
- compatibility: passes with no free slot write nothing, as today. Single-flight serve gets the `hold` reason too, because `max_unmerged` applies there as well.
- acceptance: two identical idle passes produce one write; a change in the waiting set produces a second write
- tests: tests/unit/test_slot_idle_reason.py
- post-merge source of truth: clutch/scheduler.py

### Queued row status vocabulary
- disposition: extend
- owner: clutch/observe.py (row status), clutch/help.py (help text)
- consumers: vscode-clutchwork queued rows (draws `status` text and looks up `help.status`; no JavaScript change), `view watch` text
- observable change: while an engine (drain or serve) holds the lock, a queued row that would read `ready` reads `waits for a free slot: overlaps <stems>` (status key `slot_overlap`) when its stem is in `waiting`, or `waits for merges: max_unmerged finished tickets wait to merge` (status key `merge_wait`) when `hold` is `max_unmerged`. `view watch` queue lines show the same text. When no engine holds the lock, `waiting` and `hold` are ignored, so stale reasons never show.
- compatibility: every other status is unchanged
- acceptance: rows change as described; with no engine running the rows still read `ready`
- tests: tests/unit/test_slot_idle_reason.py, tests/unit/test_help.py
- post-merge source of truth: clutch/observe.py

## Scope in / Scope out
Scope in:
- `clutch/drain.py::write_queue`: add the optional `waiting` and `hold` arguments as in the boundary contract.
- `clutch/scheduler.py::Scheduler.dispatch_next`:
  - When parallel is on, build `waiting` from the ready tickets `fill_slots` skipped this pass. For each one, use `fences_overlap` (same `shared_paths` and `rerun` arguments as `fill_slots`) to find the in-flight tickets and the barrier tickets it overlaps.
  - On the `completed_unmerged() >= max_unmerged` early return, set `hold` to `"max_unmerged"` when a slot is free and a ready ticket exists. Computing readiness for this may need the readiness filter to run before the early return. Keep that filter's logic unchanged.
  - Track the last written `(waiting, hold)` and skip a write when an idle pass's value is unchanged.
- `clutch/observe.py`: in `queue` and in `snapshot`'s `why_queued`, map waiting stems and the hold to the two new statuses, only while an engine holds the lock (`snapshot` already computes `engine`; `queue` gets the same fact from its caller).
- `clutch/help.py` `status` group: add `slot_overlap` ("The ticket is ready but its scope fence overlaps a running or barrier ticket, so it waits for a free slot.") and `merge_wait` ("The ticket is ready but dispatch waits until finished tickets merge (`scheduler.max_unmerged`)."), both linked to the existing `7.1 \`drain\`` section.
- `tests/unit/test_help.py::test_vocabularies_covered`: add both keys to the expected `status` set.
- `tests/unit/test_scheduler_parallel_fill.py`: update only assertions that a no-dispatch pass with a free slot and a skipped ready ticket writes nothing (`writes == []`), so they expect the one idle write. Change nothing else.
- New `tests/unit/test_slot_idle_reason.py` with the acceptance cases.
- `docs/how-clutch-works.md` section 7.1, item 3's `queue.json` sentence, and the `queue.json` row of the state-file table: say that `queue.json` also records why a free slot is idle (`waiting`, `hold`), and that watch and the extension show it as row status.

Scope out: `clutch view status` (`clutch/status.py` is a journal-only projection and `queue.json` is not journal), the extension JavaScript, the barrier rule itself (`barrier-admits-disjoint`), `WATCH_STATE_GLOB`, and any new state file.

## Scope fence
- clutch/drain.py
- clutch/scheduler.py
- clutch/observe.py
- clutch/help.py
- tests/unit/test_slot_idle_reason.py
- tests/unit/test_help.py
- tests/unit/test_scheduler_parallel_fill.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_slot_idle_reason.py` passes and covers:
   - `write_queue` with `waiting={"b": ["a"]}` and `hold=None` writes JSON whose `waiting` is `{"b": ["a"]}` and which has no `hold` key. With an empty `waiting` and `hold=None`, it writes exactly `{"at", "order", "runs_before"}`, with no `waiting` key, not `"waiting": {}`.
   - A parallel `Scheduler` with `max_runs=2`, one in-flight ticket fenced `src`, and a ready ticket fenced `src/x` dispatches nothing and writes `waiting == {"x-stem": ["in-flight-stem"]}`, not nothing. A second identical pass adds no write. Adding a second overlapping in-flight ticket produces a new write.
   - A scheduler stopped by `completed_unmerged() >= max_unmerged` with a ready ticket and a free slot writes `hold == "max_unmerged"`.
   - `observe` row status for a ready stem listed in `waiting`, with an engine lock held, is `waits for a free slot: overlaps <stem>` with help key `status.slot_overlap`, not `ready`. With no engine lock, the same `queue.json` gives `ready`.
2. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py` passes with `slot_overlap` and `merge_wait` in the covered `status` set.
3. `./dev.py test tests/unit/test_scheduler_parallel_fill.py tests/unit/test_scheduler_write_queue_seams.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_admission_running_set.py tests/integration/test_scheduler.py tests/integration/test_watch.py tests/integration/test_drain.py` passes, which shows existing `queue.json` shapes and the `write_queue` monkeypatches are unchanged.

## Verification
```
./dev.py test tests/unit/test_slot_idle_reason.py tests/unit/test_help.py tests/integration/test_help.py tests/unit/test_scheduler_parallel_fill.py tests/unit/test_scheduler_write_queue_seams.py tests/unit/test_admission_parallel_run_set.py tests/unit/test_admission_running_set.py tests/integration/test_scheduler.py tests/integration/test_watch.py tests/integration/test_drain.py
```

## Definition of rejected
- `queue.json` is rewritten on every idle poll even when the reason has not changed.
- A stale `waiting` or `hold` shows on rows while no engine holds the lock.
- The extension JavaScript computes or filters the reason instead of drawing the snapshot status.
- A new state file or a change to `WATCH_STATE_GLOB`.

## Time budget
- expected: 25m
- stuck: 50m
