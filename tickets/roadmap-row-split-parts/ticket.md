---
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Context
- clutch/author.py::AuthorReply
- clutch/author.py::AuthorGate
- clutch/author.py::author
- clutch/roadmap.py::_edit
- clutch/roadmap.py::link
- clutch/roadmap.py::choose
- clutch/roadmap.py::author_ahead
- tests/unit/test_author_roadmap_row.py

## On-demand
- clutch/specs/author.md
- tests/integration/test_author.py

## Goal / Why
A roadmap row that is too big for one ticket can be authored. Today `clutch/docs/host-authoring.md` tells Author to split work over 60m into more tickets, each its own stem. But `AuthorGate.check` in `clutch/author.py` refuses every stem other than the row's (`roadmap row requires stem <stem>`), and `AuthorReply` carries one `stem` and one `ticket`, so no split reply can pass. Row 21 (`test-fakes-and-conftest`) spent its re-files this way (declined-box-000639, declined-box-000644), and row 105 (P1) held the 0.3.0 gate until the hand split in 7379d55e.

After this ticket, for a `roadmap_row` message, Author may reply with the row's stem as the first ticket plus an optional list of further parts, each named `<row stem>-<suffix>`. Every part is validated, reviewed and committed like the first ticket. The roadmap link step writes every part into the row's `**Authored** (...)` prefix, which `roadmap.choose` already reads as splits, so the row is struck only when every part settles.

## Scope in / Scope out
In:
- `clutch/author.py`: `AuthorReply` gains `parts: list[AuthorPart]` (default empty; `AuthorPart` has `stem` and `ticket`, strict, extra forbidden). `AuthorGate.check` accepts a part stem only when the message carries a `roadmap_row` and the stem is `<row stem>-<suffix>` with a non-empty suffix. A non-empty `parts` on any other message class is a finding. Each part gets the same checks as the first ticket (stem rules, not existing, not in the journal, `validate_ticket`, row `kind` and `priority`). Duplicate stems in one reply are a finding. The requisition review runs for each ticket of the reply, and the reply passes only when every one approves. The commit step writes and commits every part, appends a `ticket_intake` signal per part with `part_of: <row stem>` in its body, and the Box resolves with the first ticket's stem as today.
- `clutch/roadmap.py`: `link` takes the part stems and `_edit` writes `tickets/<row.stem>/` followed by each part as `tickets/<part>/` in the one `**Authored** (...)` prefix. A new pure function `part_stems(events, stem) -> tuple[str, ...]` returns the `ticket` stems of `ticket_intake` signals whose `part_of` equals `stem`. In `author_ahead`, the part intakes are written by `author()` inside `author_messages`, so `author_ahead` must read the journal again after `author_messages` returns and pass `part_stems` of those fresh events to `link`; it must not reuse the `events` read before the call. A row with no parts is linked exactly as before.
- `clutch/specs/author.md`: the roadmap_row sentence (line 17) says that a row too big for one ticket is split by keeping the row's stem for the first part and naming the rest `<row stem>-<suffix>` in `parts`. The Output format line (line 68) also shows the optional `"parts": [{"stem": "<row stem>-<suffix>", "ticket": "..."}]` for roadmap_row requests. The exact sentence that `tests/integration/test_specs_json_reply_specs.py` asserts stays in that section unchanged. Bump `version` to the next minor above the version on main; update the pin in `tests/integration/test_author.py`, and add to its spec rule check a phrase from the new `parts` rule.
- `tests/unit/test_author_roadmap_row.py`: the one expectation that may change is the `roadmap row requires stem` finding in `test_gate_holds_roadmap_row_identity`, which keeps failing for an unrelated stem.
- New tests: `tests/unit/test_author_roadmap_parts.py`, `tests/unit/test_roadmap_split_link.py`, and `tests/integration/test_roadmap_split_author.py` (real git and journal, drives `author_ahead`; criterion 11). No existing roadmap integration test changes.

Out: the Box `Resolution` shape, `roadmap.choose`, `refile_row`, the refile/`-rN` logic (roadmap-named-stem-refile), the stale-write fix (roadmap-fresh-write), `clutch/docs/host-authoring.md`, and any non-roadmap Author path.

