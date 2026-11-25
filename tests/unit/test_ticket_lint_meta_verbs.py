"""Ticket lint reserves meta header verbs for Check."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that ticket lint rejects `clutch meta check|refresh|fill` commands in Verification and acceptance criteria because Check owns meta headers, while still allowing prose mentions and `clutch meta --help`.
# relates: [clutch/tickets.py, tests/unit/test_ticket_lint_rules.py]
# owner: engine
# verified: b40a386d
# hash: 13c649c62bde9fcfc27fb46ed3195a5a2f6d3beed0157b5e0e1c7fe3dba7a3e8

import pytest

from clutch import tickets
from tests.unit.test_ticket_lint_rules import TEXT, repo  # noqa: F401


def findings_for(repo, command="./dev.py test tests/x.py", criterion="`./dev.py test` exits 0."):
    root, _ = repo
    text = TEXT.replace("./dev.py test tests/x.py", "uv run python tests/regress_x.py")
    text = text.replace("1. `./dev.py test` exits 0.", f"1. {criterion}")
    text = text.replace("## Verification\n```\n./dev.py test\n", f"## Verification\n```\n{command}\n")
    return tickets.lint_findings(tickets.parse_ticket("example", text, root), root)


@pytest.mark.parametrize("verb", ["check", "refresh", "fill"])
@pytest.mark.parametrize("prefix", ["", "uv run "])
def test_verification_rejects_meta_verbs(repo, verb, prefix):
    [finding] = findings_for(repo, prefix + "clutch meta " + verb)
    assert "meta " + verb in finding.message
    assert "Check owns meta headers" in finding.paved_road
    assert "Verification and criteria" in finding.paved_road


@pytest.mark.parametrize("verb", ["check", "refresh", "fill"])
def test_criterion_rejects_meta_command(repo, verb):
    command = "`" + "clutch meta " + verb + "`"
    [finding] = findings_for(repo, criterion=f"Run {command}.")
    assert "meta " + verb in finding.message


@pytest.mark.parametrize("criterion", ["The meta check verb works, verified by `./dev.py test`.", "Run `clutch meta --help`."])
def test_prose_and_help_are_allowed(repo, criterion):
    assert findings_for(repo, criterion=criterion) == []


def test_replacing_meta_command_clears_finding(repo):
    assert findings_for(repo, command="./dev.py test tests/x.py") == []
