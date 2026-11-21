# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Review panel propagates dropped member findings
# relates: [clutch/artifacts.py, clutch/driver.py, clutch/panel.py, clutch/stages.py, tests/unit/test_review_panel_use.py]
# owner: engine
# verified: 21d6599d
# hash: 75ee4cdd801c9741b046e15484309af6fbaeeb873c6430e7bd17848e2bcd2127
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import stages
from clutch.artifacts import Cost, Finding, StageResult
from clutch.driver import Driver, PanelResult
from clutch.panel import DroppedMember
from tests.unit.test_review_panel_use import Recording, setup  # noqa: F401


def finding(code):
    return Finding(code=code, path="review.py", line=7, message="provider failed", paved_road="retry later")


@pytest.mark.asyncio
async def test_panel_collects_dropped_findings_in_member_order():
    quota, other = finding("quota_exhausted"), finding("other_failure")
    driver = SimpleNamespace(
        clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
        run=AsyncMock(side_effect=[StageResult("infra_error", None, [quota], Cost()), StageResult("infra_error", None, [other], Cost())]),
    )
    panel = await Driver.run_panel(driver, None, None, size=2, ticket="item", attempt=1, workspace=Path("/repo"), tier="medium", effort="low", stuck_budget=60, expected_budget=30, scope_fence=())
    assert panel.dropped_findings == [quota, other]


@pytest.mark.asyncio
async def test_all_dropped_review_propagates_quota_and_preserves_empty_default(setup):
    ticket, build = setup
    quota = finding("quota_exhausted")
    dropped = [DroppedMember(index=0, failure_class="infra_error"), DroppedMember(index=1, failure_class="infra_error")]
    result = await stages.review(build(Recording(panel=PanelResult([], dropped, [quota])), 2), ticket, None, attempt=1)
    assert any(f.code == "quota_exhausted" for f in result.findings)
    assert result == StageResult("infra_error", None, [quota], Cost())
    empty = await stages.review(build(Recording(panel=PanelResult([], dropped)), 2), ticket, None, attempt=1)
    assert empty == StageResult("infra_error", None, [], Cost())
