"""Changed-file checks compare against the merge base."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that ticket lint refuses git diff checks against main, main..HEAD or main HEAD in acceptance criteria and verification, and allows main...HEAD and other diff forms
# relates: [clutch/tickets.py]
# owner: clutch/tickets.py
# verified: 981eb002
# hash: 8e9451becca84d92ec8ac841a1d209372295438124b86ca275ef429654a84d46

import pytest

from clutch.tickets import Frontmatter, Ticket, lint_findings


@pytest.mark.parametrize("ref", ["main", "main..HEAD", "main HEAD"])
@pytest.mark.parametrize("section", ["Acceptance criteria", "Verification"])
def test_non_merge_base_diff_is_refused(tmp_path, section, ref):
    command = f"git diff --name-only {ref}"
    ticket = Ticket(
        stem="example",
        frontmatter=Frontmatter(state="confirmed", source="human", priority="P1", kind="chore"),
        sections={"Acceptance criteria": command if section == "Acceptance criteria" else "other", "Scope in / Scope out": ""},
        depends=(),
        context=(),
        on_demand=(),
        scope_fence=(),
        verification=(tuple(command.split()),) if section == "Verification" else (),
        expected_minutes=10,
        stuck_minutes=20,
    )
    [finding] = lint_findings(ticket, tmp_path)
    assert f"## {section}" in finding.message
    assert "main...HEAD" in finding.paved_road


@pytest.mark.parametrize("section", ["Acceptance criteria", "Verification"])
@pytest.mark.parametrize("command", ["git diff --name-only main...HEAD", "git diff --stat main", "git diff --name-only mainline"])
def test_other_diff_forms_are_allowed(tmp_path, section, command):
    ticket = Ticket(
        stem="example",
        frontmatter=Frontmatter(state="confirmed", source="human", priority="P1", kind="chore"),
        sections={"Acceptance criteria": command if section == "Acceptance criteria" else "other", "Scope in / Scope out": ""},
        depends=(),
        context=(),
        on_demand=(),
        scope_fence=(),
        verification=(tuple(command.split()),) if section == "Verification" else (),
        expected_minutes=10,
        stuck_minutes=20,
    )
    assert lint_findings(ticket, tmp_path) == []
