---
state: confirmed
source: box:roadmap_row
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/roadmap.py::author_ahead
- clutch/roadmap.py::status
- clutch/roadmap.py::choose
- clutch/box.py::Box.enqueue
- clutch/caps.py::supervise_draws
- clutch/box.py::parse_record
- clutch/box.py::record_path
- docs/roadmap-driver-plan.md

## Goal / Why
A roadmap row whose `roadmap_row` message Author declined, or whose linked stem was rejected, is released without a person, as the plan's "nothing waits on a person" requires. Today `author_ahead` prints "reword the row's Content" and `Box.enqueue` returns the same declined message on every pass (rows 21, 22 and 29 were held on 2026-11-16 by declined-box-000559, declined-box-000572 and declined-box-000573; the rejected `test-gate-floors` is the other case).

After this change `author_ahead` re-files such a row itself, at most `caps.supervise` times per row. `clutch roadmap status` names a row whose re-files are spent, with its last reason. A re-file under a new stem also writes that stem into the row, so the gate's `roadmap merged --release R --priority P0 P1` check stops reporting the rejected stem (box-000582).

## Scope in / Scope out
Scope in, all in `clutch/roadmap.py`:
- Declined path. Replace the nested `declined` helper and its use in the ready loop of `author_ahead`. When `Box.enqueue` returns a message with a `declined` resolution, read the decision record with `parse_record` on `record_path(resolution.link)` and take the text after `Evidence: ` in its body (the text `clutch/author.py` writes). Then file a new `roadmap_row` message whose summary is the existing summary plus that evidence text plus the marker ` [re-file <n>]`. The marker guarantees a new signature, so `Box.enqueue` does not hand back the declined message. When the record file is missing or has no `Evidence: ` text, use the marker alone; the re-file still counts.
- Post-author call site. After `author_messages` runs, a declined message is only reported (a line naming the row and the decline). It is not re-filed in that pass; the next `author_ahead` call re-files it.
- Rejected path. Rows whose stem state is `rejected` are handled by a new path over `choose` output, covering both a linked row (dropped from `open_rows` at the `state != "rejected"` test) and an unlinked row that reaches the `give the row a new stem` wait. For such a row `author_ahead` picks the new stem `<base>-r<n>`, where `<base>` is the stem with any trailing `-r<digits>` removed and `<n>` is the re-file count plus one. It rewrites the row's stem cell to that stem, removes any leading `**Authored** (...). ` prefix from the Content cell so the row is unlinked, commits as `clutch(roadmap): refile <old stem> as <new stem>`, and then files the row through the same message path with the rejection reason and the marker ` [re-file <n>]` in the summary. The reason is the text of the stem's last `reject_verdict` journal event; read that event's owner for the field and use `rejected` when it has no text. The row must not be struck and no second row is appended.
- Cap. The re-file count of a row is the number of its `roadmap_row` box messages (origin `roadmap/<base>` or `roadmap/<base>-r<digits>`) whose summary carries a ` [re-file <n>]` marker. Every re-file, on the declined path and on the rejected path, files exactly one message with that marker, so each re-file raises the count by exactly one. A row with no box message at all (linked by hand, or unlinked and only in the journal) has count 0, so its first rejected re-file is `<base>-r1`, its second `<base>-r2`, and a stem is never picked twice. The cap is `checkout.config.caps.supervise`. No new cap and no new config key. At the cap, `author_ahead` files nothing for the row and prints a line naming the row and its last reason.
- `status`: add one line per row whose re-files are spent, naming the row and its last reason; none for a row with budget left. It reads the cap from `checkout.config.caps.supervise` and the box from `checkout.config.state_dir` and `checkout.fs`.
- Tests. Fix the two shared fixtures at their source so every importer keeps passing: in `tests/unit/test_roadmap_status.py` give `fixture` a `config` with `caps.supervise` and `state_dir` and an `fs`; in `tests/unit/test_roadmap_author.py` give `setup` a `config` with `caps.supervise`. In `tests/unit/test_roadmap_author.py` update the expectations that assert the old `declined -> ...` line (lines 115, 116 and 166) to the re-file outcome. Keep every other assertion in both files, including `len(lines) == 4` for a row with budget left. `tests/unit/test_roadmap_release_boundary.py` is not edited; it must keep passing.
- Docs. In `docs/how-clutch-works.md`, update only the Roadmap driver text that describes a declined or rejected row, if such text exists. If none exists, leave the file alone.

Scope out: the Author stage, `clutch/author.py`, `clutch/box.py`, the `roadmap_row` message shape, `box_policy`, supervisor rework, and the release gate command itself. A second problem goes to `clutch suggest`.

## Scope fence
- clutch/roadmap.py
- docs/how-clutch-works.md
- tests/unit/test_roadmap_author.py
- tests/unit/test_roadmap_status.py
- tests/unit/test_roadmap_refile.py
- tests/integration/test_roadmap_refile.py

## Acceptance criteria
1. After a declined `roadmap_row` message whose decision record is written under `tmp_path`, the next `author_ahead` call files a second message whose summary contains the record's `Evidence:` text. `tests/unit/test_roadmap_refile.py` asserts the box holds two messages for the row, not one declined message returned again.
2. With the decision record file missing, the next `author_ahead` call still files a second message, and its summary differs from the first. `tests/unit/test_roadmap_refile.py` asserts the box holds two messages, not one.
3. In the same pass that Author declines a message, `author_ahead` files no second message. `tests/unit/test_roadmap_refile.py` asserts `len(box.messages()) == 1` after that call.
4. For a row whose linked stem is rejected and which has exactly one prior `roadmap_row` message, `author_ahead` files a message under a stem `<base>-r1` that differs from the rejected one and rewrites the row's stem cell to it. `tests/unit/test_roadmap_refile.py` asserts the roadmap text no longer contains the rejected stem as the row's stem and the row has no leading `**Authored**` prefix.
5. The same holds for an unlinked row whose stem is rejected in the journal and which has zero prior box messages (the real `test-gate-floors` case): `tests/unit/test_roadmap_refile.py` asserts a `<base>-r1` message is filed, not a `give the row a new stem` wait line.
6. After `caps.supervise` re-files of one row, a further `author_ahead` call files no message. `tests/unit/test_roadmap_refile.py` asserts the box count stays unchanged, not that it grows by one.
7. `status` output contains a line naming a row whose re-files are spent and its last reason, and none for a row with budget left. `tests/unit/test_roadmap_refile.py` asserts both cases.
8. The output of `author_ahead` never contains "reword the row's Content". `tests/integration/test_roadmap_refile.py` asserts this against a real journal and box in a temporary checkout.
9. The existing roadmap tests pass: `./dev.py test tests/unit/test_roadmap_author.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_release_boundary.py` exits 0.
10. For a zero-message row whose `<base>-r1` is also rejected in the journal, the next `author_ahead` call files `<base>-r2`, never `<base>-r1` again, and with `caps.supervise = 2` exactly 2 re-files happen in total before a third call files nothing. `tests/unit/test_roadmap_refile.py` asserts the filed stems are `<base>-r1` then `<base>-r2` and the box holds 2 messages, not 3.

## Verification
```
./dev.py test tests/unit/test_roadmap_refile.py tests/integration/test_roadmap_refile.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_release_boundary.py tests/integration/test_roadmap_status.py
```

## Definition of rejected
The branch is thrown away if a declined or rejected row still needs a person to reword it, if re-files exceed `caps.supervise`, if a rejected stem still blocks the gate's `roadmap merged` check, or if a new cap, config key, or dual-path fallback is added.

## Time budget
- expected: 60m
- stuck: 120m
