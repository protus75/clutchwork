from pathlib import Path

import pytest

from clutch.tickets import Ticket, TicketInvalid, _intake_plan_stem, validate_ticket

BASE = """---
state: draft
source: human
priority: P1
kind: feature
---
## Depends on
none
## Context
- context.txt
## Goal / Why
A change.
## Scope in / Scope out
In: parser. Out: other things.
## Scope fence
- parser.py
## Acceptance criteria
1. `check` passes.
## Verification
```
check
```
## Definition of rejected
Failure.
## Time budget
- expected: 10m
- stuck: 20m
"""
ENTRY = """### parser
- disposition: extend
- owner: parser.py
- consumers: intake
- observable change: new section
- compatibility: old tickets remain valid
- acceptance: valid shapes parse
- tests: parser tests
- post-merge source of truth: parser.py
"""


def check(root: Path, section: str | None, *, settled=False):
    (root / "context.txt").write_text("context")
    text = BASE + ("\n## Boundary contract\n" + section if section is not None else "")
    try:
        validate_ticket("example", text, root, _settled=settled)
    except TicketInvalid as exc:
        return [f for f in exc.findings if "Boundary contract" in f.message]
    return []


@pytest.mark.parametrize(
    "section",
    [None, "none\n- reason: unchanged behavior", ENTRY, ENTRY.replace("extend", "reuse"), ENTRY.replace("extend", "create") + "- closest existing: old.py\n- earning reason: multiple consumers\n"],
)
def test_valid_shapes(tmp_path, section):
    assert check(tmp_path, section) == []


@pytest.mark.parametrize(
    "section",
    [
        "garbage",
        "none",
        "none\n- reason:",
        ENTRY.replace("extend", "maybe"),
        ENTRY.replace("extend", "create"),
        ENTRY.replace("extend", "create") + "- closest existing: old.py\n",
        ENTRY.replace("extend", "create") + "- earning reason: multiple consumers\n",
    ],
)
def test_invalid_shapes_name_a_repair(tmp_path, section):
    findings = check(tmp_path, section)
    assert findings and all(f.paved_road for f in findings)


def test_missing_owner_names_field(tmp_path):
    findings = check(tmp_path, ENTRY.replace("- owner: parser.py\n", ""))
    assert any("owner" in f.message and "owner" in f.paved_road for f in findings)


@pytest.mark.parametrize("state", ["merged", "already_satisfied", "rejected"])
def test_settled_exemption(tmp_path, state):
    (tmp_path / "context.txt").write_text("context")
    path = tmp_path / "tickets/example/ticket.md"
    path.parent.mkdir(parents=True)
    path.write_text(BASE + "\n## Boundary contract\nmalformed\n")
    _, _, settled = _intake_plan_stem(tmp_path, "example", False, [], state)
    _, _, draft = _intake_plan_stem(tmp_path, "example", False, [], None)
    assert isinstance(settled, Ticket)
    assert isinstance(draft, list) and any("Boundary contract" in f.message for f in draft)
