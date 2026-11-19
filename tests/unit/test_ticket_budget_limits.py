"""Budget admission rules at their boundaries."""

import pytest

from clutch import tickets

TEXT = """---
state: confirmed
source: human
priority: P1
kind: feature
---
## Depends on
none
## Context
- source.py
## Goal / Why
Build the feature.
## Boundary contract
none
- reason: unchanged behavior

## Scope in / Scope out
In: source. Out: other files.
## Scope fence
- source.py
## Acceptance criteria
1. `check` succeeds.
## Verification
```
check
```
## Definition of rejected
The feature is absent.
## Time budget
- expected: {expected}m
- stuck: {stuck}m
{reason}
"""


def make(tmp_path, expected, stuck, reason=""):
    (tmp_path / "source.py").write_text("value = 1\n")
    return TEXT.format(expected=expected, stuck=stuck, reason=reason)


@pytest.mark.parametrize("reason", ["", "- reason: cohesive migration"])
def test_over_60_always_splits(tmp_path, reason):
    ticket = tickets.parse_ticket("example", make(tmp_path, 61, 122, reason), tmp_path)
    findings = tickets.lint_findings(ticket, tmp_path)
    assert len(findings) == 1
    assert "split into more tickets" in findings[0].paved_road


@pytest.mark.parametrize(
    "expected,stuck,reason,road",
    [
        (60, 120, "- reason: one cohesive migration", None),
        (60, 120, "", "reason"),
        (30, 60, "", None),
        (31, 62, "", "reason"),
        (40, 80, "- reason:", "reason"),
        (20, 41, "", "twice `expected`"),
        (20, 40, "", None),
    ],
)
def test_budget_boundaries(tmp_path, expected, stuck, reason, road):
    ticket = tickets.parse_ticket("example", make(tmp_path, expected, stuck, reason), tmp_path)
    findings = tickets.lint_findings(ticket, tmp_path)
    assert len(findings) == (1 if road else 0)
    if road:
        assert road in findings[0].paved_road


@pytest.mark.parametrize("state,refused", [(None, True), ("merged", False), ("rejected", False)])
def test_intake_exempts_settled(tmp_path, state, refused):
    path = tmp_path / "tickets/example/ticket.md"
    path.parent.mkdir(parents=True)
    path.write_text(make(tmp_path, 90, 180))
    _, _, result = tickets._intake_plan_stem(tmp_path, "example", False, [], state)
    assert isinstance(result, list) == refused
    if refused:
        assert "split into more tickets" in result[0].paved_road
