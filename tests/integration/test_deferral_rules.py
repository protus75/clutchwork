# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the rendered requisition_review spec Task raises a deferred-to-person snag and states its paved road
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 4a118128
# hash: 476753f6e8a80650c5a7a309dbaf5a245911982b8091bf97aa0fbb38cbaf1451
from pathlib import Path

import pytest

from clutch.specs import load_spec, render

ROOT = Path(__file__).resolve().parents[2]


def task_section():
    spec = load_spec((ROOT / "clutch/specs/requisition_review.md").read_text())
    rendered = render(spec, {name: "fixture" for name in spec.inputs})
    return " ".join(rendered.split("## Task", 1)[1].split("## Inputs", 1)[0].split())


@pytest.mark.parametrize(
    "rule",
    [
        "A ticket that leaves work to an operator, owner, user, or person, or to a later setup step, and names no existing ticket stem in backticks or fenced follow-up roadmap row that delivers it: raise a `snag` with code `deferred-to-person`.",
        "Paved road: name the delivering ticket stem in backticks, add a fenced follow-up roadmap row, or fence the file and put the edit in Scope in.",
    ],
)
def test_rendered_task_rejects_person_deferrals(rule):
    # Omitting either the snag or its paved road leaves the review rule incomplete.
    assert rule in task_section()
