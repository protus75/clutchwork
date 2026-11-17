import pytest
from pydantic import ValidationError

from clutch.artifacts import GraphPanel


@pytest.mark.parametrize("change", [{"extra": True}, {"approve": "yes"}, {"reason": "  "}])
def test_panel_is_closed_and_strict(change):
    raw = {"member": {"provider": "codex", "model": "x-high", "tier": "high"}, "approve": True, "reason": "sound"}
    raw.update(change)
    with pytest.raises(ValidationError):
        GraphPanel.model_validate(raw)


def test_report_accepts_absent_panel():
    from clutch.artifacts import ReviewBaselineReport
    from eval.harness import score

    rows = {tier: {"provider": "claude", "model": "c-max"} for tier in ("low", "medium", "high", "max")}
    identity = {surface: {"spec_major": 1, "rows": rows} for surface in ("review", "author")}
    scores = score([])
    raw = {
        "schema_version": 1,
        "complete": False,
        "cap_usd": 5.0,
        "spent_usd": 0.0,
        "results": [],
        "scores": scores,
        "author_graph": None,
        "verdict_signal": {
            "v": 1,
            "type": "signal",
            "ts": "2026-10-05T00:00:00+00:00",
            "ticket": None,
            "key": None,
            "body": {
                "signal": "review_baseline",
                "verdict": "NO_GO",
                "identity": identity,
                "exercised": {"surface": "review", "tier": "high", "effort": "high", "spec_version": "1.0"},
                "fixture_authors": [],
                "scores": scores,
            },
        },
    }
    assert ReviewBaselineReport.model_validate(raw).graph_panel is None
