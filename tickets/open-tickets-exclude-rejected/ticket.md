---
state: confirmed
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/author.py::list_open_tickets
- clutch/triage.py
- clutch/status.py::SETTLED
- clutch/tickets.py::split_frontmatter
- tests/integration/test_author.py::test_list_open_tickets_requires_disk_commit_and_not_merged

## Goal / Why
Triage and Author see only tickets that can still be built, and a message can no longer be tombstoned against a rejected ticket. Today `list_open_tickets` lists every committed `tickets/<stem>/ticket.md` whose last journal state is not `merged`. That includes stems whose ticket says `state: rejected` and stems whose journal state is `rejected` or `already_satisfied`. The `open_tickets` block in the triage prompt is therefore full of closed work. The triage tombstone check accepts any committed `ticket.md` as a link. A message tombstoned against a rejected stem is closed for good and never becomes a ticket. `tombstone-box-000292-782578ef` and `tombstone-box-000352-17213bc9` already point at rejected stems. One shared predicate decides whether a stem is rejected, so the listing and the tombstone check cannot drift apart.

## Scope in / Scope out
In `clutch/author.py` add a pure helper `ticket_state(text: str) -> str | None`. It returns the `state` value from the ticket's frontmatter, built on `split_frontmatter`. It returns `None` for text with no frontmatter or no `state` key, and never raises on invalid YAML. Add a second helper `is_rejected(checkout, stem)` that returns true when the last journal state of the stem is `rejected`, or the committed `ticket.md` frontmatter state is `rejected`.

`list_open_tickets` skips a stem when its journal state is in `SETTLED` (import it from `clutch.status`) or when `is_rejected` is true. A stem with no frontmatter and no journal state stays listed, which keeps the existing test passing.

In `clutch/triage.py` the tombstone link check treats a link whose stem `is_rejected` as unresolvable. The existing fallback then turns the reply into `declined` with the evidence `unresolvable link: <link>`. A link in `merged`, or a stem whose journal state is `already_satisfied`, stays valid. A link that resolves through a committed decision record stays valid.

Out of scope: existing registry records that already point at rejected stems, the triage spec text, the listing format, and any change to `merged` handling.

Class prevention: both sites call the one `is_rejected` predicate, so a future closed-state change is a single edit.

## Scope fence
- clutch/author.py
- clutch/triage.py
- tests/unit/test_author_ticket_state.py
- tests/unit/test_triage_tombstone_rejected.py
- tests/integration/test_open_tickets_closed.py

## Acceptance criteria
1. `ticket_state("---\nstate: rejected\npriority: P1\n---\n\n## Goal / Why\nx\n")` returns `"rejected"`, not `None`; `ticket_state("## Goal / Why\nx\n")` returns `None` and `ticket_state("---\n: : [\n---\nbody")` returns `None` without raising; checked by `./dev.py test tests/unit/test_author_ticket_state.py`.
2. With committed tickets `live` (`state: confirmed`), `rej` (`state: rejected` in its frontmatter), `jrej` (journal state `rejected`), `sat` (journal state `already_satisfied`) and `done` (journal state `merged`), `list_open_tickets` returns exactly the single line for `live`; the output does not contain `rej:`, `jrej:`, `sat:` or `done:`; checked by `./dev.py test tests/integration/test_open_tickets_closed.py`.
3. A triage reply `verdict: tombstone` with `link: rej` (a committed ticket whose frontmatter state is `rejected`) ends as a `declined` resolution whose evidence contains `unresolvable link: rej`, and the box message is not resolved with kind `tombstone`; checked by `./dev.py test tests/integration/test_open_tickets_closed.py`.
4. A tombstone reply whose link is a committed ticket with `state: confirmed` still resolves with kind `tombstone`, and one whose link is in the merged list still resolves with kind `tombstone`; checked by `./dev.py test tests/integration/test_open_tickets_closed.py`.
5. The existing `test_list_open_tickets_requires_disk_commit_and_not_merged` still passes unchanged; checked by `./dev.py test tests/integration/test_author.py`.
6. Through a fake checkout built from the `SimpleNamespace` git and journal fakes used in `tests/unit/test_author.py`, `is_rejected` returns true for a stem with journal state `rejected` and for a stem whose committed frontmatter says `state: rejected`, and false for a `state: confirmed` stem and for an `already_satisfied` stem; `list_open_tickets` over the same fake returns only the line for the live stem and none for the rejected, frontmatter-rejected and `already_satisfied` stems; checked by `./dev.py test tests/unit/test_author_ticket_state.py`.
7. A fenced `tests/unit/test_triage_tombstone_rejected.py` drives the triage tombstone branch with fakes (monkeypatched `is_rejected` and the committed-ticket lookup, fake box and driver): a link whose `is_rejected` is true ends as `declined` with evidence `unresolvable link: <link>`, not as `tombstone`, and a link whose `is_rejected` is false still resolves as `tombstone`; checked by `./dev.py test tests/unit/test_triage_tombstone_rejected.py`.

## Verification
```
./dev.py test tests/unit/test_author_ticket_state.py tests/unit/test_triage_tombstone_rejected.py tests/integration/test_open_tickets_closed.py tests/integration/test_author.py tests/integration/test_triage.py
```

## Definition of rejected
A branch where `list_open_tickets` still lists a rejected or already_satisfied stem, or where a tombstone against a rejected stem still resolves as `tombstone`. A branch that implements the two checks as separate copies of the rejected test instead of one shared predicate. A branch that stops a tombstone against a `merged` stem.

## Time budget
- expected: 30m
- stuck: 75m
