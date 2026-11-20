# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test harvest redaction
# relates: [clutch/artifacts.py, clutch/config.py, clutch/redact.py, clutch/runner.py]
# owner: engine
# verified: 0a308920
# hash: 5277de1fbc0665a3911624d7169dd4bb4a64b717ff06ca6f3d0391df19829efc
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from clutch import runner
from clutch.artifacts import Finding, Harvest
from clutch.config import TrainingData
from clutch.redact import Redactor

SECRET = "unique-secret-value"


def test_harvest_json_carries_no_configured_secret(monkeypatch):
    root = Path("/nonexistent-harvest-redaction-test")
    writes = []
    ctx = SimpleNamespace(
        config=SimpleNamespace(training_data=TrainingData(), state_dir=root / "state"),
        repo=root / "repo",
        worktree=lambda stem: root / "worktrees" / stem,
        git=SimpleNamespace(diff_stat=AsyncMock(return_value=f" clutch/{SECRET}.py | 1 +")),
        fs=SimpleNamespace(entries=lambda path: [], read_bytes=lambda path: b"", size=lambda path: 0, write=lambda path, data: writes.append((path, data))),
        driver=SimpleNamespace(redactor=Redactor({"FAKE_KEY": SECRET})),
    )
    lift = AsyncMock()
    monkeypatch.setattr(runner, "lift_outbox", lift)
    finding = Finding(code="scope_fence", path=f"clutch/{SECRET}.py", message=f"clutch/{SECRET}.py is outside the fence", paved_road="Revert the path")

    asyncio.run(runner.harvest(ctx, "example", attempt=0, stage="check", terminal="gate_failed", findings=[finding], results=()))

    assert len(writes) == 1
    path, data = writes[0]
    assert path == root / "worktrees/example/tickets/example/attempts/0/harvest.json"
    assert SECRET.encode() not in data
    artifact = Harvest.model_validate_json(data)
    assert "[REDACTED:FAKE_KEY]" in artifact.diff_stat
    assert "[REDACTED:FAKE_KEY]" in artifact.findings[0].path
    assert "[REDACTED:FAKE_KEY]" in artifact.findings[0].message
    assert artifact.findings[0].code == "scope_fence"
    assert artifact.terminal == "gate_failed"
    lift.assert_awaited_once_with(ctx, "example", "harvest", attempt=0, only="attempts/0/harvest.json")
