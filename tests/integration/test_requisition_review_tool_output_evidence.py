# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test requisition review tool output evidence
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 512e4a26
# hash: 22b2052bb95ab49ffb5c08bcc4e9861d1702aec30fd4a459bb2e7b1097223151
from pathlib import Path

from clutch.specs import load_spec, render


def test_tool_output_findings_require_scratch_run_evidence():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/requisition_review.md").read_text()
    spec = load_spec(text)
    rendered = render(spec, {name: f"fixture {name}" for name in spec.inputs})
    task = rendered.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0]
    bullet = next(line for line in task.splitlines() if "scratch copy" in line)
    # Each missing clause permits a distinct unsupported or overbroad finding.
    for phrase in (
        "For a finding whose claim depends on a formatter, linter, parser, or CLI output",
        "cite a run of that tool on a scratch copy outside the checkout, including the command and its result",
        "never run it in the shared checkout",
        "A prediction from reading the tool's source, or one that contradicts a run cited by the ticket, is never a snag",
        "If the tool cannot be run, put the doubt in `summary` and base the verdict on the other findings",
        "This requirement applies only to findings that depend on a tool's output",
    ):
        assert phrase in bullet
