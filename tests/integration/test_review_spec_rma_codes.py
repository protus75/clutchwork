from pathlib import Path

import pytest
from pydantic import ValidationError

from clutch.artifacts import ReviewVerdict


def test_rma_spec_requires_ticket_codes_and_preserves_in_fence_defects():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/review.md").read_text()
    task = " ".join(text.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0].split())
    output = " ".join(text.split("## Output format\n", 1)[1].split("## On-failure\n", 1)[0].split())
    # The old wording allowed mixed codes; omitting the task rule drops fixable defects.
    assert "at least one finding coded `ticket`" not in text
    assert "every finding is coded `ticket`, and no other code is allowed in an `rma` reply" in output
    assert (
        "When an out-of-fence break and in-fence defects occur together, reply `rma` "
        "and code each in-fence defect `ticket` too, with its own `path`, `line`, `message` and `paved_road`; "
        "drop no finding. Use `rma` for in-fence defects only when an out-of-fence break is present."
    ) in task
    assert "Every finding is coded `ticket`; no other code is allowed in an `rma` reply." in task


def test_rma_validator_rejects_mixed_codes_and_accepts_ticket_findings():
    outside = {"code": "ticket", "path": "outside.py", "line": 3, "message": "break", "paved_road": "expand fence"}
    inside = {"code": "ticket", "path": "inside.py", "line": 5, "message": "defect", "paved_road": "fix it"}
    # A validator accepting any ticket among mixed codes would admit an invalid reply.
    with pytest.raises(ValidationError, match="every code `ticket`"):
        ReviewVerdict(verdict="rma", summary="Both defects", findings=[outside, {**inside, "code": "acceptance"}])
    # A validator rejecting multiple ticket findings would lose the in-fence defect.
    reply = ReviewVerdict(verdict="rma", summary="Both defects", findings=[outside, inside])
    assert [finding.path for finding in reply.findings] == ["outside.py", "inside.py"]
