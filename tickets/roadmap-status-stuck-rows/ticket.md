---
state: confirmed
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/roadmap.py::choose
- clutch/roadmap.py::status
- clutch/roadmap.py::merged
- tests/unit/test_roadmap_status.py
- tests/unit/test_roadmap_table.py
- tickets/decisions/declined-box-000569-a3ea4f91.md

## Goal / Why
`clutch roadmap status` prints a `waits:` line for every held row, so `next:` never hides a stuck row. Three holds get one today only after re-files are spent, or not at all. (1) A row whose latest `roadmap_row` Suggestion Box message was declined by Author. (2) A linked row whose journal state is `rejected`; it is now counted only as "1 blocked". (3) A linked row whose `tickets/<stem>/ticket.md` has frontmatter `state: draft` and no journal state. `clutch roadmap merged` reports a draft row as `is a draft`, not `is not in the journal`. At `30059a55` status printed `next: test-fakes-and-conftest, evidence-envelope` though both messages were declined. Without this the unattended driver cannot tell a held row from a row that is just not ready.

## Scope in / Scope out
Scope in, in `clutch/roadmap.py`:
- `choose` gains a keyword `drafts: frozenset[str] = frozenset()`, so existing callers (`clutch/acceptance.py`, `tests/integration/test_roadmap_table.py`, `tests/unit/test_roadmap_release_boundary.py`) stay valid with no edit. A linked or ticket-file row with journal state `rejected` yields `Wait(row, f"{row.stem} is rejected", "give the row a new stem")`. A linked row whose stem is in `drafts` and has no journal state yields `Wait(row, f"{row.stem} is still a draft", "confirm the draft with `clutch confirm`")`. Neither row counts in `open_rows`.
- A row is skipped (not in `waits`, `open`, or `ready`) only when one of its unfinished dependencies is open, linked, ready, waiting, or an unsettled journal stem.
- `status` and `merged` build `drafts` by reading each linked row's `tickets/<stem>/ticket.md` under `checkout.repo` and keeping stems whose frontmatter `state` is `draft` (via `split_frontmatter` in `clutch/tickets.py`). A missing file is not a draft.
- `status` prints `waits: row N stem: declined -- <reason>` for any row whose latest `roadmap_row` message has resolution kind `declined`, whatever `refile_count` is (reason from `decline_reason`, else `declined`). The existing `re-files spent` line stays for `refile_count >= caps.supervise`. A row already in `choice.waits` gets no second box-derived line.
- `merged` `report` says `is a draft` for a row in `drafts` with no journal state. `is not in the journal` stays for every other row with no state.
- Scope in for `docs/how-clutch-works.md`: update only the `roadmap status` and `roadmap merged` verb rows (the `roadmap status` row says what `waits:` lines list; the `roadmap merged` row gains the draft wording).
- Scope in for tests: `tests/unit/test_roadmap_table.py::test_choose_partitions_rows` now expects `reject` (Authored, state rejected) among `choice.waits` with `new stem` in its road; its `journal` reason check moves to the `blocked` wait found by stem, not by `waits[0]`, and the later `waits == ["blocked"]` expectation is updated to what the new rule produces. In `tests/unit/test_roadmap_status.py` the status fixture checkout gains `config.state_dir` and `fs`. `test_status_buckets` expects the `x-five` rejected wait, so 5 lines, and the existing h-eight assertion is found by stem, not by index. A new test there seeds a declined `roadmap_row` box message and checks its `waits:` line. All other new tests go in the new `tests/unit/test_roadmap_stuck_rows.py`.
- Scope out: `Box.enqueue`, `author_ahead`, refile logic, and the `roadmap_gate` result. No credential wait: no row needs a credential this machine lacks.

## Scope fence
- clutch/roadmap.py
- docs/how-clutch-works.md
- tests/unit/test_roadmap_table.py
- tests/unit/test_roadmap_status.py
- tests/unit/test_roadmap_stuck_rows.py

## Acceptance criteria
1. `choose` on a linked row with state `rejected` returns it in `choice.waits` with `rejected` in the reason and `new stem` in the road, and not in `choice.open`; checked by `./dev.py test tests/unit/test_roadmap_stuck_rows.py::test_rejected_linked_row_waits`, which rules out `choice.waits == ()` and `choice.open == 1`.
2. `choose` with `drafts={"d"}` on linked row `d` with no journal state returns a wait containing `still a draft`; with `drafts` omitted the same row returns no wait; checked by `tests/unit/test_roadmap_stuck_rows.py::test_draft_linked_row_waits`.
3. `status` prints `waits: row 3 a-row: declined` for a row whose only message is declined with zero re-files, and prints `next:` without that row; checked by `tests/unit/test_roadmap_status.py::test_status_declined_row_waits`, which rules out a status with no `waits:` line for it.
4. `status` prints exactly one `waits:` line for a rejected linked row that also has spent re-files, not two; checked by `tests/unit/test_roadmap_stuck_rows.py::test_status_rejected_row_single_wait`.
5. `merged` reports `row 2 d-row is a draft` for a draft ticket file with no journal state and `is not in the journal` for a row with no ticket file; checked by `tests/unit/test_roadmap_stuck_rows.py::test_merged_reports_draft`, which rules out `is not in the journal` for the draft.
6. Class prevention: every non-struck row not in strikes, links, open, ready or waits has at least one unfinished dependency that is open, linked, ready, waiting, or an unsettled journal stem; checked by `tests/unit/test_roadmap_stuck_rows.py::test_skipped_rows_have_visible_blocker` over a fixture holding a rejected linked row, a declined row, a draft linked row, and a dependent of each.
7. The existing roadmap tests pass with the updated expectations: `./dev.py test tests/unit/test_roadmap_table.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_release_boundary.py tests/integration/test_roadmap_table.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_stuck_rows.py tests/unit/test_roadmap_table.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_release_boundary.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
The branch is rejected if status still hides a declined, rejected, or draft row from `waits:`, if `choose` changes its result for existing callers that pass no `drafts`, or if `merged` still reports a draft as not in the journal.

## Time budget
- expected: 40m
- stuck: 90m
