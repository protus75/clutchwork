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
- clutch/tickets.py::lint_findings
- clutch/tickets.py::_parse_ticket
- clutch/docs/host-authoring.md#What each section is for
- tests/unit/test_ticket_lint_rules.py
- tests/integration/test_lint_guide_parity.py

## Goal / Why
An open ticket with an oversized or inconsistent `## Time budget` is refused by `clutch lint` and by intake, so the roadmap driver's tickets are split instead of given larger budgets. Today only `stuck > expected` and the `drain.max_ticket_minutes` ceiling are checked, so a 120m ticket with `stuck` 125m passes. After this change an open ticket is refused when `expected` is over 60 minutes (road: split it into more tickets, each its own stem), when `stuck` is not exactly twice `expected`, or when `expected` is over 30 minutes and the section has no one-line reason saying why it is not split. The reason is an optional third bullet `- reason: <text>`. Settled and rejected tickets are exempt, as they are from the evidence rule. Author embeds the guide, so it follows the same rule.

## Scope in / Scope out
In: `clutch/tickets.py`. `_parse_ticket` accepts an optional third `## Time budget` bullet that starts `reason:` and still requires exactly the `expected` and `stuck` pair besides it. `lint_findings` adds three findings, each naming its paved road: `expected` over 60m (split into more tickets, each its own stem; never raise the budget instead), `stuck` not equal to twice `expected` (set `stuck` to twice `expected`), and `expected` over 30m up to 60m with no non-empty `reason:` bullet (split when possible, otherwise add `- reason: <why it is not split>`). A reason never excuses `expected` over 60m. The existing `stuck` must exceed `expected` parse finding and the `drain.max_ticket_minutes` ceiling stay as they are.
In: `clutch/docs/host-authoring.md`. Update only the `Time budget` bullet under `What each section is for`, and the lint-checks sentence in the Workflow step 2 list, to state the rule: over 30m split when possible or give the reason; over 60m always split, each part its own stem; `stuck` is twice `expected`; never raise the budget instead.
In: `tests/integration/test_lint_guide_parity.py`. Add pinned phrases for the 60m split rule, the twice-`expected` rule and the 30m `- reason:` rule. Keep the existing "`stuck` must exceed `expected`" pin if the rewritten guide bullet still contains that phrase, otherwise update the pin to the new wording.
In: `docs/how-clutch-works.md`. Update only the sentence next to the `drain.max_ticket_minutes` ceiling description to mention the budget limits.
In: existing tests whose fixture budgets the new rule refuses. In `tests/integration/test_lint_verb.py` and `tests/integration/test_drain.py`, change the budget numbers and the asserted message numbers, and add a `- reason: <text>` bullet where the new budget needs one, so the ceiling cases still trip the ceiling and every other case stays clean. For example, the drain ceiling case (stuck 200m) becomes `expected: 50m` / `stuck: 100m` / `- reason: ...` so it passes intake and still reaches the dispatch park; the lint-verb clean case (stuck 90m, must exit 0) becomes `expected: 45m` / `stuck: 90m` / `- reason: ...`. In `tests/harness/daemon_soak.py` and `tests/harness/reliability_battery.py`, change the `expected: 1m` / `stuck: 20m` pair to `expected: 10m` / `stuck: 20m`.
In: a new `tests/unit/test_ticket_budget_limits.py` using only `tmp_path`.
Out: the skeleton text in `clutch/tickets.py`, the Author and requisition prompt specs, journal handling, existing tickets under `tickets/`, `tests/unit/test_lint_guide_parity.py`, and any new config knob for the 30 and 60 limits.

## Scope fence
- clutch/tickets.py
- clutch/docs/host-authoring.md
- docs/how-clutch-works.md
- tests/unit/test_ticket_budget_limits.py
- tests/integration/test_lint_guide_parity.py
- tests/integration/test_lint_verb.py
- tests/integration/test_drain.py
- tests/harness/daemon_soak.py
- tests/harness/reliability_battery.py

## Acceptance criteria
1. `lint_findings` on a ticket with `expected: 61m` and `stuck: 122m` returns a finding whose paved road says to split into more tickets; it does not return `[]`, and a `- reason:` bullet does not clear it. Checked by `./dev.py test tests/unit/test_ticket_budget_limits.py`.
2. `lint_findings` on `expected: 60m`, `stuck: 120m` with a `- reason: one cohesive migration` bullet returns `[]`; the same ticket without the reason returns one finding, not `[]`. Checked by `./dev.py test tests/unit/test_ticket_budget_limits.py`.
3. `lint_findings` on `expected: 30m`, `stuck: 60m` returns `[]` with no reason; `expected: 31m`, `stuck: 62m` with no reason returns a finding. Checked by `./dev.py test tests/unit/test_ticket_budget_limits.py`.
4. `lint_findings` on `expected: 20m`, `stuck: 41m` returns a finding naming twice `expected`; `stuck: 40m` returns `[]`. Checked by `./dev.py test tests/unit/test_ticket_budget_limits.py`.
5. A ticket whose `- reason:` bullet is empty counts as having no reason, so `expected: 40m`, `stuck: 80m`, `- reason:` returns a finding, not `[]`. Checked by `./dev.py test tests/unit/test_ticket_budget_limits.py`.
6. Intake of a ticket with `expected: 90m` refuses it when open, but a ticket already journaled `merged` or `rejected` with the same budget is not refused, as with the evidence rule. Checked by `./dev.py test tests/unit/test_ticket_budget_limits.py`.
7. `clutch lint` on a stem whose `expected` is 61m exits 1 and prints the split road, not exit 0. Checked by `./dev.py test tests/integration/test_lint_verb.py`.
8. `clutch/docs/host-authoring.md` contains the phrases for the 60m split rule, the twice-`expected` rule and the 30m `- reason:` rule, and the guide parity pin fails if any of them is removed. Checked by `./dev.py test tests/integration/test_lint_guide_parity.py tests/unit/test_host_authoring.py`.
9. The existing time budget and ceiling tests still pass. Checked by `./dev.py test tests/integration/test_tickets.py tests/integration/test_drain.py tests/unit/test_ticket_lint_rules.py`.

## Verification
```
./dev.py test tests/unit/test_ticket_budget_limits.py tests/unit/test_ticket_lint_rules.py tests/integration/test_lint_guide_parity.py tests/unit/test_host_authoring.py tests/integration/test_lint_verb.py tests/integration/test_tickets.py tests/integration/test_drain.py
```

## Definition of rejected
The branch adds a config knob for the limits, raises or ignores a budget instead of refusing it, refuses settled or rejected tickets, or lets a reason excuse `expected` over 60m.

## Time budget
- expected: 25m
- stuck: 50m
