# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the Implement spec task omits Check-owned full runs and keeps Verification and base-commit handoff rules
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 9be395f4
# hash: 01f448f922fe3644d2447cbc999b7e0867e772cf95e1d62311f5cae789bd5187
from pathlib import Path

import pytest

from clutch.specs import load_spec, render


@pytest.mark.parametrize(
    "obsolete",
    ["Run each hard always-trigger host Check entry", "hard coverage gate", "one further full run"],
)
def test_implement_task_omits_check_runs(obsolete):
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/implement.md").read_text()
    spec = load_spec(text)
    task = render(spec, {name: "fixture" for name in spec.inputs}).split("## Task\n", 1)[1].split("## Inputs\n", 1)[0]
    # Reintroducing each obsolete requirement must fail.
    assert obsolete not in task


@pytest.mark.parametrize(
    "required",
    [
        "Run lint and format only on the files the diff changes, and leave the full suites, coverage gates and base comparisons to Check, whose failures come back as retry findings.",
        "Run every `## Verification` command yourself as a whole command",
        "When a `## Verification` command still fails after your work, rerun the ticket's `## Verification` command exactly as written once in a base-commit git worktree",
        "Never label a failure base-red without running it on the base commit.",
    ],
)
def test_implement_task_preserves_verification_and_handoff(required):
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/implement.md").read_text()
    spec = load_spec(text)
    task = " ".join(render(spec, {name: "fixture" for name in spec.inputs}).split("## Task\n", 1)[1].split("## Inputs\n", 1)[0].split())
    # Removing each requirement would permit skipping its corresponding obligation.
    assert required in task
