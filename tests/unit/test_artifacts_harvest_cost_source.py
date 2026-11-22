# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that old Harvest records load with unknown cost-source fields and that harvest takes provider, model and estimate flags from the last LLM cost
# relates: [clutch/artifacts.py, clutch/config.py, clutch/redact.py, clutch/runner.py]
# owner: engine
# verified: bc0baafb
# hash: 78a5ca7d2dded4814dd626a37cf51bf08eb1ceadaf2a8f392522dd97bd4908e6
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import runner
from clutch.artifacts import Cost, Harvest, StageResult
from clutch.config import TrainingData
from clutch.redact import Redactor
from tests.git_fake import GitFake


def test_old_harvest_has_unknown_source():
    # Required fields or invented defaults would reject or mislabel old records.
    h = Harvest.model_validate(
        dict(attempt=2, stage="check", terminal="gate_failed", findings=[], reason="failed", diff_stat="x", stage_log_tail="y", events_tail="z", wall_seconds=2, usd=1, run_record=None)
    )
    assert (h.provider, h.model, h.usd_estimated, h.budget_capable) == (None, None, None, None)


@pytest.mark.parametrize(("provider", "estimated", "capable"), [("codex", True, False), ("claude", False, True)])
def test_harvest_last_llm_cost(tmp_path, monkeypatch, provider, estimated, capable):
    writes = []
    ctx = SimpleNamespace(
        config=SimpleNamespace(training_data=TrainingData(), state_dir=tmp_path / "state", providers=[SimpleNamespace(name="codex"), SimpleNamespace(name="claude")]),
        repo=tmp_path / "repo",
        worktree=lambda stem: tmp_path / stem,
        git=GitFake(diff_stat=AsyncMock(return_value="changed")),
        fs=SimpleNamespace(entries=lambda path: [], read_bytes=lambda path: b"", size=lambda path: 0, write=lambda path, data: writes.append(data)),
        driver=SimpleNamespace(redactor=Redactor({})),
    )
    monkeypatch.setattr(runner, "lift_outbox", AsyncMock())

    def result(cost):
        return StageResult(outcome="gate_failed", artifact=None, findings=[], cost=cost)

    results = (result(Cost(provider="qwen", model="old")), result(Cost(provider=provider, model="chosen-model", usd=1)), result(Cost()))
    asyncio.run(runner.harvest(ctx, "example", attempt=1, stage="check", terminal="gate_failed", findings=[], results=results))
    h = Harvest.model_validate_json(writes[0])
    # The last LLM cost, not the first or the final non-LLM cost, owns the flags.
    assert (h.provider, h.model, h.usd_estimated, h.budget_capable) == (provider, "chosen-model", estimated, capable)
