---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/observe.py::commits
- clutch/observe.py::snapshot
- vscode-clutchwork/media/view.js
- tests/unit/test_snapshot_merged_cap.py
- tests/unit/test_menu_admission.py::fake_snapshot_inputs
- tests/unit/test_menu_admission.py::dispatch_ticket

## Goal / Why
Hovering a merged row in the Tickets view shows only the generic help text for the merged status, so finding out what a merged ticket changed means opening Details or git. After this ticket, hovering a merged row shows the full message of the commit that merged that ticket into main (subject and body), followed by the status help. A merged row with no commit on main, and every non-merged row, keeps today's hover text.

## Boundary contract
### Snapshot merged commit and row hover
- disposition: extend
- owner: clutch/observe.py (`commits` and `snapshot`)
- consumers: vscode-clutchwork/media/view.js row `title`
- observable change: each `commits()` entry gains `message`, the full commit message (`%s`, then a blank line and `%b` when the body is non-empty, trailing whitespace stripped); every snapshot ticket row gains `tooltip`: for a merged row whose `commit` is set, `commit["message"] + "\n\n" + help[row["help"]["status"]]["text"]`, otherwise `help[row["help"]["status"]]["text"]`
- compatibility: existing `commits()` keys (`sha`, `short`, `author`, `date`, `subject`) and every existing row key are unchanged; Details still shows the subject
- acceptance: criteria 1 and 2
- tests: tests/unit/test_observe_commit_message.py and tests/unit/test_snapshot_merged_tooltip.py
- post-merge source of truth: clutch/observe.py

## Scope in / Scope out
Scope in:
- clutch/observe.py `commits`: read `git log --format=%H%x1f%h%x1f%an%x1f%aI%x1f%s%x1f%b%x1e main`, split records on `\x1e` (a body has newlines, so `splitlines` no longer works), and add `message`.
- clutch/observe.py `snapshot`: set `tooltip` on every ticket row as stated in the boundary contract.
- vscode-clutchwork/media/view.js: ticket rows set `row.title = r.tooltip` instead of `snap.help[r.help.status].text`; nothing else changes.
- tests/unit/test_snapshot_merged_cap.py and tests/integration/test_watch.py: their `commits` stand-ins reach the new `message` read; add a `"message"` key to each stand-in dict and nothing else.
- New tests/unit/test_observe_commit_message.py: monkeypatch `observe.git_output` with fake log bytes holding one commit with a multi-line body and one subject-only commit.
- New tests/unit/test_snapshot_merged_tooltip.py: build a snapshot with the stand-ins `test_snapshot_merged_cap.py` uses (imported `dispatch_ticket` and `fake_snapshot_inputs`), one merged row with a commit, one merged row without, and one queued row.
Scope out:
- The Details view, box rows, the steps tree and the merge commit format.

## Scope fence
- clutch/observe.py
- vscode-clutchwork/media/view.js
- tests/unit/test_snapshot_merged_cap.py
- tests/integration/test_watch.py
- tests/unit/test_observe_commit_message.py
- tests/unit/test_snapshot_merged_tooltip.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_observe_commit_message.py` proves a commit with a two-line body yields `message == "subject\n\nline one\nline two"` (not the subject alone, and not split into extra commits), and a subject-only commit yields `message == "subject"` with no trailing blank lines.
2. `./dev.py test tests/unit/test_snapshot_merged_tooltip.py` proves the merged row with a commit has `tooltip` starting with its commit `message` and ending with the merged status help text, while the merged row without a commit and the queued row have `tooltip` equal to their status help text alone.
3. `./dev.py test tests/unit/test_snapshot_merged_cap.py tests/integration/test_watch.py` passes with the `message` key added to their stand-ins.

## Verification
```
./dev.py test tests/unit/test_observe_commit_message.py tests/unit/test_snapshot_merged_tooltip.py tests/unit/test_snapshot_merged_cap.py tests/integration/test_watch.py tests/unit/test_help_snapshot.py
```

## Definition of rejected
JavaScript composes the hover text or reads the commit itself, non-merged rows change hover text, or files outside the fence change.

## Time budget
- expected: 12m
- stuck: 24m
