---
state: rejected
source: box:suggestion
priority: P0
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/tickets.py::lint_findings
- clutch/docs/host-authoring.md#What each section is for

## Goal / Why
Author-written tickets cite literal line numbers and literal current values (for example "about line 452" or "the pin is 1.1"). When a sibling ticket merges first and moves those lines or bumps the value, requisition review snags the ticket as a stale fact and parks it. `specs-json-reply-first-char-lint` was parked this way on 2026-11-16 after `rework-supervise-gate` bumped `rework.md`. A premise park holds the stem until someone hand-edits `ticket.md`, so the queue stalls. `clutch/docs/host-authoring.md` is the single authoring source that Author embeds, and it has no rule against line-number citations. After this change the guide states the rule and `clutch lint` refuses a line citation with a road to cite a symbol or heading instead.

## Scope in / Scope out
In `clutch/docs/host-authoring.md`, update only the `Scope in / Scope out` and `Acceptance criteria` bullets under "What each section is for". They gain two rules. First, cite code as `path::Name`, by heading, or by exact text, never by line number. Second, state a version or other changing value relative to main at the base commit (for example "the next minor above the version on main"), never as a literal current value.

In `clutch/tickets.py::lint_findings`, add one decidable authoring finding. It fires on a line citation in the `## Scope in / Scope out` or `## Acceptance criteria` text. A line citation is the word `line` or `lines` followed by digits (any case), or a file name with extension py, md, js, toml or json followed by a colon and digits. The finding's road says to cite the definition as `path::Name`, or the heading, or the exact text. The rule lives only in `lint_findings`, the authoring-lint seam. It must not be added to `_parse_ticket` or any code that merge admission, the mergequeue, drain, watcher or serve run on every parse. Other sections stay as they are.

Out: rewriting existing tickets that already cite lines; the supervising session fixes those as wording updates. Out: any check on literal version values, because lint cannot decide them. The guide rule covers those.

The new tests go in a new file and do not touch existing test files.

## Scope fence
- clutch/tickets.py
- clutch/docs/host-authoring.md
- tests/unit/test_ticket_lint_line_citations.py

## Acceptance criteria
1. `clutch/docs/host-authoring.md` contains a rule that tells authors to cite code by `path::Name`, heading or exact text and not by line number, and to state version values relative to main. `./dev.py test tests/unit/test_host_authoring.py` still exits 0.
2. In `tests/unit/test_ticket_lint_line_citations.py`, a ticket parsed with `tickets.parse_ticket` whose Scope in text is built in the test as the word `lines`, a space and a four-digit range yields exactly one finding from `tickets.lint_findings(ticket, root)`. An empty list is the wrong result.
3. A ticket whose Acceptance criteria item is built in the test as a `.py` path, a colon and a line number yields exactly one finding from `tickets.lint_findings`. An empty list is the wrong result.
4. The same ticket with the citation replaced by a `path::Name` reference yields `[]` from `tickets.lint_findings`, and so does a ticket whose text says `lines of code` with no digit. A non-empty list is the wrong result.
5. The finding text names `path::Name` as the replacement, checked in the test with `"path::Name" in` the finding's road or message text.
6. A ticket containing the citation still parses: `tickets.parse_ticket` returns a `Ticket` and does not raise `TicketInvalid`, so merge admission is unaffected. Raising is the wrong result.
7. `./dev.py test tests/integration/test_tickets.py tests/integration/test_lint_verb.py` exits 0, so existing lint behavior is unchanged.

## Verification
```
./dev.py test tests/unit/test_ticket_lint_line_citations.py tests/unit/test_host_authoring.py tests/integration/test_tickets.py tests/integration/test_lint_verb.py
```

## Definition of rejected
The rule runs in `_parse_ticket` or any parse path used by merge admission, so a ticket with a citation fails to parse. Or the lint refuses a ticket for text outside `## Scope in / Scope out` and `## Acceptance criteria`. Or it refuses a ticket that cites a symbol or heading with no line number. Or the guide gains a rule with no lint finding for line citations. Or the branch edits an existing ticket or an existing test file.

## Time budget
- expected: 30m
- stuck: 60m