Simplest approach rejected: letting the gate accept any stem that starts with the row stem and leaving `AuthorReply` single-ticket. That passes the gate but can write only one ticket, so the other parts are never authored.

## Scope fence
- clutch/author.py
- clutch/roadmap.py
- clutch/specs/author.md
- tests/integration/test_author.py
- tests/integration/test_roadmap_split_author.py
- tests/unit/test_author_roadmap_row.py
- tests/unit/test_author_roadmap_parts.py
- tests/unit/test_roadmap_split_link.py

## Acceptance criteria
1. A gate test in `tests/unit/test_author_roadmap_parts.py` passes a roadmap_row reply with stem `<row stem>` and one part `<row stem>-b`, and the report verdict is `pass`, not `fail`.
2. A gate test in `tests/unit/test_author_roadmap_parts.py` shows a part named `other-b` fails with a `ticket_schema` finding, and a reply with `parts` on a non-roadmap message fails; the verdict is `fail`, not `pass`.
3. A test in `tests/unit/test_author_roadmap_parts.py` shows a part whose frontmatter `kind` or `priority` differs from the row fails with `roadmap row requires kind` or `priority`, and a reply with two parts of the same stem fails.
4. A commit test in `tests/unit/test_author_roadmap_parts.py` shows both tickets are committed and the journal holds a `ticket_intake` signal for the part with `part_of` equal to the row stem; the part is not left uncommitted.
5. `link(text, row, parts=("<stem>-b",))` in `tests/unit/test_roadmap_split_link.py` returns a row whose content starts `**Authored** (` and lists both `tickets/<stem>/` and `tickets/<stem>-b/`; with no parts the output is byte-identical to today's `link` output, not a changed prefix.
6. A test in `tests/unit/test_roadmap_split_link.py` runs `choose` on that linked row with the first ticket settled and the part not settled, and the row is not in `strike`; once both are settled it is.
7. `./dev.py test tests/integration/test_author.py` passes with the pin set to the bumped `clutch/specs/author.md` version, and the existing roadmap-row tests still pass.
8. A commit test in `tests/unit/test_author_roadmap_parts.py` uses a fake `review_ticket` that records the `stem` of each call and asserts calls for both `<row stem>` and `<row stem>-b`, and that the Box resolution link is the first ticket's stem, not the part's. In a second case the fake returns `snag` for the part only, and the test asserts that no ticket is committed and no `ticket_intake` signal is written for either stem, not just for the part.
9. A test in `tests/unit/test_roadmap_split_link.py` calls `part_stems(events, stem)` on in-memory events holding a `ticket_intake` for `<stem>-b` with `part_of: <stem>`, one for an unrelated stem, and one with a different `part_of`, and asserts the result is `("<stem>-b",)`, not a tuple that includes the other two.
10. The spec rule check in `tests/integration/test_author.py` asserts that `clutch/specs/author.md` contains the `"parts"` key in its Output format section and a phrase of the new split rule, and `./dev.py test tests/integration/test_specs_json_reply_specs.py` still passes.
11. A test in `tests/integration/test_roadmap_split_author.py` drives `author_ahead` with real git and journal. The journal holds no `<stem>-b` intake before `author_ahead` is called. A fake `author_messages` appends a `ticket_intake` signal for `<stem>-b` with `part_of: <stem>` to the journal while it resolves the Box message as `ticket`. The test asserts the written `docs/roadmap.md` row contains both `tickets/<stem>/` and `tickets/<stem>-b/`, not only `tickets/<stem>/`; an implementation that reuses the pre-call `events` fails it. A second case whose fake appends no part intake asserts the row's prefix lists only `tickets/<stem>/`, as today.

## Verification
```
./dev.py test tests/unit/test_author_roadmap_parts.py tests/unit/test_roadmap_split_link.py tests/unit/test_author_roadmap_row.py tests/integration/test_author.py tests/integration/test_roadmap_split_author.py tests/integration/test_specs_json_reply_specs.py
```

## Definition of rejected
The branch is rejected if a single-stem roadmap row reply or a non-roadmap Author reply behaves differently from today, if a part is accepted without the row-stem prefix, or if a part ticket is committed without being reviewed.

## Time budget
- expected: 45m
- stuck: 90m
- reason: the gate, commit and link edits share one reply schema, and splitting them would leave a reply shape that the link step cannot read
