import re
from pathlib import Path

from clutch.specs import lint_spec, load_spec

ROOT = Path(__file__).resolve().parents[2] / "clutch/specs"


def test_implement_omitted_choice_and_outcome_schema():
    text = (ROOT / "implement.md").read_text()
    body = load_spec(text).body
    premise = " ".join(body.split("- `premise_failed` --", 1)[1].split("- `incomplete` --", 1)[0].split())
    # Without this rule, implementation could invent the missing contract.
    assert "material contract choice" in premise and "omitted by the ticket" in premise
    assert "existing canonical owner" in premise and "name the omitted choice in a finding" in premise
    assert "never decide it during implementation" in premise
    output = " ".join(body.split("## Output format", 1)[1].split("## On-failure", 1)[0].split())
    # Dropping any outcome or allowing an empty premise finding changes the reply contract.
    assert '"ok" | "already_satisfied" | "premise_failed" | "incomplete"' in output
    assert "`premise_failed` carries at least one finding" in output


def test_review_boundary_conformity_and_codes():
    text = (ROOT / "review.md").read_text()
    assert lint_spec(text) == []
    body = load_spec(text).body
    task = " ".join(body.split("## Task", 1)[1].split("## Inputs", 1)[0].split())
    # The old review rules did not catch either undeclared boundaries or parallel owners.
    assert "Snag an undeclared boundary added by the diff" in task
    assert "check changed consumers against the declared owner" in task
    assert "Snag a second owner, parser, or registry" in task
    assert "a declared or existing canonical owner already provides" in task
    # A new code would change the review finding vocabulary.
    output = body.split("## Output format", 1)[1].split("## On-failure", 1)[0]
    codes = re.search(r'"code": (.*?),\s*"path"', output, re.S).group(1)
    assert re.findall(r'"([a-z]+)"', codes) == ["logic", "acceptance", "scope", "leak", "ticket"]
