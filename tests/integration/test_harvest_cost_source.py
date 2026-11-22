# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that a failed-run harvest records the provider, model, cost and estimate/budget flags from the stage result, and that an orphan harvest leaves those fields null
# relates: [clutch/artifacts.py, clutch/config.py, clutch/redact.py, clutch/runner.py, clutch/seams.py, tests/integration/test_harvest_orphans.py]
# owner: engine
# verified: 10f08d74
# hash: 108001c318a74067a1268dcc0767a418fd928d8df16ed9ac08204f03af6fc099
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import runner
from clutch.artifacts import Cost, StageResult
from clutch.config import TrainingData
from clutch.redact import Redactor
from clutch.seams import LocalFileSystem
from tests.git_fake import GitFake
from tests.integration.test_harvest_orphans import invoke, orphan
from tests.integration.test_stages import STEM, agent, verdict
from tests.integration.test_terminal import repo  # noqa: F401


@pytest.mark.parametrize(("provider", "estimated", "capable"), [("codex", True, False), ("claude", False, True)])
def test_failed_harvest_writes_cost_source(tmp_path, monkeypatch, provider, estimated, capable):
    fs = LocalFileSystem()
    ctx = SimpleNamespace(
        config=SimpleNamespace(training_data=TrainingData(), state_dir=tmp_path / "state", providers=[SimpleNamespace(name=provider)]),
        repo=tmp_path,
        worktree=lambda stem: tmp_path / "worktree",
        git=GitFake(diff_stat="changed"),
        fs=fs,
        driver=SimpleNamespace(redactor=Redactor({})),
    )
    monkeypatch.setattr(runner, "lift_outbox", AsyncMock())
    result = StageResult(outcome="gate_failed", artifact=None, findings=[], cost=Cost(provider=provider, model="seam-model", usd=1.0))
    asyncio.run(runner.harvest(ctx, "example", attempt=3, stage="check", terminal="gate_failed", findings=[], results=(result,)))
    data = json.loads((tmp_path / "worktree/tickets/example/attempts/3/harvest.json").read_text())
    # Opposite flags, missing source, or a changed cost all differ here.
    assert (data["provider"], data["model"], data["usd_estimated"], data["budget_capable"], data["usd"]) == (provider, "seam-model", estimated, capable, 1.0)


def test_orphan_has_no_invented_source(repo):
    orphan(repo)
    invoke(repo, [agent({"clutch/thing.py": "ok\n"}), verdict()])
    data = json.loads((repo / "tickets" / STEM / "attempts/0/harvest.json").read_text())
    # Guessing a configured provider or either flag changes this record.
    assert (data["provider"], data["model"], data["usd_estimated"], data["budget_capable"]) == (None, None, None, None)
