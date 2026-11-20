# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test precondition rules
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 96e46658
# hash: 877ed43b7fea72954548b4e4541ced46e0b0169cfebfb138d575a0d66d410c26
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
        "Check every stated repo-state precondition against HEAD.",
        "If it does not hold and no `## Depends on` stem delivers it, raise a `snag` naming the precondition",
        "add a `## Depends on` edge to a ticket that delivers it",
        "fence the file and put the edit in Scope in",
        "A precondition delivered by a declared `## Depends on` is not a snag.",
        "For a `tickets/` path, use `## Depends on`, never fence the file for Implement to edit.",
        "When a listed sibling's Scope in changes an interface",
        "A path in `## Scope fence` or a `## Verification` command does not exist at the review commit",
    ],
)
def test_rendered_task_preserves_review_rules(rule):
    # Removing each rule permits the corresponding missed snag or destroys an existing check.
    assert rule in task_section()


@pytest.mark.parametrize(
    "rule",
    [
        "Never state a precondition that a person must perform outside the pipeline.",
        "add a `## Depends on` edge to a ticket that delivers it",
        "fence the file and put the edit in Scope in",
        "For a `tickets/` path, use `## Depends on`; Implement cannot edit ticket files.",
    ],
)
def test_depends_on_guide_rules(rule):
    # A rule elsewhere in the guide would leave the Depends on guidance incomplete.
    guide = (ROOT / "clutch/docs/host-authoring.md").read_text()
    section = guide.split("- `Depends on`:", 1)[1].split("- `Runs before`:", 1)[0]
    assert rule in " ".join(section.split())
