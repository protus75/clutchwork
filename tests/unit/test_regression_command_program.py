"""Regression programs must exist in the base worktree."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that ticket lint rejects a `## Regression` command whose program is missing from the base worktree (.venv/venv paths, uncarried scripts) and accepts programs on PATH and carried scripts or directories
# relates: [clutch/tickets.py, tests/unit/test_ticket_lint_rules.py]
# owner: engine
# verified: 19f68561
# hash: af3697d1139088da408b1702981a16ddef93c84f6aa63488a4ce09d74ec240ce

import pytest

from clutch import tickets
from tests.unit.test_ticket_lint_rules import TEXT, repo  # noqa: F401


@pytest.mark.parametrize("program", [".venv/bin/python", "venv/bin/python", "tests/regress_x.py_extra"])
def test_un_carried_program_is_rejected(repo, program):
    root, _ = repo
    text = TEXT.replace("./dev.py test tests/x.py", f"{program} tests/regress_x.py")
    [finding] = tickets.lint_findings(tickets.parse_ticket("example", text, root), root)
    assert finding.message == f"`## Regression` command runs {program}, which the base worktree does not have"
    assert finding.paved_road == "start the command with a program on PATH, such as `uv run python <carried reproducer>`"


@pytest.mark.parametrize("command", ["uv run python tests/regress_x.py", "python tests/regress_x.py", "tests/regress_x.py"])
def test_path_program_or_carried_script_is_allowed(repo, command):
    root, _ = repo
    text = TEXT.replace("./dev.py test tests/x.py", command)
    assert tickets.lint_findings(tickets.parse_ticket("example", text, root), root) == []


def test_carried_directory_contains_program(repo):
    root, _ = repo
    text = TEXT.replace("./dev.py test tests/x.py", "tests/scripts/repro.py")
    text = text.replace("tests/regress_x.py", "tests/scripts/")
    assert tickets.lint_findings(tickets.parse_ticket("example", text, root), root) == []
