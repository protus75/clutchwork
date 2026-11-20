"""Lint authoring rules against isolated ticket repositories."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Lint authoring rules against isolated ticket repositories.
# relates: [clutch/tickets.py]
# owner: clutch/tickets.py
# verified: 0a308920
# hash: 170099e77525b38dd821caab67efa70fcd6092dca7f9d500301b64740835d607

import pytest

from clutch import tickets

TEXT = """---
state: confirmed
source: human
priority: P2
kind: chore
---
## Depends on
none
## Context
- clutch/x.py
## Goal / Why
Change x.
## Boundary contract
none
- reason: unchanged behavior

## Scope in / Scope out
In: change x. Out: other work.
## Scope fence
- clutch/x.py
## Acceptance criteria
1. `x` changes.
## Verification
```
check x
```
## Definition of rejected
x stays the same.
## Time budget
- expected: 10m
- stuck: 20m
"""


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "clutch").mkdir()
    (tmp_path / "clutch/x.py").write_text("x = 1")
    return tmp_path


def lint(repo, text):
    return tickets.lint_findings(tickets.parse_ticket("example", text, repo), repo)


def test_spec_version_requires_pin(repo):
    text = TEXT.replace("In: change x.", "In: change version.").replace("- clutch/x.py\n## Acceptance", "- clutch/x.py\n- clutch/specs/author.md\n## Acceptance")
    [finding] = lint(repo, text)
    assert "spec" in finding.message and "pin" in finding.message
    assert lint(repo, text.replace("## Acceptance", "- tests/unit/test_specs.py\n## Acceptance")) == []
    for word in ("versions", "conversion"):
        assert lint(repo, text.replace("version", word)) == []


def test_named_document_requires_fence(repo):
    (repo / "docs").mkdir()
    (repo / "docs/guide.md").write_text("Guide")
    text = TEXT.replace("In: change x.", "In: update `docs/guide.md`.")
    [finding] = lint(repo, text)
    assert "docs/guide.md" in finding.message
    assert lint(repo, text.replace("## Acceptance", "- docs/guide.md\n## Acceptance")) == []
    assert lint(repo, text.replace("In: update `docs/guide.md`. Out: other work.", "In: change x. Out: `docs/guide.md`.")) == []
    assert lint(repo, text.replace("docs/guide.md", "docs/missing.md")) == []


def test_missing_dependency_is_refused(repo):
    with pytest.raises(tickets.TicketInvalid) as exc:
        tickets.parse_ticket("example", TEXT.replace("## Depends on\nnone", "## Depends on\n- missing-ticket"), repo)
    assert any("missing-ticket" in finding.message for finding in exc.value.findings)
