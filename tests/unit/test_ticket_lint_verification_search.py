"""Verification rejects direct search programs with ambiguous exit status."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that ticket lint rejects grep/rg-style search programs in Verification and points to a unit test as the fix, while allowing other commands.
# relates: [clutch/tickets.py, tests/unit/test_ticket_lint_rules.py]
# owner: engine
# verified: 6a14858a
# hash: 1ac9f6a9f0f8513cc60ed56fd0ac12fdd15fbb0a373852fefef15f53f8448867

import pytest

from clutch import tickets
from tests.unit.test_ticket_lint_rules import TEXT, repo  # noqa: F401


def findings_for(repo, command):
    root, _ = repo
    text = TEXT.replace("./dev.py test tests/x.py", "uv run python tests/regress_x.py")
    text = text.replace("## Verification\n```\n./dev.py test\n", f"## Verification\n```\n{command}\n")
    return tickets.lint_findings(tickets.parse_ticket("example", text, root), root)


@pytest.mark.parametrize("program", ["rg", "grep", "egrep", "fgrep", "ripgrep", "/usr/bin/grep"])
def test_search_program_is_rejected(repo, program):
    [finding] = findings_for(repo, f"{program} -r x .")
    assert program in finding.message
    assert "unit test" in finding.paved_road
    assert "positive or negative assertion" in finding.paved_road


@pytest.mark.parametrize("command", ["./dev.py test tests/x.py", "uv run python tests/regress_x.py", "rgx x ."])
def test_other_program_is_allowed(repo, command):
    assert findings_for(repo, command) == []
