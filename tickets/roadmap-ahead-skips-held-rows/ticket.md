---
state: rejected
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/roadmap.py::choose
- clutch/roadmap.py::author_ahead
- clutch/roadmap.py::draft_stems
- clutch/status.py::reject_queue
- tests/unit/test_roadmap_author.py

## Goal / Why
On 2026-11-17 the drain stopped with "quiescent: nothing eligible" while `clutch roadmap status` listed 14 ready 0.3.0 rows. The two rows filling the AHEAD=2 window were both held: `supervise-every-route` (in the Reject queue, diagnosis cap spent) and `test-gate-floors-measured` (an unconfirmed draft). `author_ahead` calls `choose` without `drafts=`, so a draft row counts as open. `choose` turns a row into a wait only when its state is `rejected`, so a Reject-queue row also counts as open. `opened = choice.open` then blocks both the refile loop and the authoring loop.

After this change a row that is waiting on a person's verdict (an unconfirmed draft, or a stem in the Reject queue) is reported under `waits:` and does not count toward the window. `author_ahead` keeps filing ready rows past held ones, so the drain does not quiesce behind them. The ahead window exists to avoid authoring too early, not to stall behind held rows (docs/roadmap-driver-plan.md, the `--ahead` paragraph).

## Scope in / Scope out
Scope in:
- `choose` gains a keyword `held: frozenset[str] = frozenset()` of stems in the Reject queue. A linked or file-backed row whose stem is in `held` and has no `rejected` state becomes a `Wait` with reason `<stem> is in the Reject queue` and a road that names the verb that releases it (`clutch reject` family verbs as they exist in `clutch/__main__.py`; read that file for the exact verb). It is not added to `open_rows`.
- `author_ahead` passes `drafts=draft_stems(repo, rows)` and `held=frozenset(reject_queue(events))` to `choose`. Its existing waits output loop already prints the new waits.
- `docs/how-clutch-works.md`: update only the sentence that describes which rows count toward the author-ahead window, if one exists.
- New unit test file `tests/unit/test_roadmap_ahead_held.py`; it imports the `setup`, `put`, `r` and `run` helpers from `tests/unit/test_roadmap_author.py` and builds Reject-queue events in `checkout.journal`.

Scope out: `status`, `merged`, refile logic, the plan, the table format, and any new config knob. Existing `choose` callers keep working because `held` defaults to empty.

## Scope fence
- clutch/roadmap.py
- docs/how-clutch-works.md
- tests/unit/test_roadmap_ahead_held.py

## Acceptance criteria
1. With ahead=2, one draft row (ticket.md with `state: draft` under `tmp_path`), one Reject-queue row (journal events from `reject_queue`'s own shape), and two ready rows, `test_ready_rows_filed_past_held_rows` in `tests/unit/test_roadmap_ahead_held.py` asserts that both ready rows are filed and the returned lines end with `roadmap: 2 of 2 rows open`, not `roadmap: 0 of 2 rows open` or a count that includes the held rows.
2. In the same test, `test_held_rows_listed_under_waits` asserts that the returned lines contain a `waits:` line for the draft row (`is still a draft`) and one for the Reject-queue row (`is in the Reject queue`), and that neither is counted as open.
3. `test_choose_held_default_unchanged` calls `roadmap.choose` without `held` on a linked row whose stem is in the Reject queue and asserts it is still in `open`, so the default keeps the old behavior for existing callers.
4. `./dev.py test tests/unit/test_roadmap_author.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_stuck_rows.py` passes unchanged.

## Verification
```
./dev.py test tests/unit/test_roadmap_ahead_held.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_stuck_rows.py tests/unit/test_roadmap_table.py
```

## Definition of rejected
A held row still counts toward the window in `author_ahead`; the change adds a config knob or a second code path beside `choose`; or an existing roadmap test is edited to pass.

## Time budget
- expected: 25m
- stuck: 60m
