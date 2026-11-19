import re
from pathlib import Path

import pytest

from clutch.specs import SPEC_MAX_LINES, SPEC_SECTIONS, lint_spec, load_spec, render, validate_data_blocks

SPECS = Path(__file__).resolve().parents[2] / "clutch/specs"


@pytest.mark.parametrize("name", ["requisition_review", "review"])
def test_graphics_specs_load_and_render(name):
    text = (SPECS / f"{name}.md").read_text()
    assert lint_spec(text) == []
    spec = load_spec(text)
    assert tuple(line[3:] for line in spec.body.splitlines() if line.startswith("## ")) == SPEC_SECTIONS
    assert len(text.splitlines()) <= SPEC_MAX_LINES
    rendered = render(spec, {key: f"fixture for {key}" for key in spec.inputs})
    assert validate_data_blocks(rendered) == []


def test_requisition_graphics_snags():
    spec = load_spec((SPECS / "requisition_review.md").read_text())
    task = spec.body.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0]
    for phrase in (
        "snag a `visual:` criterion that cannot be decided from its named artifact alone",
        "`mode: generate` ticket with no `- input:` bullet and no prompt in `## Goal / Why`",
        "`review_visual` route that the ticket text or Context shows resolves to the same provider and model as the generator's `implement` route",
        "`visual:` criterion naming a declared artifact and a concrete visible outcome is not a hit",
    ):
        assert phrase in task


def test_review_graphics_artifact_snags():
    spec = load_spec((SPECS / "review.md").read_text())
    task = spec.body.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0]
    for phrase in (
        "judge the code, never the picture; the picture is `review_visual`'s to judge",
        "Check owns select provenance",
        "Snag as `acceptance`, attached to the changed line",
        "adds or changes a `cand-` candidate file",
        "image path that `## Render` does not declare as a `generate`-mode `- artifact:`",
    ):
        assert phrase in task
    assert re.findall(r"^- `([^`]+)`:", task, re.MULTILINE) == ["logic", "acceptance", "scope", "leak"]
