# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test boundary contract required
# relates: [clutch/tickets.py]
# owner: clutch/tickets.py
# verified: 0a308920
# hash: c70d93697ff8d9f90459069b2669f372951598abbe838dfff7f51e65f98d8cc2
import pytest

from clutch.tickets import TicketInvalid, validate_ticket

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


def boundary_findings(tmp_path, text, *, settled=False):
    (tmp_path / "context.txt").write_text("context")
    try:
        validate_ticket("example", text, tmp_path, _settled=settled)
    except TicketInvalid as exc:
        return [finding for finding in exc.findings if "Boundary contract" in finding.message]
    return []


def test_missing_boundary_names_fix(tmp_path):
    findings = boundary_findings(tmp_path, BASE)
    assert len(findings) == 1
    assert "add a non-empty `## Boundary contract` section" in findings[0].paved_road


def test_settled_missing_boundary_is_exempt(tmp_path):
    assert boundary_findings(tmp_path, BASE, settled=True) == []


@pytest.mark.parametrize("state", ["merged", "rejected"])
def test_closed_state_missing_boundary_is_exempt(tmp_path, state):
    assert boundary_findings(tmp_path, BASE.replace("state: draft", f"state: {state}")) == []


def test_valid_boundary_has_no_finding(tmp_path):
    assert boundary_findings(tmp_path, BASE + "\n## Boundary contract\nnone\n- reason: unchanged behavior\n") == []


def test_malformed_boundary_retains_shape_finding(tmp_path):
    findings = boundary_findings(tmp_path, BASE + "\n## Boundary contract\nnone\n")
    assert len(findings) == 1
    assert "none needs a non-empty reason" in findings[0].message
