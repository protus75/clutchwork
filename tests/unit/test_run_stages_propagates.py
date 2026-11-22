# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verifies run_stages re-raises a ProviderCallError from a stage without calling the driver's provider_failure handler
# relates: [clutch/providers.py, clutch/stages.py]
# owner: engine
# verified: df236100
# hash: 9d7ba052563d531612fa7068f59e14b48dbc70492fea5e825dcb36ead4bf6bbd
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from clutch import stages
from clutch.providers import ProviderCallError
from tests.git_fake import GitFake


@pytest.mark.asyncio
async def test_provider_error_from_stage_propagates(monkeypatch):
    error = ProviderCallError("codex", "quota exhausted", rc=1, stderr_tail="usage limit reached")
    driver = SimpleNamespace(journal=SimpleNamespace(read=Mock(return_value=[])), provider_failure=AsyncMock(), detector=None)
    ctx = stages.StageContext(
        repo=Path("/repo"),
        config=SimpleNamespace(worktree_root=Path("/worktrees")),
        env={},
        exec_=None,
        git=GitFake(rev_parse="ticket-sha"),
        fs=None,
        driver=driver,
        specs_dir=Path("/specs"),
    )
    ticket = SimpleNamespace(stem="example")
    monkeypatch.setattr(stages, "ticket_change_findings", AsyncMock(return_value=[]))
    monkeypatch.setattr(stages, "implement", AsyncMock(side_effect=error))

    with pytest.raises(ProviderCallError) as caught:
        await stages.run_stages(ctx, ticket)
    assert caught.value is error
    driver.provider_failure.assert_not_awaited()
